# -*- coding: utf-8 -*-
"""structure_check.py —— 文档结构前置检查（正文/历史两层契约）。

检查项（契约数据驱动，默认契约适配「docs/ 正文 + docs/history/ 历史」分层）：
  allowedDirs      bodyDir 下的 .md 必须属于已知一级目录（防止自由生长）
  historyLink      正文层文档必须含指向历史档案的跳转位（正文不写历史，只留跳转）
  roadmapPast      roadmap 类文件不得含过去时措辞（日期/已交付/本轮/时点计数…）
  historyIndex     历史目录存在时必须有 README 索引

项目可在 <project>/docs/doc-contract.json（或 --contract 指定路径）覆盖契约。
退出码：0 = 通过；1 = 有违规；2 = 配置/环境问题。
stdout 恒为结果信封 JSON；stderr 为人类可读明细。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CONFIG = 2

DEFAULT_CONTRACT = {
    "bodyDir": "docs",
    "historyDir": "docs/history",
    "historyIndex": "docs/history/README.md",
    "allowedDirs": None,  # null = 不限制；数组 = 仅允许这些 bodyDir 一级子目录
    "indexFiles": ["README.md", "index.md"],  # 免 historyLink 检查的索引文件
    "historyLinkExempt": [],  # 免 historyLink 检查的存量正文（相对路径；新写文档不得加入）
    "historyLinkRegex": r"\[[^\]]*\]\(([^)\s]*history[^)\s]*)\)",
    "historyLinkWhy": "正文层文档缺少「历史档案」跳转位（正文不写历史，只留跳转）",
    "historyLinkSeverity": "error",
    "roadmapFiles": ["docs/roadmap.md"],
    "roadmapPastPatterns": [r"\b20\d{2}-\d{2}-\d{2}\b", "已交付", "本轮", "首轮", "上轮",
                            "时点", "上次交付"],
    "roadmapWhy": "roadmap 只写未来方向，不得含过去时措辞/时点数据",
}


class ContractError(Exception):
    """契约文件缺失/解析失败/字段非法 —— 退出码 2。"""


def load_contract(contract_path: Path | None, project: Path) -> dict:
    contract = dict(DEFAULT_CONTRACT)
    path = contract_path or (project / "docs" / "doc-contract.json")
    if path.is_file():
        try:
            overrides = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ContractError(f"契约文件解析失败：{path}（{exc}）") from exc
        if not isinstance(overrides, dict):
            raise ContractError(f"契约文件必须是 JSON 对象：{path}")
        unknown = set(overrides) - set(DEFAULT_CONTRACT) - {"$doc"}
        if unknown:
            raise ContractError(f"契约含未知字段：{sorted(unknown)}（合法字段见 DEFAULT_CONTRACT）")
        contract.update(overrides)
    if not contract.get("bodyDir"):
        raise ContractError("契约缺少 bodyDir")
    return contract


def check(project: Path, contract: dict) -> tuple[dict, list[str], int]:
    findings: list[dict] = []
    body_dir = project / contract["bodyDir"]
    history_dir = project / contract["historyDir"]

    if not body_dir.is_dir():
        return ({"status": "passed", "scanned": 0, "violations": 0, "findings": [],
                 "note": f"bodyDir 不存在，跳过：{contract['bodyDir']}"},
                [f"⚠ bodyDir 不存在，跳过：{contract['bodyDir']}"], EXIT_OK)

    md_files = sorted(p for p in body_dir.rglob("*.md"))

    def rel(path: Path) -> str:
        return path.relative_to(project).as_posix()

    history_link_re = re.compile(contract["historyLinkRegex"])
    index_names = set(contract.get("indexFiles") or [])
    allowed = contract.get("allowedDirs")

    # ① allowedDirs：正文层一级目录归属
    for path in md_files:
        r = rel(path)
        inside_history = history_dir in path.parents or path == history_dir
        if inside_history:
            continue
        parent = path.parent.relative_to(body_dir).as_posix()
        top = parent.split("/")[0] if parent != "." else "."
        if allowed is not None and top not in allowed and r not in index_names:
            findings.append({"check": "allowed-dirs", "severity": "error", "file": r,
                             "line": 0, "why": f"正文层文件不在已知目录（合法：{allowed}）",
                             "text": r})

    # ② historyLink：正文层文档必须含历史跳转位（契约豁免清单只收纳存量正文）
    exempt_links = set(contract.get("historyLinkExempt") or [])
    for path in md_files:
        r = rel(path)
        inside_history = history_dir in path.parents or path == history_dir
        if inside_history or path.name in index_names or r in exempt_links:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not history_link_re.search(text):
            findings.append({"check": "history-link",
                             "severity": contract.get("historyLinkSeverity") or "error",
                             "file": r, "line": 0,
                             "why": contract.get("historyLinkWhy") or "缺少历史跳转位",
                             "text": ""})

    # ③ roadmapPast：roadmap 不得含过去时措辞
    for name in contract.get("roadmapFiles") or []:
        path = project / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.split("\n")):
            for pattern in contract.get("roadmapPastPatterns") or []:
                if re.search(pattern, line):
                    findings.append({"check": "roadmap-past", "severity": "error", "file": name,
                                     "line": i + 1, "why": contract.get("roadmapWhy"),
                                     "text": line.strip()[:140]})
                    break

    # ④ historyIndex：历史目录存在则必须有索引
    if history_dir.is_dir() and not (project / contract["historyIndex"]).is_file():
        findings.append({"check": "history-index", "severity": "error",
                         "file": contract["historyIndex"], "line": 0,
                         "why": "历史目录存在但缺少 README 索引（档案必须可发现）",
                         "text": contract["historyIndex"]})

    errors = [f for f in findings if f["severity"] == "error"]
    lines = [f"{'✗' if f['severity'] == 'error' else '⚠'} [{f['check']}] "
             f"{f['file']}:{f['line']}  {f['why']}" + (f"\n    {f['text']}" if f["text"] else "")
             for f in findings]
    envelope = {"status": "passed" if not errors else "failed",
                "scanned": len(md_files), "violations": len(errors), "findings": findings}
    if not errors:
        lines.append(f"✓ 文档结构检查通过（扫描 {len(md_files)} 个 .md；"
                     f"allowedDirs={'on' if allowed else 'off'} / historyLink=on / "
                     f"roadmapPast={len(contract.get('roadmapFiles') or [])} 文件 / historyIndex=on）")
        code = EXIT_OK
    else:
        lines.append(f"\n✗ 文档结构检查失败：{len(errors)} 处 error。"
                     "按 nodes/ 方法论修正结构后重跑。")
        code = EXIT_FINDINGS
    return envelope, lines, code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="je-docs-ops-structure",
                                     description="文档结构前置检查（正文/历史两层契约）")
    parser.add_argument("--project", default=".")
    parser.add_argument("--contract", default=None, help="契约 JSON 路径（默认 <project>/docs/doc-contract.json）")
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    try:
        contract = load_contract(Path(args.contract).resolve() if args.contract else None, project)
    except ContractError as exc:
        print(exc, file=sys.stderr)
        return EXIT_CONFIG
    envelope, lines, code = check(project, contract)
    for line in lines:
        print(line, file=sys.stderr)
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
