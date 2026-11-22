# residue-guard 迁移档案

> 只进不改的归档记录。正文入口见 [文档地图](../README.md)。

## 归档事实

原 `~/.agents/skills/residue-guard/`（Node 铸造器 + Node 引擎）整体移入 `~/.agents/skills/.archive/residue-guard-20261122/`。

其全部触发词（残留检测、改名清扫、旧名扫描、rename ledger、重构验收残留、升级后旧标识符、生成物漂移）迁入本 skill 的 `description`，保证路由不丢。

`document-governance` 不归档，仍是通用格式规范 owner；本 skill 通过 manifest 声明依赖，引用不重写。

## 迁移决策

- 检测逻辑本身语言无关（遍历 + 正则 + glob + 路径比较），语言差异只在「怎么被调用」的 3 行 hook 薄壳。
- 新引擎读同一份 `residue.rules.json`，与旧 Node 引擎判定一致（合同测试用 fixture 对拍），现有项目规则无需改动。
- 砍掉了绑定表 / revision / sha256 / fallback / 多语言 adapter 等过度设计。
