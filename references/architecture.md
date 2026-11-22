# 架构

je-docs-ops = 文档体系前置规范 + 残留检测后置门禁，一个体系一个入口。

## 分层

- `nodes/`：方法论节点（架构分层 → 正文规则 → 归档流程 → 守卫接入），每节点一篇 README。
- `references/`：契约与链路。`doc-system.md` 是文档分层唯一事实源；`residue-taxonomy.md` 是残留类型学与 rules.json schema 唯一事实源；`references/workflow/node-flow.json` 是机器可读节点链路。
- `jedocsops/`：可执行层。
  - `residue.py` —— 单一通用检测引擎（纯标准库，自包含单文件，可被铸造复制进项目独立运行）。
  - `extract_ledger.py` —— git 历史旧名清单提取。
  - `mint.py` —— 铸造器：引擎拷贝 + rules.json + 调用钩子 + CI 片段（幂等，--force 覆盖）。
  - `structure_check.py` —— 文档结构前置检查（契约数据驱动）。
  - `cli.py` —— 统一入口 check/new/migrate/residue/describe。
- `assets/templates/`：文档骨架模板 + 各 runner 的守卫调用钩子由 mint 内置模板生成。
- `scripts/je-docs-ops.py`：只读入口 shim，转发到 `jedocsops/cli.py`。

## 关键设计

- **检测逻辑语言无关**：四类检测（patterns/dirLists/deadLinks/generatedDrift）全部由 `residue.rules.json` 数据驱动；各语言 test runner 只差一个 3 行调用钩子（vitest/jest/pytest 统一 spawn Python 引擎）。未来加语言 = 加一个钩子模板，核心零改动。
- **守卫进项目，skill 只铸不养**：mint 把自包含引擎复制到项目 `tools/accept/`，守卫生命周期与项目一致，不依赖 skill 存活。
- **合同保证**：同一份 rules.json，Python 引擎与旧 Node 引擎（residue-guard 0.1.0）判定一致，由合同测试 fixture 守护。
- **退出码契约**：0 = 干净/通过；1 = 有违规；2 = 配置/环境问题（与 skills-diagnosis 约定对齐）。

## 归属

- 节点 README、`SKILL.md`、`references/doc-system.md`、`jedocsops/**`、`assets/**` 属扩展文件。
- `skill.manifest.json`、`references/workflow/node-flow.json`、`tests/test_structure.py`、`tests/test_cli_contract.py`、`conftest.py`、`tools/run_tests.py` 属受管文件（脚手架维护）。
- 业务事实不进入本 skill；项目特有词形/目录契约全部在项目的 `residue.rules.json` 与 `docs/doc-contract.json` 数据里。

## 边界

静态检查只证明结构一致；不验证行为正确、不提供沙箱、不代表 Agent 实际遵守。L4 行为/语义残留与 L5 架构错位静态不可检（见 residue-taxonomy.md 第 5 节），属项目纪律。
