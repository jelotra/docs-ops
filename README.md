# docs-ops

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](docs/history/README.md)。

文档体系多 lane 统一入口，按文档域分治：**docs-system** 管项目说明文档（前置写对 + 后置拦住），**demand-lifecycle** 管需求文档（结构分类 + 状态映射 + 结构门禁）。两 lane 检查对象互斥、契约分离、引擎独立。

本 skill 自带通用文档的最小格式规范与[交付前清单](assets/checklists/preflight.md)；深度格式 lint（emoji 词表、超宽表格等）可由 `document-governance` 可选增强。

## 文档地图

正文层文档地图见 [docs/README.md](docs/README.md)；历史档案见 [docs/history/README.md](docs/history/README.md)；节点与链路见 [node-flow.json](references/workflow/node-flow.json)。

## 安装

作为用户级 Skill，放到 `~/.agents/skills/docs-ops/` 即可（本仓库即该目录）。

依赖：**仅 Python 3.9+**（标准库，零第三方依赖），开箱即用。同家族 `skills_runtime_toolkit` 若存在则用于报告输出，缺失时 CLI 自动回退内置实现。

## 快速开始

统一入口脚本：`scripts/docs-ops.py`。所有命令支持 `--format text|json|markdown`（或 `--json` / `--markdown`）与 `--out <文件>`。

```bash
# ── docs-system lane ──
python scripts/docs-ops.py check --project <项目>          # 结构前置 + 残留守卫，退出码 0/1/2
python scripts/docs-ops.py new --type body-doc|roadmap|reference-cli|history-index --out <路径>
python scripts/docs-ops.py migrate --file <旧文档> --project <项目>
python scripts/docs-ops.py residue --project <项目> [--generated]

# ── demand-lifecycle lane ──
python scripts/docs-ops.py demand --project <项目>          # 需求文档结构检查
```

两 lane 隔离：项目的 `docs/doc-contract.json` 配 `exemptDirs: ["docs/request"]` 让 docs-system 跳过需求目录，demand 只扫 `docs/request/`。需求契约默认模板见 [demand-contract.json](assets/schemas/demand-contract.json)。

## 验证

```bash
python -I -m pytest tests -q   # 结构 + 引擎行为 + 合同测试（含两 lane 行为测试）
python tools/run_tests.py      # 并行入口
python scripts/docs-ops.py check --project .   # 本仓库自有文档体系门禁
```

结构测试只能证明目录与链路一致，不能证明行为正确；行为由上述测试覆盖。
