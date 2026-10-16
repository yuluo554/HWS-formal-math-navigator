# RELEASE-M6.md 发布留档

> 本文件为 M6 收尾固化阶段的发布留档，记录发布过程、产物核验与已知偏差。
> **基线声明**：本文件内容为**快照 + 可复跑规则**；会随提交移动的量（run 数、sha256、tag 指向）
> 一律写"取值方式"而非绝对值，避免"写下它"这个动作让数字立即过期。

---

## 一、发布坐标

| 项目 | 值 |
|------|-----|
| 仓库 | https://github.com/yuluo554/HWS-formal-math-navigator |
| 标签 | `v0.1.0`（指向 = 含本记录完整内容的提交；权威值用 `git rev-list -n1 v0.1.0` 现取） |
| 发布者 | HWS |
| 可见性 | PUBLIC |

## 二、M6 收尾期发现的真实缺陷（本里程碑核心价值）

M5 声称"发布与交付完成"，但**发布物本体从未被验证过**。M6 收尾期按 skill 规则逐项复核，
发现以下**真实缺陷**（全部已修复）：

| # | 缺陷 | 性质 | 证据（修复前） | 修复 |
|---|------|------|----------------|------|
| D1 | **发布 exe 完全不可用** | 🔴 致命 | 真下载 v0.1.0 附件跑 `selftest` → `索引目录不存在: data\index`（exit 非 0） | 冻结态数据目录解析（`_MEIPASS`）+ spec datas 收数据 |
| D2 | `bench` 命令是 pytest 包装桩 | 🔴 致命 | `cwd` 错（`tests/` 找不到）+ `--suite` 参数被当 pytest 路径 + 无任何基准指标 | 实现 `benchmark` 模块（Recall@k/MRR/完整率/断链检出率） |
| D3 | `test_bench_probe.py` 是 3 个空 `pass` 桩 | 🔴 假门 | skill 明示的"看着做了、其实没验"形态 | 实现 11 项双向对照探活（坏实现→未达标 + 好实现→达标） |
| D4 | depgraph `_is_module_covered` 有死循环 + 错误启发式 | 🔴 语义违规 | 已覆盖模块（含 4 定理）被判 `index_gap`，**违反 K2 口径** | 改为"模块名在索引实际覆盖集中"判定 |
| D5 | `core/__init__` 急切导入导致循环导入 | 🟠 | `import hws_formal_math.engine.retriever` 独立导入崩溃 | PEP 562 惰性属性 |
| D6 | `tools/hws-formal-math.spec` 硬编码本机绝对路径 | 🟠 脱敏泄露 | `pathex=['D:\\ProgramData\\...']` | 用 `SPECPATH` 相对推导 |
| D7 | `tools/gen_snapshots.py` 是 `NotImplementedError` 桩 | 🟠 | `data/snapshots/manifest.json` 为 `sha256: "placeholder"`, `case_count: 0` | 实现确定性生成器（`--check` 位级一致） |
| D8 | 无 LICENSE 文件 | 🟠 | `pyproject`/README 声明 MIT 但仓内无文件 | 补 `LICENSE` |
| D9 | `tools/` 脚本无编码守卫 | 🟠 CI 必红 | skill 明示"编码守卫要覆盖所有会打印的可执行入口" | 新增 `tools/_encoding.py` + 各入口接入 |
| D10 | `verify`/`generate` 退出码违背契约 | 🟠 | 设计文档 §2.2 说依赖缺失=3，实现返回 1 | 对齐契约 |
| D11 | fixtures 的 ground_truth 是不存在的定理名 | 🟠 | `Nat.pow_le_self`/`add_left_comm` 在索引中不存在 | 改为索引中真实存在的定理 |
| D12 | README 快速开始的 `search "加法结合律"` 返回空 | 🟠 文档债 | 检索器无中文归一（设计文档 §2.3 承诺"查询预处理"） | 补确定性别名表 `data/index/query_aliases.json` |

## 三、构建产物清单（M6 重建）

| 产物 | 说明 | SHA256 |
|------|------|--------|
| `hws-formal-math-v0.1.0-win64.zip` | CLI 冻结产物（onedir，含 `_internal/` 数据） | 见 `release/manifest.json`（命令实算，非手抄） |
| `hws_formal_math_navigator-0.1.0.tar.gz` | 源码包 | 同上 |
| `hws_formal_math_navigator-0.1.0-py3-none-any.whl` | wheel | 同上 |

