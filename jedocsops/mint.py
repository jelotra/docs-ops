# -*- coding: utf-8 -*-
"""mint.py —— 铸造器：为任意项目生成自有残留守卫（守卫代码进项目，skill 只铸不养）。

铸造产物（全部幂等，已存在则跳过，--force 覆盖）：
  <project>/tools/accept/residue-guard.py          通用引擎（本 skill 引擎的自包含拷贝）
  <project>/tools/accept/residue.rules.json        规则（patterns 来自 --ledger 确认项）
  测试钩子（按探测到的 runner：vitest/jest/pytest → 统一 spawn 本 Python 引擎）
  .github/workflows/residue-guard.snippet.yml      CI 片段（检测到 GitHub workflows 时，需人工合并）

用法：
  python mint.py --project <path> [--ledger ledger.json] [--min-count 3] [--force]
stdout 恒为结果信封 JSON；stderr 为人类可读摘要。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ENGINE_NAME = "residue-guard.py"


def _runner_of(project: Path) -> str:
    """探测 test runner：package.json 含 vitest/jest → 对应 runner；pyproject/setup.py → pytest。"""
    pkg = project / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            data = {}
        blob = json.dumps({"test": (data.get("scripts") or {}).get("test", ""),
                           "dev": data.get("devDependencies") or {},
                           "deps": data.get("dependencies") or {}}, ensure_ascii=False)
        if "vitest" in blob:
            return "vitest"
        if re.search(r"\bjest\b", blob):
            return "jest"
        return "none"
    if (project / "pyproject.toml").is_file() or (project / "setup.py").is_file():
        return "pytest"
    return "none"


def _ledger_patterns(ledger_path: Path, min_count: int) -> tuple[list[dict], list[str]]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8", errors="replace")).get("ledger") or []
    patterns: list[dict] = []
    for item in ledger:
        if item.get("deleted", 0) < min_count:
            continue
        token = item["token"]
        escaped = re.escape(token)
        patterns.append({
            "id": "legacy-" + re.sub(r"[^a-z0-9-]", "-", token.lower())[:40],
            "regex": r"\b" + escaped + r"\b",
            "flags": "i",
            "severity": "error",
            "why": f"改名残留候选（ledger：删除 {item['deleted']} 次 / 新增 0 次），人工确认后保留",
            "exclude": ["**/ledger.json", "**/residue.rules.json"],
            "exemptLine": "残留|漏网|事故|旧名|历史|时点",
        })
    hints = [f"ledger 自动收录 {len(patterns)} 条 pattern（deleted ≥ {min_count}）——"
             "请人工复核，删掉误报项（常见误报：恰好只在删除行出现的无关词）。"]
    return patterns, hints


VITEST_HOOK = """import { describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

describe('残留守卫', () => {
\tit('全仓无已固化的残留模式（规则见 tools/accept/residue.rules.json）', () => {
\t\tconst guard = fileURLToPath(new URL('../tools/accept/residue-guard.py', import.meta.url));
\t\tconst project = fileURLToPath(new URL('..', import.meta.url));
\t\tconst r = spawnSync(process.env.PYTHON ?? 'python', [guard, '--project', project], { encoding: 'utf8' });
\t\tif (r.status !== 0) throw new Error('残留守卫失败：\\n' + (r.stdout ?? '') + (r.stderr ?? ''));
\t\texpect(r.status).toBe(0);
\t});
});
"""

JEST_HOOK = '''"use strict";
const { spawnSync } = require("node:child_process");
const path = require("node:path");

describe("残留守卫", () => {
\ttest("全仓无已固化的残留模式", () => {
\t\tconst guard = path.join(__dirname, "..", "tools", "accept", "residue-guard.py");
\t\tconst project = path.join(__dirname, "..");
\t\tconst r = spawnSync(process.env.PYTHON || "python", [guard, "--project", project], { encoding: "utf8" });
\t\tif (r.status !== 0) throw new Error("残留守卫失败：\\n" + (r.stdout || "") + (r.stderr || ""));
\t\texpect(r.status).toBe(0);
\t});
});
'''

PYTEST_HOOK = '''"""残留守卫钩子：全仓无已固化的残留模式（规则见 tools/accept/residue.rules.json）。"""
import os
import subprocess
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "tools" / "accept" / "residue-guard.py"


def test_residue_guard():
    r = subprocess.run([os.environ.get("PYTHON", "python"), str(GUARD),
                        "--project", str(GUARD.parents[2])], capture_output=True, text=True)
    assert r.returncode == 0, "残留守卫失败：\\n" + r.stdout + r.stderr
'''

CI_SNIPPET = """# residue-guard 片段：合并进你的 CI workflow（job 或 steps 均可）
# 最小步骤（需要 Python ≥3.11）：
#   - name: 残留守卫（字面量/清单/死链）
#     run: python tools/accept/residue-guard.py
# 有生成物时追加（规则 generatedDrift 配好后）：
#   - name: 残留守卫（含生成物漂移）
#     run: python tools/accept/residue-guard.py --generated
"""


def mint(project: Path, ledger_path: Path | None = None, min_count: int = 3,
         force: bool = False) -> dict:
    if not project.is_dir():
        raise SystemExit(f"✗ 项目目录不存在：{project}")

    here = Path(__file__).resolve().parent
    engine_src = here.parent / "jedocsops" / "residue.py"
    accept_dir = project / "tools" / "accept"
    created: list[str] = []
    skipped: list[str] = []
    hints: list[str] = []

    def write_if(abs_path: Path, content: str, label: str) -> None:
        if abs_path.exists() and not force:
            skipped.append(label)
            return
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        created.append(label)

    # ① 引擎拷贝（自包含单文件，直接复制）
    write_if(accept_dir / ENGINE_NAME, engine_src.read_text(encoding="utf-8"),
             "tools/accept/residue-guard.py")

    # ② 规则文件（patterns 来自 ledger 确认项）
    patterns: list[dict] = []
    if ledger_path:
        if not ledger_path.is_file():
            raise SystemExit(f"✗ ledger 文件不存在：{ledger_path}")
        patterns, ledger_hints = _ledger_patterns(ledger_path, min_count)
        hints.extend(ledger_hints)

    rules = {
        "version": 1,
        "skipDirs": [],
        "patterns": patterns,
        "dirLists": [],  # 建议：把「清单文件声明条目」的检查加进来，schema 见 references/residue-taxonomy.md
        "deadLinks": {
            "include": ["README.md", "**/*.md"],
            "why": "相对链接目标不存在（路径改名残留）",
        },
        "generatedDrift": [],  # 建议：有生成物时加 {id, command, paths}，CI 用 --generated 执行
    }
    write_if(accept_dir / "residue.rules.json",
             json.dumps(rules, ensure_ascii=False, indent=2) + "\n",
             "tools/accept/residue.rules.json")

    # ③ 测试钩子（按探测到的 runner；钩子只是调用入口薄壳，引擎统一是 Python）
    runner = _runner_of(project)
    if runner == "vitest":
        write_if(project / "tests" / "residue-guard.test.mjs", VITEST_HOOK,
                 "tests/residue-guard.test.mjs (vitest)")
        hints.append("vitest 钩子写在 tests/ 下——若你的 vitest include 不含 tests/**，"
                     "请把该文件移到被收集的目录。")
    elif runner == "jest":
        write_if(project / "__tests__" / "residue-guard.test.js", JEST_HOOK,
                 "__tests__/residue-guard.test.js (jest)")
    elif runner == "pytest":
        write_if(project / "tests" / "test_residue_guard.py", PYTEST_HOOK,
                 "tests/test_residue_guard.py (pytest)")
    else:
        hints.append("未探测到 vitest/jest/pytest——未生成测试钩子。可手动接入："
                     "python tools/accept/residue-guard.py（退出码 0 = 干净）。")

    # ④ CI 片段（检测到 GitHub workflows 时）
    if (project / ".github" / "workflows").is_dir():
        write_if(project / ".github" / "workflows" / "residue-guard.snippet.yml", CI_SNIPPET,
                 ".github/workflows/residue-guard.snippet.yml")
        hints.append("CI 片段已生成（snippet.yml）——请人工合并进你的 workflow，避免直接覆盖。")

    return {
        "status": "passed",
        "project": str(project),
        "runner": runner,
        "created": created,
        "skipped": skipped,
        "hints": hints,
        "rules": {"patterns": len(patterns)},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="je-docs-ops-mint",
                                     description="为项目铸造自有残留守卫（Python 引擎）")
    parser.add_argument("--project", required=True)
    parser.add_argument("--ledger", default=None)
    parser.add_argument("--min-count", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    envelope = mint(Path(args.project).resolve(),
                    Path(args.ledger).resolve() if args.ledger else None,
                    args.min_count, args.force)
    print(json.dumps(envelope, ensure_ascii=False, indent=2), file=sys.stdout)
    print(f"✓ 铸造完成（runner={envelope['runner']}）：新建 {len(envelope['created'])}、"
          f"跳过 {len(envelope['skipped'])}。守卫用法："
          f"python tools/accept/residue-guard.py --project <path>（--generated 含生成物漂移）。",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
