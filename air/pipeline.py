"""研究流水线编排器。

结构由确定性代码持有，LLM 只在阶段内部干活（Stripe 模式：确定性 gate 与
LLM 步骤交替咬合）。每个阶段的输出是磁盘上的 checkpoint JSON——中断后
`--resume` 从断点继续（agent 会忘，磁盘不会）；预算是硬顶，超了立即停，
checkpoint 保证已花的钱不作废。

阶段图：
  scope → bom(逐系统 fan-out) → bottleneck(逐系统) → companies(逐 P0/P1)
  → cards(逐核心标的) → cycle → render v1 → 确定性完整性校验
  → 4 专家对抗评审(fresh) → 补丁修复轮 → 复审 → 终稿三件套
"""

from __future__ import annotations

import importlib.resources
import json
import time
from datetime import date
from pathlib import Path

from . import agent, assemble, schemas
from .reviewers import REVIEWERS

MAX_BOTTLENECKS_MAPPED = 10   # 只对 P0/P1 前 N 个做公司映射（超出记录，不静默丢弃）
MAX_CARDS = 12                # 核心个股卡片上限（龙头+业绩优先，黑马精选）


class BudgetExceeded(Exception):
    pass


def _prompt(name: str) -> str:
    return (importlib.resources.files("air") / "prompts" / f"{name}.md").read_text()


