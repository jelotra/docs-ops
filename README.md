# je-docs-ops

项目文档体系规范与残留检测的统一入口：**前置**让 agent「写对」（分层契约 + 模板 + 交付清单），**后置**让门禁「拦住」（语言无关残留检测 + 文档结构检查）。

一个体系、一个入口。通用的语言 / 链接 / 表格 / 命名格式规范归 [`document-governance`](https://github.com/jelotra/document-governance)（引用不重写）；本 skill 只拥有项目文档的**体系分层**与**残留检测**两项能力。

## 为什么需要它

后置的残留规则是否定式的——只说「不能写什么」，不说「该怎么写」。agent 写不出正确结构时，会反过来给检测器加豁免来自我反制（真实发生过：为规则加「不写日期」豁免）。但只有前置也不行：没有机械门禁的约定必然腐烂。

因此本 skill 把两件事绑在一个体系里：

- **前置**：方法论（`nodes/`）+ 模板（`assets/templates/`）+ 清单，回答「这是什么层的文档、该怎么写、写到哪」；
- **后置**：单一 Python 标准库检测引擎（`jedocsops/residue.py`），回答「有没有违规、有没有断链、生成物有没有漂移」。前置失败可返工，后置红灯阻断提交。

## 安装

作为用户级 Skill 使用，放到 `~/.agents/skills/je-docs-ops/` 即可（本仓库即该目录）。

依赖：

- Python 3.9+（仅标准库，零第三方依赖）；
- 同级 `skills-runtime-toolkit`，或环境变量 `SKILLS_RUNTIME_TOOLKIT` 指向其根目录（报告型 CLI 输出需要）。

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

`check` 默认读取 `<项目>/docs/doc-contract.json`（文档契约）与 `<项目>/tools/accept/residue.rules.json`（残留规则），可用 `--contract` / `--rules` 覆写；`--skip-structure` / `--skip-residue` 可分别跳过某一项检测。

### 残留规则与 ledger

```bash
# 铸造：为项目生成残留规则（--project 写回项目）
python scripts/je-docs-ops.py residue --mint --project <项目> [--ledger ledger.json]

# 从 git 历史提取旧名清单（rename ledger）
python scripts/je-docs-ops.py residue --extract-ledger --repo <项目> --commit <sha>
python scripts/je-docs-ops.py residue --extract-ledger --repo <项目> --range <a..b> --min-count <n>
```

四类检测全部数据驱动、语言无关：

| 检测 | 说明 |
|---|---|
| `patterns` | 正则扫描旧名 / 违规措辞残留 |
| `dirLists` | 清单目录存在性（该归档/该建的目录是否到位） |
| `deadLinks` | Markdown 相对链接死链 |
| `generatedDrift` | 重跑生成命令后 `git status` 是否干净 |

## 目录结构

```text
je-docs-ops/
├─ SKILL.md                     skill 入口与路由说明
├─ skill.manifest.json          能力声明与依赖（depends_on: skills-runtime-toolkit）
├─ node/                        方法论：每个节点一篇 README（何时进入/怎么做/产出/完成条件）
│  ├─ n01-architecture          正文 / 历史两层目录契约
│  ├─ n02-body-rules            正文前置规范：现在时、无历史措辞、跳转位
│  ├─ n03-archive-flow          归档流程：先 git mv 归档再重写
│  └─ n04-guard                 后置检测能力与守卫接入
├─ references/                  契约与链路（不写节点方法）
│  ├─ doc-system.md             正文 / 历史分层规范（唯一事实源）
│  ├─ residue-taxonomy.md       五层残留分类、检测原语、rules.json 契约
│  ├─ architecture.md           架构
│  ├─ cli-contracts.json        机器可读 CLI 契约
│  └─ workflow/node-flow.json   节点与链路契约（脚手架管理）
├─ assets/templates/            文档模板 + 守卫接入模板
├─ jedocsops/                   可执行层：统一 CLI 与自包含检测 / 铸造引擎
│  ├─ cli.py                    命令分派与退出码
│  ├─ structure_check.py        文档结构前置检查
│  ├─ residue.py                残留检测引擎
│  ├─ mint.py                   规则铸造
│  └─ extract_ledger.py         git 历史旧名提取
├─ scripts/je-docs-ops.py       CLI shim
├─ tests/                       结构 / 行为 / 合同测试（含与 Node 引擎对拍快照）
└─ tools/run_tests.py           并行测试入口
```

事实不放在本 skill：项目特有内容全部在项目的 `residue.rules.json` 与 `doc-contract.json` 数据里。

## 守卫接入（后置门禁）

检测引擎是唯一实现；各项目只需一个 3 行薄 hook 把守卫接进自己的 test runner（模板见 `assets/templates/`）：

- **pytest 项目**：`subprocess.run([python, guard_hook.py])`
- **vitest / Node 项目**：`spawnSync(python, [guard_hook.py])`

新增语言 = 新增一个 3 行 hook 模板，核心引擎零改动。旧 `residue-guard` 的 Node 引擎判定与本引擎读同一份 `residue.rules.json`，合同测试用 fixture 对拍保证判定一致，现有项目规则无需改动。

## 验证

```bash
python -I -m pytest tests -q   # 结构 + 引擎行为 + 合同测试（含 Node 对拍）
python tools/run_tests.py      # 并行入口
```

当前基线：51 passed, 1 skipped。结构测试只能证明目录与链路一致，不能证明行为正确；行为由上述测试覆盖。

`SKILL.md` 第 7 节列出的受管文件（`references/workflow/node-flow.json`、`tests/test_structure.py`、`tests/test_cli_contract.py`、`conftest.py`、`tools/run_tests.py`）由脚手架维护，手改会触发 `PROJECT-DRIFT`。本 skill 由 Workloop N19 脚手架生成，`python_module` 使用连写包名 `jedocsops`。

## 迁移说明

原 `~/.agents/skills/residue-guard/`（Node 铸造器 + Node 引擎）已归档至 `~/.agents/skills/.archive/residue-guard-20261122/`，其全部触发词（残留检测、改名清扫、旧名扫描、rename ledger、重构验收残留、升级后旧标识符、生成物漂移）已迁入本 skill 的 `description`，路由不丢。`document-governance` 不归档，仍是通用格式规范 owner。

## License / 归属

Owner：`eavelabs`。仓库：`jelotra/je-docs-ops`（private）。
