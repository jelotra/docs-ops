"""Report CLI skeleton; domain renderers belong to this skill.

je-docs-ops 统一入口：
  describe  骨架自描述（脚手架契约，勿破坏其输出形状）
  check     一次跑完：文档结构前置检查 + 残留守卫检测
  new       从模板起文档（自带历史跳转位）
  migrate   旧文档改造操作清单（先归档、再重写）
  residue   仅跑残留检测引擎（pattern/dirList/deadLinks/generatedDrift）
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

configured = os.environ.get("SKILLS_RUNTIME_TOOLKIT")
toolkit = Path(configured) if configured else Path(__file__).resolve().parents[2] / "skills-runtime-toolkit"
sys.path.insert(0, str(toolkit))
try:
    from skills_runtime_toolkit.report_output import add_report_arguments, emit_report  # noqa: E402
except ImportError:  # 纯可选依赖缺失时内联等价实现，保证核心命令不瘫痪
    import argparse as _argparse

    def add_report_arguments(parser: _argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--format", choices=("text", "json", "markdown"), default="text")
        group.add_argument("--json", dest="format", action="store_const", const="json")
        group.add_argument("--markdown", "--md", dest="format", action="store_const", const="markdown")
        parser.add_argument("--out", help="Write the selected format to a new file.")

    def emit_report(report, output_format, text_renderer, markdown_renderer, out=None) -> None:
        if output_format == "json":
            text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        elif output_format == "markdown":
            text = markdown_renderer(report)
        else:
            text = text_renderer(report)
        text = text.rstrip("\n") + "\n"
        if out is not None:
            with open(out, "x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
            sys.stderr.write(f"Saved report: {out}\n")
        sys.stdout.write(text)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jedocsops import residue, structure_check  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
DOC_TYPES = {
    "body-doc": "body-doc.template.md",
    "history-index": "history-index.template.md",
    "roadmap": "roadmap.template.md",
    "reference-cli": "reference-cli.template.md",
}

# migrate 用的「过去时措辞」启发式（与 n03-archive-flow 方法论一致）
MIGRATE_PAST_RE = re.compile(
    r"\b20\d{2}-\d{2}-\d{2}\b|已交付|已完成|本轮|首轮|上轮|N\d{1,2}\b|P[0-3]\b|时点")


def _cmd_describe(args) -> tuple[int, dict]:
    result = {"status": "ok", "data": {"name": "je-docs-ops", "mode": "read-only"}}
    emit_report(result, args.format, lambda data: data["data"]["name"],
                lambda data: "# " + data["data"]["name"], args.out)
    return 0


def _render_findings_rows(findings: list[dict]) -> str:
    if not findings:
        return "| 检查项 | 文件 | 行 | 说明 |\n|---|---|---|---|\n| （无） | | | |"
    rows = []
    for f in findings[:40]:
        why = (f.get("why") or "").replace("|", "\\|")
        text = (f.get("text") or "").replace("|", "\\|")[:60]
        rows.append(f"| {f.get('check', f.get('rule'))} | {f.get('file')}:{f.get('line')} | "
                    f"{why} | {text} |")
    return "| 检查项 | 位置 | 说明 | 摘录 |\n|---|---|---|---|\n" + "\n".join(rows)


def _cmd_check(args) -> tuple[int, dict]:
    project = Path(args.project).resolve()
    codes: list[int] = []
    data: dict = {"project": str(project)}

    if not args.skip_structure:
        try:
            contract = structure_check.load_contract(
                Path(args.contract).resolve() if args.contract else None, project)
            env, lines, code = structure_check.check(project, contract)
        except structure_check.ContractError as exc:
            print(exc, file=sys.stderr)
            return 2
        for line in lines:
            print(line, file=sys.stderr)
        data["structure"] = env
        codes.append(code)

    if not args.skip_residue:
        rules_path = Path(args.rules).resolve() if args.rules \
            else project / "tools" / "accept" / "residue.rules.json"
        try:
            rules = residue.load_rules(rules_path)
        except residue.ConfigError as exc:
            print(exc, file=sys.stderr)
            return 2
        env, lines, code = residue.scan(project, rules)
        for line in lines:
            print(line, file=sys.stderr)
        data["residue"] = env
        codes.append(code)

    status = "ok" if all(c == 0 for c in codes) else "failed"
    result = {"status": status, "data": data}
    emit_report(result, args.format,
                lambda d: f"check：{status}\nstructure={d['data'].get('structure', {}).get('status')} "
                          f"residue={d['data'].get('residue', {}).get('status')}",
                lambda d: "# check 报告\n\n## 结构检查\n\n"
                          + _render_findings_rows((d["data"].get("structure") or {}).get("findings", []))
                          + "\n\n## 残留检测\n\n"
                          + _render_findings_rows((d["data"].get("residue") or {}).get("hits", [])),
                args.out)
    return max(codes) if codes else 0


def _cmd_new(args) -> tuple[int, dict]:
    template_name = DOC_TYPES.get(args.doc_type)
    template_path = TEMPLATE_DIR / template_name
    if not template_path.is_file():
        print(f"✗ 模板缺失：{template_path}", file=sys.stderr)
        return 2
    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"✗ 目标已存在（--force 覆盖）：{out}", file=sys.stderr)
        return 1
    title = args.title or out.stem

    # 历史索引跳转位：从目标文件位置到 docs/history/README.md 的相对路径
    out_abs = out.resolve()
    project = Path(args.project).resolve() if args.project else Path.cwd()
    history_index = project / "docs" / "history" / "README.md"
    try:
        rel_history = (history_index).resolve().relative_to(out_abs.parent).as_posix()
    except ValueError:
        rel_history = os.path.relpath(history_index.resolve(), out_abs.parent).replace("\\", "/")

    content = (template_path.read_text(encoding="utf-8")
               .replace("$title", title)
               .replace("$historyPath", rel_history))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    data = {"created": str(out), "type": args.doc_type,
            "historyJump": rel_history}
    result = {"status": "ok", "data": data}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"✓ created {out}（type={args.doc_type}，历史跳转位 → {rel_history}）")
    return 0


def _cmd_migrate(args) -> tuple[int, dict]:
    source = Path(args.file).resolve()
    if not source.is_file():
        print(f"✗ 文件不存在：{source}", file=sys.stderr)
        return 2
    project = Path(args.project).resolve()
    history_dir = Path(args.history_dir) if args.history_dir else project / "docs" / "history"
    text = source.read_text(encoding="utf-8", errors="replace")

    move_lines, keep_lines = [], []
    for i, line in enumerate(text.split("\n")):
        (move_lines if MIGRATE_PAST_RE.search(line) else keep_lines).append(
            {"line": i + 1, "text": line.strip()[:120]})

    rel_source = source.relative_to(project).as_posix() if source.is_relative_to(project) else source.name
    archive_target = f"{history_dir.as_posix().rstrip('/')}/{source.stem}.md"
    steps = [
        f"1. git mv {rel_source} {archive_target}  # 原文整体进历史，事实零丢失",
        f"2. 在原路径用 body-doc 骨架重写：python scripts/je-docs-ops.py new --type body-doc "
        f"--out {rel_source} --title \"{source.stem}\"",
        f"3. 重写稿只写当前是什么；历史细节一律链接到 {archive_target}",
        f"4. 跑门禁：python scripts/je-docs-ops.py check --project {project}",
    ]
    data = {
        "source": rel_source,
        "archiveTarget": archive_target,
        "moveLines": move_lines,
        "keepLinesCount": len(keep_lines),
        "steps": steps,
    }
    result = {"status": "ok", "data": data}
    emit_report(result, args.format,
                lambda d: f"migrate 计划：{d['data']['source']} → {d['data']['archiveTarget']}"
                          f"（{len(d['data']['moveLines'])} 行含历史措辞）",
                lambda d: "# migrate 计划\n\n## 操作步骤\n\n"
                          + "\n".join(d["data"]["steps"])
                          + "\n\n## 建议随原文归档的行（含过去时/时点措辞）\n\n"
                          + _render_findings_rows(
                              [{"check": "move", "file": d["data"]["source"], "line": m["line"],
                                "why": "历史措辞", "text": m["text"]} for m in d["data"]["moveLines"]]),
                args.out)
    return 0


def _cmd_residue(args) -> tuple[int, dict]:
    from jedocsops import extract_ledger, mint as mint_mod

    # 模式① ledger 提取：转发 extract_ledger.main（stdout 信封契约一致）
    if args.extract_ledger:
        if not args.repo:
            print("✗ --extract-ledger 需要 --repo", file=sys.stderr)
            return 2
        return extract_ledger.main(["--repo", args.repo,
                                    *(["--commits", args.commits] if args.commits else []),
                                    *(["--commit", args.commit] if args.commit else []),
                                    *(["--range", args.range_] if args.range_ else []),
                                    "--min-count", str(args.min_count)])

    # 模式② 铸造：转发 mint.mint（幂等产物 + 信封）
    if args.mint:
        project = Path(args.project).resolve()
        try:
            envelope = mint_mod.mint(project,
                                     Path(args.ledger).resolve() if args.ledger else None,
                                     args.min_count, args.force)
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
        print(f"✓ 铸造完成（runner={envelope['runner']}）：新建 {len(envelope['created'])}、"
              f"跳过 {len(envelope['skipped'])}。守卫用法："
              f"python tools/accept/residue-guard.py --project <path>。", file=sys.stderr)
        return 0

    # 模式③ 检测（默认）
    project = Path(args.project).resolve()
    rules_path = Path(args.rules).resolve() if args.rules \
        else project / "tools" / "accept" / "residue.rules.json"
    try:
        rules = residue.load_rules(rules_path)
    except residue.ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2
    env, lines, code = residue.scan(project, rules, with_generated=args.generated,
                                    verbose=args.verbose)
    for line in lines:
        print(line, file=sys.stderr)
    result = {"status": env["status"], "data": env}
    emit_report(result, args.format,
                lambda d: f"residue：{d['data']['status']}（errors={d['data']['errors']}，"
                          f"scanned={d['data']['scanned']}）",
                lambda d: "# 残留检测报告\n\n" + _render_findings_rows(d["data"].get("hits", [])),
                args.out)
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(prog="je-docs-ops")
    commands = parser.add_subparsers(dest="command", required=True)

    describe = commands.add_parser("describe")
    add_report_arguments(describe)
    describe.set_defaults(func=_cmd_describe)

    check = commands.add_parser("check", help="文档结构前置检查 + 残留守卫，一次跑完")
    add_report_arguments(check)
    check.add_argument("--project", default=".")
    check.add_argument("--contract", default=None, help="文档契约 JSON（默认 <project>/docs/doc-contract.json）")
    check.add_argument("--rules", default=None, help="残留规则 JSON（默认 <project>/tools/accept/residue.rules.json）")
    check.add_argument("--skip-structure", action="store_true")
    check.add_argument("--skip-residue", action="store_true")
    check.set_defaults(func=_cmd_check)

    new = commands.add_parser("new", help="从模板新建文档（自带历史跳转位）")
    new.add_argument("--type", dest="doc_type", required=True, choices=sorted(DOC_TYPES))
    new.add_argument("--out", required=True, help="新文档目标路径")
    new.add_argument("--title", default=None)
    new.add_argument("--project", default=None)
    new.add_argument("--force", action="store_true")
    new.add_argument("--json", action="store_true")
    new.set_defaults(func=_cmd_new)

    migrate = commands.add_parser("migrate", help="旧文档改造操作清单（先归档、再重写）")
    add_report_arguments(migrate)
    migrate.add_argument("--file", required=True)
    migrate.add_argument("--project", default=".")
    migrate.add_argument("--history-dir", default=None)
    migrate.set_defaults(func=_cmd_migrate)

    residue_cmd = commands.add_parser("residue", help="残留检测 / 铸造 / ledger 提取")
    add_report_arguments(residue_cmd)
    residue_cmd.add_argument("--project", default=".")
    residue_cmd.add_argument("--rules", default=None)
    residue_cmd.add_argument("--generated", action="store_true", help="追加生成物漂移检查")
    residue_cmd.add_argument("--verbose", action="store_true")
    residue_cmd.add_argument("--mint", action="store_true", help="铸造守卫进项目（需 --project）")
    residue_cmd.add_argument("--extract-ledger", action="store_true", help="提取 git ledger（需 --repo）")
    residue_cmd.add_argument("--repo", default=None)
    residue_cmd.add_argument("--commits", default=None, help="逗号分隔多个 sha")
    residue_cmd.add_argument("--commit", default=None, help="单个 sha")
    residue_cmd.add_argument("--range", dest="range_", default=None)
    residue_cmd.add_argument("--ledger", default=None)
    residue_cmd.add_argument("--min-count", type=int, default=3)
    residue_cmd.add_argument("--force", action="store_true")
    residue_cmd.set_defaults(func=_cmd_residue)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OSError as exc:
        parser.exit(1, "Cannot save report: " + exc.__class__.__name__ + "\n")
