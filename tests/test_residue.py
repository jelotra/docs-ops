# -*- coding: utf-8 -*-
"""residue.py 引擎行为测试：注入残留 → 必须检出；清偿后 → 必须通过。"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jedocsops import residue  # noqa: E402


def write_rules(project: Path, rules: dict) -> Path:
    p = project / "residue.rules.json"
    p.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


@pytest.fixture
def proj(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    return tmp_path


# ── patterns ────────────────────────────────────────────────────────────────

def test_pattern_detects_legacy_token(proj):
    (proj / "src" / "a.ts").write_text('const k = "acme-old-token";\n', encoding="utf-8")
    rules = {"patterns": [{"id": "legacy-acme", "regex": "\\bacme-old-token\\b", "flags": "i",
                           "severity": "error", "why": "改名残留"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 1 and env["errors"] == 1
    assert env["hits"][0]["file"].replace("\\", "/") == "src/a.ts"
    assert env["hits"][0]["line"] == 1


def test_pattern_exempt_line(proj):
    (proj / "src" / "a.ts").write_text(
        'const k = "acme-old-token";  // 旧名残留事故：此处为叙述行\n'
        'const k2 = "acme-old-token";\n', encoding="utf-8")
    rules = {"patterns": [{"id": "legacy-acme", "regex": "\\bacme-old-token\\b", "flags": "i",
                           "severity": "error", "why": "改名残留",
                           "exemptLine": "残留|事故|旧名"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 1 and env["errors"] == 1
    assert env["hits"][0]["line"] == 2


def test_pattern_clean_project_passes(proj):
    (proj / "src" / "a.ts").write_text("const k = 'new-token';\n", encoding="utf-8")
    rules = {"patterns": [{"id": "legacy-acme", "regex": "\\bacme-old-token\\b",
                           "severity": "error", "why": "改名残留"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 0 and env["status"] == "passed" and env["scanned"] == 1


def test_pattern_warn_not_blocking(proj):
    (proj / "src" / "a.ts").write_text("old-token\n", encoding="utf-8")
    rules = {"patterns": [{"id": "w", "regex": "old-token", "severity": "warn", "why": "提示"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 0 and env["errors"] == 0 and len(env["hits"]) == 0  # warn 不进默认信封


def test_pattern_exclude_and_self_exempt(proj):
    (proj / "src" / "gen.md").write_text("acme-old-token\n", encoding="utf-8")
    rules = {"patterns": [{"id": "x", "regex": "acme-old-token", "severity": "error",
                           "why": "r", "exclude": ["**/gen.md"]}]}
    _, _, code = residue.scan(proj, rules)
    assert code == 0


def test_pattern_bad_regex_exit_config(proj):
    rules = {"patterns": [{"id": "bad", "regex": "([unclosed", "severity": "error", "why": "r"}]}
    with pytest.raises(residue.ConfigError):
        residue.scan(proj, rules)


def test_skip_dirs_respected(proj):
    (proj / "node_modules" / "pkg").mkdir(parents=True)
    (proj / "node_modules" / "pkg" / "a.js").write_text("acme-old-token\n", encoding="utf-8")
    rules = {"patterns": [{"id": "x", "regex": "acme-old-token", "severity": "error", "why": "r"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 0 and env["scanned"] == 0


# ── dirLists ────────────────────────────────────────────────────────────────

def test_dirlist_missing_entry(proj):
    (proj / "scripts").mkdir()
    (proj / "scripts" / "build.mjs").write_text('const PACKAGES = ["alpha", "ghost"];\n',
                                                encoding="utf-8")
    (proj / "packages").mkdir()
    (proj / "packages" / "alpha").mkdir()
    rules = {"dirLists": [{"id": "pkgs", "file": "scripts/build.mjs",
                           "extractRegex": r"const PACKAGES = \[([^\]]+)\]",
                           "baseDir": "packages", "why": "清单引用不存在的条目"}]}
    env, _, code = residue.scan(proj, rules)
    assert code == 1 and env["errors"] == 1
    assert env["hits"][0]["text"] == "ghost"


def test_dirlist_all_present_passes(proj):
    (proj / "scripts").mkdir()
    (proj / "scripts" / "build.mjs").write_text('const PACKAGES = ["alpha"];\n', encoding="utf-8")
    (proj / "packages" / "alpha").mkdir(parents=True)
    rules = {"dirLists": [{"id": "pkgs", "file": "scripts/build.mjs",
                           "extractRegex": r"const PACKAGES = \[([^\]]+)\]",
                           "baseDir": "packages", "why": "r"}]}
    _, _, code = residue.scan(proj, rules)
    assert code == 0


# ── deadLinks ───────────────────────────────────────────────────────────────

def test_deadlink_detected_with_line_number(proj):
    (proj / "docs" / "readme.md").write_text(
        "# 标题\n\n看 [这里](../gone/target.md)。\n", encoding="utf-8")
    rules = {"deadLinks": {"include": ["**/*.md"], "why": "相对链接目标不存在"}}
    env, _, code = residue.scan(proj, rules)
    assert code == 1 and env["hits"][0]["rule"] == "dead-links"
    assert env["hits"][0]["line"] == 3


def test_deadlink_external_and_anchor_ok(proj):
    (proj / "docs" / "readme.md").write_text(
        "[外](https://example.com) [锚](#sec) [图](pic.png)\n", encoding="utf-8")
    (proj / "docs" / "pic.png").write_bytes(b"x")
    rules = {"deadLinks": {"include": ["**/*.md"]}}
    _, _, code = residue.scan(proj, rules)
    assert code == 0


# ── glob 语义（对齐 Node 引擎） ─────────────────────────────────────────────

@pytest.mark.parametrize("pattern,relpath,expect", [
    ("**/*.md", "a.md", True),
    ("**/*.md", "docs/a.md", True),
    ("**/*.md", "docs/sub/a.md", True),
    ("**/*.md", "a.ts", False),
    ("docs/**/*.md", "docs/a.md", True),
    ("docs/**/*.md", "docs/sub/a.md", True),
    ("docs/**/*.md", "a.md", False),
    ("README.md", "README.md", True),
    ("*.md", "a.md", True),
    ("*.md", "docs/a.md", False),
])
def test_glob_semantics(pattern, relpath, expect):
    m = residue.glob_to_regexp(pattern)
    assert bool(m.match(relpath)) is expect, (pattern, relpath)


# ── 退出码契约 ──────────────────────────────────────────────────────────────

def test_missing_rules_exit_config(tmp_path):
    p = residue.main(["--project", str(tmp_path)])
    assert p == residue.EXIT_CONFIG


def test_generated_drift_requires_git(proj):
    rules = {"generatedDrift": [{"id": "d", "command": "true", "paths": ["out.txt"], "why": "r"}]}
    env, _, code = residue.scan(proj, rules, with_generated=True)
    # proj 不是 git 仓库 → git status 失败按配置错误计（drift error），信封 status=failed
    assert env["status"] == "failed"


def test_generated_drift_skipped_without_flag(proj):
    rules = {"generatedDrift": [{"id": "d", "command": "false", "paths": ["out.txt"], "why": "r"}]}
    _, _, code = residue.scan(proj, rules, with_generated=False)
    assert code == 0
