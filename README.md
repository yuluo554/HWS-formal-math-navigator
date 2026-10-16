# HWS-formal-math-navigator

形式化数学库导航与证明骨架生成器。

[![CI](https://github.com/yuluo554/HWS-formal-math-navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/yuluo554/HWS-formal-math-navigator/actions/workflows/ci.yml)

**状态**：✅ v0.1.0 已发布（[Release](https://github.com/yuluo554/HWS-formal-math-navigator/releases/tag/v0.1.0)）

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
| **Windows x64** | `hws-formal-math-<tag>-win64.zip` | 解压后运行 `hws-formal-math.exe` |
| **Linux x86_64** | `hws-formal-math-<tag>-linux-x86_64.zip` | 解压后运行 `./hws-formal-math`（zip 已保留可执行位） |
| **macOS** | `hws-formal-math-<tag>-macos-*.zip` | 解压后运行 `./hws-formal-math`；首次运行可能需在「隐私与安全性」放行 |
| 源码安装 | `*.tar.gz` / `*.whl` | `pip install`（Python 3.8+） |

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

### 已知环境问题

| 问题 | 说明 |
|------|------|
| onedir 需整包 | 只拷可执行文件不行；必须连同 `_internal/` 一起解压使用 |
| macOS 首次运行被拦 | 未签名二进制，需在「系统设置 → 隐私与安全性」手动放行 |
| 无 Lean 时内核验证不可用 | 未安装 Lean 工具链时检索与依赖图**降级可用**，内核验证如实标注"未执行"；`bench --suite skeleton` 报告 `not_enabled`（不冒充通过） |
| Windows 中文控制台 | 已内置 UTF-8 守卫（按 `stream.encoding` 探针 reconfigure），无需手动 `chcp` |

## 前置条件

### 必需

- **Python 3.8+**（源码安装时；免安装包不需要）

### 可选（功能分级）

| 功能 | 前置条件 | 说明 |
|------|----------|------|
| 检索、依赖图 | 无 | 离线可用，零模型依赖 |
| 内核验证 | **Lean 4 + elan**（用户自备） | 需安装 Lean 工具链 |
| 骨架生成 | **模型端点**（用户自备） | OpenAI 兼容端点 / llama.cpp server |
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

# 生成骨架（需配置模型端点；未配置时接受已形式化的 Lean 声明）
hws-formal-math generate "theorem my_thm (n : ℕ) : n + 0 = n := by sorry"

# 验证 Lean 代码（需安装 Lean 工具链；未装时如实标注"未执行"）
hws-formal-math verify "theorem add_zero (n : ℕ) : n + 0 = n := by simp"
```

### 退出码语义

| 码 | 语义 |
|----|------|
| 0 | 成功 / 基准达标 |
| 1 | 未达标（检索无结果、基准未通过） |
| 2 | 用法错误（参数错误、套件名未知） |
| 3 | 依赖缺失（如 Lean 未安装） |
| 4 | 配置错误 |

### 基准套件状态

| 套件 | 依赖 | 无 Lean 时 |
|------|------|-----------|
| `retrieval` | 索引数据（随包） | ✅ 可用 |
| `depgraph` | 索引数据（随包） | ✅ 可用 |
| `skeleton` | Lean 内核真值 + 预置快照 | ⚠️ 报告 `not_enabled`（**不冒充通过**） |

## 项目结构

```
src/hws_formal_math/
├── cli.py              # CLI 入口
├── config.py           # 配置管理
├── core/               # 编排层
│   ├── orchestrator.py
│   └── model_gateway.py
├── engine/             # 引擎层
│   ├── retriever.py
│   ├── skeleton_gen.py
│   ├── kernel.py
│   └── depgraph.py
├── viewer/             # 桌面查看器
└── templates/          # 报告模板
```

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

## 许可证

MIT License
