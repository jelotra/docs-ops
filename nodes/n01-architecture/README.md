# 文档架构分层：正文/历史两层目录契约

> **何时进入**：新建项目文档体系，或既有文档出现「正文混入历史措辞 / roadmap 越来越长 / 想翻旧决策翻不到」时。
> **离开条件**：目录契约成立——正文层每份 `.md` 属于已知目录、历史层有索引、正文→历史跳转位存在且可判定（`structure_check` 通过）。

## 输入

- 项目文档根目录现状（`docs/` 或等效目录的文件清单）。
- 本 skill 的默认契约 `jedocsops/structure_check.py::DEFAULT_CONTRACT`；项目有定制时以 `<project>/docs/doc-contract.json` 覆盖。

## 怎么做

1. **划两层**：正文层只描述「当前是什么」；历史层（默认 `docs/history/`）存放变更记录、决策、基线与已交付快照。判定标准一句话——**会过期的内容进历史，不会过期的进正文**。
2. **定目录**：正文层一级子目录收敛为有限集合（如 `concepts/ channels/ reference/ integration/`），写入 `doc-contract.json` 的 `allowedDirs`，防止自由生长。
3. **立索引**：历史层必须有 `README.md` 索引（档案清单表），正文层有文档地图（`index.md`）。
4. **接跳转**：每份正文文档开头/结尾留「历史档案」跳转链接；运行 `python scripts/je-docs-ops.py check --skip-residue` 验证跳转位存在。

## 产出

- `doc-contract.json`（可选，定制契约时）。
- `structure_check` 通过的目录结构 + 门禁证据。

## 边界

- 本节点不决定「每份文档写什么内容」（那是 n02）。
- 语言/表格/链接格式契约归 `document-governance`，本 skill 只管结构分层。
- 无 `docs/` 目录的项目：检查器自动跳过并提示，不算失败。
