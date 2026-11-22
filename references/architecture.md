# 架构

docs-ops = 文档体系多 lane 路由器。一个入口、多条隔离 lane，按文档域分治。

## 分层

- `nodes/`：方法论节点，分两 lane——
  - docs-system：n01 架构分层 → n02 正文规则 → n03 归档流程 → n04 守卫接入
  - demand-lifecycle：n05 需求结构 → n06 状态映射 → n07 结构门禁
- `references/`：契约与链路。`doc-system.md` 是文档分层唯一事实源；`residue-taxonomy.md` 是残留类型学唯一事实源；`references/workflow/node-flow.json` 是机器可读的多 lane 节点链路；`assets/schemas/demand-contract.json` 是需求契约默认模板。
- `jedocsops/`：可执行层。
  - `structure_check.py` —— docs-system lane 文档结构前置检查（契约数据驱动）。
  - `residue.py` —— 通用残留检测引擎（纯标准库，自包含单文件，可被铸造复制进项目独立运行）。
  - `extract_ledger.py` —— git 历史旧名清单提取。
  - `mint.py` —— 铸造器：引擎拷贝 + rules.json + 调用钩子 + CI 片段（幂等，--force 覆盖）。
  - `demand_check.py` —— demand-lifecycle lane 需求文档结构检查（只读 docs/request/）。
  - `cli.py` —— 统一入口 describe/check/demand/new/migrate/residue。
- `assets/templates/`：文档骨架模板 + 各 runner 的守卫调用钩子由 mint 内置模板生成。
- `scripts/docs-ops.py`：只读入口 shim，转发到 `jedocsops/cli.py`。

## 两 lane 隔离（关键设计）

| | docs-system | demand-lifecycle |
|---|---|---|
| 检查对象 | 正文/历史层 | `docs/request/` |
| 引擎 | structure_check.py + residue.py | demand_check.py |
| 契约 | doc-contract.json | demand-contract.json |
| CLI | check / residue / new / migrate | demand |
| 规则取向 | 正文禁日期/状态词 | 需求必须有状态/验收编号 |

隔离靠两道机制保证：
1. **docs-system 侧**：项目 `doc-contract.json` 配 `exemptDirs: ["docs/request"]` 让 structure_check 跳过需求目录。
2. **demand 侧**：demand_check 只 `rglob` 自己的 `requestDir`，永不触碰正文/历史层。

因此需求文档（天然带日期/状态、会过期）不会被正文规则误伤，也不会出现两套互相打架的状态源。这条隔离由 `test_demand_check.py` 的双 lane 测试守护。

## 关键设计

- **检测逻辑语言无关**：四类残留（patterns/dirLists/deadLinks/generatedDrift）由 residue.rules.json 数据驱动；各语言 test runner 只差一个 3 行调用钩子。
- **守卫进项目，skill 只铸不养**：mint 把自包含引擎复制到项目 `tools/accept/`，守卫生命周期与项目一致。
- **合同保证**：同一份 rules.json，Python 引擎与旧 Node 引擎判定一致，由合同测试 fixture 守护。
- **退出码契约**：0 = 干净/通过；1 = 有 error；2 = 配置/环境问题（两 lane 一致）。warning 不影响退出码。

## 归属

- 节点 README、`SKILL.md`、`references/doc-system.md`、`jedocsops/**`、`assets/**` 属扩展文件。
- `skill.manifest.json`、`references/workflow/node-flow.json`、`tests/test_structure.py`、`tests/test_cli_contract.py`、`conftest.py`、`tools/run_tests.py` 属受管文件（脚手架维护）。
- 业务事实不进入本 skill；项目特有词形/目录契约全部在项目数据文件里。

## 边界

静态检查只证明结构一致；不验证行为正确、不提供沙箱、不代表 Agent 实际遵守。L4 行为/语义残留与 L5 架构错位静态不可检（见 residue-taxonomy.md 第 5 节），属项目纪律。需求内容正确性归 Workloop N05/N11，本 skill 只管结构。
