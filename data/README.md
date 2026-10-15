# data/README.md — 依据查证与数据纪律

仓库 `HWS-formal-math-navigator`（形式化数学库导航与证明骨架生成器）。基准日：**2026-10-15**。

## 一、依据查证记录（三态）

| # | 依据 | 三态 | 渠道与说明 |
|---|---|---|---|
| 1 | openPangu-2.0-Flash 模型规格 | ✅已核对 | 官方模型卡（hf-mirror 镜像直连）：MoE，92B 总参数 / ~6B 每 token 激活，**原生 512K（524,288）上下文**，~34T tokens 训练 |
| 2 | **512K 上下文 + 满上下文压缩 MLA KV 仅约 12GB** | ✅已核对 | 官方模型卡 + `mrexodia/llama.cpp-openPangu-2.0-Flash` README——**"大库索引进上下文"的工程可行性前提** |
| 3 | openPangu-2.0-Flash 代码与 Agent 基准 | ✅已核对 | 官方模型卡：**LiveCodeBench V6 85.1 / 50.9**（对应 Lean 代码生成）；**TAU2-Bench 88.0 / 74.0**（对应"检索→编译→修正"多步循环）；SWE-bench Verified 63.1 / 57.6；MCP-Atlas 58.9 / 47.9 |
| 4 | openPangu-2.0-Flash 工具调用与 `<think>` 解析 | ✅已核对 | `mrexodia/llama.cpp-openPangu-2.0-Flash` README（GitHub API 直连）：fork 支持 "tool calling and `<think>` reasoning parsing" |
| 5 | **mathlib4**（检索底座，核心） | ✅已获取 | `https://api.github.com/repos/leanprover-community/mathlib4` 直连 200；tarball `https://codeload.github.com/leanprover-community/mathlib4/tar.gz/refs/heads/master` HTTP 200，`application/x-gzip` |
| 6 | **Lean 4**（内核验证，硬真值来源） | ✅已获取 | `https://api.github.com/repos/leanprover/lean4` 直连 200 |
| 7 | mathlib4 版本快照 commit hash | ⬜待核对 | 入库时**固定并登记**（检索结果可复现的前提） |
| 8 | Lean / elan 版本要求与安装指引 | ⬜待核对 | 官方文档核对；题面已声明为**用户自备前置条件** |
| 9 | 公开题库（回归集） | ⬜待核对 | `marcusm117/ProofNet-Verified`(1★)、miniF2F 风格、`lean-dojo/ITPEval`(4★)、`Sequential-Intelligence-Lab/MathlibLemma`(2★)——**逐库 license 核对**；不可用则退回纯合成命题 |
| 10 | openPangu 部署路径 | ✅/⬜ | llama.cpp fork ✅；CUDA/ROCm 引擎 ✅；omni-infer（昇腾，gitcode）⬜ 待核对 |
| 11 | 模型许可 | ⬜待核对 | OPENPANGU MODEL LICENSE AGREEMENT VERSION 2.0；入库时核对"不随仓分发权重"措辞 |
| 12 | 开源空白论据（硬） | ✅已核对 | GitHub repo 检索（基准日 2026-10-15）：`mathlib theorem retrieval benchmark` **0**；`formal math library benchmark long context` **0**；`openpangu-2.0` **4**（零应用层） |
| 13 | 开源空白论据（软，辅助；**可对标的既有件**） | ⬜软论据 | `LeanEuclid` 144★（欧氏几何 autoformalization 基准）、`lean-graph` 55★（Lean4 依赖图）、`ITPEval` 4★、`MathlibLemma` 2★、`ProofNet-Verified` 1★、`Lean4-Faithful-Translator` 1★、`lean4-eros-vs-aphrodite` 0★、`PROOF-CHECKER` 0★；**均单点，无"检索+骨架生成+内核验证+公开基准"闭环** |

## 二、数据源可获取性记录

| 源 | 可获取性 | 获取方式 | 用途 |
|---|---|---|---|
| mathlib4（源码） | ✅ 已获取 | GitHub API / tarball（**用户自取，不入仓**） | 构建库索引（元数据） |
| mathlib4 索引元数据 | ✅ 自产 | 抽取器从快照生成 | 随仓分发（检索底座） |
| Lean 4 / elan 工具链 | ⬜ 用户自备 | 官方安装器（**前置条件**） | 内核验证（硬真值） |
| openPangu-2.0-Flash 端点 | ✅ 可达（用户自备） | OpenAI 兼容端点 / llama.cpp server | 骨架生成（显式开关，默认关） |
| 模型权重 | ⛔ 不分发 | — | **不随包分发** |
| mathlib4 完整源码 | ⛔ 不入仓 | — | 体积过大；只入索引元数据 |
| 公开题库 | ⬜ 待核对 | 逐库 license 核对后可选下载 | 可选回归集 |

## 三、合成数据纪律

1. **合成命题生成器**：程序化生成命题集，含**"可形式化"与"不可形式化"对照**（前者有 Lean 真值，后者用于验证"不可形式化"识别的诚实性——不得把不可形式化者硬编成通过）。
2. **真值来源 = Lean 内核编译结果**（硬真值，无需合成真值台账）。但**`sorry` 占位不计入证明成功**：真值台账须分列 `proved_no_sorry` / `compiles_with_sorry` / `fails`。
3. **索引元数据快照**：`data/index/` 存定理名/签名/依赖边 + mathlib4 commit hash + sha256；**不含 mathlib4 源码**。
4. **假数据白名单**（合成命题中的占位标识，防与真实内容混淆）：
   - 假定理名前缀：`Sample.theorem_*` / `Demo.lemma_*`（明确标注为合成）
   - 假 DOI 前缀：`10.9999/`；假 arXiv 号段：`9999.99999`
   - 假作者：`A. Example` / `Test Author`；假机构：`Example University` / `样例大学`
5. **预置模型输出快照**：含模型名、版本、生成参数、原始输出（含 `<think>` 段）、sha256；随仓只存快照。
6. **只增不改**：`data/index/**` 与 `data/snapshots/**` 入仓后标 `.gitattributes` `-text` 防 EOL 改写字节。

## 四、编码纪律

Lean 源码与索引元数据一律按 **UTF-8** 读写，**不做编码猜测**。非 UTF-8 一律报错并提示转换。Lean 源码中若含非 ASCII 标识符（mathlib 有 Unicode 记号），统一按 UTF-8 处理并登记。
