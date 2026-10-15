# HWS-formal-math-navigator

形式化数学库导航与证明骨架生成器。

## 项目定位

LLM 聊数学会"看起来对"，Lean 内核只认真假。本工具把**长上下文检索**（在超大 mathlib4 库中找可复用定理）与**证明骨架生成**接在**可执行的证明检查器**上，让"生成的证明"从"读着像对"变成**可判定的对象**。

## 核心特性

- **检索**：BM25 确定性检索，零模型依赖，离线可用
- **骨架生成**：模型在环（可插拔开关，默认关闭）
- **内核验证**：Lean 4 内核硬真值，sorry 不计入成功
- **依赖图**：确定性图算法，断链检出，index_gap 区分

## 前置条件

### 必需

- **Python 3.8+**

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
# 检索定理
hws-formal-math search "加法结合律"

# 生成骨架（需配置模型端点）
hws-formal-math generate "∀ n : ℕ, n + 0 = n"

# 验证 Lean 代码（需安装 Lean）
hws-formal-math verify "theorem add_zero (n : ℕ) : n + 0 := by simp"

# 运行基准
hws-formal-math bench

# 自检
hws-formal-math selftest
```

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