class Pipeline:
    def __init__(self, topic: str, workdir: Path, budget_usd: float = 15.0,
                 model_fanout: str = "sonnet", model_review: str = "opus"):
        self.topic = topic
        self.workdir = workdir
        self.budget = budget_usd
        self.m_fan = model_fanout
        self.m_rev = model_review
        self.spent = 0.0
        self.discipline = _prompt("discipline")
        self.run_dir: Path | None = None  # scope 之后确定（按 slug）

    # —— 基础设施 ——
    def _log(self, msg: str) -> None:
        print(f"[air] {msg}（累计 ${self.spent:.2f}）", flush=True)

    def _ledger(self, stage: str, cost: float) -> None:
        self.spent += cost
        if self.run_dir:
            with open(self.run_dir / "ledger.jsonl", "a") as f:
                f.write(json.dumps({"stage": stage, "cost_usd": round(cost, 4),
                                    "at": time.strftime("%F %T")}) + "\n")
        if self.spent >= self.budget:
            raise BudgetExceeded(
                f"预算 ${self.budget} 已用尽（${self.spent:.2f}）。"
                f"checkpoint 已落盘，追加预算后 --resume 继续。")

    def _call(self, stage: str, prompt: str, schema: dict, *, model: str | None = None,
              budget: float = 1.5, timeout: int = 1200, search: bool = True,
              retries: int = 1):
        for attempt in range(retries + 1):
            r = agent.run(prompt, system=self.discipline, schema=schema,
                          model=model or self.m_fan, budget_usd=budget,
                          timeout_s=timeout, search=search)
            self._ledger(stage, r.cost_usd)
            if r.ok:
                return r.data
            self._log(f"⚠️ {stage} 失败: {r.error}" + ("，重试" if attempt < retries else ""))
        raise RuntimeError(f"{stage} 在 {retries + 1} 次尝试后仍失败")

    def _ck_path(self, name: str) -> Path:
        return self.run_dir / f"{name}.json"

    def _ck(self, name: str, producer):
        """checkpoint：存在即复用（断点续跑），否则执行并落盘。"""
        p = self._ck_path(name)
        if p.exists():
            self._log(f"⏭  {name}: 使用已有 checkpoint")
            return json.loads(p.read_text())
        data = producer()
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        self._log(f"✅ {name}: 完成并落盘")
        return data

    # —— 阶段实现 ——
    def stage_scope(self) -> dict:
        return self._call("scope", _prompt("scope").format(topic=self.topic),
                          schemas.SCOPE, budget=1.0)

    def stage_bom(self, scope: dict) -> list[dict]:
        ctx = json.dumps({"boundary": scope["boundary"], "demand": scope["demand_l0"]},
                         ensure_ascii=False)
        out = []
        for sys_ in scope["l1_systems"]:
            name = sys_["name"]
            out.append(self._ck(f"02-bom-{assemble.slugify(name)}", lambda n=name: self._call(
                f"bom:{n}", _prompt("bom").format(
                    industry=scope["industry_name"], system=n, context=ctx),
                schemas.BOM_TREE, budget=2.0)))
        return out

    def stage_bottleneck(self, scope: dict, boms: list[dict]) -> list[dict]:
        out = []
        for bom in boms:
            atoms = [{"atom": a["name"], "notes": a.get("notes", ""),
                      "system": bom["system"]}
                     for l2 in bom["l2_items"] for a in l2["l3_atoms"]]
            out.append(self._ck(f"03-bn-{assemble.slugify(bom['system'])}",
                                lambda ats=atoms: self._call(
                f"bottleneck:{bom['system']}", _prompt("bottleneck").format(
                    industry=scope["industry_name"],
                    atoms=json.dumps(ats, ensure_ascii=False)),
                schemas.BOTTLENECK, budget=2.0)))
        return out

    def _ranked_bottlenecks(self, bns: list[dict]) -> list[dict]:
        items = [i for b in bns for i in b["items"]]
        items.sort(key=lambda i: (i["priority"], -sum(i["scores"].values())))
        return items

    def stage_companies(self, scope: dict, bns: list[dict]) -> list[dict]:
        ranked = [i for i in self._ranked_bottlenecks(bns) if i["priority"] in ("P0", "P1")]
        mapped, dropped = ranked[:MAX_BOTTLENECKS_MAPPED], ranked[MAX_BOTTLENECKS_MAPPED:]
        if dropped:
            self._log(f"ℹ️ P0/P1 共 {len(ranked)} 个，映射前 {len(mapped)} 个；"
                      f"未映射: {', '.join(d['atom'] for d in dropped)}")
        out = []
        for it in mapped:
            out.append(self._ck(f"04-co-{assemble.slugify(it['atom'])}",
                                lambda i=it: self._call(
                f"companies:{i['atom']}", _prompt("companies").format(
                    industry=scope["industry_name"], bottleneck=i["atom"],
                    rationale=i["rationale"]),
                schemas.COMPANY_MAP, budget=2.5)))
        return out

    def _core_stocks(self, maps: list[dict]) -> list[dict]:
        """核心标的去重收集：龙头+业绩全收，黑马按序补足到上限。"""
        seen, core = set(), []
        for layer in ("a_leaders", "a_earnings", "a_darkhorse"):
            for m in maps:
                for c in m[layer]:
                    key = c["ticker"] or c["name"]
                    if key in seen or len(core) >= MAX_CARDS:
                        continue
                    seen.add(key)
                    core.append({"name": c["name"], "ticker": c["ticker"],
                                 "layer": layer, "bottleneck": m["bottleneck"]})
        return core

    def stage_cards(self, scope: dict, maps: list[dict]) -> list[dict]:
        out = []
        for s in self._core_stocks(maps):
            out.append(self._ck(f"05-card-{assemble.slugify(s['ticker'] or s['name'])}",
                                lambda st=s: self._call(
                f"card:{st['name']}", _prompt("stock_card").format(
                    industry=scope["industry_name"], **st),
                schemas.STOCK_CARD, budget=2.0)))
        return out

    def stage_cycle(self, scope: dict, bns: list[dict]) -> dict:
        ctx = json.dumps([{"atom": i["atom"], "priority": i["priority"],
                           "rationale": i["rationale"][:100]}
                          for i in self._ranked_bottlenecks(bns)[:15]], ensure_ascii=False)
        return self._call("cycle", _prompt("cycle").format(
            industry=scope["industry_name"], context=ctx), schemas.CYCLE, budget=2.0)

    def stage_review(self, report: str, only: list[str] | None = None) -> dict[str, dict]:
        """四类专家对抗评审，各自 fresh 会话。only 限定复审的专家。"""
        results = {}
        for key, spec in REVIEWERS.items():
            if only and key not in only:
                continue
            results[key] = self._call(
                f"review:{key}", _prompt("review").format(
                    role=spec["role"], lens=spec["lens"], report=report[:60000]),
                schemas.REVIEW, model=self.m_rev, budget=2.5)
        return results

    PATCH_SCHEMA = {
        "type": "object",
        "properties": {
            "corrections": {"type": "array", "items": {"type": "object", "properties": {
                "target": {"type": "string", "description": "修正落点：章节/公司/瓶颈名"},
                "content": {"type": "string", "description": "修正后的完整表述（含证据或待核验标注）"},
            }, "required": ["target", "content"]}},
            "unresolved": {"type": "array", "items": {"type": "string"},
                           "description": "本轮无法修复、留给下一轮人工核验的事项"},
        },
        "required": ["corrections", "unresolved"],
    }

    def stage_repair(self, gaps: list[dict], report: str) -> dict:
        prompt = (f"以下是四类专家对一份「{self.topic}」产业研报的 P0/P1 级缺口清单。\n"
                  f"逐条处理：能用检索核实并修正的，产出修正内容（写明证据或标注待核验）；"
                  f"无法在线核实的进 unresolved。\n\n缺口：\n"
                  f"{json.dumps(gaps, ensure_ascii=False, indent=1)}\n\n"
                  f"报告相关上下文：\n{report[:40000]}")
        return self._call("repair", prompt, self.PATCH_SCHEMA, model=self.m_rev, budget=3.0)

    # —— 主流程 ——
    def run(self) -> Path:
        # scope 决定 slug/run_dir，因此先跑再落盘（resume 时以旧 checkpoint 为准）
        r = agent.run(_prompt("scope").format(topic=self.topic), system=self.discipline,
                      schema=schemas.SCOPE, model=self.m_fan, budget_usd=1.0)
        if not r.ok:
            raise RuntimeError(f"scope 失败: {r.error}")
        scope = r.data
        self.run_dir = self.workdir / scope["slug"]
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if self._ck_path("01-scope").exists():
            scope = json.loads(self._ck_path("01-scope").read_text())
        else:
            self._ck_path("01-scope").write_text(json.dumps(scope, ensure_ascii=False, indent=2))
        self._ledger("scope", r.cost_usd)
        self._log(f"研究对象: {scope['industry_name']}（{scope['slug']}），预算 ${self.budget}")

        boms = self.stage_bom(scope)
        bns = self.stage_bottleneck(scope, boms)
        maps = self.stage_companies(scope, bns)
        cards = self.stage_cards(scope, maps)
        cycle = self._ck("06-cycle", lambda: self.stage_cycle(scope, bns))

        # 装配 v1 + 确定性完整性校验（机械化强制，先于 LLM 评审）
        issues = assemble.validate(scope, boms, bns, maps, cards)
        if issues:
            self._log(f"⚠️ 完整性校验发现 {len(issues)} 处问题（将列入迭代清单并供评审参考）")
        report_v1 = assemble.render(self.topic, scope, boms, bns, maps, cards, cycle,
                                    reviews=None, issues=issues, spent=self.spent)

        # 对抗评审 → 修复 → 复审
        reviews = self._ck("07-review", lambda: self.stage_review(report_v1))
        hard_gaps = [g for rv in reviews.values() for g in rv["gaps"]
                     if g["severity"] in ("P0", "P1")]
        patch = None
        if hard_gaps:
            self._log(f"评审发现 {len(hard_gaps)} 个 P0/P1 缺口，进入修复轮")
            patch = self._ck("08-repair", lambda: self.stage_repair(hard_gaps, report_v1))
            failed = [k for k, rv in reviews.items() if rv["verdict"] == "FAIL"]
            report_v2 = assemble.render(self.topic, scope, boms, bns, maps, cards, cycle,
                                        reviews=reviews, issues=issues, patch=patch,
                                        spent=self.spent)
            reviews2 = self._ck("09-review2", lambda: self.stage_review(report_v2, only=failed))
            reviews.update(reviews2)

        # 终稿三件套
        final = assemble.render(self.topic, scope, boms, bns, maps, cards, cycle,
                                reviews=reviews, issues=issues, patch=patch, spent=self.spent)
        (self.run_dir / "report.md").write_text(final)
        (self.run_dir / "canvas.md").write_text(
            assemble.render_canvas(scope, boms, bns, maps))
        (self.run_dir / "ppt.md").write_text(
            assemble.render_ppt(scope, bns, cards, cycle, self._ranked_bottlenecks(bns)))
        self._log(f"🎉 三件套已生成: {self.run_dir}")
        return self.run_dir

    # —— 增量更新（把新事件放回框架）——
    UPDATE_SCHEMA = {
        "type": "object",
        "properties": {
            "event_summary": {"type": "string"},
            "affected_boms": {"type": "array", "items": {"type": "string"}},
            "impact_type": {"type": "string",
                            "description": "影响需求/价格/订单/产能/成本/认证中的哪个"},
            "affected_companies": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string"}, "direction": {"type": "string", "enum": ["利好", "利空", "中性"]},
                "chain": {"type": "string", "description": "传导链条"},
            }, "required": ["name", "direction", "chain"]}},
            "horizon": {"type": "string", "enum": ["短期交易催化", "中长期业绩逻辑", "噪音"]},
            "priced_in": {"type": "string"},
            "verdict": {"type": "string", "description": "是否改变原有 P0/P1 排序或标的分层的判断"},
        },
        "required": ["event_summary", "affected_boms", "impact_type",
                     "affected_companies", "horizon", "verdict"],
    }

    def update(self, slug: str, news: str) -> Path:
        self.run_dir = self.workdir / slug
        if not (self.run_dir / "01-scope.json").exists():
            raise RuntimeError(f"没有找到研究库 {slug}（先跑全量研究）")
        scope = json.loads((self.run_dir / "01-scope.json").read_text())
        bns = [json.loads(p.read_text()) for p in sorted(self.run_dir.glob("03-bn-*.json"))]
        ctx = json.dumps([{"atom": i["atom"], "priority": i["priority"]}
                          for i in self._ranked_bottlenecks(bns)], ensure_ascii=False)
        data = self._call("update", (
            f"产业「{scope['industry_name']}」出现新事件，把它翻译成产业链和财务语言，"
            f"放回已有研究框架判断影响。\n\n事件：{news}\n\n"
            f"已有瓶颈排序：{ctx}\n\n用搜索核实事件细节。"), self.UPDATE_SCHEMA, budget=2.0)
        out = self.run_dir / f"update-{date.today():%Y%m%d}.md"
        out.write_text(assemble.render_update(news, data))
        self._log(f"增量更新已写入 {out}")
        return out
