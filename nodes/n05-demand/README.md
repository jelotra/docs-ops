# n05-demand 需求文档体系

> **何时进入**：新建需求，或既有需求目录混乱（编号不齐、状态与卡片对不上、结构漂移）时。
> **离开条件**：需求目录符合分类法、状态有唯一真值、`demand` 检查 errors=0（`demand` 检查见 guard 模块）。

需求文档是**一个实体**（`docs/request/<id>-<slug>/`），有三个内聚侧面——结构、状态、门禁。它们不是三项独立方法论，所以收在一个节点下、拆为三个模块，按层次阅读：

```
n05-demand/
├── README.md       # 本页：进入条件、模块导航、退出条件
├── structure.md    # ① 需求目录分类法：实体与视图分离，文件放哪叫什么
├── status.md       # ② 状态机与视图映射：三套状态词归一、唯一真值
└── guard.md        # ③ 结构门禁：demand 检查器与两 lane 隔离
```

## 模块导航（按顺序读）

| 模块 | 回答的问题 | 产出 |
|---|---|---|
| [structure.md](structure.md) | 需求文档分几类、放哪、叫什么？ | 符合分类法的需求目录 + 必备文件 |
| [status.md](status.md) | 状态有哪几种、看板/树/文档怎么对齐？ | 状态映射表 + 唯一真值约定 |
| [guard.md](guard.md) | 怎么机械校验、怎么和 docs-system lane 隔离？ | `demand` 检查报告 + 退出码 |

## 依赖顺序

`structure`（定目录）→ `status`（定状态）→ `guard`（验结构）。前两者是「写对」的前置，guard 是「拦住」的后置——这与 docs-system lane 的 n01→n04 前置/后置结构同构，只是换了一个文档域。

## 边界

- 整个节点只管「需求全生命周期文档」；项目说明文档归 docs-system lane（n01–n04）。
- 不定义需求内容写法（归 Workloop spec 模板）、不定义格式细节（归 `document-governance`）、不执行状态流转（归 Workloop 看板）、不写 `.tree/`（归 dsh-project-tree 插件）。
- 本节点及三个模块是方法论；机器可读契约在 `assets/schemas/demand-contract.json`，链路在 `references/workflow/node-flow.json`。
