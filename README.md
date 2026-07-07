# AIR — AI Industry Research

机构级产业链投研流水线：输入一个板块/主题/概念，输出**三件套**——Markdown 深度报告、
产业画布蓝图、PPT 路演稿大纲。目标是像 A 股顶尖机构产业研究员那样吃透一个产业：

```
air "光模块"
   │
   ▼
边界识别(L0-L1) → 递归 BOM 拆解(L2-L4, 逐系统 fan-out) → 瓶颈八维评分(P0-P3)
→ 标的映射(逐 P0/P1, 分层+证据) → 核心个股卡片 → 周期定位与传导链
→ 确定性装配 + 完整性校验（代码级）
→ 四类专家对抗评审（产业/工程/交易/机构, 独立 fresh 会话）
→ 缺口修复轮 → 复审 → 三件套落盘
```

## 为什么不是一个大 System Prompt

本项目的前身是一份万字系统提示词。它的问题不在内容（内容已全部保留在
`air/prompts/` 与 `air/schemas.py`），在于**交付机制**——把结构、质量、完整性
全部押在模型单次运行的自觉上。AIR 用 harness engineering 的方式重建它：

| 提示词时代 | AIR 的实现 |
|---|---|
| 「必须拆到可映射公司的粒度」 | JSON Schema 强制 `l3_atoms.upstream/midstream/downstream` 字段 |
| 「送样≠认证≠量产≠主供」 | `relation_stage` 枚举——模型必须选一个实际阶段 |
| 「所有断言可验证」 | 每家公司 `evidence[]` 必填，`confidence: confirmed/pending` |
| 「专家对抗式 Review」 | 4 个**独立 fresh 会话**评审员（写报告的模型给自己打分太手软） |
| 「输出结构必须包含 10 部分」 | 确定性代码装配 + 完整性校验（缺节/缺证据/字数越界/空泛词直接列缺口） |
| 「持续更新的研究操作系统」 | 磁盘研究库：分阶段 checkpoint，`--update` 把新事件放回框架 |
| （无） | 预算硬顶 + 费用台账 + 断点续跑 |

核心原则：**结构由确定性代码持有，判断由 LLM 产生，质量由独立评审把关。**

## 依赖与安装

需要：Python ≥ 3.11、[Claude Code](https://claude.com/claude-code) CLI 已登录
（研究 agent 通过它调用模型与联网搜索，无需另配 API key）。

```bash
pipx install git+https://github.com/1055373165/AI-Industry-Research.git
# 或 pip install git+https://github.com/1055373165/AI-Industry-Research.git
```

## 使用

```bash
air "光模块"                      # 全量研究，默认预算 $15
air "HBM 存储" --budget 25        # 更深的研究给更多预算
air --resume optical-module       # 中断/超预算后断点续跑（已完成阶段不重花钱）
air --update optical-module "英伟达下调 1.6T 光模块订单预期"   # 事件放回框架
air --list                        # 已有研究库
```

产出在 `~/.air/<slug>/`：
- `report.md` — 深度报告（结论先行/产业链地图/BOM 总表/瓶颈排序/标的映射/个股卡片/周期/传导链/价值适配/评审与迭代清单）
- `canvas.md` — 画布蓝图（mermaid 产业脑图 + 瓶颈高亮 + 投研仪表盘 + 待核验审计区）
- `ppt.md` — 路演大纲（每页一个高价值判断）
- `0X-*.json` — 各阶段结构化 checkpoint（研究库的真正资产，支持增量更新）
- `ledger.jsonl` — 费用台账

## 成本与模型

全量研究约 25-45 次模型调用（视产业复杂度），默认拆解/映射用 sonnet、
评审/修复用 opus，一次完整研究约 $8-15。**评审员用最好的模型**——
流水线的下限由评判器决定。`--model-fanout` / `--model-review` 可调。

## 研究纪律（内建）

- 所有结论可验证可证伪；空泛表述（行业领先/前景广阔）被代码级检测并列为缺口
- 查不到一手来源的事实必须标「待核验」，宁缺毋滥
- 不因股价上涨倒推基本面；不因名字相关纳入标的池
- **本工具输出不构成投资建议**；所有供应链关系、订单、认证需以公开资料二次核验

## 路线图

- ✅ v0.1：全量流水线 + 对抗评审 + 修复轮 + 三件套 + 增量更新
- ⬜ 阶段内并行 fan-out（当前串行，便于预算控制）
- ⬜ 研报质量监测模块（卖方研报 Alpha/预测偏离度审计）
- ⬜ 定时 triage loop：盘后自动扫描产业新闻 → 影响分析入库
- ⬜ 聊天触发（复用 auto-dev-agent 的 ChatAdapter 网关）

## License

MIT
