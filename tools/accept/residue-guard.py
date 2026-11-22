# -*- coding: utf-8 -*-
"""residue.py —— 通用残留守卫引擎（数据驱动，零项目硬编码，纯 Python 标准库）。

本模块是自包含引擎：只依赖标准库、不含任何 jedocsops 内部引用，
可被 mint 复制进目标项目独立运行（与原 Node 引擎「守卫代码进项目」同一契约）。

所有检测内容来自项目的 residue.rules.json（由 docs-ops 的 mint 铸造或手工编写）。规则类型：
  patterns        正则残留扫描（旧名字面量 / 令牌改名 / 过期计数…），含范围与行豁免
  dirLists        清单文件里声明的目录/条目必须真实存在
  deadLinks       Markdown 相对链接/图片目标存在性
  generatedDrift  生成物漂移：重跑 command 后 git status 必须干净（仅 --generated 时执行）

判定语义与原 residue-guard.mjs（Node ≥18）逐条对齐；一致性由合同测试
（同一 fixture + 同一 rules，Node 引擎与本引擎判定必须相同）守护。

用法：
  python residue.py --project <path> [--rules <path>] [--json] [--generated] [--verbose]
退出码：0 = 干净；1 = 有 error；2 = 配置/环境问题。
stdout 恒为结果信封 JSON；stderr 为人类可读明细。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CONFIG = 2

SKIP_DIRS_BASE = ("node_modules", ".git", "dist", ".tmp", "coverage", "build",
                  "__pycache__", ".venv", "venv", "target")
TEXT_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".java",
            ".kt", ".rb", ".php", ".cs", ".html", ".css", ".scss", ".json", ".md", ".txt",
            ".sh", ".yml", ".yaml", ".toml", ".sql", ".vue", ".svelte", ".properties",
            ".ini", ".conf", ".rst", ".env"}

DEAD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
DEAD_LINK_SKIP_RE = re.compile(r"^(https?:|mailto:|#|data:)")


class ConfigError(Exception):
    """规则文件缺失 / 解析失败 / 正则非法 —— 退出码 2。"""


def _ext_of(name: str) -> str:
    """与 Node '.' + name.split('.').pop().toLowerCase() 一致（含无点文件与 .env 形态）。"""
    return "." + name.rsplit(".", 1)[-1].lower()


def walk(root: Path, skip_dirs: set[str]) -> list[Path]:
    out: list[Path] = []
    if not root.is_dir():
        return out

    def rec(dir_path: Path) -> None:
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: p.name)
        except OSError:
            return
        for entry in entries:
            if entry.name in skip_dirs:
                continue
            if entry.is_dir():
                rec(entry)
            elif _ext_of(entry.name) in TEXT_EXT:
                out.append(entry)

    rec(root)
    return out


def glob_to_regexp(pattern: str) -> re.Pattern:
    """极简 glob（零依赖）：双星段匹配零层或多层目录（根级文件也命中）、单星段内、问号单字符。"""
    src = re.sub(r"[.+^${}()|[\]\\]", lambda m: "\\" + m.group(0), pattern)
    src = src.replace("**/", "\x01")
    src = src.replace("/**", "\x02")
    src = src.replace("**", "\x03")
    src = src.replace("*", "[^/]*")
    src = src.replace("?", "[^/]")
    src = src.replace("\x01", "(?:.*/)?")
    src = src.replace("\x02", "(?:/.*)?")
    src = src.replace("\x03", ".*")
    return re.compile("^" + src + "$")


def js_flags(flags: str) -> int:
    """JS RegExp flags 子集映射；g/u/y 不影响 test 语义，其余未知 flag 视为配置错误。"""
    value = 0
    for ch in flags:
        if ch == "i":
            value |= re.I
        elif ch == "m":
            value |= re.M
        elif ch == "s":
            value |= re.S
        elif ch in ("g", "u", "y"):
            continue
        else:
            raise ConfigError(f"不支持的 RegExp flag：{ch!r}")
    return value


def compile_regex(pattern: str, flags: str, label: str) -> re.Pattern:
    try:
        return re.compile(pattern, js_flags(flags or ""))
    except re.error as exc:
        raise ConfigError(f"规则 {label} 的正则非法：{exc}") from exc


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_rules(rules_path: Path) -> dict:
    if not rules_path.is_file():
        raise ConfigError(
            f"找不到规则文件：{rules_path}\n"
            "  请先用 docs-ops 的 mint 子命令铸造，或手工编写"
            "（schema 见 skill 的 references/residue-taxonomy.md）。"
        )
    try:
        return json.loads(_read_text(rules_path))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"规则文件解析失败：{exc}") from exc


def scan(project: Path, rules: dict, with_generated: bool = False,
         verbose: bool = False) -> tuple[dict, list[str], int]:
    """执行四类检测。返回 (envelope, 人类可读行, 退出码)。"""
    hits: list[dict] = []
    drift_errors: list[dict] = []

    skip_dirs = set(SKIP_DIRS_BASE) | set(rules.get("skipDirs") or [])
    all_files = walk(project, skip_dirs)

    def rel(path: Path) -> str:
        return path.relative_to(project).as_posix() if path != project else ""

    def in_scopes(rel_path: str, include=None, exclude=None) -> bool:
        """作用域判定：include 全匹配；exclude 与 `!` 前缀的 include 项做排除（后者优先）。"""
        def g(pat: str) -> re.Pattern:
            return glob_to_regexp(pat.lstrip("!") if pat.startswith("!") else pat)
        raw = list(include or [])
        include = [p for p in raw if not p.startswith("!")]
        negated = [p for p in raw if p.startswith("!")]
        if include and not any(glob_to_regexp(p).match(rel_path) for p in include):
            return False
        if any(g(p).match(rel_path) for p in negated + list(exclude or [])):
            return False
        return True

    # ── patterns：正则残留扫描 ────────────────────────────────────────────
    for rule in rules.get("patterns") or []:
        regex = compile_regex(rule["regex"], rule.get("flags") or "", rule.get("id", "?"))
        exempt_line = (compile_regex(rule["exemptLine"], "", rule["id"] + ".exemptLine")
                       if rule.get("exemptLine") else None)
        for path in all_files:
            r = rel(path)
            if not in_scopes(r, rule.get("include"), rule.get("exclude")):
                continue
            if rule.get("selfExemptFile") and r.endswith(rule["selfExemptFile"]):
                continue
            lines = _read_text(path).split("\n")
            for i, line in enumerate(lines):
                if not regex.search(line):
                    continue
                if exempt_line and exempt_line.search(line):
                    continue
                hits.append({"rule": rule.get("id"), "severity": rule.get("severity") or "error",
                             "file": r, "line": i + 1, "why": rule.get("why") or "",
                             "text": line.strip()[:140]})

    # ── dirLists：清单声明的条目必须真实存在 ─────────────────────────────
    for rule in rules.get("dirLists") or []:
        listing = project / rule["file"]
        if not listing.is_file():
            hits.append({"rule": rule.get("id"), "severity": rule.get("severity") or "error",
                         "file": rule["file"], "line": 0,
                         "why": "清单文件不存在（可能已被移动或删除）", "text": rule["file"]})
            continue
        extract = compile_regex(rule["extractRegex"], "s", rule.get("id", "?"))
        m = extract.search(_read_text(listing))
        if not m:
            continue
        for raw in m.group(1).split(","):
            name = raw.strip().replace('"', "").replace("'", "")
            if not name:
                continue
            if not (project / (rule.get("baseDir") or ".") / name).exists():
                hits.append({"rule": rule.get("id"), "severity": rule.get("severity") or "error",
                             "file": rule["file"], "line": 0,
                             "why": rule.get("why") or "清单引用的条目不存在（曾致静默跳过）",
                             "text": name})

    # ── deadLinks：Markdown 相对链接/图片目标存在性 ──────────────────────
    cfg = rules.get("deadLinks")
    if cfg:
        for path in all_files:
            r = rel(path)
            if not in_scopes(r, cfg.get("include") or ["**/*.md"], cfg.get("exclude") or []):
                continue
            rel_dir = path.relative_to(project).parent.as_posix()
            text = _read_text(path)
            for m in DEAD_LINK_RE.finditer(text):
                target = m.group(1)
                if DEAD_LINK_SKIP_RE.match(target):
                    continue
                clean = target.split("#")[0]
                if not clean:
                    continue
                if not (project / rel_dir / clean).exists():
                    hits.append({"rule": "dead-links", "severity": cfg.get("severity") or "error",
                                 "file": r, "line": text[:m.start()].count("\n") + 1,
                                 "why": cfg.get("why") or "相对链接目标不存在（路径改名残留）",
                                 "text": target})

    # ── generatedDrift：重跑生成命令后 git status 必须干净（仅 --generated） ─
    if with_generated:
        for rule in rules.get("generatedDrift") or []:
            try:
                subprocess.run(rule["command"], cwd=project, shell=True, timeout=600, check=True)
            except (subprocess.SubprocessError, OSError) as exc:
                drift_errors.append({"rule": rule.get("id"), "why": "生成命令执行失败",
                                     "text": str(exc)[:200]})
                continue
            try:
                dirty = subprocess.run(
                    ["git", "-C", str(project), "status", "--porcelain", "--",
                     *(rule.get("paths") or [])],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=120, check=True).stdout
            except (subprocess.SubprocessError, OSError) as exc:
                drift_errors.append({"rule": rule.get("id"), "why": "git status 失败（本规则需要 git 仓库）",
                                     "text": str(exc)[:200]})
                continue
            if dirty.strip():
                drift_errors.append({"rule": rule.get("id"),
                                     "why": "生成物已漂移：请重跑生成命令并提交",
                                     "text": " | ".join(dirty.strip().split("\n")[:10])})

    # ── 输出：stdout 恒为结果信封；stderr 为人类可读明细 ──────────────────
    errors = [h for h in hits if h["severity"] == "error"] + [
        {"rule": d["rule"], "file": "(drift)", "line": 0, "why": d["why"], "text": d["text"]}
        for d in drift_errors]

    lines: list[str] = []
    for h in hits:
        mark = "✗" if h["severity"] == "error" else "⚠"
        show_text = verbose or h["severity"] == "error"
        body = f"{mark} [{h['rule']}] {h['file']}:{h['line']}  {h['why']}"
        if show_text:
            body += f"\n    {h['text']}"
        lines.append(body)
    for d in drift_errors:
        lines.append(f"✗ [{d['rule']}] {d['why']}\n    {d['text']}")

    envelope = {
        "status": "passed" if not errors else "failed",
        "scanned": len(all_files),
        "errors": len(errors),
        "hits": hits if (verbose) else [h for h in hits if h["severity"] == "error"],
    }
    if not errors:
        lines.append(
            f"✓ 残留守卫通过（扫描 {len(all_files)} 个文件；"
            f"patterns {len(rules.get('patterns') or [])} / "
            f"dirLists {len(rules.get('dirLists') or [])} / "
            f"deadLinks {1 if rules.get('deadLinks') else 0} / "
            f"drift {len(rules.get('generatedDrift') or []) if with_generated else 'skip'}）")
        code = EXIT_OK
    else:
        lines.append(f"\n✗ 残留守卫失败：{len(errors)} 处 error。修复后重跑；"
                     "若属新残留类型，在 rules.json 追加规则（回归测试化）。")
        code = EXIT_FINDINGS
    return envelope, lines, code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="residue-guard",
                                     description="通用残留守卫引擎（Python 标准库版）")
    parser.add_argument("--project", default=None)
    parser.add_argument("--rules", default=None)
    parser.add_argument("--json", action="store_true", help="信封中包含 warn 级命中")
    parser.add_argument("--generated", action="store_true", help="追加生成物漂移检查")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    # stdout/stderr 统一 UTF-8（GBK 终端下信封含全角字符会 UnicodeEncodeError 崩溃）
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass

    project = Path(args.project or ".").resolve()
    rules_path = (Path(args.rules).resolve() if args.rules
                  else project / "tools" / "accept" / "residue.rules.json")
    try:
        rules = load_rules(rules_path)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return EXIT_CONFIG

    envelope, lines, code = scan(project, rules, with_generated=args.generated,
                                 verbose=args.verbose or args.json)
    for line in lines:
        print(line, file=sys.stderr)
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
