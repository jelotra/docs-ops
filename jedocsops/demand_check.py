# -*- coding: utf-8 -*-
"""demand_check.py —— 需求生命周期文档结构检查（demand-lifecycle lane）。

与 structure_check.py（docs-system lane）隔离：本引擎只扫描
<project>/docs/request/<id>-<slug>/，绝不触碰正文/历史层。

检查项（契约数据驱动，默认契约适配 Workloop docs/request/ 布局）：
  required-files  每个需求至少含 01-spec.md（error）
  numbering       编号文件 >=02 时须按 01..N 连续，缺号报 warning（允许缺 02/中间号）
  acceptance-ids  01-spec.md 的「验收标准」段须含 - [ ] A<n> 编号（error）
  traceability    03-plan.md 若存在须含「验收追溯」段（warning）
  pointer         需求目录名须符合 <id>-<slug> kebab-case（error）
  dashboard-link  需求目录须在 docs/dashboard/ 有同名或含 id 的卡片（warning，可选）

项目可在 <project>/docs/demand-contract.json 覆盖契约。
退出码：0 = 通过；1 = 有 error；2 = 配置/环境问题。
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
    "requestDir": "docs/request",          # 需求全量产出物根目录
    "dashboardDir": "docs/dashboard",      # 看板卡片目录（进度视图）
    "requiredFiles": ["01-spec.md"],       # 每个需求必备文件
    "numberedPattern": r"^(\d{2})-[a-z0-9-]+\.md$",  # 编号文件命名
    "numberingStrict": False,              # False = 缺号只报 warning；True = 缺号报 error
    "acceptanceHeading": "验收标准",
    "acceptancePattern": r"^\s*-\s*\[[ xX]\]\s*A(\d+)",  # - [ ] A<n>
    "traceabilityFile": "03-plan.md",
    "traceabilityHeading": "验收追溯",
    "pointerPattern": r"^[A-Z]+-?\d+-[a-z0-9]+(?:-[a-z0-9]+)*$",  # DEMAND-001-xxx / R001-xxx
    "checkDashboard": True,                # 是否检查看板卡片存在
    "note": "需求文档结构契约；与 docs/doc-contract.json（正文/历史）互不干涉。",
}


class ContractError(Exception):
    """契约文件缺失/解析失败/字段非法 —— 退出码 2。"""


def load_contract(contract_path: Path | None, project: Path) -> dict:
    contract = dict(DEFAULT_CONTRACT)
    path = contract_path or (project / "docs" / "demand-contract.json")
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
    return contract


def _find_requests(project: Path, request_dir: str) -> list[Path]:
    root = project / request_dir
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def check(project: Path, contract: dict) -> tuple[dict, list[str], int]:
    findings: list[dict] = []
    request_dirs = _find_requests(project, contract["requestDir"])

    def add(check_name: str, severity: str, file: str, why: str, text: str = "") -> None:
        findings.append({"check": check_name, "severity": severity, "file": file,
                         "line": 0, "why": why, "text": text})

    numbered_re = re.compile(contract["numberedPattern"])
    pointer_re = re.compile(contract["pointerPattern"])
    accept_re = re.compile(contract["acceptancePattern"])
    numbering_severity = "error" if contract.get("numberingStrict") else "warning"

    dashboard_files: list[str] = []
    if contract.get("checkDashboard"):
        dash = project / contract["dashboardDir"]
        if dash.is_dir():
            dashboard_files = [p.name for p in dash.rglob("*.md")]

    for req in request_dirs:
        rel = req.relative_to(project).as_posix()

        # ⑤ pointer：目录名 <id>-<slug>
        if not pointer_re.match(req.name):
            add("pointer", "error", rel,
                f"需求目录名须符合 <id>-<slug> kebab-case（正则：{contract['pointerPattern']}）",
                req.name)

        # ① required-files
        for required in contract.get("requiredFiles") or []:
            if not (req / required).is_file():
                add("required-files", "error", f"{rel}/{required}",
                    f"需求缺少必备文件：{required}")

        # ② numbering：编号文件须 01..N 连续
        nums: list[int] = []
        for p in sorted(req.glob("*.md")):
            m = numbered_re.match(p.name)
            if m:
                nums.append(int(m.group(1)))
        if nums:
            nums_sorted = sorted(nums)
            missing = [n for n in range(1, max(nums_sorted) + 1) if n not in nums_sorted]
            for n in missing:
                add("numbering", numbering_severity, rel,
                    f"编号文件缺 {n:02d}-*（现有最大 {max(nums_sorted):02d}；允许缺号但须有意为之）",
                    f"缺 {n:02d}")

        # ③ acceptance-ids：01-spec 的验收标准段须含 A<n>
        spec = req / "01-spec.md"
        if spec.is_file():
            text = spec.read_text(encoding="utf-8", errors="replace")
            lines = text.split("\n")
            heading = contract["acceptanceHeading"]
            in_section = False
            found_ids: list[int] = []
            for line in lines:
                if line.strip().startswith("## "):
                    in_section = heading in line
                    continue
                if in_section:
                    m = accept_re.match(line)
                    if m:
                        found_ids.append(int(m.group(1)))
            if not found_ids:
                add("acceptance-ids", "error", f"{rel}/01-spec.md",
                    f"「{heading}」段缺少 - [ ] A<n> 编号验收项（机器门禁无法校验）")

        # ④ traceability：03-plan 须含验收追溯段
        plan = req / contract["traceabilityFile"]
        if plan.is_file():
            text = plan.read_text(encoding="utf-8", errors="replace")
            if contract["traceabilityHeading"] not in text:
                add("traceability", "warning", f"{rel}/{contract['traceabilityFile']}",
                    f"缺少「{contract['traceabilityHeading']}」段（验收项无法逐条追溯到任务）")

        # ⑥ dashboard-link：看板卡片存在
        if contract.get("checkDashboard") and dashboard_files:
            req_id = req.name.split("-")[0:2]
            # 宽松匹配：卡片名含需求 id 前缀（如 DEMAND-001）
            id_prefix = "-".join(req_id) if len(req_id) == 2 else req.name.split("-")[0]
            if not any(id_prefix in name for name in dashboard_files):
                add("dashboard-link", "warning", rel,
                    f"docs/dashboard/ 下未发现含 {id_prefix} 的进度卡片（进度视图缺失）")

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    lines = [f"{'✗' if f['severity'] == 'error' else '⚠'} [{f['check']}] "
             f"{f['file']}  {f['why']}" + (f"\n    {f['text']}" if f["text"] else "")
             for f in findings]
    envelope = {
        "status": "passed" if not errors else "failed",
        "scanned": len(request_dirs),
        "errors": len(errors),
        "warnings": len(warnings),
        "findings": findings,
    }
    if not errors:
        lines.append(f"✓ 需求文档结构检查通过（扫描 {len(request_dirs)} 个需求；"
                     f"errors=0 / warnings={len(warnings)}）")
        code = EXIT_OK
    else:
        lines.append(f"\n✗ 需求文档结构检查失败：{len(errors)} 处 error，{len(warnings)} 处 warning。")
        code = EXIT_FINDINGS
    return envelope, lines, code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="docs-ops-demand",
                                     description="需求生命周期文档结构检查（demand-lifecycle lane）")
    parser.add_argument("--project", default=".")
    parser.add_argument("--contract", default=None, help="契约 JSON 路径（默认 <project>/docs/demand-contract.json）")
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
