# je-docs-ops

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](docs/history/README.md)。

项目文档体系规范与残留检测的统一入口：**前置**让 agent「写对」（分层契约 + 模板 + 清单），**后置**让门禁「拦住」（语言无关残留检测 + 文档结构检查）。一个体系、一个入口。

通用的语言 / 链接 / 表格 / 命名格式规范归 `document-governance`（引用不重写）；本 skill 只拥有项目文档的**体系分层**与**残留检测**两项能力。

## 文档地图

正文层文档地图见 [docs/README.md](docs/README.md)；历史档案见 [docs/history/README.md](docs/history/README.md)。

## 安装

作为用户级 Skill 使用，放到 `~/.agents/skills/je-docs-ops/` 即可（本仓库即该目录）。

依赖：

- Python 3.9+（仅标准库，零第三方依赖）；
- 通用运行时库 `skills_runtime_toolkit`（提供 `report_output`：报告型 CLI 的 `--format/--json/--markdown/--out` 输出）。它按以下顺序定位，找不到则导入失败：
  1. 环境变量 `SKILLS_RUNTIME_TOOLKIT` 指向其根目录；
  2. 与本 skill 同级的 `skills-runtime-toolkit/` 目录。

这是一个纯库（`kind: library`，只被 import、不参与任务路由），不是需要单独安装或调用的技能。CLI 在加载时统一导入其 `report_output`，因此所有命令都依赖它——缺失时任何 CLI 子命令都会因 `ModuleNotFoundError` 无法启动。

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
