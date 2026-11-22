# -*- coding: utf-8 -*-
"""合同测试：同一 fixture + 同一 rules，Python 引擎与旧 Node 引擎判定必须一致。

Node 侧只读 skills 根下已安装的旧引擎（residue-guard/scripts/residue-guard.mjs）；
Node/引擎缺失时跳过（SKILL-MERGE-CONTRACT 依赖在迁移窗口内有效，归档后由
fixture 快照守护，见 test_node_snapshot_parity）。
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jedocsops import residue  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_HOME = SKILL_ROOT.parent
NODE_ENGINE = SKILLS_HOME / "residue-guard" / "scripts" / "residue-guard.mjs"

FIXTURE_RULES = {
    "version": 1,
    "skipDirs": ["vendor"],
    "patterns": [
        {"id": "legacy-acme", "regex": "\\bacme-old-token\\b", "flags": "i",
         "severity": "error", "why": "改名残留",
         "exemptLine": "残留|事故|旧名|历史",
         "exclude": ["**/excluded.md"]},
        {"id": "legacy-counter", "regex": "680/680", "severity": "error",
         "why": "时点计数", "include": ["**/*.md"]},
        {"id": "warn-only", "regex": "warn-me", "severity": "warn", "why": "提示"},
    ],
    "dirLists": [
        {"id": "pkgs", "file": "scripts/build.mjs",
         "extractRegex": r"const PACKAGES = \[([^\]]+)\]",
         "baseDir": "packages", "why": "清单实存", "severity": "error"}
    ],
    "deadLinks": {"include": ["**/*.md"], "why": "死链", "severity": "error"},
    "generatedDrift": [],
}


def _build_fixture(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "vendor").mkdir()
    (root / "scripts").mkdir()
    (root / "packages" / "alpha").mkdir(parents=True)  # ghost 故意不建：dirList 应检出
    (root / "src" / "code.ts").write_text(
        'const a = "acme-old-token";\nconst b = 680/680;\n', encoding="utf-8")
    (root / "docs" / "note.md").write_text(
        "acme-old-token 属旧名残留事故（叙述行豁免）\n"
        "仍然出现 680/680\n"
        "[缺](nope.md) [外链](https://x.y) [锚](#s)\n", encoding="utf-8")
    (root / "docs" / "excluded.md").write_text("acme-old-token\n", encoding="utf-8")
    (root / "vendor" / "v.js").write_text("acme-old-token\n", encoding="utf-8")
    (root / "scripts" / "build.mjs").write_text('const PACKAGES = ["alpha", "ghost"];\n',
                                                encoding="utf-8")


def _py_judge(root: Path) -> dict:
    rules = json.loads(json.dumps(FIXTURE_RULES))
    env, _, code = residue.scan(root, rules)
    return {"code": code, "status": env["status"], "errors": env["errors"],
            "hits": sorted([f"{h['rule']}:{h['file'].replace(chr(92), '/')}"
                            for h in env["hits"] if h.get("severity") == "error"])}


def _node_judge(root: Path, rules_snapshot: Path) -> dict | None:
    if not NODE_ENGINE.is_file() or shutil.which("node") is None:
        return None
    r = subprocess.run(["node", str(NODE_ENGINE), "--project", str(root),
                        "--rules", str(rules_snapshot), "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    if r.returncode not in (0, 1):
        pytest.fail(f"Node 引擎执行异常（exit={r.returncode}）：{r.stderr[:400]}")
    env = json.loads(r.stdout)
    return {"code": r.returncode, "status": env["status"], "errors": env["errors"],
            "hits": sorted([f"{h['rule']}:{h['file'].replace(chr(92), '/')}"
                            for h in env["hits"] if h.get("severity") == "error"])}


@pytest.mark.skipif(not NODE_ENGINE.is_file() or shutil.which("node") is None,
                    reason="Node 引擎或 node 运行时不可用（迁移完成后走快照对拍）")
def test_node_live_parity(tmp_path):
    """迁移窗口内的活体对拍：两个引擎对同一 fixture 判定完全一致。"""
    _build_fixture(tmp_path)
    rules_snapshot = tmp_path.with_suffix(".rules.json")
    rules_snapshot.write_text(json.dumps(FIXTURE_RULES, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    py = _py_judge(tmp_path)
    node = _node_judge(tmp_path, rules_snapshot)
    assert node is not None
    assert py == node, f"\npy  = {json.dumps(py, ensure_ascii=False)}\nnode= {json.dumps(node, ensure_ascii=False)}"


def test_node_snapshot_parity(tmp_path):
    """归档后仍可复验的快照对拍：期望值来自迁移窗口内记录的 Node 引擎基准判定。

    基准（residue-guard 0.1.0 引擎在 FIXTURE_RULES + 标准fixture 上）：
      exit=1, status=failed, errors=4, hits=
        dead-links:docs/note.md / legacy-acme:src/code.ts /
        legacy-counter:docs/note.md / pkgs:scripts/build.mjs
    （legacy-acme:docs/note.md 被 exemptLine 豁免；excluded.md 被文件级排除；
      vendor 被 skipDirs 排除；warn-only 是 warn 不计入 errors）
    """
    _build_fixture(tmp_path)
    py = _py_judge(tmp_path)
    expected = {
        "code": 1, "status": "failed", "errors": 4,
        "hits": sorted([
            "dead-links:docs/note.md",
            "legacy-acme:src/code.ts",
            "legacy-counter:docs/note.md",
            "pkgs:scripts/build.mjs",
        ]),
    }
    assert py == expected, f"py = {json.dumps(py, ensure_ascii=False)}"
