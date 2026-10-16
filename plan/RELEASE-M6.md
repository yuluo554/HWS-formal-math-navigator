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
| D6 | `tools/hws-formal-math.spec` 硬编码本机绝对路径 | 🟠 脱敏泄露 | spec 的 `pathex` 写死了本机构建路径（盘符 + 工作根）| 用 `SPECPATH` 相对推导；**历史残留见 §九** |
| D7 | `tools/gen_snapshots.py` 是 `NotImplementedError` 桩 | 🟠 | `data/snapshots/manifest.json` 为 `sha256: "placeholder"`, `case_count: 0` | 实现确定性生成器（`--check` 位级一致） |
| D8 | 无 LICENSE 文件 | 🟠 | `pyproject`/README 声明 MIT 但仓内无文件 | 补 `LICENSE` |
| D9 | `tools/` 脚本无编码守卫 | 🟠 CI 必红 | skill 明示"编码守卫要覆盖所有会打印的可执行入口" | 新增 `tools/_encoding.py` + 各入口接入 |
| D10 | `verify`/`generate` 退出码违背契约 | 🟠 | 设计文档 §2.2 说依赖缺失=3，实现返回 1 | 对齐契约 |
| D11 | fixtures 的 ground_truth 是不存在的定理名 | 🟠 | `Nat.pow_le_self`/`add_left_comm` 在索引中不存在 | 改为索引中真实存在的定理 |
| D12 | README 快速开始的 `search "加法结合律"` 返回空 | 🟠 文档债 | 检索器无中文归一（设计文档 §2.3 承诺"查询预处理"） | 补确定性别名表 `data/index/query_aliases.json` |

## 三、构建产物清单（M6 重建，最终基线）

**基线**：`git rev-parse HEAD`（本文件所在提交的父提交为产物构建基线；`git diff <基线>..HEAD -- src/ tools/hws-formal-math.spec` 为空表示产物与源码同基线）。

| 产物 | 说明 | 大小 | SHA256 |
|------|------|------|--------|
| `hws-formal-math-v0.1.0-win64.zip` | CLI 冻结产物（onedir，含 `_internal/` 数据） | 17,604,753 | `42ad6af586fb10164140d25d40a353ceeab2192a785887641f031ab0fa7be1e2` |
| `hws_formal_math_navigator-0.1.0.tar.gz` | 源码包 | 58,664 | `3f24a4540fdc0483606cadaaddf3975037475d115b72439754bf6c69d8f1fc1a` |
| `hws_formal_math_navigator-0.1.0-py3-none-any.whl` | wheel | 43,124 | `a75c3a104aa79000df5b4169596e413514db0f75c88848218255b9633c199aa1` |

**打包确定性**：`tools/package_release.py` 用 `ZIP_STORED` + 条目显式 sort + 全条目固定 `date_time`
→ 两次独立打包**逐个字节一致**（实测两轮 sha256 均为 `42ad6af5…`）。可复跑的是**打包这一步**；
exe 构建本身（PyInstaller）不承诺跨机字节一致。

> **M5 附件已作废**：v0.1.0 原附件（`31bb6c7d…` exe / `fdd7558a…` tar.gz / `85d51157…` whl）
> 因 D1/D2 缺陷不可用，其 sha256 保留于此仅作历史对账，**不作为发布基线**。

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
| 下载件 sha256 与留档一致 | ✅ M6 重建附件（`42ad6af5…` 逐位一致，含**匿名**裸 https 下载复验） |
| 中立目录 selftest | ❌ **M5 附件失败**（D1）→ ✅ M6 重建附件通过 |
| 中立目录 search / bench | ❌ **M5 附件失败**（D2）→ ✅ M6 重建附件通过 |
| 冻结态数据随包断言 | ✅（`✅ 冻结态数据目录随包`） |

> **口径说明**：§四 验的是**从 GitHub 真下载回来的文件**；与"本机 dist 冻结态验收"是两回事
> ——中间隔着一次上传与一次下载，只有前者能证明"附件没在上传环节坏掉或被替换"。

## 五、CI 对账

**规则（权威）**：`gh api repos/<u>/<r>/actions/runs` 逐条列 `head_sha`+`event`+`conclusion`，
与本地 `git log` 对齐——**每个 push/tag 事件恰一 run**（一次 push 推多个提交仍只算 1 个 run）。

**逐 sha 快照**（截至本文件所在提交；本文件自身的提交还会再产生 1 个 run）：

| 提交 | 事件 | 结论 | 说明 |
|------|------|------|------|
| a31a75c | push | ❌ failure | M5 收尾，CI 配置有误（setup-python 无效 env 参数 + 缺 build 模块） |
| a0eefbd | push + release | ❌ failure | M5 发布，同上 |
| 28d0eae | push | ✅ success | CI 配置修复 |
| c52a646 / 08ccbd5 | push | ✅ success | README 转正 / RELEASE 初版 |
| 4fa63b3 | push | ❌ failure | **四矩阵已全绿**，build job 因 onedir 路径错红一轮 |
| 6987289 | push | ✅ success | 四矩阵 + build 全绿 |
| 42a4a7c / 2b76120 | push | ✅ success | 文档回写 |
| 2b76120 | release | ❌ failure | tag 触发的 release job 对 onedir 目录跑 `sha256sum` |
| 3c6ae35 | push | ✅ success | release job 修复（确定性打包器） |
| 3c6ae35 | release | ❌ failure | **旧 workflow 修订**的陈旧 run（当时 `release: published` 触发仍在） |
| 24f963b | push | ✅ success | **移除自动发 Release** + build job 内打包确定性自测 |

