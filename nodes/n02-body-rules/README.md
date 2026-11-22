# 正文前置规范：现在时、无历史措辞、跳转位

> **何时进入**：在 n01 目录契约内新写或重写一份正文文档时。
> **离开条件**：文档满足三条前置规则，且从模板起步（不是从空白自由发挥）。

## 输入

- 文档类型（body-doc / roadmap / reference-cli / history-index）。
- 对应模板：`assets/templates/<type>.template.md`。

## 怎么做

1. **取模板**：`python scripts/je-docs-ops.py new --type body-doc --out docs/concepts/x.md --title "X"`——模板自带历史跳转位，跳转路径按目标位置自动计算。
2. **现在时写作**：只描述当前机制。禁写：具体日期、需求号/轮次编号、「已交付/本轮/首轮」、时点计数（如「680 个测试」）。
3. **历史外链**：需要交代演变时写一句「详见历史档案」+ 链接，不复制历史内容进正文。
4. **roadmap 特例**：路线图只写未来方向与搁置理由，已完成条目直接移除（事实已在历史层）。

## 产出

- 一份从模板起步、当前时态、带跳转位的正文文档。
- 自检：`python scripts/je-docs-ops.py check --project <项目>` 不得出现 `roadmap-past` / `history-link` 违规。

## 边界

- 不写「为什么这么设计」的长论证——那是 ADR/决策档案（历史层）的事。
- 表格短值短判定、命名 kebab-case 等最小格式纪律见自带清单 `assets/checklists/preflight.md` D 节；emoji 词表等深度 lint 可由 `document-governance` 可选增强。
- 后置守卫（n04）是兜底不是替代：本节点失败可返工，门禁红灯阻断提交。
