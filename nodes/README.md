# 节点索引

两个 lane 各一个节点，节点内以子模块表达内聚侧面（层次同时落在目录结构与
[`node-flow.json`](../references/workflow/node-flow.json) 的 `modules` 字段，不平铺）。
节点只讲方法与门禁，不写实例事实。

| 节点 | lane | 子模块 |
|---|---|---|
| [n01-doc-system](n01-doc-system/README.md) | docs-system | architecture · body-rules · archive-flow · guard |
| [n02-demand](n02-demand/README.md) | demand-lifecycle | structure · status · guard |

每个节点 README 是入口：何时进入、模块导航、退出条件；子模块按「前置写对 → 后置拦住」顺序阅读。
