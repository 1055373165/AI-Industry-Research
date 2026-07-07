"""各阶段的结构化输出 schema——结构由 harness 强制，不靠 prompt 祈祷。

设计原则：研究纪律落进字段。每个「事实性断言」都带 evidence 与 confidence
（confirmed / pending=待核验），送样≠认证≠量产的红线体现在 relation_stage
枚举里——模型必须选一个，而不是笼统地说"供应商"。
"""

EVIDENCE = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "source": {"type": "string", "description": "公开来源（公告/财报/官网/新闻，给出处名称或URL）"},
        "confidence": {"type": "string", "enum": ["confirmed", "pending"]},
    },
    "required": ["claim", "confidence"],
}

SCOPE = {
    "type": "object",
    "properties": {
        "industry_name": {"type": "string"},
        "slug": {"type": "string", "description": "英文短横线小写标识，如 optical-module"},
        "boundary": {"type": "string", "description": "研究边界：包含什么、明确不包含什么"},
        "demand_l0": {"type": "object", "properties": {
            "who_pays": {"type": "string"},
            "demand_nature": {"type": "string",
                              "description": "政策驱动/技术驱动/价格驱动/国产替代/库存周期，以及需求真实性判断"},
        }, "required": ["who_pays", "demand_nature"]},
        "l1_systems": {"type": "array", "minItems": 3, "items": {"type": "object", "properties": {
            "name": {"type": "string"},
            "role": {"type": "string", "description": "决定性能/成本/可靠性/交付中的哪个"},
        }, "required": ["name", "role"]}},
        "key_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["industry_name", "slug", "boundary", "demand_l0", "l1_systems"],
}

BOM_TREE = {
    "type": "object",
    "properties": {
        "system": {"type": "string"},
        "l2_items": {"type": "array", "minItems": 2, "items": {"type": "object", "properties": {
            "name": {"type": "string"},
            "l3_atoms": {"type": "array", "minItems": 1, "items": {"type": "object", "properties": {
                "name": {"type": "string", "description": "可映射到具体公司的粒度"},
                "upstream": {"type": "array", "items": {"type": "string"},
                             "description": "上游材料/设备/软件"},
                "midstream": {"type": "array", "items": {"type": "string"},
                              "description": "中游制造/封装/模组/测试"},
                "downstream": {"type": "array", "items": {"type": "string"},
                               "description": "下游客户/应用/认证"},
                "notes": {"type": "string", "description": "工艺难点/技术路线/替代关系"},
                "sources": {"type": "array", "items": {"type": "string"}},
            }, "required": ["name", "upstream", "midstream", "downstream"]}},
        }, "required": ["name", "l3_atoms"]}},
    },
    "required": ["system", "l2_items"],
}

_DIM = {"type": "integer", "minimum": 1, "maximum": 5}
BOTTLENECK = {
    "type": "object",
    "properties": {
        "items": {"type": "array", "items": {"type": "object", "properties": {
            "atom": {"type": "string"},
            "scores": {"type": "object", "properties": {
                "demand": _DIM, "supply_rigidity": _DIM, "expansion_years": _DIM,
                "certification": _DIM, "price_elasticity": _DIM, "profit_elasticity": _DIM,
                "localization": _DIM, "financial_delivery": _DIM,
            }, "required": ["demand", "supply_rigidity", "expansion_years", "certification",
                            "price_elasticity", "profit_elasticity", "localization",
                            "financial_delivery"]},
            "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
            "rationale": {"type": "string",
                          "description": "稀缺逻辑+扩产周期+认证周期，落到具体事实"},
        }, "required": ["atom", "scores", "priority", "rationale"]}},
    },
    "required": ["items"],
}

_COMPANY = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "ticker": {"type": "string", "description": "A股代码或海外代码，未上市写 private"},
        "relation_stage": {"type": "string",
                           "enum": ["主供", "量产", "认证", "送样", "概念映射", "未核验"],
                           "description": "红线：送样≠认证≠量产≠主供，必须选实际阶段"},
        "evidence": {"type": "array", "items": EVIDENCE, "minItems": 1},
    },
    "required": ["name", "ticker", "relation_stage", "evidence"],
}
COMPANY_MAP = {
    "type": "object",
    "properties": {
        "bottleneck": {"type": "string"},
        "international": {"type": "array", "items": _COMPANY},
        "a_leaders": {"type": "array", "items": _COMPANY},
        "a_earnings": {"type": "array", "items": _COMPANY},
        "a_darkhorse": {"type": "array", "items": _COMPANY},
        "a_theme": {"type": "array", "items": _COMPANY,
                    "description": "概念相关证据不足，只进观察池"},
        "excluded": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "reason": {"type": "string"},
        }, "required": ["name", "reason"]}},
    },
    "required": ["bottleneck", "international", "a_leaders", "a_earnings",
                 "a_darkhorse", "a_theme", "excluded"],
}

