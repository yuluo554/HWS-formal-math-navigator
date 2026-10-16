# 缓议项清零表（M6 收尾固化）

> 本表记录所有"待议/待定/待核"项的最终处置决策。
> 处置类型：✅ 完成 / ⬜ 跳过（含理由）/ ⏳ 延期（含原因）

## 一、来自 plan/00-README总览.md 承诺-证据台账的待核项

| 编号 | 承诺项 | 原始状态 | 处置 | 理由/证据 |
|------|--------|----------|------|-----------|
| D1 | 公开题库回归集（ProofNet-Verified / miniF2F 风格） | ⬜ 待核对 | ⬜ 跳过 | 非首期目标；用户明确要求"先跑通核心流程"；列入扩展项 |
| D2 | Lean/elan 版本与安装指引 | ⬜ 待核对 | ✅ 完成 | README 已含安装指引；版本要求写进 pyproject.toml requires-python |
| D3 | 模型许可合规（OPENPANGU MODEL LICENSE 2.0） | ⬜ 待核对 | ✅ 完成 | 不分发权重即合规；README 显式声明"不随包分发模型权重" |

## 二、来自 M1-M5 开发过程中的待议项

| 编号 | 待议项 | 来源 | 处置 | 理由/证据 |
|------|--------|------|------|-----------|
| D4 | GUI 桌面查看器（PySide6） | M4 设计 | ⬜ 跳过 | 首期聚焦 CLI；GUI 列扩展项；pyproject.toml 已声明 gui extra 但 CI 不跑 |
| D5 | 向量化检索（numpy + scikit-learn） | M3 设计 | ⬜ 跳过 | BM25 已满足首期需求；vector extra 已声明但 CI 不跑 |
| D6 | 模型端点接入（OpenAI / llama.cpp） | M4 设计 | ⬜ 跳过 | 模型在环但默认关闭；首期不强制；config.yaml 已含配置模板 |
| D7 | mathlib4 全量源码入仓 | M1 数据计划 | ⬜ 跳过 | 数 GB 体积，不适合入仓；版本化快照 + 索引元数据已满足需求 |
| D8 | 跨平台 exe（Windows + Linux + macOS） | M5 发布 | ⏳ 延期 | CI 仅构建 sdist/wheel；exe 仅 Windows；Linux/macOS 列入扩展项 |
| D9 | 中文 Lean 文档/教程 | M0 计划 | ⬜ 跳过 | 非工具功能；列入文档扩展项 |
| D10 | 论文格式/文献审计 / AIGC 检测 | M0 弃选项 | ⬜ 跳过 | 与系列⑪文献审计工作台撞域；已显式弃选 |

## 三、CI 相关待议项

| 编号 | 待议项 | 来源 | 处置 | 理由/证据 |
|------|--------|------|------|-----------|
| D11 | CI 四矩阵（windows 3.8 / windows 3.12 / ubuntu 3.8 / ubuntu 3.12） | M6 DoD | ⏳ 延期 | 本机网络不可达，无法推送触发 CI；已修复 CI 配置（移除无效 env 参数 + 安装 build 模块）；本地等价校验 169 passed；CI 待首推验证 |
| D12 | Windows CI 矩阵 | M6 DoD | ⏳ 延期 | 同上；当前 CI 仅 ubuntu-latest；windows 矩阵列入扩展项 |

## 四、发布后元信息待核项

| 编号 | 待议项 | 来源 | 处置 | 理由/证据 |
|------|--------|------|------|-----------|
| D13 | GitHub topics 补齐 | M6 DoD | ⏳ 延期 | gh 未认证，无法设置；待首推后手动设置：lean4, mathlib4, formal-math, theorem-proving |
| D14 | Release assets digest 与留档一致 | M6 DoD | ✅ 完成 | 本地 sha256 与 GitHub API 返回一致（见下方对账表） |

### D14 对账证据

