"""CLI entrypoint for running browser tasks from JSON payloads."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.agent.browser_agent import BrowserAgent


def _read_task(task_arg: str) -> dict:
    if task_arg == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(task_arg).read_text(encoding="utf-8")
    return json.loads(raw)


async def _run(args: argparse.Namespace) -> int:
    task = _read_task(args.task)
    agent = BrowserAgent(config_path=args.config)
    result = await agent.run_task(task)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))

    return 0 if result.get("success") else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="LUCAS Browser Skill CLI")
    parser.add_argument("run", nargs="?", default="run", help="Run task")
    parser.add_argument("--task", required=True, help="JSON task path or '-' for stdin")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args()
    code = asyncio.run(_run(args))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
