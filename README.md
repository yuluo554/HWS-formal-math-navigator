# HWS-formal-math-navigator

形式化数学库导航与证明骨架生成器。

[![CI](https://github.com/yuluo554/HWS-formal-math-navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/yuluo554/HWS-formal-math-navigator/actions/workflows/ci.yml)

**状态**：✅ v0.1.2 已发布（[Release](https://github.com/yuluo554/HWS-formal-math-navigator/releases/tag/v0.1.2)）

## 项目定位

LLM 聊数学会"看起来对"，Lean 内核只认真假。本工具把**长上下文检索**（在超大 mathlib4 库中找可复用定理）与**证明骨架生成**接在**可执行的证明检查器**上，让"生成的证明"从"读着像对"变成**可判定的对象**。

## 核心特性

- **检索**：BM25 确定性检索，零模型依赖，离线可用
- **骨架生成**：模型在环（可插拔开关，默认关闭）
- **内核验证**：Lean 4 内核硬真值，sorry 不计入成功
- **依赖图**：确定性图算法，断链检出，index_gap 区分

## 下载即用

从 [Release](https://github.com/yuluo554/HWS-formal-math-navigator/releases) 下载对应平台的免安装包：

| 平台 | 附件 | 说明 |
|------|------|------|
| **Windows x64** | `hws-formal-math-<tag>-win64.zip` | 解压后运行 `hws-formal-math.exe`（CLI）或 `hws-formal-math-viewer.exe`（桌面查看器） |
| **Linux x86_64** | `hws-formal-math-<tag>-linux-x86_64.zip` | 解压后运行 `./hws-formal-math` / `./hws-formal-math-viewer`（zip 已保留可执行位） |
| **macOS** | `hws-formal-math-<tag>-macos-*.zip` | 同上；首次运行可能需在「隐私与安全性」放行 |
| 源码安装 | `*.tar.gz` / `*.whl` | `pip install`（Python 3.12+）；GUI 需 `[gui]` extra |

> **每个 zip 内含两个可执行件**：`hws-formal-math`（CLI）与 `hws-formal-math-viewer`（桌面查看器）。
> 两者共用同一份 `_internal/data/`（索引/命题/快照）。

```bash
# 校验下载件（Linux/macOS）
sha256sum hws-formal-math-<tag>-linux-x86_64.zip
# Windows
certutil -hashfile hws-formal-math-<tag>-win64.zip SHA256

# 自检（索引数据随包分发，无需额外下载）
./hws-formal-math selftest

# 检索（离线可用）
./hws-formal-math search "加法结合律"
```

> **注意**：产物为 **onedir** 形态（可执行文件与 `_internal/` 目录需同目录，数据在 `_internal/data/`）；
> 单独拷贝可执行文件会因缺数据目录而自检失败。

### pip 安装后数据来自哪里

`pip install` 装的可执行件与仓库布局无关，所以随包资源装到**解释器前缀的共享数据目录**，
不依赖当前工作目录：

| 内容 | 安装位置 | 说明 |
|------|----------|------|
| 索引 / 快照 / 命题 | `<prefix>/share/hws-formal-math/data/` | `default_data_dir()` 在此回落查找 |
| 基准用例 | `<prefix>/share/hws-formal-math/fixtures/` | `bench --suite …` 的用例来源 |

因此在**任意目录**都能跑（已实测：新建 venv 装 wheel 后在空目录执行
`selftest` / `search` / `export` / `bench --suite retrieval` / `viewer --selftest` 全部 exit 0）：

```bash
pip install hws_formal_math_navigator-<版本>-py3-none-any.whl
cd /tmp && hws-formal-math selftest      # 无需 --index-path，无需 cd 到仓根
```

在仓库根运行时仍优先用仓内 `data/`（源码态行为不变）；`--index-path` 可显式覆盖。
若数据目录缺失或与 `manifest.json` 登记的 `sha256` 不符，`selftest` 会**非 0 退出**
（不静默降级成"可用"）。

### 已知环境问题

| 问题 | 说明 |
|------|------|
| onedir 需整包 | 只拷可执行文件不行；必须连同 `_internal/` 一起解压使用 |
| macOS 首次运行被拦 | 未签名二进制，需在「系统设置 → 隐私与安全性」手动放行 |
| 无 Lean 时内核验证不可用 | 未安装 Lean 工具链时检索与依赖图**降级可用**，内核验证如实标注"未执行"；`bench --suite skeleton` 报告 `not_enabled`（不冒充通过） |
| **模型端点尚未实现** | "骨架生成"的三条端点（OpenAI 兼容 / llama.cpp / omni-infer）**目前只有接口与分发逻辑，调用一律抛 `NotImplementedError`**。启用模型（`model.enabled=true`）后 `generate` 会以 `骨架生成失败: …端点待实现`、exit 1 如实失败，**不会**返回凭空编造的骨架。未配置端点时 exit 4（配置错误） |
| Windows 中文控制台 | 已内置 UTF-8 守卫（按 `stream.encoding` 探针 reconfigure），无需手动 `chcp` |

## 前置条件

### 必需

- **Python 3.12+**（源码安装时；免安装包不需要）

### 可选（功能分级）

| 功能 | 前置条件 | 说明 |
|------|----------|------|
| 检索、依赖图 | 无 | 离线可用，零模型依赖 |
| 内核验证 | **Lean 4 + elan**（用户自备） | 需安装 Lean 工具链；调用形态为 `lean <file>`，以退出码为编译判据 |
| 骨架生成 | **模型端点**（用户自备） | ⚠️ **端点尚未实现**（`NotImplementedError`），见「已知环境问题」 |
| 桌面查看器 | **PySide6** | GUI 依赖 |

### Lean 工具链安装

```bash
# 1. 安装 elan
curl --proto '=https' --tlsv1.2 -sSf https://sh.leanprover.com | sh

# 2. 安装 Lean 4
elan default leanprover/lean4:stable

# 3. 验证
lean --version
```

### 模型端点配置

```yaml
# config.yaml
model:
  enabled: false  # 默认关闭
  endpoint: https://api.openai.com/v1
  api_key: ${OPENAI_API_KEY}
  model: openpangu-2.0-flash
```

## 安装

```bash
# 核心依赖
git clone https://github.com/yuluo554/HWS-formal-math-navigator.git
cd HWS-formal-math-navigator
pip install -e .

# 可选：向量化检索
pip install -e ".[vector]"

# 可选：GUI
pip install -e ".[gui]"

# 开发依赖
pip install -e ".[dev]"
```

## 快速开始

```bash
# 自检（索引可读性 + 引擎初始化）
hws-formal-math selftest

# 检索定理（离线可用，零模型依赖）
hws-formal-math search "加法结合律"

# 运行基准（检索 Recall@k/MRR + 依赖图完整率）
hws-formal-math bench --suite retrieval
hws-formal-math bench --suite depgraph

# 生成骨架（模型关闭时接受已形式化的 Lean 声明；模型端点见「已知环境问题」）
hws-formal-math generate "theorem my_thm (n : ℕ) : n + 0 = n := by sorry"

# 验证 Lean 代码（需安装 Lean 工具链；未装时如实标注"未执行"）
hws-formal-math verify "theorem add_zero (n : ℕ) : n + 0 = n := by simp"

# 导出报告（-o 决定文件名；--proposition 可传命题，默认用内置示例）
hws-formal-math export --format json -o out/report.json --proposition "加法结合律"

# 版本
hws-formal-math --version
```

### 桌面查看器

```bash
# 零 Qt 自检（CI / 无图形环境可用）：索引 → 检索 → 依赖图 → 导出 HTML 四步
hws-formal-math-viewer --selftest
# 等价：python -m hws_formal_math.viewer --selftest

# 启动窗口（需要 PySide6：pip install -e ".[gui]"）
hws-formal-math-viewer
```

窗口功能：输入命题 → 「检索定理」列出 Top-K（定理/模块/分数）→ 选中一行即构建依赖图
（节点/边/断链/index_gap 分列）→ 「导出依赖图 HTML」写出 0 外链单文件。
未装 PySide6 时窗口模式返回退出码 **3**（依赖缺失），不会静默当成成功。

### 退出码语义

| 码 | 语义 |
|----|------|
| 0 | 成功 / 基准达标 |
| 1 | 未达标（检索无结果、基准未通过、内核编译失败） |
| 2 | 用法错误（参数错误、套件名未知） |
| 3 | 依赖缺失（如 Lean 未安装、模型未启用时的自然语言骨架生成） |
| 4 | 配置错误（如模型已启用但未配置任何端点） |

### 基准套件状态

| 套件 | 依赖 | 无 Lean 时 |
|------|------|-----------|
| `retrieval` | 索引数据（随包） | ✅ 可用 |
| `depgraph` | 索引数据（随包） | ✅ 可用 |
| `skeleton` | Lean 内核真值 + 预置快照 | ⚠️ 报告 `not_enabled`（**不冒充通过**） |

> `bench` 输出末尾还会打印**领域覆盖度**（`[coverage]` 段）：随包 35 条样例里
> `algebra` / `combinatorics` 达标，`analysis` / `number_theory` 不足。
> 这是**如实披露**，不参与 `all_passed` 判定——样例索引本就不覆盖全库，
> 把它接进门禁会让基准恒红，静默降级成 verified 则是开后门。

## 项目结构

```
src/hws_formal_math/
├── cli.py              # CLI 入口
├── config.py           # 配置管理（含"装态数据目录"回落）
├── core/               # 编排层
│   ├── orchestrator.py
│   ├── model_gateway.py
│   └── report.py       # HTML + JSON 双轨报告（f-string 生成，无模板文件）
├── engine/             # 引擎层
│   ├── retriever.py
│   ├── skeleton_gen.py
│   ├── kernel.py
│   └── depgraph.py
└── viewer/             # 桌面查看器（UI 内联在 main.py，controller 为零 Qt 业务层）
```

## 索引：随包是样例，全量需自建

随包 `data/index/` 是 **35 条精选样例索引**（`manifest.json` 的 `index_kind = curated-sample`），
用于离线检索 / 依赖图 / 基准的可复跑演示——**不是** mathlib4 全量索引。
全量索引由用户用自己指定的 mathlib4 版本构建（只存元数据，不存源码）：

```bash
git clone https://github.com/leanprover-community/mathlib4
python tools/build_index.py --mathlib4 ./mathlib4     --commit-hash $(git -C mathlib4 rev-parse HEAD) --output data/index
```

`build_index.py` 强制要求真实 commit（拒绝 `unknown`），manifest 写 `index_kind=extracted`
与 `upstream_commit`，便于复现与对账。

## 验证与质量

- **CI 矩阵**：`ubuntu-latest` / `windows-latest` × Python `3.12` / `3.13`（4 job）
- **三平台原生构建 + 原生冒烟**：Linux / Windows / macOS 各自在原生 runner 上构建并真实运行冻结产物
- **266 项测试全绿**（本地 Python 3.12 实测；CI 矩阵见上）

  ```bash
  python -m pytest tests/ -q     # 266 passed
  ```
- **数据自证**：每个 `manifest.json` 登记随包数据的 `sha256`，`selftest` 与
  `tools/check_data_integrity.py --data-dir data --strict` 双处核验（篡改即非 0 退出）
- **字节冻结**：`.gitattributes` 用 `data/**` 覆盖全部层级（`-text`），防止 EOL 改写数据字节
- **确定性**：检索/依赖图同输入同结果；报告 JSON 逐字节可复现；生成器支持 `--check` 位级一致
- **打包确定性**：同 dist 树两次独立打包逐字节一致（`ZIP_STORED` + 条目排序 + 固定时间戳）
- **判定不虚高**：`skeleton` 基准在无 Lean 内核时报告 `not_enabled` 而非冒充通过；
  领域覆盖度不足时如实打印而非静默降级

## 确定性纪律

- **检索**：同输入同结果，零模型依赖
- **内核验证**：sorry 不计入成功，报告分列
- **依赖图**：index_gap ≠ 定理不存在
- **模型接入**：可插拔显式开关，默认关闭，不随包分发权重

## 免责声明

> **本工具不随包分发 Lean 工具链、模型权重或 mathlib4 完整源码。**
> - Lean / elan 工具链 = 用户自备前置条件
> - 模型接入 = 可插拔显式开关，默认关闭
> - mathlib4 以版本化快照接入，随仓只存索引元数据
> - 未装 Lean 工具链时：检索与依赖图降级可用，内核验证标注"未执行"

## 文档

- [plan/00-README总览.md](plan/00-README总览.md) - 项目计划总览
- [plan/01-题目详细定义.md](plan/01-题目详细定义.md) - 题目定稿
- [plan/02-算法与口径说明.md](plan/02-算法与口径说明.md) - 算法与判定语义
- [plan/03-基准套件设计.md](plan/03-基准套件设计.md) - 基准设计
- [plan/04-测试与验收.md](plan/04-测试与验收.md) - 测试与验收
- [plan/05-发布与交付.md](plan/05-发布与交付.md) - 发布与交付
- [docs/技术报告.md](docs/技术报告.md) - 技术报告（索引抽取/BM25/内核语义/依赖图/基准）
- [docs/demo/demo.gif](docs/demo/demo.gif) - 查看器演示（检索 → 依赖图 → 导出）

## 许可证

MIT License
