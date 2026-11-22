# -*- coding: utf-8 -*-
"""统一入口 CLI 行为测试：check / new / migrate / residue 四个子命令。"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jedocsops import cli  # noqa: E402

SHIM = ROOT / "scripts" / "je-docs-ops.py"


def _run_shim(*args):
    """经真实入口 shim 调用：捕获 SystemExit(main()) 的退出码，防止 tuple 泄漏类回归。"""
    env = {"PYTHONIOENCODING": "utf-8"}
    import os
    env = {**os.environ, **env}
    return subprocess.run([sys.executable, str(SHIM), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def _doc_tree(tmp_path):
    docs = tmp_path / "docs"
    hist = docs / "history"
    hist.mkdir(parents=True)
    (hist / "README.md").write_text("# 档案索引\n", encoding="utf-8")
    (docs / "concepts").mkdir()
    (docs / "concepts" / "a.md").write_text(
        "# A\n当前机制。[历史档案](../history/README.md)\n", encoding="utf-8")
    accept = tmp_path / "tools" / "accept"
    accept.mkdir(parents=True)
    (accept / "residue.rules.json").write_text(json.dumps({"version": 1}), encoding="utf-8")


def test_describe_contract_unchanged(capsys):
    assert cli.main(["describe", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert cli.main(["describe", "--markdown"]) == 0
    assert capsys.readouterr().out.startswith("# ")


def test_check_full_green(tmp_path, capsys):
    _doc_tree(tmp_path)
    code = cli.main(["check", "--project", str(tmp_path)])
    assert code == 0


def test_check_reports_violation(tmp_path):
    _doc_tree(tmp_path)
    (tmp_path / "docs" / "concepts" / "b.md").write_text("# B\n无跳转\n", encoding="utf-8")
    code = cli.main(["check", "--project", str(tmp_path)])
    assert code == 1


def test_check_missing_rules_is_config_error(tmp_path):
    code = cli.main(["check", "--project", str(tmp_path), "--skip-structure"])
    assert code == 2


def test_new_creates_doc_with_history_jump(tmp_path):
    _doc_tree(tmp_path)
    out = tmp_path / "docs" / "concepts" / "newdoc.md"
    code = cli.main(["new", "--type", "body-doc", "--out", str(out), "--title", "新文档",
                     "--project", str(tmp_path), "--json"])
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "history/README.md" in text
    assert "$historyPath" not in text and "$title" not in text


def test_new_refuses_existing_target(tmp_path, capsys):
    _doc_tree(tmp_path)
    out = tmp_path / "docs" / "concepts" / "a.md"
    code = cli.main(["new", "--type", "body-doc", "--out", str(out)])
    assert code == 1


def test_migrate_lists_move_lines(tmp_path, capsys):
    doc = tmp_path / "legacy.md"
    doc.write_text("# 旧文档\n\n已完成 X（2026-10-01）。\n当前机制不变。\n", encoding="utf-8")
    code = cli.main(["migrate", "--file", str(doc), "--project", str(tmp_path), "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ok"
    move_lines = data["data"]["moveLines"]
    assert move_lines and any("2026-10-01" in m["text"] for m in move_lines)
    assert not any("当前机制不变" in m["text"] for m in move_lines)
    assert "git mv" in data["data"]["steps"][0]


def test_residue_clean_exit_zero(tmp_path):
    (tmp_path / "a.md").write_text("干净内容\n", encoding="utf-8")
    accept = tmp_path / "tools" / "accept"
    accept.mkdir(parents=True)
    (accept / "residue.rules.json").write_text(json.dumps(
        {"version": 1, "deadLinks": {"include": ["**/*.md"]}}), encoding="utf-8")
    code = cli.main(["residue", "--project", str(tmp_path)])
    assert code == 0


def test_residue_missing_rules_exit_two(tmp_path):
    code = cli.main(["residue", "--project", str(tmp_path)])
    assert code == 2


def test_shim_exit_codes_no_tuple_leak(tmp_path):
    """入口 shim 退出码契约：migrate 文件缺失=2、mint 成功=0；stderr 不得泄漏 tuple 字面量。"""
    missing = tmp_path / "missing.md"
    bad = _run_shim("migrate", "--file", missing, "--project", tmp_path)
    assert bad.returncode == 2
    assert "(" not in bad.stderr or "'status'" not in bad.stderr  # 禁止 (2, {...}) 泄漏

    ok = _run_shim("residue", "--mint", "--project", tmp_path)
    assert ok.returncode == 0
    assert "(0," not in ok.stderr
