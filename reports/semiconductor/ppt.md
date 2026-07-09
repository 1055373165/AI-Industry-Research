# 半导体（Semiconductor） 路演 PPT 大纲

> 原则：每页一个高价值判断；矩阵/热力图/传导链/卡片，不搬运长文。

## P1 封面：半导体（Semiconductor）——谁在买单，钱最终流向谁
- ① AI/云算力：AWS/Azure/Google/阿里/腾讯/字节等超大规模云厂商资本开支采购GPU、HBM、AI ASIC，买单方明确，订单有季度级可见性，需求真实性最高。② 智能手机OEM（苹果/三星/小米/华为）：换机周期+SoC升级，2025-2026处于补库周期，需求真实但弹性大。③ 汽车OEM/Tier1（比亚迪/特斯拉/博世）：EV渗透率+智驾NOA落地驱动MCU/SoC/功率器件采购，需求真实性较高。④ 中国晶圆厂（中芯国际/华虹/长鑫/长江存储）：政策基金注资+国产替代双轮驱动，采购国产设备/材料，最终资金含政策资本，受管制风险影响。；多重驱动并存须分赛道判断。AI算力芯片：技术驱动（大模型参数规模扩张）+资本开支驱动，景气处于上行周期但估值已大幅透支，需警惕云厂商CapEx单季波动传导至砍单风险。消费电子芯片：库存周期驱动为主，2022-2023去库完成后补库，全球手机出货增速个位数非结构性增长。汽车半导体：技术驱动（智驾算力需求≥1000TOPS）+国产替代（MCU/功率器件进口依赖度高），周期性弱于消费电子，单车半导体价值量提升逻辑可验证。国产设备/材料：政策驱动+国产替代，大基金三期2024年成立（规模3440亿元），招标订单是可验证指标，但送样≠认证≠量产≠主供，须逐级核验切勿跳跃。

## P2 一图看全产业链（画布导出）

## P3 P0 瓶颈：静态时序分析工具（STA / PrimeTime）
- EDA单体工具壁垒最高节点。卡点具体化：TSMC PDK lib文档以PrimeTime格式原生校验，换工具需Foundry额外签字确认——制度性锁定，非仅技术依赖；30年工程师脚本积累无法快速迁移；中国无等价商业产品，缺先进节点signoff案例；从零开发至TSMC主signoff认证估计>7年。Synopsys EDA订阅收入FY2024超$3B（全线），价格随节点升级持续上行。证伪条件：Cadence Tempus获TSMC官方primary signoff认可（需持续跟踪）。

## P4 P0 瓶颈：硬件仿真加速器（Hardware Emulator）
- AI时代需求超线性增长的硬件稀缺品。具体事实：Blackwell 2080亿晶体管，设计复杂度使仿真需求呈4-8x非线性放大；Cadence Palladium Z2单台$5-15M，交货周期6-12个月，上游卡点是AMD FPGA供应；仅Cadence/Synopsys/Siemens有商业产品，中国无商业化硬件仿真器；Cadence硬件业务（Palladium/Protium）年营收约$6-8亿（pending精确核验），backlog可见；中国头部AI芯片公司受出口管制无法合法采购新系统，国内空白明确。扩产周期受AMD FPGA供应链制约≥3年。financial_delivery=5因需求驱动AI算力扩张，Cadence硬件增长已体现在公开财报。

## P5 P0 瓶颈：物理验证工具（DRC/LVS — Calibre垄断节点）
- 确定性最高的出口管制卡点。具体事实：TSMC rule deck以Calibre格式原生交付，由TSMC自有工程师维护——切换需Foundry投入2-3年重写rule deck，属Foundry侧成本，Foundry无替换动力；Siemens 2017年以$45亿收购Mentor/Calibre，嵌入全球主要Foundry生产流程；中国无任何商业DRC/LVS工具具备先进节点rule deck覆盖；EDA出口管制下Calibre续约成为中国Fab最直接供应链风险。证伪条件：TSMC发布Synopsys ICV官方primary signoff认证（目前ICV仅辅助验证）。

## P6 瓶颈热力图（8 维评分矩阵）

