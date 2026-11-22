# n01-doc-system 文档体系

> **何时进入**：新建或改造项目文档体系，写正文文档、归档历史、跑残留门禁时。
> **离开条件**：目录契约成立——正文层每份 `.md` 属于已知目录、历史层有索引、正文→历史跳转位存在且可判定（`structure_check` 通过）。

文档体系是**一个实体**（项目的 `docs/` 正文 + `docs/history/` 历史），有四个内聚侧面。它们收在一个节点下、拆为四个模块，按层次阅读：

```
n01-doc-system/
├── README.md          # 本页：进入条件、模块导航、退出条件
├── architecture.md    # ① 文档架构分层：正文/历史两层目录契约
├── body-rules.md      # ② 正文前置规范：现在时、无历史措辞、跳转位
├── archive-flow.md    # ③ 归档流程：先 git mv 归档再重写
└── guard.md           # ④ 后置检测：残留检测能力与守卫接入
```

## 模块导航（按顺序读）

| 模块 | 回答的问题 | 产出 |
|---|---|---|
| [architecture](architecture.md) | 文档分几层、哪些目录、怎么立索引？ | `doc-contract.json` + 通过的目录结构 |
| [body-rules](body-rules.md) | 正文怎么写才不过期？ | 符合现在时/跳转位规范的正文 |
| [archive-flow](archive-flow.md) | 会过期的内容怎么迁历史？ | 归档后的正文 + 历史档案 |
| [guard](guard.md) | 怎么机械拦截残留与结构违规？ | `check` 报告 + 退出码 |

## 依赖顺序

`architecture`（定分层）→ `body-rules`（定写法）→ `archive-flow`（定归档）→ `guard`（验结构）。前三者是「写对」的前置，guard 是「拦住」的后置——与 `n02-demand` 的 structure/status → guard 结构同构。

## 边界

- 整个节点只管「项目说明文档」；需求全生命周期文档归 `n02-demand` lane。
- 不定义需求内容写法（归 Workloop）、不定义深度格式 lint（归 `document-governance`）。
- 本节点及四个模块是方法论；机器可读契约在 `references/workflow/node-flow.json`，目录契约数据在项目的 `doc-contract.json` / `residue.rules.json`。
