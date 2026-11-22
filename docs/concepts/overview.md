# je-docs-ops 概览

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](../history/README.md)。

## 概述

je-docs-ops 是项目文档体系规范与残留检测的统一入口。它把两件事绑在一个体系里：**前置**让 agent 写对（分层契约 + 模板 + 清单），**后置**让门禁拦住（语言无关残留检测 + 文档结构检查）。

后置规则是否定式的——只说「不能写什么」，不说「该怎么写」；agent 写不出正确结构时会反过来给检测器加豁免。但只有前置也不行：没有机械门禁的约定必然腐烂。因此两者缺一不可。

本 skill 自带通用文档的最小格式规范与交付前清单（`assets/checklists/preflight.md`），独立即可完成结构分层、写作规则、归档流程与残留检测；深度格式 lint 可由 `document-governance` 可选增强。

## 工作方式

1. **划两层**：正文层只描述「当前是什么」；历史层（`docs/history/`）存放变更记录、决策、基线与交付结果快照。判定标准——会过期的内容进历史，不会过期的进正文。
2. **定目录**：正文一级子目录收敛为有限集合，写入 `doc-contract.json` 的 `allowedDirs`，防止自由生长。
3. **立索引**：历史层必须有 `README.md` 索引（档案清单表），正文层有文档地图。
4. **接跳转**：每份正文文档留「历史档案」跳转链接；`check` 验证跳转位存在。
5. **跑门禁**：`check` 一次跑完结构前置 + 残留守卫，红灯阻断提交。

## 四类残留检测

| 检测 | 说明 |
|---|---|
| `patterns` | 正则扫描旧名 / 违规措辞残留 |
| `dirLists` | 清单目录存在性（该归档/该建的目录是否到位） |
| `deadLinks` | Markdown 相对链接死链 |
| `generatedDrift` | 重跑生成命令后 `git status` 是否干净 |

四类全部数据驱动、语言无关，由项目的 `residue.rules.json` 配置。写规则的三条纪律见 [残留类型学与规则 schema](../../references/residue-taxonomy.md)。

## 三层分工

| 层 | 位置 | 内容 |
|---|---|---|
| 方法论 | `nodes/` | 每个节点一篇 README：何时进入、怎么做、产出、完成条件 |
| 契约与链路 | `references/` | 架构边界、残留类型学、分层规范、链路契约 |
| 可执行层 | `jedocsops/` + `scripts/` | 统一入口 CLI 与自包含检测 / 铸造引擎 |

本 skill 不保存任何项目 / 环境 / 账号事实；项目特有内容全部在项目的 `residue.rules.json` 与 `doc-contract.json` 数据里。

## 参考

- [文档地图](../README.md)
- [CLI 命令参考](cli-reference.md)
- [守卫接入](guard-integration.md)
- [历史档案](../history/README.md)
