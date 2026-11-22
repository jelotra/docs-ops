# -*- coding: utf-8 -*-
"""mint / extract_ledger / structure_check 行为测试。"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jedocsops import mint as mint_mod  # noqa: E402
from jedocsops import structure_check  # noqa: E402


# ── mint 铸造 ───────────────────────────────────────────────────────────────

def _pyproject_runner(tmp_path, kind):
    if kind == "pytest":
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]\n", encoding="utf-8")
    elif kind in ("vitest", "jest"):
        deps = "vitest" if kind == "vitest" else "jest"
        (tmp_path / "package.json").write_text(
            json.dumps({"devDependencies": {deps: "^1.0"}}), encoding="utf-8")


def test_mint_creates_engine_rules_and_pytest_hook(tmp_path):
    _pyproject_runner(tmp_path, "pytest")
    env = mint_mod.mint(tmp_path)
    assert env["runner"] == "pytest"
    engine = tmp_path / "tools" / "accept" / "residue-guard.py"
    rules = tmp_path / "tools" / "accept" / "residue.rules.json"
    hook = tmp_path / "tests" / "test_residue_guard.py"
    assert engine.is_file() and rules.is_file() and hook.is_file()
    # 引擎自包含：直接用项目内拷贝跑一遍
    r = json.loads(engine.read_text(encoding="utf-8").split("def main")[0][:0] or "{}") if False else None
    import subprocess
    proc = subprocess.run([sys.executable, str(engine), "--project", str(tmp_path)],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["status"] == "passed"


def test_mint_vitest_hook_spawns_python(tmp_path):
    _pyproject_runner(tmp_path, "vitest")
    env = mint_mod.mint(tmp_path)
    hook = tmp_path / "tests" / "residue-guard.test.mjs"
    assert env["runner"] == "vitest" and hook.is_file()
    text = hook.read_text(encoding="utf-8")
    assert "spawnSync" in text and "residue-guard.py" in text


def test_mint_idempotent_then_force(tmp_path):
    _pyproject_runner(tmp_path, "pytest")
    first = mint_mod.mint(tmp_path)
    second = mint_mod.mint(tmp_path)
    assert first["created"] and not second["created"]
    assert second["skipped"]
    forced = mint_mod.mint(tmp_path, force=True)
    assert forced["created"]


def test_mint_ledger_patterns(tmp_path):
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"ledger": [
        {"token": "oldWidget", "deleted": 5, "added": 0, "samples": []},
        {"token": "rare", "deleted": 1, "added": 0, "samples": []},
    ]}), encoding="utf-8")
    patterns, _ = mint_mod._ledger_patterns(ledger, min_count=3)
    assert len(patterns) == 1
    assert patterns[0]["id"] == "legacy-oldwidget"
    assert patterns[0]["regex"] == r"\boldWidget\b"


def test_mint_ci_snippet_when_workflows(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    env = mint_mod.mint(tmp_path)
    assert (tmp_path / ".github" / "workflows" / "residue-guard.snippet.yml").is_file()


# ── structure_check ─────────────────────────────────────────────────────────

def _doc_tree(tmp_path):
    docs = tmp_path / "docs"
    hist = docs / "history"
    hist.mkdir(parents=True)
    (hist / "README.md").write_text("# 档案索引\n", encoding="utf-8")
    (docs / "index.md").write_text("# 地图\n- [概念](concepts/a.md)\n", encoding="utf-8")
    (docs / "concepts").mkdir()
    (docs / "concepts" / "a.md").write_text(
        "# A\n\n当前机制说明。[历史档案](../history/README.md)\n", encoding="utf-8")
    (docs / "roadmap.md").write_text(
        "# 路线图\n\n- 做增强 X\n\n历史：[历史档案](history/README.md)\n", encoding="utf-8")


def test_structure_clean_tree_passes(tmp_path):
    _doc_tree(tmp_path)
    env, _, code = structure_check.check(tmp_path, dict(structure_check.DEFAULT_CONTRACT))
    assert code == 0, [f for f in env["findings"]]


def test_structure_missing_history_link_fails(tmp_path):
    _doc_tree(tmp_path)
    (tmp_path / "docs" / "concepts" / "b.md").write_text("# B\n无跳转位\n", encoding="utf-8")
    env, _, code = structure_check.check(tmp_path, dict(structure_check.DEFAULT_CONTRACT))
    assert code == 1
    assert any(f["check"] == "history-link" and f["file"].endswith("b.md")
               for f in env["findings"])


def test_structure_roadmap_past_word_fails(tmp_path):
    _doc_tree(tmp_path)
    (tmp_path / "docs" / "roadmap.md").write_text(
        "# 路线图\n\n- 已交付的 X（2026-11-05 归档）\n\n历史：[历史档案](history/README.md)\n",
        encoding="utf-8")
    env, _, code = structure_check.check(tmp_path, dict(structure_check.DEFAULT_CONTRACT))
    assert code == 1
    assert any(f["check"] == "roadmap-past" for f in env["findings"])


def test_structure_allowed_dirs_contract(tmp_path):
    _doc_tree(tmp_path)
    (tmp_path / "docs" / "rogue").mkdir()
    (tmp_path / "docs" / "rogue" / "c.md").write_text(
        "# C\n[历史](../history/README.md)\n", encoding="utf-8")
    contract = dict(structure_check.DEFAULT_CONTRACT)
    contract["allowedDirs"] = ["concepts", "reference", "integration"]
    env, _, code = structure_check.check(tmp_path, contract)
    assert code == 1
    assert any(f["check"] == "allowed-dirs" for f in env["findings"])


def test_structure_contract_unknown_field_rejected(tmp_path):
    bad = tmp_path / "doc-contract.json"
    bad.write_text(json.dumps({"noSuchField": 1}), encoding="utf-8")
    with pytest.raises(structure_check.ContractError):
        structure_check.load_contract(bad, tmp_path)


def test_structure_missing_bodydir_passes_with_note(tmp_path):
    env, _, code = structure_check.check(tmp_path, dict(structure_check.DEFAULT_CONTRACT))
    assert code == 0 and env["scanned"] == 0
