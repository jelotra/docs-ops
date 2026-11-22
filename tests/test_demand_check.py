# -*- coding: utf-8 -*-
"""demand_check.py 引擎行为测试：注入需求文档 → 结构判定；两 lane 隔离验证。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jedocsops import demand_check, structure_check  # noqa: E402


def _contract(proj: Path) -> dict:
    return demand_check.load_contract(None, proj)


def _make_request(proj: Path, name: str = "DEMAND-001-demo") -> Path:
    req = proj / "docs" / "request" / name
    req.mkdir(parents=True, exist_ok=True)
    return req


# ── 必备文件 ────────────────────────────────────────────────────────────────

def test_missing_required_spec_is_error(tmp_path):
    _make_request(tmp_path)
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 1
    assert any(f["check"] == "required-files" and f["severity"] == "error"
               for f in env["findings"])


def test_valid_minimal_request_passes(tmp_path):
    req = _make_request(tmp_path)
    (req / "01-spec.md").write_text(
        "# 需求\n\n## 验收标准\n\n- [ ] A1 第一项\n- [ ] A2 第二项\n", encoding="utf-8")
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 0, env["findings"]
    assert env["status"] == "passed"


# ── 验收编号 ────────────────────────────────────────────────────────────────

def test_spec_without_acceptance_ids_is_error(tmp_path):
    req = _make_request(tmp_path)
    (req / "01-spec.md").write_text("# 需求\n\n## 验收标准\n\n- 没有编号\n", encoding="utf-8")
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 1
    assert any(f["check"] == "acceptance-ids" for f in env["findings"])


# ── 编号连续（warning 级）──────────────────────────────────────────────────

def test_numbering_gap_is_warning_not_error(tmp_path):
    req = _make_request(tmp_path)
    (req / "01-spec.md").write_text("## 验收标准\n\n- [ ] A1 x\n", encoding="utf-8")
    (req / "03-plan.md").write_text("# 计划\n", encoding="utf-8")
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 0, "缺 02 应为 warning，不阻断"
    assert any(f["check"] == "numbering" and f["severity"] == "warning"
               for f in env["findings"])


# ── 目录名 kebab-case ───────────────────────────────────────────────────────

def test_bad_pointer_name_is_error(tmp_path):
    _make_request(tmp_path, "Bad_Name_With_Underscore")
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 1
    assert any(f["check"] == "pointer" for f in env["findings"])


# ── 两 lane 隔离：需求文档不被正文规则误伤 ─────────────────────────────────

def test_demand_docs_invisible_to_structure_when_exempt(tmp_path):
    """docs-system 通过 doc-contract 的 exemptDirs 排除 docs/request。"""
    (tmp_path / "docs").mkdir()
    req = _make_request(tmp_path)
    # 需求文档含日期/状态词，正文规则会判违规——但它在 exempt 目录里应被跳过
    (req / "01-spec.md").write_text("# 需求\n日期 2026-11-23 已交付 本轮\n", encoding="utf-8")
    contract = structure_check.load_contract(None, tmp_path)
    contract["exemptDirs"] = ["docs/request"]
    env, _, code = structure_check.check(tmp_path, contract)
    assert code == 0, "需求目录被 exempt 后不应产生 body-past 违规"
    assert all("request" not in f["file"] for f in env["findings"])


def test_demand_check_only_scans_request_dir(tmp_path):
    """demand_check 不扫正文层文档。"""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture.md").write_text("# 架构\n无验收标准\n", encoding="utf-8")
    env, _, code = demand_check.check(tmp_path, _contract(tmp_path))
    assert code == 0
    assert env["scanned"] == 0, "正文层文档不算需求"
    assert not env["findings"]
