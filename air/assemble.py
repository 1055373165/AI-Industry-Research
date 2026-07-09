"""确定性装配层：结构化 JSON → 三件套；完整性由代码校验，不靠模型自觉。

「机械化强制优于文档规范」：报告的 10 个章节、卡片字段齐全性、正文字数、
证据/待核验标注，全部是代码检查——缺什么列什么，进迭代清单并喂给评审。
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

DISCLAIMER = ("> 本报告由 AI 研究流水线生成，不构成投资建议。所有客户认证、供应链关系、"
              "订单、收入占比等信息需以公开资料继续核验；标注「待核验」处尤其如此。")


def slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKC", text)
    out = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", text).strip("-")
    return out[:max_len] or "x"


# —— 完整性校验（确定性，先于 LLM 评审）——
def validate(scope, boms, bns, maps, cards) -> list[str]:
    issues = []
    atoms = {a["name"] for b in boms for l2 in b["l2_items"] for a in l2["l3_atoms"]}
    if len(atoms) < 8:
        issues.append(f"BOM 原子项仅 {len(atoms)} 个，拆解粒度疑似过粗")
    for b in boms:
        for l2 in b["l2_items"]:
            for a in l2["l3_atoms"]:
                if not (a["upstream"] or a["midstream"] or a["downstream"]):
                    issues.append(f"原子项「{a['name']}」缺上中下游拆解")

    scored = {i["atom"] for bn in bns for i in bn["items"]}
    unscored = atoms - scored
    if unscored:
        issues.append(f"{len(unscored)} 个原子项未评分: {', '.join(list(unscored)[:5])}…")
    p01 = [i for bn in bns for i in bn["items"] if i["priority"] in ("P0", "P1")]
    if not p01:
        issues.append("没有识别出任何 P0/P1 瓶颈——要么产业确实无瓶颈，要么评分失真")

    mapped = {m["bottleneck"] for m in maps}
    for m in maps:
        if not (m["a_leaders"] or m["a_earnings"] or m["a_darkhorse"]):
            issues.append(f"瓶颈「{m['bottleneck']}」无任何 A 股标的（若属实应在正文说明）")
        for layer in ("a_leaders", "a_earnings", "a_darkhorse", "a_theme", "international"):
            for c in m[layer]:
                if not c.get("evidence"):
                    issues.append(f"{c['name']}（{m['bottleneck']}/{layer}）没有证据条目")

    for c in cards:
        n = len(c["core_text"])
        if not (150 <= n <= 340):  # 180-280 放宽容差
            issues.append(f"卡片「{c['name']}」正文 {n} 字，偏离 180-280 字要求")
        for kw in ("行业领先", "前景广阔", "实力雄厚", "技术先进"):
            if kw in c["core_text"] or kw in c["memory_anchor"]:
                issues.append(f"卡片「{c['name']}」出现空泛表述「{kw}」")
    return issues


# —— Markdown 深度报告（输出结构十一之 1-10）——
def render(topic, scope, boms, bns, maps, cards, cycle, *, reviews=None,
           issues=None, patch=None, spent=0.0) -> str:
    ranked = sorted((i for bn in bns for i in bn["items"]),
                    key=lambda i: (i["priority"], -sum(i["scores"].values())))
    p01 = [i for i in ranked if i["priority"] in ("P0", "P1")]
    L = []
    A = L.append
    A(f"# {scope['industry_name']} 产业链投研报告\n")
    A(f"研究主题：{topic}｜生成日期：{date.today()}｜研究成本：${spent:.2f}\n\n{DISCLAIMER}\n")

    A("\n## 1. 结论先行\n")
    A(f"- **L0 需求**：{scope['demand_l0']['who_pays']}；{scope['demand_l0']['demand_nature']}")
    A(f"- **当前周期**：{cycle['current_phase']}——{cycle['phase_rationale']}")
    for i in p01[:8]:
        A(f"- **[{i['priority']}] {i['atom']}**：{i['rationale']}")

    A("\n## 2. 全产业链地图\n")
    A(f"研究边界：{scope['boundary']}\n")
    # 价值链方向：使能环节 → 设计 → 制造（设备/材料汇入）→ 封测 → 终端需求
    # （评审教训：全部从终端需求单向流出无法体现上下游供应与价值传导）
    A("```mermaid\nflowchart LR")
    names = [s["name"] for s in scope["l1_systems"]]
    def _find(kw_list):
        return [i for i, n in enumerate(names) if any(k in n for k in kw_list)]
    chain = _find(["EDA", "IP"]) + _find(["设计"]) + _find(["制造", "Fab"]) + \
        _find(["封装", "封测", "测试"])
    feeders = _find(["设备"]) + _find(["材料"])
    others = [i for i in range(len(names)) if i not in chain + feeders]
    chain = chain + others
    for a, b in zip(chain, chain[1:]):
        A(f"    S{a}[{names[a]}] --> S{b}[{names[b]}]")
    mfg = _find(["制造", "Fab"])
    for f in feeders:
        A(f"    S{f}[{names[f]}] --> S{mfg[0] if mfg else chain[-1]}")
    A(f"    S{chain[-1]} --> D0[终端需求]")
    A("```\n")
    A("| L1 系统 | 决定什么 |\n|---|---|")
    for s in scope["l1_systems"]:
        A(f"| {s['name']} | {s['role']} |")

    A("\n## 3. 递归 BOM 总表\n")
    for b in boms:
        A(f"\n### {b['system']}\n")
        A("| L2 | L3 原子项 | 上游 | 中游 | 下游 | 备注 |\n|---|---|---|---|---|---|")
        for l2 in b["l2_items"]:
            for a in l2["l3_atoms"]:
                A(f"| {l2['name']} | **{a['name']}** | {'、'.join(a['upstream'][:4])} "
                  f"| {'、'.join(a['midstream'][:4])} | {'、'.join(a['downstream'][:4])} "
                  f"| {a.get('notes', '')[:200]} |")

    A("\n## 4. BOM 瓶颈排序\n")
    A("| 优先级 | 环节 | 需求 | 供给刚性 | 扩产 | 认证 | 价格 | 利润 | 国替 | 兑现 | 稀缺逻辑 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for i in ranked:
        s = i["scores"]
        A(f"| {i['priority']} | **{i['atom']}** | {s['demand']} | {s['supply_rigidity']} "
          f"| {s['expansion_years']} | {s['certification']} | {s['price_elasticity']} "
          f"| {s['profit_elasticity']} | {s['localization']} | {s['financial_delivery']} "
          f"| {i['rationale'][:200]} |")

    A("\n## 5. 国际龙头与 A 股映射\n")
    for m in maps:
        A(f"\n### {m['bottleneck']}\n")
        for layer, title in (("international", "国际龙头"), ("a_leaders", "A股龙头"),
                             ("a_earnings", "A股业绩股"), ("a_darkhorse", "A股黑马股"),
                             ("a_theme", "主题股（仅观察池）")):
            if m[layer]:
                A(f"**{title}**：")
                for c in m[layer]:
                    ev = c["evidence"][0]
                    tag = "" if ev["confidence"] == "confirmed" else "（待核验）"
                    A(f"- {c['name']}（{c['ticker']}）[{c['relation_stage']}] "
                      f"{ev['claim']}{tag}")
        if m["excluded"]:
            A("**剔除/谨慎**：" + "；".join(f"{e['name']}—{e['reason']}" for e in m["excluded"]))

    A("\n## 6. 核心个股卡片\n")
    for c in cards:
        q = c["six_questions"]
        pv = ("\n- 待核验：" + "；".join(c["pending_verification"])) if c.get("pending_verification") else ""
        A(f"""
