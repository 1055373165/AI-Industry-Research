"""air：机构级产业链投研流水线。

  air "光模块"                          全量研究（三件套）
  air "光模块" --budget 25              提高预算上限
  air --resume optical-module           断点续跑（checkpoint 已存在的阶段跳过）
  air --update optical-module "新闻…"    把新事件放回已有研究框架
  air --list                            列出已有研究库
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(prog="air", description="AI 产业链投研流水线（机构级三件套输出）")
    p.add_argument("topic", nargs="?", default="", help="板块/主题/新闻/概念，如：光模块、HBM、固态电池")
    p.add_argument("--budget", type=float, default=15.0, help="本次运行费用上限（美元），默认 15")
    p.add_argument("--workdir", default="~/.air", help="研究库根目录")
    p.add_argument("--model-fanout", default="sonnet", help="拆解/映射/卡片阶段模型")
    p.add_argument("--model-review", default="opus", help="评审/修复阶段模型（评判器值得用最好的）")
    p.add_argument("--resume", metavar="SLUG", help="断点续跑指定研究库")
    p.add_argument("--update", metavar="SLUG", help="对指定研究库做事件增量更新（配合 topic 传入新闻）")
    p.add_argument("--list", action="store_true", help="列出已有研究库")
    args = p.parse_args()

    workdir = Path(args.workdir).expanduser()
    workdir.mkdir(parents=True, exist_ok=True)

    if args.list:
        runs = sorted(d.name for d in workdir.iterdir() if (d / "01-scope.json").exists())
        print("\n".join(runs) if runs else "（空）研究库: " + str(workdir))
        return

    from .pipeline import BudgetExceeded, Pipeline

    if args.update:
        if not args.topic:
            sys.exit("增量更新需要传入事件内容：air --update <slug> \"<新闻/公告/涨价信息>\"")
        pipe = Pipeline(args.topic, workdir, budget_usd=args.budget,
                        model_fanout=args.model_fanout, model_review=args.model_review)
        pipe.update(args.update, args.topic)
        return

    topic = args.topic
    if args.resume:
        scope_p = workdir / args.resume / "01-scope.json"
        if not scope_p.exists():
            sys.exit(f"研究库 {args.resume} 不存在。--list 查看已有研究库。")
        import json
        topic = json.loads(scope_p.read_text())["industry_name"]
    if not topic:
        sys.exit("用法: air \"<板块/主题>\"（air --help 查看全部能力）")

    pipe = Pipeline(topic, workdir, budget_usd=args.budget,
                    model_fanout=args.model_fanout, model_review=args.model_review)
    try:
        run_dir = pipe.run()
    except BudgetExceeded as e:
        sys.exit(f"⛔ {e}")
    print(f"\n📄 报告: {run_dir / 'report.md'}\n🗺  画布: {run_dir / 'canvas.md'}\n"
          f"📽  PPT: {run_dir / 'ppt.md'}\n💰 本次花费: ${pipe.spent:.2f}")


if __name__ == "__main__":
    main()
