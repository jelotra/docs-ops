# -*- coding: utf-8 -*-
"""extract_ledger.py —— 从 git 历史自动提取「改名残留清单」（ledger）。

通用原理：任何重构/改名都有 commit；diff 的**删除行**里包含旧名的全部出现形态
（类名/localStorage 键/文案/env 名/大小写变体）。对选定提交统计「删除频次高、
新增频次为零」的 token —— 它们就是改名受害者候选，人工确认后写入 residue.rules.json。

为什么不做项目特有硬编码：token 全部来自 git diff 本身，本脚本不含任何业务词汇。

用法：
  python extract_ledger.py --repo <path> --commit <sha> [--min-count 2]
  python extract_ledger.py --repo <path> --range <a..b | ref> [--min-count 2]
输出：stdout 恒为结果信封 JSON；stderr 为人类可读摘要。
判定语义与原 extract-ledger.mjs 逐条对齐。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DIFF_NOISE = re.compile(r"^(?:diff --git|index |@@|--- |\+\+\+ |rename |similarity )")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")
FILE_HEAD_RE = re.compile(r"^\+\+\+ b/(.+)$")
QUOTED_RE = re.compile(r"'([^'\\]{3,160})'|\"([^\"\\]{3,160})\"|`([^`\\]{3,160})`")
TOKEN_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$.\-/]{2,}")
CLEAN_TAIL_RE = re.compile(r"[.\-_,;:]+$")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} 失败")
    return result.stdout


def _tokenize(line: str, kind: str, file: str, line_no: int,
              dele: dict, adde: dict) -> None:
    def push(token: str) -> None:
        if not token or len(token) < 3 or not re.search(r"[A-Za-z]", token):
            return
        clean = CLEAN_TAIL_RE.sub("", token)
        if len(clean) < 3:
            return
        target = dele if kind == "del" else adde
        entry = target.setdefault(clean, {"count": 0, "samples": []})
        entry["count"] += 1
        if kind == "del" and len(entry["samples"]) < 3 and file:
            entry["samples"].append(f"{file}:{line_no}")

    for m in QUOTED_RE.finditer(line):
        push(m.group(1) or m.group(2) or m.group(3))
    for m in TOKEN_RE.finditer(line):
        push(m.group(0))


def extract(repo: Path, commits: list[str], min_count: int) -> dict:
    dele: dict = {}
    adde: dict = {}
    for sha in commits:
        try:
            diff = _git(repo, "show", sha, "--no-color", "-U0", "--no-renames")
        except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
            print(f"跳过 {sha}：git show 失败（{exc}）", file=sys.stderr)
            continue
        file = ""
        line_no = 0
        for line in diff.split("\n"):
            fm = FILE_HEAD_RE.match(line)
            if fm:
                file = fm.group(1)
                continue
            hm = HUNK_RE.match(line)
            if hm:
                line_no = int(hm.group(1)) - 1
                continue
            if DIFF_NOISE.match(line):
                continue
            kind = "del" if line.startswith("-") else "add" if line.startswith("+") else None
            if not kind:
                continue
            line_no += 1
            _tokenize(line[1:], kind, file, line_no, dele, adde)

    ledger = []
    for token, entry in dele.items():
        added = adde.get(token, {}).get("count", 0)
        if entry["count"] >= min_count and added == 0:
            ledger.append({"token": token, "deleted": entry["count"],
                           "added": added, "samples": entry["samples"]})
    ledger.sort(key=lambda item: item["deleted"], reverse=True)
    return ledger


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="je-docs-ops-extract-ledger",
                                     description="从 git 历史提取改名残留候选（ledger）")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--commits", default=None, help="逗号分隔的多个 sha")
    parser.add_argument("--commit", default=None, help="单个 sha")
    parser.add_argument("--range", dest="range_", default=None, help="a..b 或 ref（上限 200）")
    parser.add_argument("--min-count", type=int, default=2)
    args = parser.parse_args(argv)

    repo = Path(args.repo or ".").resolve()
    commits: list[str] = []
    try:
        if args.commits:
            commits = [s.strip() for s in args.commits.split(",") if s.strip()]
        elif args.commit:
            commits = [args.commit]
        elif args.range_:
            out = _git(repo, "rev-list", "--max-count=200", args.range_)
            commits = [s.strip() for s in out.split("\n") if s.strip()]
        else:
            print("缺少提交范围：--commit <sha> / --commits <sha,...> / --range <a..b|ref>",
                  file=sys.stderr)
            return 2
    except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
        print(f"git rev-list 失败：{exc}", file=sys.stderr)
        return 2

    ledger = extract(repo, commits, args.min_count)
    envelope = {
        "status": "passed",
        "commits": len(commits),
        "minCount": args.min_count,
        "ledgerSize": len(ledger),
        "ledger": ledger,
    }
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    print(f"✓ ledger 提取完成：{len(commits)} 个提交，{len(ledger)} 个候选"
          f"（deleted ≥ {args.min_count} 且 added = 0）。人工确认后写入 residue.rules.json。",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
