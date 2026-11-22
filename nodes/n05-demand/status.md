# 需求状态机与视图映射

> 所属节点：[n05-demand 需求文档体系](README.md) · 结构 → 状态 → 门禁

> **何时进入**：需求状态与看板卡片对不上、多套状态词打架、或要接入 `.tree/` 节点状态时。
> **离开条件**：状态有唯一真值，视图（看板卡片 / 树节点）由它投影生成，无第二份状态源。

## 输入

- 需求的当前状态（来自 Workloop 看板流转）。
- 三套状态词的映射约定（见下表）。

## 状态归一（唯一真值 → 视图）

| 统一状态 | Workloop 看板 | .tree status | 含义 |
|---|---|---|---|
| planned | todo | planned | 待定界 |
| scoped | pending | designed | 定界就绪，待开工 |
| implementing | doing | implementing | 实施中 |
| blocked | blocked | （无，需 journal reason） | 外部依赖阻断 |
| achieved | done | achieved | 已交付且复核通过 |
| archived | archived | pruned | 归档结项 |

**真值原则**：状态只在一处写入（Workloop 看板卡片），其余视图只读投影。禁止在需求文档正文、树节点、看板卡片里各写一份相互独立的状态。

## 怎么做

1. 确定唯一真值源：默认用 Workloop 看板卡片（`docs/dashboard/`）作为状态写入点。
2. 状态回退（achieved → 任何）必须在 `.tree/journal` 带 reason（沿用 dsh-project-tree 五不变量）。
3. 若项目使用 dsh-project-tree 插件，树节点 status 由看板状态按上表投影，不手写。
4. `demand` 检查的 `dashboard-link` 项验证每个需求目录在看板有对应卡片（warning 级）。

## 产出

- 状态映射表落项目 `docs/demand-contract.json`（可选定制）+ 看板卡片与树节点一致。

## 边界

- 不执行状态流转（归 Workloop `board_cli.py`）。
- 不定义树的存储与不变量（归 dsh-project-tree 插件）。
- 状态门禁（什么条件才能推进）归 Workloop `stage_gate.py`，本节点只管状态词的一致与投影。