| 产物 | 本地 sha256 | GitHub API digest | 一致 |
|------|-------------|-------------------|------|
| hws-formal-math.exe | 31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b | sha256:31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b | ✅ |
| hws_formal_math_navigator-0.1.0-py3-none-any.whl | 85d511575bab10e58d9e578cca63cb6f25aabdf77149b1899f017e9fc7c3db2f | sha256:85d511575bab10e58d9e578cca63cb6f25aabdf77149b1899f017e9fc7c3db2f | ✅ |
| hws_formal_math_navigator-0.1.0.tar.gz | fdd7558a74cbd515643a223654a22fc0d5c661b50274bf6cc94114488d6cc12c | sha256:fdd7558a74cbd515643a223654a22fc0d5c661b50274bf6cc94114488d6cc12c | ✅ |

## 五、处置统计

| 处置类型 | 数量 | 说明 |
|----------|------|------|
| ✅ 完成 | 3 | D2, D3, D14 |
| ⬜ 跳过 | 7 | D1, D4, D5, D6, D7, D9, D10 |
| ⏳ 延期 | 4 | D8, D11, D12, D13 |
| **总计** | **14** | |

## 六、M6 收尾期新增缺陷（复核发现，已全部修复）

> 这些不是"缓议项"，而是 **M5 声称完成却实际未达成**的项——M6 发布物本体复核后暴露。
> 按 skill"如实登记"纪律，单列成表（不回填 M5 的 ✅）。

| 编号 | 缺陷 | 原声称 | 实测 | 修复 |
|------|------|--------|------|------|
| X1 | 发布 exe 跑不通 | M5"exe 构建成功，selftest/search 正常" | 真下载附件 `selftest` → `索引目录不存在` | 冻结态数据目录解析 + spec datas 收数据 |
| X2 | `bench` 是 pytest 包装桩 | M4"CLI 入口实现" | `--suite` 不生效、cwd 错、无基准指标 | 实现 `benchmark` 模块 |
| X3 | `test_bench_probe.py` 空桩 | plan/03 承诺"探活" | 3 个 `pass`（假门） | 11 项双向对照探活 + 变异验证 |
| X4 | depgraph 违反 K2 | M3"index_gap 语义" | 已覆盖模块被判 index_gap（`_is_module_covered` 死循环） | 模块覆盖集判定 |
| X5 | 循环导入 | — | `import ...engine.retriever` 崩溃 | PEP 562 惰性属性 |
| X6 | spec 硬编码本机路径 | M5"脱敏扫描通过" | spec 的 `pathex` 写死本机构建路径（盘符+工作根） | `SPECPATH` 相对推导；历史残留见 RELEASE-M6 §九 |
| X7 | 快照生成器是桩 | M1"预置快照完成" | `manifest.json` 为 `sha256: "placeholder"` | 实现生成器 + `--check` |
| X8 | 无 LICENSE | 声明 MIT | 仓内无文件 | 补 LICENSE |
| X9 | tools 无编码守卫 | — | CI windows 必红 | `tools/_encoding.py` + 各入口 |
| X10 | 退出码违约 | plan/04 §2.2 契约=3 | 实现返回 1 | 对齐契约 |
| X11 | fixtures 真值不存在 | — | `Nat.pow_le_self` 等不在索引中 | 改为真实定理名 |
| X12 | README 命令返回空 | README 快速开始 | `search "加法结合律"` exit 1 | 确定性别名表 |

## 七、延期项后续行动

| 编号 | 延期项 | 后续行动 | 状态 |
|------|--------|----------|------|
| D8 | 跨平台 exe | 扩展项：Linux/macOS 打包 | 待定 |
| D11 | CI 首跑全绿 | ✅ 已完成（run 38853699358 四矩阵全绿） | 结案 |
| D12 | Windows CI 矩阵 | ✅ 已完成（`matrix.os: [ubuntu-latest, windows-latest]`） | 结案 |
| D13 | GitHub topics | M6 补齐并回读核验 | 进行中 |

---

> **本表状态**：✅ v2 定稿（2026-10-16，M6 收尾期真实缺陷复核后补充 §六）
