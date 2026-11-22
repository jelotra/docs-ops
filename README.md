# je-docs-ops

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](docs/history/README.md)。

项目文档体系规范与残留检测的统一入口：**前置**让 agent「写对」（分层契约 + 模板 + 清单），**后置**让门禁「拦住」（语言无关残留检测 + 文档结构检查）。一个体系、一个入口。

本 skill 自带通用文档的最小格式规范与[交付前清单](assets/checklists/preflight.md)，独立即可完成分层、写作、归档与残留检测的全部职责；深度格式 lint（emoji 词表、超宽表格等）可由 `document-governance` 可选增强，非必需。

## 文档地图

正文层文档地图见 [docs/README.md](docs/README.md)；历史档案见 [docs/history/README.md](docs/history/README.md)；交付前自检见 [preflight 清单](assets/checklists/preflight.md)。

## 安装

作为用户级 Skill 使用，放到 `~/.agents/skills/je-docs-ops/` 即可（本仓库即该目录）。

依赖：**仅 Python 3.9+**（标准库，零第三方依赖），开箱即用。

同家族的 `skills_runtime_toolkit` 若存在会被用于报告输出（`--format/--json/--markdown/--out`）；它是可选库，缺失时 CLI 自动用内置等价实现，所有命令照常工作。

## 快速开始

统一入口脚本：`scripts/je-docs-ops.py`。所有命令都支持报告格式 `--format text|json|markdown`（或 `--json` / `--markdown`）与 `--out <文件>`。

```bash
# 一次跑完：文档结构前置检查 + 残留守卫，退出码 0/1/2
python scripts/je-docs-ops.py check --project <项目>

# 从模板新建文档（自带历史跳转位）
python scripts/je-docs-ops.py new --type body-doc|roadmap|reference-cli|history-index --out <路径>

# 旧文档改造：输出「先 git mv 归档再重写」的操作清单
python scripts/je-docs-ops.py migrate --file <旧文档> --project <项目>

# 仅残留检测；--generated 追加生成物漂移检测
python scripts/je-docs-ops.py residue --project <项目> [--generated]
```

`check` 默认读取 `<项目>/docs/doc-contract.json`（文档契约）与 `<项目>/tools/accept/residue.rules.json`（残留规则），可用 `--contract` / `--rules` 覆写；`--skip-structure` / `--skip-residue` 可分别跳过某一项检测。完整参数见 [CLI 命令参考](docs/concepts/cli-reference.md)。

## 验证

```bash
python -I -m pytest tests -q   # 结构 + 引擎行为 + 合同测试（含 Node 对拍）
python tools/run_tests.py      # 并行入口
python scripts/je-docs-ops.py check --project .   # 本仓库自有文档体系门禁
```

结构测试只能证明目录与链路一致，不能证明行为正确；行为由上述测试覆盖。
