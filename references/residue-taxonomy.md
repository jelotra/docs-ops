# 残留类型学与规则 schema（je-docs-ops 方法论文）

> 本文件只含通用方法论与数据契约；任何项目特有的词形（旧名、路径）都属于项目的
> `residue.rules.json` 数据，不进入本文。

## 1. 五层残留分类与机械可检性

| 层 | 类型 | 典型形态 | 检测原语 | 可检性 |
|---|---|---|---|---|
| L1 | 字面量/标识符改名残留 | 类名、CSS 类、localStorage 键、env 名、文案里的旧名（含大小写与连字符变体） | git ledger 提取 + 词边界大小写不敏感扫描 | ~90%（ledger 完整时） |
| L2 | 结构一致性 | 清单声明 vs 目录实存、Markdown 相对死链、生成物与源漂移、exports vs dist | dirList / deadLinks / generatedDrift 规则 | ~85% |
| L3 | 动态数字过期 | 单测数、断言数、覆盖率手写进活文档 | 旧值模式规则 + 行内「时点」豁免约定 | ~60%（需约定） |
| L4 | 行为/语义残留 | 新增必选参数导致消费方静默失败、API 收窄 | 静态不可检：只能「枚举消费方 + 全量行为验收」 | 0%（守卫提醒清单存在） |
| L5 | 架构错位 | 模块住错层、宿主知识进错包 | 静态不可检：架构图 + 人工审计 | 0% |

实测标定：某渲染引擎仓库一轮改造产生 8 起残留事故，其中 7 起属 L1/L2（87%），全部被
本守卫的规则形态覆盖。通用项目保守估计 60-80%。

## 2. git ledger 提取原理

- 任何改名都有 commit；`git show <sha> -U0` 的删除行（`-` 前缀）包含旧名的全部出现形态。
- 统计规则：token 在删除行出现 ≥ minCount 次、在新增行出现 0 次 → 改名受害者候选。
- token 来源（通用，无业务词）：引号字面量（`'…'` `"…"` 反引号）+ 词元（≥3 字符且含字母，
  允许 `$`/`.`/`-`/`/` 中缀——覆盖 CSS 类、键名、路径片段、env 名）。
- 噪音控制：diff 元数据行（`diff --git`/`index`/`@@`/`---`/`+++`）排除；`added=0` 过滤
  「仍在使用的词」；频次排序供人工确认。
- 边界：无明确 rename 点的渐进漂移提取弱；commit 范围过大时用 `--min-count` 提阈值。

## 3. rules.json schema（完整契约）

```jsonc
{
  "version": 1,
  "skipDirs": ["额外跳过目录"],                    // 引擎内置跳过 node_modules/.git/dist/.tmp/coverage/build/__pycache__/.venv/venv/target
  "patterns": [                                    // L1/L3：正则残留扫描
    {
      "id": "legacy-acme-token",                  // kebab-case 稳定 id
      "regex": "\\bacme-old-token\\b",            // 建议词边界 + 转义；大小写变体用 flags "i"
      "flags": "i",
      "severity": "error",                        // error 阻断 / warn 仅列出
      "why": "事故出处一句话",                     // 必写：规则即回归测试
      "include": ["**/*"],                        // glob（** 跨段、* 段内、? 单字符）
      "exclude": ["**/residue-guard.py"],         // 引擎自引用等合法出现
      "exemptLine": "残留|漏网|事故|旧名|历史|时点", // 行级豁免：叙述事故的文档行
      "selfExemptFile": "tools/accept/residue-guard.py" // 文件级豁免（规则自引用）
    }
  ],
  "dirLists": [                                    // L2：清单声明 vs 实存
    {
      "id": "build-packages",
      "file": "scripts/build.mjs",                // 清单所在文件
      "extractRegex": "const PACKAGES = \\[([^\\]]+)\\]", // 带 1 个捕获组
      "baseDir": "packages",                      // 捕获项以此为基准目录验存在性
      "why": "清单引用不存在的条目曾致静默跳过构建",
      "severity": "error"
    }
  ],
  "deadLinks": {                                   // L2：Markdown 相对链接/图片
    "include": ["README.md", "**/*.md"],
    "exclude": [],
    "why": "相对链接目标不存在（路径改名残留）",
    "severity": "error"
  },
  "generatedDrift": [                              // L2：生成物漂移（仅 --generated 时执行，需 git）
    { "id": "bundle", "command": "node scripts/build-bundle.mjs", "paths": ["dist/bundle.js"], "why": "改源未重出" }
  ]
}
```

写规则的三条纪律：
1. 每条规则 `why` 写明事故出处——规则即回归测试，没有出处的规则不应存在。
2. 行级豁免（`exemptLine`）用于「叙述事故的文档行」；豁免词要收窄，避免吞掉真残留。
3. `patterns` 的 token 一律词边界 + 转义；大小写变体多的用 `flags: "i"`。

## 4. 铸造与维护契约

- 铸造器（`residue --mint`）探测 test runner（vitest/jest/pytest）生成统一 spawn Python 引擎的调用钩子、探测
  `.github/workflows` 生成 CI 片段；产物幂等（`--force` 覆盖）。
- 守卫代码**进项目仓库**（`tools/accept/residue-guard.py`，自包含 Python 引擎拷贝），skill 只铸不养——守卫的生命
  周期与项目一致，不依赖 skill 存活。
- 维护契约（随守卫交付给项目）：事故固化新规则、生成物禁手改、动态数字标时点、
  守卫进测试与 CI。

## 5. 不可检边界（诚实声明）

- L4/L5 静态原理上不可检：本 skill 的职责边界是 L1/L2/L3 的机械检出 + L4/L5 的
  「检查清单提醒」（behavior-acceptance / architecture-audit 须由项目纪律承担）。
- ledger 依赖 commit 记录；squash/无历史项目需人工提供旧名清单（`patterns` 直接手写）。
- 引擎为零依赖 Python ≥3.9 标准库脚本（PEP 585 泛型注解）：检测能力=文本与文件系统层；AST 级语义匹配（ast-grep 等）
  属未来增强，不在本版承诺内。