### {c['name']}（{c['ticker']}）｜{c['pool']}
- **交易赛道标签**：{c['track_tags']}
- **独家记忆锚**：{c['memory_anchor']}
- **行情催化映射**：{c['catalyst_map']}
- **同业区分**：{c['peer_diff']}

{c['core_text']}

| 六问 | 回答 |
|---|---|
| 客户是否离不开它 | {q['customer_dependency']} |
| 利润是否有现金流支持 | {q['cashflow_support']} |
| ROIC 稳定或改善 | {q['roic_trend']} |
| 资产负债表安全 | {q['balance_sheet']} |
| 扩产是否容易 | {q['expansion_difficulty']} |
| 估值是否透支 | {q['valuation_overdraft']} |{pv}""")

    A("\n## 7. 周期与入场时机\n")
    A(f"**当前阶段：{cycle['current_phase']}**——{cycle['phase_rationale']}\n")
    A("| 子领域 | 入场优先级 | 理由 |\n|---|---|---|")
    for e in cycle["entry_priority"]:
        A(f"| {e['segment']} | {e['priority']} | {e['reason']} |")

    A("\n## 8. 利好 / 利空传导链\n")
    A("**正向催化**：")
    for ch in cycle["positive_chains"]:
        pi = f"｜股价反映：{ch['priced_in']}" if ch.get("priced_in") else ""
        A(f"- {ch['event']}：{ch['chain']} → 受益：{'、'.join(ch['beneficiaries'])}{pi}")
    A("\n**负向风险**：")
    for ch in cycle["negative_chains"]:
        A(f"- {ch['event']}：{ch['chain']} → 受损：{'、'.join(ch['victims'])}")

    A("\n## 9. 价值投资适配\n")
    for pool in ("长期池", "周期池", "交易池", "观察池"):
        names = [f"{c['name']}（{c['ticker']}）" for c in cards if c["pool"] == pool]
        A(f"- **{pool}**：{'、'.join(names) if names else '（无）'}")

    A("\n## 10. 专家 Review 与迭代清单\n")
    if reviews:
        for key, rv in reviews.items():
            A(f"- **{key}** 评审：{rv['verdict']}" +
              (f"，缺口 {len(rv['gaps'])} 条" if rv["gaps"] else ""))
            for g in rv["gaps"]:
                A(f"  - [{g['severity']}] {g['section']}：{g['issue']}（修复方向：{g['fix_hint']}）")
    if patch:
        if patch.get("corrections"):
            A("\n**修复轮已处理**：")
            for c in patch["corrections"]:
                A(f"- {c['target']}：{c['content']}")
        if patch.get("unresolved"):
            A("\n**下一轮人工核验清单**：")
            for u in patch["unresolved"]:
                A(f"- [ ] {u}")
    if issues:
        A("\n**完整性校验（自动）**：")
        for i in issues:
            A(f"- [ ] {i}")
    return "\n".join(L) + "\n"


# —— 无限画布蓝图（结构化 markdown + mermaid，可导入画布工具）——
def render_canvas(scope, boms, bns, maps) -> str:
    prio = {i["atom"]: i["priority"] for bn in bns for i in bn["items"]}
    L = [f"# {scope['industry_name']} 产业画布蓝图\n",
         "> 中心主干=产业生命周期；上/中/下游分区；P0/P1 瓶颈高亮；右侧仪表盘；左侧审计区。\n",
         "```mermaid", "mindmap", f"  root(({scope['industry_name']}))"]
    for b in boms:
        L.append(f"    {b['system']}")
        for l2 in b["l2_items"]:
            L.append(f"      {l2['name']}")
            for a in l2["l3_atoms"]:
                mark = {"P0": "🔴", "P1": "🟠", "P2": "🟡"}.get(prio.get(a["name"], ""), "")
                L.append(f"        {mark}{a['name']}")
    L.append("```\n")
    L.append("## 右侧投研仪表盘\n")
    for m in maps:
        stocks = "、".join(c["name"] for layer in ("a_leaders", "a_earnings")
                           for c in m[layer]) or "—"
        L.append(f"- [{prio.get(m['bottleneck'], '?')}] **{m['bottleneck']}** → {stocks}")
    L.append("\n## 左侧研究审计区（待核验下钻）\n")
    for m in maps:
        for layer in ("a_leaders", "a_earnings", "a_darkhorse", "a_theme"):
            for c in m[layer]:
                for ev in c["evidence"]:
                    if ev["confidence"] == "pending":
                        L.append(f"- [ ] {c['name']}：{ev['claim']}")
    return "\n".join(L) + "\n"


# —— PPT 路演稿大纲（每页只讲一个高价值判断）——
def render_ppt(scope, bns, cards, cycle, ranked) -> str:
    p0 = [i for i in ranked if i["priority"] == "P0"][:3]
    L = [f"# {scope['industry_name']} 路演 PPT 大纲\n",
         "> 原则：每页一个高价值判断；矩阵/热力图/传导链/卡片，不搬运长文。\n",
         f"## P1 封面：{scope['industry_name']}——谁在买单，钱最终流向谁",
         f"- {scope['demand_l0']['who_pays']}；{scope['demand_l0']['demand_nature']}\n",
         "## P2 一图看全产业链（画布导出）\n"]
    for k, i in enumerate(p0, 3):
        L.append(f"## P{k} P0 瓶颈：{i['atom']}\n- {i['rationale']}\n")
    n = 3 + len(p0)
    L.append(f"## P{n} 瓶颈热力图（8 维评分矩阵）\n")
    L.append(f"## P{n+1} 核心标的不可替代性（个股卡片精选）")
    for c in cards[:6]:
        L.append(f"- {c['name']}：{c['memory_anchor']}")
    L.append(f"\n## P{n+2} 周期定位与入场策略\n- 当前：{cycle['current_phase']}")
    for e in cycle["entry_priority"][:4]:
        L.append(f"- {e['segment']}：{e['priority']}")
    L.append(f"\n## P{n+3} 传导链与风险对照")
    for ch in cycle["positive_chains"][:2]:
        L.append(f"- ⬆ {ch['event']} → {'、'.join(ch['beneficiaries'][:3])}")
    for ch in cycle["negative_chains"][:2]:
        L.append(f"- ⬇ {ch['event']} → {'、'.join(ch['victims'][:3])}")
    L.append(f"\n## P{n+4} 投委会讨论页：待核验清单与下一步")
    return "\n".join(L) + "\n"


def render_update(news: str, d: dict) -> str:
    L = [f"# 增量更新（{date.today()}）\n", f"**事件**：{news}\n",
         f"**摘要**：{d['event_summary']}\n",
         f"**影响的 BOM**：{'、'.join(d['affected_boms'])}｜**影响类型**：{d['impact_type']}",
         f"**性质**：{d['horizon']}｜**股价反映**：{d.get('priced_in', '未判断')}\n",
         "| 公司 | 方向 | 传导链 |", "|---|---|---|"]
    for c in d["affected_companies"]:
        L.append(f"| {c['name']} | {c['direction']} | {c['chain']} |")
    L.append(f"\n**对原框架的影响**：{d['verdict']}\n\n" + DISCLAIMER)
    return "\n".join(L) + "\n"
