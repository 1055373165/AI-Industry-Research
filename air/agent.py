"""Claude Code headless 适配层（研究版）。

与编码 agent（auto-dev-agent）的差异：研究 agent 是"纯函数"——只需要
WebSearch/WebFetch 两个工具，不碰文件系统、不执行命令，因此天然安全，
不需要沙箱；结构化输出用 --json-schema 强制（字段缺失由 CLI 层重试，
不靠 prompt 祈祷）。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass


@dataclass
class AgentResult:
    ok: bool
    data: dict | list | None = None   # 结构化模式下的 schema 校验结果
    text: str = ""                    # 文本模式下的正文
    cost_usd: float = 0.0
    error: str = ""


def run(prompt: str, *, system: str = "", schema: dict | None = None,
        model: str = "sonnet", budget_usd: float = 1.0, timeout_s: int = 900,
        search: bool = True) -> AgentResult:
    """单次 headless 调用。search=True 时开放 WebSearch/WebFetch（研究必需），
    否则禁用全部工具（纯推理/纯整理，更快更便宜）。"""
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "json",
        "--no-session-persistence",
        "--max-budget-usd", str(budget_usd),
        "--tools", "WebSearch,WebFetch" if search else "",
        "--permission-mode", "dontAsk",
    ]
    if system:
        cmd += ["--system-prompt", system]
    if schema is not None:
        cmd += ["--json-schema", json.dumps(schema, ensure_ascii=False)]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s, cwd=tempfile.gettempdir())
    except subprocess.TimeoutExpired:
        return AgentResult(ok=False, error=f"超时（{timeout_s}s）")
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return AgentResult(ok=False, error=f"输出解析失败: {proc.stderr[-300:] or proc.stdout[-300:]}")

    cost = float(out.get("total_cost_usd") or 0.0)
    if out.get("is_error"):
        return AgentResult(ok=False, cost_usd=cost, error=str(out.get("result", ""))[-500:])
    if schema is not None:
        so = out.get("structured_output")
        if so is None:
            return AgentResult(ok=False, cost_usd=cost, error="缺少 structured_output")
        return AgentResult(ok=True, data=so, cost_usd=cost)
    return AgentResult(ok=True, text=out.get("result") or "", cost_usd=cost)
