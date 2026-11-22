# 脚手架生成与包名决策档案

> 只进不改的归档记录。正文入口见 [文档地图](../README.md)。

## 决策事实

本 skill 由 Workloop N19 脚手架生成。Python 包名采用连写 `jedocsops`（无下划线）。

为此给 scaffold 增加了可选 `python_module` 覆写字段：缺省仍从 skill 名派生（连字符→下划线），显式覆写要求连写单词；其他受管 skill 的 lock 不受影响。

## 决策理由

连写单词符合 kebab 包目录命名规范；`je_docs_ops` 这种下划线派生命名被判定不合规范，因此改为 `jedocsops`。

 generators 与 lock 通过该字段往返一致（`render(lock["config"])` 能重现相同输出），check 不漂移。
