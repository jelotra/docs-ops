---
name: docs-ops
description: "文档体系多 lane 统一入口：docs-system（项目说明文档分层/正文规则/归档/残留检测 pattern/dirList/deadLinks/generatedDrift）+ demand-lifecycle（需求文档结构/状态视图/结构门禁）。触发：文档体系、文档分层、正文规范、历史归档、残留检测、改名清扫、旧名扫描、rename ledger、重构验收残留、升级后旧标识符、生成物漂移、需求文档、需求目录、需求结构、需求状态、验收编号、需求门禁。"
argument-hint: "<项目路径> / <lane> / <文档类型> / <期望输出>"
user-invocable: true
metadata:
  version: "0.4.0"
---

# docs-ops

## 1. 定位

<!-- skill-content:start -->
一个入口、多条隔离 lane，按文档域分治：**docs-system** 让项目说明文档「写对 + 拦住」（分层契约 + 模板 + 清单 + 残留检测 + 结构检查）；**demand-lifecycle** 让需求文档「结构清晰 + 状态一致 + 可门禁」（分类法 + 状态映射 + 结构检查）。两 lane 检查对象互斥、契约分离、引擎独立，互不误伤。深度格式 lint（emoji 词表、超宽表格等）由 `document-governance` 可选增强。
<!-- skill-content:end -->

本 Skill 采用 Workloop 结构：方法论在 `nodes/`，契约与链路在
`references/`，机器可读的节点与链路契约在 [`node-flow.json`](references/workflow/node-flow.json)。

## 2. 两 lane 分治（不要混）

| lane | 检查对象 | 引擎 | 契约 | 入口命令 |
|---|---|---|---|---|
| `docs-system` | 项目说明文档（正文/历史层） | `structure_check.py` + `residue.py` | `docs/doc-contract.json` | `check` / `residue` / `new` / `migrate` |
| `demand-lifecycle` | 需求全量产出物 `docs/request/` | `demand_check.py` | `docs/demand-contract.json` | `demand` |

**隔离保证**：项目 `doc-contract.json` 配 `exemptDirs: ["docs/request"]` 让 docs-system 跳过需求目录；`demand_check.py` 只读 `docs/request/`。需求文档因此不会被正文规则（禁日期/状态词）误伤，也不会两套状态源打架。

**归属边界**：
- 流程/门禁/节点路由归 `workloop`（本 skill 被其节点调用，不反向接管）。
- 格式/命名/链接/Schema 细则归 `document-governance`（本 skill 的模板引用，不复制）。
- 树的存储与五不变量归 `dsh-project-tree` 插件（本 skill 只读投影，不写树）。
- 本 skill 不保存任何项目/环境/账号事实；项目特有内容在项目的 `doc-contract.json` / `demand-contract.json` / `residue.rules.json` 数据里。

## 3. 三层分工（不要混）

| 层 | 位置 | 内容 | 不做什么 |
|---|---|---|---|
| 方法论 | `nodes/` | 每个节点一篇 README：何时进入、怎么做、产出、何时算完 | 不写实例事实 |
| 契约与链路 | `references/`, `assets/schemas/` | 架构边界、分层规范、链路契约、契约模板 | 不写节点方法 |
| 可执行层 | `jedocsops/` + `scripts/` | 统一入口 CLI 与自包含检测/铸造引擎 | 不授予任何权限 |

## 4. 统一入口

```bash
# ── docs-system lane ──
# 一次跑完：文档结构前置检查 + 残留守卫（退出码 0/1/2）
python scripts/docs-ops.py check --project <项目>

# 从模板新建文档（自带历史跳转位）
python scripts/docs-ops.py new --type body-doc|roadmap|reference-cli|history-index --out <路径>

# 旧文档改造：先归档再重写的操作清单
python scripts/docs-ops.py migrate --file <旧文档> --project <项目>

# 仅残留检测 / 铸造 / ledger 提取
python scripts/docs-ops.py residue --project <项目> [--generated]
python scripts/docs-ops.py residue --mint --project <项目> [--ledger ledger.json]

# ── demand-lifecycle lane ──
# 需求文档结构检查（必备文件/验收编号/状态卡片/两 lane 隔离）
python scripts/docs-ops.py demand --project <项目> [--contract docs/demand-contract.json]
```

所有命令支持 `--format text|json|markdown`（或 `--json` / `--markdown`）与 `--out <文件>`。

## 5. 节点与链路

两个 lane 各一个节点、节点内拆内聚子模块（层次同时落在目录结构与 `node-flow.json` 的 `modules` 字段，不平铺）：

| 节点 | lane | 职责 | 子模块 |
|---|---|---|---|
| [n01-doc-system](nodes/n01-doc-system/README.md) | docs-system | 项目说明文档体系 | [architecture](nodes/n01-doc-system/architecture.md) · [body-rules](nodes/n01-doc-system/body-rules.md) · [archive-flow](nodes/n01-doc-system/archive-flow.md) · [guard](nodes/n01-doc-system/guard.md) |
| [n02-demand](nodes/n02-demand/README.md) | demand-lifecycle | 需求文档体系 | [structure](nodes/n02-demand/structure.md) · [status](nodes/n02-demand/status.md) · [guard](nodes/n02-demand/guard.md) |

每个节点内按「前置写对 → 后置拦住」的依赖顺序阅读子模块；各节点 README 是入口（何时进入、模块导航、退出条件）。

## 6. 验证

```bash
python -I -m pytest tests -q          # 结构 + 引擎行为 + 合同测试（含 Node 对拍）
python tools/run_tests.py             # 并行入口
```

结构测试只能证明目录与链路一致，不能证明行为正确；行为由上述测试覆盖。

## 7. 知识索引

- [残留类型学与规则 schema](references/residue-taxonomy.md)：五层残留分类、每层检测原语、rules.json 完整契约。
- [文档分层规范](references/doc-system.md)：正文/历史两层判定、模板契约、目录契约数据。
- [需求契约模板](assets/schemas/demand-contract.json)：demand-lifecycle lane 默认契约。
- [交付前清单](assets/checklists/preflight.md)：正文规则、分层归档、残留门禁、自带最小格式纪律的自检项。
- [架构](references/architecture.md)

## 8. 扩展

新增节点三步：加 `nodes/<id>/README.md` → 改 `references/workflow/node-flow.json` → 更新本文件节点列表。
新增 lane 还须：加引擎模块 `jedocsops/<lane>_check.py` → 加 CLI 子命令 → 加契约模板 `assets/schemas/` → 加行为测试。
受管文件（`references/workflow/node-flow.json`、`tests/test_structure.py`、`tests/test_cli_contract.py`、`conftest.py`、`tools/run_tests.py`）由脚手架维护，手改会触发 `PROJECT-DRIFT`。