## P7 核心标的不可替代性（个股卡片精选）
- 华大九天：全球主流EDA厂商（Cadence/Synopsys/Siemens）均已放弃独立FPD专用EDA产品线，华大九天是唯一同时覆盖TFT-LCD/AMOLED阵列设计全流程的商业化EDA平台；BOE/CSOT/天马等中国面板厂的驱动及阵列设计flow在FPD赛道上无可替代替代方案——这一细分全球竞争空白是可验证的排他性壁垒，非政策依赖型。
- 海光信息：国内唯一持有x86指令集架构合法授权的处理器设计公司：2016年经中AMD合资主体THATIC获得Zen1架构IP许可，使海光CPU可在不重写任何软件的前提下直接运行Windows/Linux x86生态——该授权因美国2019年出口管制已不可续期、不可复制，同类授权无第二家国内公司持有（龙芯/飞腾/申威均为非x86架构，生态迁移成本量级不同）。
- 龙芯中科：LoongArch是中国唯一完全自主设计、已合并进Linux内核主线（v5.19，2022年）的商业处理器ISA——不依赖Arm/MIPS/RISC-V任何外部IP授权协议，从架构定义层切断美国出口管制对指令集许可证的管辖链条；这一法律层面的隔离在A股上市处理器公司中唯一无二，可通过kernel.org commit log及公司招股书第4章独立核实。
- 寒武纪：自研MLU架构与寒武纪ISA指令集（已申请数百项AI芯片专利，2019年曾对苹果发起专利侵权诉讼），是科创板唯一可独立交易的AI训练芯片设计上市主体——政府算力采购体系对"自主可控"标的存在政策性优先指向，该稀缺性身份在国内无直接公开上市替代品。
- 华卓精科：国内唯一经SMEE光刻机产线工程验证、实现双工件台（亚纳米扫描定位，步进精度＜1nm）可交付的供应商——双工件台是光刻机中技术门槛最高的单体子系统，历史上仅ASML与Nikon两家掌握，可验证证据：华卓精科招股书及历年年报披露"双工件台已完成客户联调交付"。
- 国芯科技：国芯科技是A股极少数同时拥有自研处理器IP核授权（C*Core，基于PowerPC EREF规范自研实现，非Arm/RISC-V路线）并对外商业授权的公司——其IP核已嵌入国内多家电力终端设备厂商的定制SoC中，客户一旦流片即形成ISA级锁定，切换成本等同于重新设计底层架构。

## P8 周期定位与入场策略
- 当前：业绩行情后段
- 先进封装（CoWoS / SoIC / HBM substrate）：P0——当前最高优先级
- HBM 内存（SK Hynix / Micron / Samsung HBM 相关设备与材料）：P1——高优先级，需注意 HBM ASP 可持续性
- EDA 工具链（STA / P&R / 物理验证 / 硬件仿真加速器）：P1——高优先级，估值已不便宜
- 晶圆设备（ASML / Lam Research / KLA / Applied Materials）：P1——强基本面，但股价已部分反映

## P9 传导链与风险对照
- ⬆ 超大型科技公司 AI 基础设施资本开支持续高增（Meta/MSFT/Google/Amazon 多年期指引） → TSMC（CoWoS/SoIC 封装）、ASE/Amkor（OSat 高端封测）、Besi（TC Die Bonder，HBM 键合设备）
- ⬆ HBM3E/HBM4 供给分配持续紧张，AI 训练集群内存带宽需求呈超线性增长 → SK Hynix（HBM 主供，市占>50%）、Micron（HBM3E 进入量产，毛利率改善期）、Besi（TC Die Bonder，三家 HBM 厂均使用）
- ⬇ 美国对华半导体出口管制进一步升级（Entity List 扩展 / 甲类技术管制） → Lam Research（中国收入历史占比~30%，管制敏感）、Applied Materials（中国区占比~25-30%）、KLA（中国区占比~40%，已受 BIS 管制影响）
- ⬇ 超大型科技公司 AI 资本开支增速放缓（ROI 质疑、盈利压力） → NVIDIA（最大受益者同时是最大风险暴露点）、TSMC（CoWoS 需求降温）、SK Hynix/Micron（HBM 需求下修）

## P10 投委会讨论页：待核验清单与下一步
