# 需求结构门禁（后置检测）

> 所属节点：[n02-demand 需求文档体系](README.md) · 结构 → 状态 → 门禁

> **何时进入**：需求文档写完、交付前、或 CI 中需要机械校验需求结构时。
> **离开条件**：`demand` 检查 errors=0，warning 已确认是有意缺号/待补项。

## 输入

- 项目根路径 + 需求契约 `docs/demand-contract.json`（可选，缺省用内置默认契约）。

## 检查项（数据驱动）

| 检查 | 级别 | 说明 |
|---|---|---|
| `pointer` | error | 需求目录名符合 `<id>-<slug>` kebab-case |
| `required-files` | error | 每个需求至少含 `01-spec.md` |
| `acceptance-ids` | error | 01-spec 的「验收标准」段含 `- [ ] A<n>` 编号 |
| `numbering` | warning | 编号文件 01..N 连续（缺号有意则忽略） |
| `traceability` | warning | 03-plan 含「验收追溯」段 |
| `dashboard-link` | warning | 看板有对应状态卡片 |

- error 阻断（退出码 1），warning 只提示（退出码仍 0）——与 docs-system lane 的 exit 0/1/2 契约一致。
- 检查器 `jedocsops/demand_check.py` 只读，不改任何文件。

## 怎么做

```bash
# 检查全部需求
python scripts/docs-ops.py demand --project <项目>

# 自定义契约（如严格编号）
python scripts/docs-ops.py demand --project <项目> --contract docs/demand-contract.json --json

# 报告格式
python scripts/docs-ops.py demand --project <项目> --markdown --out report.md
```

## 与 docs-system lane 的隔离

| | docs-system lane | demand-lifecycle lane |
|---|---|---|
| 入口 | `check` | `demand` |
| 检查对象 | 正文/历史层 | `docs/request/` |
| 契约 | `doc-contract.json` | `demand-contract.json` |
| 引擎 | `structure_check.py` | `demand_check.py` |

两 lane 互不扫描对方目录：`structure_check` 通过 `exemptDirs` 排除 `docs/request/`，`demand_check` 只读 `docs/request/`。隔离保证需求文档不会被正文规则（如"不得含日期/状态词"）误伤。

## 产出

- 检查报告（JSON/文本/Markdown）+ 退出码，可接入 CI。

## 边界

- 只做结构检查，不验证需求内容的正确性（归 Workloop N05 设计评审、N11 独立复核）。
- 不执行修复——只报告，修复由 agent/人按本节点的 structure / status 模块完成。
