# 需求文档结构：实体与视图分离

> 所属节点：[n02-demand 需求文档体系](README.md) · 结构 → 状态 → 门禁

> **何时进入**：新建需求，或既有需求目录混乱（编号不齐、文件散落、状态与卡片不一致）时。
> **离开条件**：需求目录符合分类法——必备文件齐全、编号有意、目录名 kebab-case（`demand` 检查 errors=0）。

## 输入

- 需求 ID 与标题（来自 Workloop N03 定界或看板 `board_cli.py create`）。
- 本 skill 的默认契约 `assets/schemas/demand-contract.json`；项目可在 `docs/demand-contract.json` 覆盖。

## 分类法（四层，职责单一）

需求文档分四层，**结构与内容分离、实体与视图分离**：

| 层 | 落点 | 内容 | 谁拥有 |
|---|---|---|---|
| L0 视图 | `docs/dashboard/<state>/<id>.md` | 轻量状态卡片（进度投影） | Workloop 看板 |
| L1 索引 | `.tree/nodes/<id>.md`（可选） | 节点摘要 + 详情指针（跨会话） | dsh-project-tree 插件 |
| L2 实体 | `docs/request/<id>-<slug>/` | 需求全量产出物（固定目录，不因状态搬迁） | 本 lane |
| L3 治理 | 本 skill 的 `references/`、`document-governance` | 格式/命名/链接/Schema 规则 | 横切 |

## 实体目录固定布局

```
docs/request/<id>-<slug>/
  01-spec.md      需求定界（目标/事实基线/验收 A<n>/排除/开放问题）
  02-design.md    架构与契约（选型/ADR/设计门禁回执）—— 允许缺，缺须有意为之
  03-plan.md      任务拆分（checkbox 账本 + 验收追溯）
  04-delivery.md  实施记录与验证证据索引
  reviews/        独立复核与评审包
  verifications/  验收证据
  handoffs/       会话交接快照
```

- 目录名固定 `<id>-<slug>`，kebab-case；不因状态变化搬迁。
- 编号文件允许缺号（如尚无设计就缺 02），但 `demand` 检查会报 warning 提醒——这是「有意缺号」的显式信号，不是错误。
- 详细格式规范委托 `document-governance`（中文、链接、表格、命名）；本节点只定义「有哪些文件、放哪、叫什么」。

## 怎么做

1. 从 Workloop 定界拿到需求 ID，建 `docs/request/<id>-<slug>/`。
2. 至少落 `01-spec.md`；验收项必须带 A<n> 编号（机器门禁可校验）。
3. 若设计已完成补 `02-design.md`，实施前补 `03-plan.md`（含「验收追溯」段逐条对应 A<n>）。
4. 跑 `python scripts/docs-ops.py demand --project <项目>`，清 error，确认 warning 是有意的。

## 产出

- 符合分类法的需求目录 + `demand` 检查通过证据。

## 边界

- 不定义需求「写什么内容」（验收粒度、技术链路映射归 Workloop spec 模板）。
- 不定义文档格式细节（归 `document-governance`）。
- 不管理状态流转（归本节点 [status.md](status.md) 与 Workloop 看板）。
- 不写项目说明文档（归 `docs-system` lane）。
