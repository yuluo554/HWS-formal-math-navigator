# HWS-formal-math-navigator v0.1.2

> **v0.1.2 变更（2026-10-21）**：按二次迭代诊断（`update/`）修三洞 + 补数据自证——
> ① **pip 渠道装完能用**：`data/` 与基准用例此前**一个都没进 wheel/sdist**，
>    `pip install` 后 `selftest`/`search`/`export`/`bench` 全部失败；现在装到
>    `<prefix>/share/hws-formal-math/` 并由 `default_data_dir()` 在装态回落查找；
> ② **内核验证真能跑**：此前调 `lean --check`，而该选项**在 Lean 4 里不存在**
>    （上游 `shell.cpp` 无此项）→ 正确证明也判 FAIL；改为 `lean <file>` 以退出码为判据；
> ③ **发布形态门禁不再假通过**：`assert_release_shape.py` 用子串判 CLI，
>    而 CLI 名是查看器名的前缀 → 只含查看器的 zip 曾被判"含 CLI + 查看器"；
>    改为 basename 精确比较并补两条负控；
> ④ **冻结数据字节自证**：`.gitattributes` 原规则 `*` 不匹配二级目录，
>    `data/snapshots/v1/snapshots.json` 等三个文件已发生 CRLF/LF 漂移且无人发现；
>    改用 `data/**`，并新增 `tools/check_data_integrity.py` + `selftest` 双处核验。
>
> **不兼容变更**：Python floor `>=3.8` → **`>=3.12`**（3.8 已 EOL，且与
> `setuptools>=77` 的 PEP 639 SPDX license 不可兼得）；移除未使用依赖 `jinja2`。

形式化数学库导航与证明骨架生成器 —— 让"生成的证明"从"读着像对"变成**可判定的对象**。

## 下载即用

| 平台 | 附件 | 说明 |
|------|------|------|
| **Windows x64** | `hws-formal-math-<tag>-win64.zip` | 解压后运行 `hws-formal-math.exe` |
| **Linux x86_64** | `hws-formal-math-<tag>-linux-x86_64.zip` | `chmod +x` 后运行 `hws-formal-math`（zip 已保留可执行位，通常无需手动 chmod） |
| **macOS** | `hws-formal-math-<tag>-macos-*.zip` | 解压后运行 `hws-formal-math`；首次运行可能需在「隐私与安全性」放行 |
| 源码安装 | `hws_formal_math_navigator-*.tar.gz` / `*.whl` | `pip install`（需 Python 3.12+） |

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

- **Python 3.12+**（源码安装时；冻结产物免安装）
- **Lean 4 + elan**（内核验证需要，**用户自备**）——未安装时检索与依赖图**降级可用**，内核验证如实标注"未执行"
- **模型端点**（骨架生成需要，可选；OpenAI 兼容端点 / llama.cpp server）——
  ⚠️ **三条端点目前均未实现**（调用抛 `NotImplementedError`，`generate` 以 exit 1 如实失败）

## 验证与质量

- **CI 矩阵**：ubuntu-latest / windows-latest × Python 3.12 / 3.13
- **三平台原生构建 + 原生冒烟**：Linux / Windows / macOS 各自在原生 runner 上构建并真实运行冻结产物
- **227 tests passed**（本地 Python 3.12 实测）
- **数据自证**：`manifest.json` 的 `sha256` 与磁盘实算对撞（`selftest` + `tools/check_data_integrity.py --strict`）
- **确定性**：检索/依赖图同输入同结果；报告 JSON 逐字节可复现；生成器支持 `--check` 位级一致（只读）
- **打包确定性**：同 dist 树两次独立打包逐字节一致（`ZIP_STORED` + 条目排序 + 固定时间戳）
- **判定不虚高**：`skeleton` 基准在无 Lean 内核时报告 `not_enabled` 而非冒充通过；
  领域覆盖度不足时如实打印（不接进 `all_passed`，也不静默降级）

## 免责声明

本工具**不随包分发** Lean 工具链、模型权重或 mathlib4 完整源码。检索候选与骨架均为**建议**；
形式化忠实度（自然语言命题 → Lean statement 是否等价）**不承诺自动保证**，须人工确认。

## 许可证

MIT