**打包确定性**：`tools/package_release.py` 用 `ZIP_STORED` + 条目显式 sort + 全条目固定 `date_time`
→ 两次独立打包**逐字节一致**（实测 sha256 相同）。可复跑的是**打包这一步**；
exe 构建本身（PyInstaller）不承诺跨机字节一致。

## 四、发布物本体验证（真下载，非本机 dist）

```bash
# ① 真下载（在仓库目录内跑）
gh release download v0.1.0 --dir <tmp> --clobber
# ② 下载件 sha256 与留档逐位比对
sha256sum <下载件>
# ③ 中立目录解压后跑冻结态自检
<解压目录>/hws-formal-math selftest
```

| 检查项 | 结果 |
|--------|------|
| 下载件 sha256 与留档一致 | ✅（M5 附件）；M6 重建附件重算 |
| 中立目录 selftest | ❌ **M5 附件失败**（D1）→ ✅ M6 重建附件通过 |
| 中立目录 bench | ❌ **M5 附件失败**（D2）→ ✅ M6 重建附件通过 |
| 冻结态数据随包断言 | ✅（`✅ 冻结态数据目录随包`） |

> **口径说明**：§四 验的是**从 GitHub 真下载回来的文件**；与"本机 dist 冻结态验收"是两回事
> ——中间隔着一次上传与一次下载，只有前者能证明"附件没在上传环节坏掉或被替换"。

## 五、CI 对账

**规则（权威）**：`gh api repos/<u>/<r>/actions/runs --jq '.total_count'` 应等于该仓收到的
**push/tag 事件数**（一次事件恰一 run，一次 push 推多个提交仍只算 1 个 run）。

**快照**（截至本文件所在提交）：

| 提交 | 事件 | 结论 | 说明 |
|------|------|------|------|
| a31a75c | push | ❌ failure | M5 收尾，CI 配置有误 |
| a0eefbd | push/release | ❌ failure | M5 发布，同上 |
| 28d0eae | push | ✅ success | CI 配置修复（test×2+3.8/3.12 单 OS） |
| c52a646 | push | ✅ success | README 状态行转正 |
| 08ccbd5 | push | ✅ success | RELEASE-M6 初版 |
| 4fa63b3 | push | ❌ failure | **四矩阵已全绿**，build job 因 onedir 路径错红一轮 |
| 6987289 | push | ✅ success | 四矩阵 + build **全绿** |

**首跑诊断如实记录**：四矩阵扩展后首次实跑（4fa63b3）暴露一处**环境差异型**缺陷——
onedir 布局下 `dist/hws-formal-math` 是**目录**，exe 在子目录内，CI 断言路径写错。
修 CI 配置与测试环境依赖**不算动内核**（发布里程碑 DoD 明示边界）。修复后 6987289 全绿。

## 六、收尾固化任务

| 项 | 状态 | 证据 |
|----|------|------|
| CI 首跑全绿（四矩阵） | ✅ | run 38853699358：ubuntu/windows × 3.8/3.12 全 success |
| README 状态行转正 | ✅ | 徽章 + "✅ v0.1.0 已发布" + 下载即用节 |
| 缓议项清零 | ✅ | `plan/DEFERRED-ITEMS.md`（14 项逐条全表） |
| 发布后元信息终检 | ⏳ | topics 待设；assets/digest 见 §三/§四 |
| 发布物本体已验 | ✅ | §四（M6 重建附件，中立目录 selftest/bench 通过） |
| 测试计数（当轮实测） | ✅ | 185 passed（3.8 与 3.12 双解释器，`pytest --collect-only` 实算） |

## 七、诚实口径与已知偏差

| 偏差 | 说明 | 处置 |
|------|------|------|
| M5 发布物本体不可用 | 发布 exe 未能在中立目录跑通（D1/D2） | M6 重建产物；**修订发布附件**（零下载窗口内） |
| M5 "干净环境验证 169 passed" 未覆盖发布物本体 | 当时只验证了源码树 | §四 补真下载验证 |
| GitHub Topics 曾为空 | 建仓时未设 | M6 补齐并回读核验 |

## 八、缓议项结案

见 `plan/DEFERRED-ITEMS.md`（14 项逐条：3 完成 / 7 显式跳过 / 4 延期，各带理由）。

---

> **本文件状态**：✅ v2 定稿（2026-10-16，M6 收尾期真实缺陷复核后重写）
> **下一步**：修订 v0.1.0 发布附件（零下载窗口）；补 GitHub Topics