STOCK_CARD = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "ticker": {"type": "string"},
        "track_tags": {"type": "string", "description": "申万二级行业+定位+3个交易概念"},
        "memory_anchor": {"type": "string", "description": "1条最硬核可验证壁垒，禁套话"},
        "catalyst_map": {"type": "string", "description": "什么事件直接带动它"},
        "peer_diff": {"type": "string", "description": "与同赛道公司的本质差异，一句话"},
        "core_text": {"type": "string",
                      "description": "180-280字单段：行业/主业/新业务/客户认证/产能收入/毛利率现金流ROIC/供应链位置/同业对比"},
        "six_questions": {"type": "object", "properties": {
            "customer_dependency": {"type": "string"},
            "cashflow_support": {"type": "string"},
            "roic_trend": {"type": "string"},
            "balance_sheet": {"type": "string"},
            "expansion_difficulty": {"type": "string"},
            "valuation_overdraft": {"type": "string"},
        }, "required": ["customer_dependency", "cashflow_support", "roic_trend",
                        "balance_sheet", "expansion_difficulty", "valuation_overdraft"]},
        "pool": {"type": "string", "enum": ["长期池", "周期池", "交易池", "观察池"]},
        "pending_verification": {"type": "array", "items": {"type": "string"}},
        "sources": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "ticker", "track_tags", "memory_anchor", "catalyst_map",
                 "peer_diff", "core_text", "six_questions", "pool"],
}

CYCLE = {
    "type": "object",
    "properties": {
        "current_phase": {"type": "string",
                          "enum": ["金融行情", "业绩行情前段", "业绩行情后段", "反金融行情", "反业绩行情"]},
        "phase_rationale": {"type": "string"},
        "entry_priority": {"type": "array", "items": {"type": "object", "properties": {
            "segment": {"type": "string"}, "priority": {"type": "string"},
            "reason": {"type": "string"},
        }, "required": ["segment", "priority", "reason"]}},
        "positive_chains": {"type": "array", "items": {"type": "object", "properties": {
            "event": {"type": "string"},
            "chain": {"type": "string", "description": "事件→订单→稼动率→ASP→毛利率→现金流→盈利上修→估值重估"},
            "beneficiaries": {"type": "array", "items": {"type": "string"}},
            "priced_in": {"type": "string", "description": "是否已反映在股价中的判断"},
        }, "required": ["event", "chain", "beneficiaries"]}},
        "negative_chains": {"type": "array", "items": {"type": "object", "properties": {
            "event": {"type": "string"}, "chain": {"type": "string"},
            "victims": {"type": "array", "items": {"type": "string"}},
        }, "required": ["event", "chain", "victims"]}},
    },
    "required": ["current_phase", "phase_rationale", "entry_priority",
                 "positive_chains", "negative_chains"],
}

REVIEW = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "gaps": {"type": "array", "items": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["P0", "P1", "P2"]},
            "section": {"type": "string"},
            "issue": {"type": "string", "description": "具体缺口/错误，不写套话"},
            "fix_hint": {"type": "string"},
        }, "required": ["severity", "section", "issue", "fix_hint"]}},
    },
    "required": ["verdict", "gaps"],
}