**首跑诊断如实记录**（两轮，均为环境差异型，非业务逻辑缺陷）：
1. `4fa63b3`：onedir 布局下 `dist/hws-formal-math` 是**目录**，exe 在子目录内 → CI 路径断言写错。
2. `2b76120`(release)：同因，release job 对目录跑 `sha256sum`。

**发布模型定夺（重要）**：移除 `release: published` 触发与自动发 Release job，原因两条：
① **PyInstaller 产物不承诺跨机字节一致**——CI 构建的 exe 哈希必与本地台账不同，自动上传会让
"附件哈希可对账"这一承诺失效；② 该触发与发版动作形成**重跑循环**。
故最终形态 = **CI 只验证**（四矩阵测试 + exe 能构建能运行 + 打包确定性自测），
**发布附件走本地确定性构建 + 手工上传 + sha256 入台账**。
`3c6ae35` 的那次 release 失败 run 属**被移除的旧触发**留下的陈旧记录，
其 head_sha 指向的 workflow 修订已不含该 job——如实登记，不删 run（历史留痕面）。

## 六、收尾固化任务

| 项 | 状态 | 证据 |
|----|------|------|
| CI 首跑全绿（四矩阵） | ✅ | run 38853699358 / 38855312502 / 38855814967：ubuntu+windows × 3.8/3.12 全 success |
| README 状态行转正 | ✅ | CI 徽章 + "✅ v0.1.0 已发布" + 下载即用节 + CI 矩阵说明 |
| 缓议项清零 | ✅ | `plan/DEFERRED-ITEMS.md`（14 项 + §六 12 项复核发现） |
| 发布后元信息终检 | ✅ | topics 已设并回读；assets/digest 见 §三/§四 |
| 发布物本体已验 | ✅ | §四（**匿名**真下载 → sha256 一致 → 中立目录 selftest/search/bench 通过） |
| 发布附件修订 | ✅ | §九（tag 迁移 + 附件替换 + Release 转正） |
| 测试计数（当轮实测） | ✅ | 185 passed（3.8 与 3.12 双解释器实测） |

## 七、诚实口径与已知偏差

| 偏差 | 说明 | 处置 |
|------|------|------|
| M5 发布物本体不可用 | 发布 exe 未能在中立目录跑通（D1/D2） | M6 重建产物；**修订发布附件**（零下载窗口内） |
| M5 "干净环境验证 169 passed" 未覆盖发布物本体 | 当时只验证了源码树 | §四 补真下载验证 |
| GitHub Topics 曾为空 | 建仓时未设 | M6 补齐并回读核验 |

## 八、缓议项结案

见 `plan/DEFERRED-ITEMS.md`（14 项逐条：3 完成 / 7 显式跳过 / 4 延期，各带理由）。

## 九、修订执行记录与残留暴露面（如实登记）

### 9.1 发布附件修订（用户已授权）

| 步骤 | 结果 |
|------|------|
| 删除旧附件 | ✅ 3 个（含损坏 exe） |
| tag 迁移到当前全绿提交 | ✅ `git rev-list -n1 v0.1.0` == `git rev-parse HEAD` |
| 上传 M6 重建附件 | ✅ 4 个（zip + sdist + wheel + SHA256SUMS） |
| **tag 移动致 Release 转 draft** | ✅ 实测确认（skill 记录的行为）；已 `gh release edit --draft=false` 转正 |
| 发布物本体复核（真下载） | ✅ 下载件 sha256 与台账逐位一致；中立目录 `selftest`/`search`/`bench` 全通过 |
| 版本号一致性 | ✅ 仍为 v0.1.0（改版本号需重建产物，本次未改版本号） |

### 9.2 历史残留（未改写历史，如实登记）

**发现**：脱敏扫描全历史 blob 时命中 **2 个提交**的 `tools/hws-formal-math.spec` 含硬编码构建路径
（`a0eefbd` = M5 引入，`4fa63b3` = M6 修复该文件的那次提交本身仍在旧内容 diff 中）。
HEAD 已修（spec 现用 `SPECPATH` 相对推导），但**历史 blob 中仍在**。

**严重度定夺**（按 skill 分级问询）：该串构成 = 盘符 + 工作根父目录 + **项目名（有意公开的坐标）** + `src`；
**不含**用户名、邮箱、凭据、令牌、个人标识。属"本机工作根路径签名"，非个人敏感信息。

**处置决策**：**不重写历史**。理由三条（skill"发布前历史扫描的发现要分级处置"判别三问）：
1. 词面在审计分级里**不是 HARD**（无用户名/邮箱/密钥；工作根名本身是公开项目坐标）；
2. 重写代价（全提交改写 + CI 留痕断裂 + tag 迁移）与泄露面（一处构建路径、无个人标识）**不匹配**；
3. HEAD 已清干净，词面不再增量。

**判别依据留档**：该串**是**我们工作过程的路径痕迹，但**不是**个人身份信息——按 skill
"低敏词面 → HEAD 修干净 + 定夺理由留档 + 不重写"的中间端处置。

### 9.3 留档自伤（已修）

本书写"验证描述"时曾**逐字复述**该路径字面值（skill 明示的"验证描述是最高频自命中源"反模式）。
已改为描述性指代（"盘符 + 工作根"），并复跑扫描确认归零。

---

> **本文件状态**：✅ v4 定稿（2026-10-16，含发布修订执行记录、CI 对账、历史残留定夺）
> **项目状态**：M1–M6 全部里程碑达成；发布物本体已验；CI 四矩阵全绿
