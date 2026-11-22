# 守卫接入

> 本文档描述**当前是什么**。历史演变、决策过程与时点数据一律不写在正文，见 [历史档案](../history/README.md)。

## 单一实现 + 薄 hook

残留检测引擎是唯一实现（`jedocsops/residue.py`）。各项目只需一个 3 行薄 hook，把守卫接进自己的 test runner（模板见 `assets/templates/`）：

- **pytest 项目**：`subprocess.run([python, guard_hook.py])`
- **vitest / Node 项目**：`spawnSync(python, [guard_hook.py])`

新增语言 = 新增一个 3 行 hook 模板，核心引擎零改动。守卫代码进项目仓库（`tools/accept/residue-guard.py`，自包含 Python 引擎拷贝），skill 只铸不养——守卫的生命周期与项目一致，不依赖 skill 存活。

用 `residue --mint --project <项目>` 铸造：探测 test runner 生成统一 spawn Python 引擎的调用钩子、探测 `.github/workflows` 生成 CI 片段；产物幂等（`--force` 覆盖）。

## 维护契约

随守卫交付给项目：

- 事故固化新规则：每条规则 `why` 写明事故出处——规则即回归测试。
- 生成物禁手改：`generatedDrift` 检测源改后未重出。
- 动态数字标时点：单测数等会过期的值不写进活文档。
- 守卫进测试与 CI：让门禁随项目每次提交运行。

## 检测边界

| 层 | 类型 | 可检性 |
|---|---|---|
| L1 | 字面量 / 标识符改名残留 | git ledger 提取 + 词边界大小写不敏感扫描 |
| L2 | 结构一致性（清单/死链/漂移） | dirList / deadLinks / generatedDrift 规则 |
| L3 | 动态数字过期 | 旧值模式规则 + 行内时点豁免 |
| L4 | 行为 / 语义残留 | 静态不可检：枚举消费方 + 全量行为验收 |
| L5 | 架构错位 | 静态不可检：架构图 + 人工审计 |

本 skill 的职责边界是 L1/L2/L3 的机械检出 + L4/L5 的检查清单提醒，静态不可检部分由项目纪律承担。详见 [残留类型学与规则 schema](../../references/residue-taxonomy.md)。

## 参考

- [文档地图](../README.md)
- [概览](overview.md)
- [历史档案](../history/README.md)
