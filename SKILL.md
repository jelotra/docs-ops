---
name: je-docs-ops
description: "项目文档体系规范与残留检测统一入口：前置（文档分层/正文规则/归档流程/模板）+ 后置（语言无关残留检测引擎，pattern/dirList/deadLinks/generatedDrift）。触发：文档体系、文档分层、正文规范、历史归档、残留检测、改名清扫、旧名扫描、rename ledger、重构验收残留、升级后旧标识符、生成物漂移。"
argument-hint: "<项目路径> / <文档类型> / <期望输出>"
user-invocable: true
metadata:
  version: "0.2.0"
---

# je-docs-ops

## 1. 定位

<!-- skill-content:start -->
一个体系、一个入口：**前置**让 agent「写对」（分层契约 + 模板 + 清单），**后置**让门禁「拦住」（语言无关残留检测 + 结构检查）。通用文档格式规范归 `document-governance`（引用不重写）；本 skill 拥有项目文档**体系分层**与**残留检测**能力。
<!-- skill-content:end -->

本 Skill 采用 Workloop 结构：方法论在 `nodes/`，契约与链路在
`references/`，机器可读的节点与链路契约在 [`node-flow.json`](references/workflow/node-flow.json)。

## 2. 三层分工（不要混）

| 层 | 位置 | 内容 | 不做什么 |
|---|---|---|---|
| 方法论 | `nodes/` | 每个节点一篇 README：何时进入、怎么做、产出、何时算完 | 不写实例事实 |
| 契约与链路 | `references/` | 架构边界、残留类型学、分层规范、链路契约 | 不写节点方法 |
| 可执行层 | `jedocsops/` + `scripts/` | 统一入口 CLI 与自包含检测/铸造引擎 | 不授予任何权限 |

事实归各自的拥有者：本 skill 不保存任何项目/环境/账号事实；项目特有内容全部在项目的 `residue.rules.json` 与 `doc-contract.json` 数据里。

## 3. 统一入口

```bash
# 一次跑完：文档结构前置检查 + 残留守卫（退出码 0/1/2）
python scripts/je-docs-ops.py check --project <项目>

# 从模板新建文档（自带历史跳转位）
python scripts/je-docs-ops.py new --type body-doc|roadmap|reference-cli|history-index --out <路径>

# 旧文档改造：先归档再重写的操作清单
python scripts/je-docs-ops.py migrate --file <旧文档> --project <项目>

# 仅残留检测 / 铸造 / ledger 提取
python scripts/je-docs-ops.py residue --project <项目> [--generated]
python scripts/je-docs-ops.py residue --mint --project <项目> [--ledger ledger.json]
python scripts/je-docs-ops.py residue --extract-ledger --repo <项目> --commit <sha>
```

## 4. 节点

- [n01-architecture 文档架构分层：正文/历史两层目录契约](nodes/n01-architecture/README.md)
- [n02-body-rules 正文前置规范：现在时、无历史措辞、跳转位](nodes/n02-body-rules/README.md)
- [n03-archive-flow 归档流程：先 git mv 归档再重写](nodes/n03-archive-flow/README.md)
- [n04-guard 后置检测：残留检测能力与守卫接入](nodes/n04-guard/README.md)

链路：

| 链路 | 何时 | 节点序列 |
|---|---|---|
| `docs-system` | 新建或改造项目文档体系、写正文文档、归档历史、跑残留门禁 | n01-architecture → n02-body-rules → n03-archive-flow → n04-guard |

## 5. 验证

结构测试只能证明目录与链路一致，不能证明行为正确；行为由下列测试覆盖：

```bash
python -I -m pytest tests -q          # 结构 + 引擎行为 + 合同测试（含 Node 对拍）
python tools/run_tests.py             # 并行入口
```

报告型 CLI：`--format text|json|markdown`、`--json`、`--markdown`、`--out`；依赖同级 `skills-runtime-toolkit` 或 `SKILLS_RUNTIME_TOOLKIT` 指向其根目录。

## 6. 知识索引

- [残留类型学与规则 schema](references/residue-taxonomy.md)：五层残留分类、每层检测原语、rules.json 完整契约。
- [文档分层规范](references/doc-system.md)：正文/历史两层判定、模板契约、目录契约数据。
- [架构](references/architecture.md)

## 7. 扩展

新增节点三步：加 `nodes/<id>/README.md` → 改 `references/workflow/node-flow.json` → 更新本文件节点列表。
受管文件（`references/workflow/node-flow.json`、`tests/test_structure.py`、`tests/test_cli_contract.py`、`conftest.py`、`tools/run_tests.py`）由脚手架维护，手改会触发 `PROJECT-DRIFT`。
