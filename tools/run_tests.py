#!/usr/bin/env python
# managed-by: scaffold/test-runner v1
"""并行测试入口（由脚手架维护，勿手改；更新请重跑 scaffold.py tests --write）。

用法：
    python tools/run_tests.py                  # 自动并发（半核数）
    python tools/run_tests.py --jobs 4         # 指定进程数
    python tools/run_tests.py --json           # 末尾追加一行机器可读摘要
    python tools/run_tests.py -- -x -k "not slow"   # 透传给 pytest
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = ("tests",)
EXIT_USAGE = 2


class UsageError(Exception):
    """参数不合法：统一转成 EXIT_USAGE 退出码。"""


def xdist_available() -> bool:
    return importlib.util.find_spec("xdist") is not None


def worker_count(raw: str) -> int:
    if raw == "auto":
        # 半核数：多数 Python 测试套件会再派子进程（git/kubectl/CLI），
        # 满核并发会过度订阅；实测 workloop 8 进程 216s、4 进程 99s。
        return max(1, (os.cpu_count() or 1) // 2)
    try:
        value = int(raw)
    except ValueError:
        raise UsageError(f"--jobs 需要正整数或 auto，收到 {raw!r}") from None
    if value < 1:
        raise UsageError(f"--jobs 必须 >= 1，收到 {value}")
    return value


def build_command(paths: list[str], jobs: int, passthrough: list[str]) -> tuple[list[str], bool]:
    command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"]
    parallel = jobs > 1 and xdist_available()
    if parallel:
        command += ["-n", str(jobs)]
    return command + paths + passthrough, parallel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_tests", description="并行执行本 Skill 的测试")
    parser.add_argument("--jobs", default="auto", help="进程数，默认 auto（半核数）")
    parser.add_argument("--paths", action="append", default=None, help="测试目录，可重复；默认 tests")
    parser.add_argument("--json", action="store_true", help="末尾输出一行机器可读摘要")
    raw = list(sys.argv[1:] if argv is None else argv)
    passthrough: list[str] = []
    if "--" in raw:
        split = raw.index("--")
        raw, passthrough = raw[:split], raw[split + 1:]
    args = parser.parse_args(raw)

    roots = args.paths or list(DEFAULT_PATHS)
    resolved = [Path(root) for root in roots]
    missing = [str(item) for item in resolved if not (SKILL_ROOT / item).exists()]
    if missing:
        sys.stderr.write("missing test paths: " + ", ".join(missing) + "\n")
        return EXIT_USAGE
    # 测试路径必须落在 Skill 根内：绝对路径与 .. 穿越会跑到别的项目上
    escaped = [
        str(item)
        for item in resolved
        if item.is_absolute() or not (SKILL_ROOT / item).resolve().is_relative_to(SKILL_ROOT.resolve())
    ]
    if escaped:
        sys.stderr.write("test paths escape the skill root: " + ", ".join(escaped) + "\n")
        return EXIT_USAGE
    try:
        jobs = worker_count(args.jobs)
    except UsageError as exc:
        sys.stderr.write(f"{exc}\n")
        return EXIT_USAGE
    command, parallel = build_command([str(item) for item in resolved], jobs, passthrough)
    mode = f"parallel: {jobs} workers (pytest-xdist)" if parallel else (
        "serial: pytest-xdist missing" if jobs > 1 else "serial: --jobs 1"
    )
    sys.stderr.write(mode + "\n")

    started = time.monotonic()
    completed = subprocess.run(command, cwd=SKILL_ROOT)
    elapsed = round(time.monotonic() - started, 2)
    if args.json:
        sys.stdout.write(json.dumps({
            "command": "run_tests",
            "parallel": parallel,
            "jobs": jobs if parallel else 1,
            "paths": [str(item) for item in resolved],
            "exit_code": completed.returncode,
            "seconds": elapsed,
        }, ensure_ascii=False) + "\n")
    else:
        sys.stderr.write(f"exit {completed.returncode} in {elapsed}s\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
