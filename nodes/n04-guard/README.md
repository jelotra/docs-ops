# 后置检测：残留检测能力与守卫接入

> **何时进入**：文档/代码交付前，每次测试与 CI；或新发生一次「残留事故」需要固化为规则时。
> **离开条件**：`python scripts/docs-ops.py check --project <项目>`（结构 + 残留）退出码 0；守卫已接入项目 test runner / CI。

## 输入

- 项目规则文件 `<project>/tools/accept/residue.rules.json`（缺失时先铸造，见下）。
- 改名事故的 commit（用于 ledger 提取）。

## 怎么做

1. **铸造**（首次或新项目）：
   ```bash
   # ① 从 git 历史提取旧名候选（人工确认误报后进入下一步）
   python scripts/docs-ops.py residue --extract-ledger --repo <项目> --commit <sha> > ledger.json
   # ② 为项目铸造守卫（Python 引擎 + rules.json + 测试钩子 + CI 片段）
   python scripts/docs-ops.py residue --mint --project <项目> --ledger ledger.json
   ```
   铸造产物：`tools/accept/residue-guard.py`（自包含引擎拷贝）+ `residue.rules.json` + 按 runner 生成的 3 行调用钩子（vitest/jest/pytest 统一 spawn Python 引擎）。
2. **维护规则**：每次新残留事故固化一条新规则（`why` 写事故出处——规则即回归测试）；四类检测：`patterns`（正则旧名）、`dirLists`（清单实存）、`deadLinks`（Markdown 死链）、`generatedDrift`（生成物漂移，`--generated` 时执行）。
3. **跑门禁**：`python scripts/docs-ops.py check --project <项目>` 一次跑完结构 + 残留；退出码 0/1/2（干净/有违规/配置错误）。

## 产出

- 门禁证据（envelope JSON：`status/scanned/errors/hits`）。
- 项目自有守卫（进项目仓库，生命周期与项目一致，不依赖 skill 存活）。

## 边界

- 检测逻辑**语言无关**：一份 Python 引擎承接全部四类检测；各语言 test runner 只差一个 3 行调用钩子。未来加语言 = 加一个钩子模板，核心零改动。
- **不做的检测**：L4 行为/语义残留、L5 架构错位（静态原理上不可检，属项目纪律；见 `references/residue-taxonomy.md`）。
- 合同保证：同一份 `residue.rules.json`，本 Python 引擎与旧 Node 引擎（residue-guard 0.1.0）判定一致，由合同测试 fixture 守护——现有项目规则无需修改。
