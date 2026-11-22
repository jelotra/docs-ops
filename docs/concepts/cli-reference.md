# CLI 命令参考

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](../history/README.md)。

## 统一入口

入口脚本：`scripts/docs-ops.py`。子命令：`describe` / `check` / `new` / `migrate` / `residue`。

所有命令都支持报告格式 `--format text|json|markdown`（或 `--json` / `--markdown`）与 `--out <文件>`。退出码：`0` 通过 / `1` 有违规 / `2` 配置或环境问题。

## check

一次跑完文档结构前置检查 + 残留守卫。

```bash
python scripts/docs-ops.py check --project <项目>
```

| 参数 | 说明 |
|---|---|
| `--project` | 项目根目录 |
| `--contract` | 文档契约 JSON，默认 `<project>/docs/doc-contract.json` |
| `--rules` | 残留规则 JSON，默认 `<project>/tools/accept/residue.rules.json` |
| `--skip-structure` | 跳过结构检查 |
| `--skip-residue` | 跳过残留检测 |

## new

从模板新建文档，自带历史跳转位（跳转路径按目标位置自动计算）。

```bash
python scripts/docs-ops.py new --type body-doc|roadmap|reference-cli|history-index --out <路径> [--title <标题>]
```

| 参数 | 说明 |
|---|---|
| `--type` | 模板类型 |
| `--out` | 目标文件路径 |
| `--title` | 文档标题 |
| `--project` | 项目根目录 |
| `--force` | 覆盖已存在文件 |

## migrate

输出旧文档改造的操作清单：按过去时措辞启发式列出建议随原文归档的行，以及 `git mv` 目标路径。

```bash
python scripts/docs-ops.py migrate --file <旧文档> --project <项目>
```

## residue

残留检测 / 铸造 / ledger 提取。

```bash
# 仅检测；--generated 追加生成物漂移
python scripts/docs-ops.py residue --project <项目> [--generated]

# 铸造：为项目生成残留规则
python scripts/docs-ops.py residue --mint --project <项目> [--ledger ledger.json]

# 从 git 历史提取旧名清单（rename ledger）
python scripts/docs-ops.py residue --extract-ledger --repo <项目> --commit <sha>
python scripts/docs-ops.py residue --extract-ledger --repo <项目> --range <a..b> --min-count <n>
```

| 参数 | 说明 |
|---|---|
| `--rules` | 残留规则 JSON |
| `--generated` | 追加生成物漂移检测（需 git） |
| `--verbose` | 详细输出 |
| `--mint` | 铸造模式，写回 `--project` |
| `--extract-ledger` | 提取 git ledger，配合 `--repo` |
| `--commits` / `--commit` / `--range` | 指定 commit 范围 |
| `--ledger` | ledger 输出路径 |
| `--min-count` | 旧名出现频次阈值 |
| `--force` | 覆盖产物 |

规则 schema 的完整契约见 [残留类型学与规则 schema](../../references/residue-taxonomy.md)。

## 参考

- [文档地图](../README.md)
- [概览](overview.md)
- [历史档案](../history/README.md)
