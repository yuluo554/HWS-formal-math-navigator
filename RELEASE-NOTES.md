# HWS-formal-math-navigator v0.1.1

> **v0.1.1 变更（2026-10-18）**：回访修复三项"承诺未兑现"——
> ① 桌面查看器**真实现并随包分发**（检索/依赖图/导出接线 + 零 Qt 自检 + 双 exe 打包）；
> ② 索引溯源**诚实化**（随包 35 条为 `curated-sample` 样例，拒绝 `unknown` commit）；
> ③ **技术报告与演示 GIF 落仓并进附件**。测试 198 → 212 全绿。


形式化数学库导航与证明骨架生成器 —— 让"生成的证明"从"读着像对"变成**可判定的对象**。

## 下载即用

| 平台 | 附件 | 说明 |
|------|------|------|
| **Windows x64** | `hws-formal-math-<tag>-win64.zip` | 解压后运行 `hws-formal-math.exe` |
| **Linux x86_64** | `hws-formal-math-<tag>-linux-x86_64.zip` | `chmod +x` 后运行 `hws-formal-math`（zip 已保留可执行位，通常无需手动 chmod） |
| **macOS** | `hws-formal-math-<tag>-macos-*.zip` | 解压后运行 `hws-formal-math`；首次运行可能需在「隐私与安全性」放行 |
| 源码安装 | `hws_formal_math_navigator-*.tar.gz` / `*.whl` | `pip install`（需 Python 3.8+） |

**onedir 形态**：可执行文件与 `_internal/` 目录必须**同目录**（索引等数据随包分发在 `_internal/data/`）。单独拷贝可执行文件会因缺数据而自检失败。

```bash
# 校验下载件（Linux/macOS）
sha256sum hws-formal-math-<tag>-linux-x86_64.zip
# Windows
certutil -hashfile hws-formal-math-<tag>-win64.zip SHA256

# 自检（索引数据随包，无需额外下载）
./hws-formal-math selftest

# 检索（离线可用，零模型依赖）
./hws-formal-math search "加法结合律"

# 基准
./hws-formal-math bench --suite retrieval
./hws-formal-math bench --suite depgraph
```

## 功能

- **检索**：mathlib4 定理检索（BM25，零模型依赖，离线可用；含确定性中文别名归一）
- **骨架生成**：证明骨架生成（规则模式；模型端点可选，默认关闭）
- **内核验证**：Lean 4 内核硬真值，`sorry` 不计入成功，三态判定（PASS_NO_SORRY / PASS_WITH_SORRY / FAIL）
- **依赖图**：确定性图算法，断链检出，`index_gap` ≠ 定理不存在
- **基准**：Recall@k / MRR / 依赖图完整率，阈值反射自代码常量
- **报告**：HTML（0 外链，断网可开）+ JSON 逐字节可复现

## 前置条件

- **Python 3.8+**（源码安装时；冻结产物免安装）
- **Lean 4 + elan**（内核验证需要，**用户自备**）——未安装时检索与依赖图**降级可用**，内核验证如实标注"未执行"
- **模型端点**（骨架生成需要，可选；OpenAI 兼容端点 / llama.cpp server）

## 验证与质量

- **CI 四矩阵**：ubuntu-latest / windows-latest × Python 3.8 / 3.12
- **三平台原生构建 + 原生冒烟**：Linux / Windows / macOS 各自在原生 runner 上构建并真实运行冻结产物
- **185 tests passed**（双解释器）
- **确定性**：检索/依赖图同输入同结果；报告 JSON 逐字节可复现；生成器支持 `--check` 位级一致
- **打包确定性**：同 dist 树两次独立打包逐字节一致（`ZIP_STORED` + 条目排序 + 固定时间戳）
- **判定不虚高**：`skeleton` 基准在无 Lean 内核时报告 `not_enabled` 而非冒充通过

## 免责声明

本工具**不随包分发** Lean 工具链、模型权重或 mathlib4 完整源码。检索候选与骨架均为**建议**；
形式化忠实度（自然语言命题 → Lean statement 是否等价）**不承诺自动保证**，须人工确认。

## 许可证

MIT
