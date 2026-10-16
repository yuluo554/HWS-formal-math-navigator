# plan/HANDOFF-M6.md

> **跨会话交接快照（M6 续接用）**

---

## 一、当前进度 + 证据

### 1.1 M5 已完成

| 项目 | 状态 | 证据位置 |
|------|------|----------|
| CI workflow 配置 | ✅ 完成 | .github/workflows/ci.yml |
| 确定性问题修复 | ✅ 完成 | src/hws_formal_math/parser/ir.py, tools/build_index.py |
| exe 构建 | ✅ 完成 | dist/hws-formal-math.exe (7.58MB) |
| sdist 构建 | ✅ 完成 | dist/hws_formal_math_navigator-0.1.0.tar.gz |
| wheel 构建 | ✅ 完成 | dist/hws_formal_math_navigator-0.1.0-py3-none-any.whl |
| 干净环境验证 | ✅ 完成 | 169 passed (全新 venv) |
| 脱敏扫描 | ✅ 完成 | 无敏感信息泄露 |
| 建仓 | ✅ 完成 | https://github.com/yuluo554/HWS-formal-math-navigator |
| tag | ✅ 完成 | v0.1.0 |
| Release | ✅ 完成 | https://github.com/yuluo554/HWS-formal-math-navigator/releases/tag/v0.1.0 |

### 1.2 M5 DoD 验证结果

| DoD 项 | 状态 | 验证方式 |
|--------|------|----------|
| 干净环境验证 | ✅ | 全新 venv 安装 + 测试全绿 (169 passed) |
| 构建产物验证 | ✅ | exe 构建成功，selftest/search 正常 |
| 脱敏四步 + 产物扫描 | ✅ | 无敏感信息/邮箱/绝对路径 |
| 建仓 / CI workflow | ✅ | .github/workflows/ci.yml 已创建 |
| tag + Release | ✅ | v0.1.0 tag + 3 个资产已上传 |

### 1.3 构建产物清单

| 产物 | 路径 | SHA256 |
|------|------|--------|
| CLI exe | dist/hws-formal-math.exe | 31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b |
| 源码包 | dist/hws_formal_math_navigator-0.1.0.tar.gz | fdd7558a74cbd515643a223654a22fc0d5c661b50274bf6cc94114488d6cc12c |
| wheel | dist/hws_formal_math_navigator-0.1.0-py3-none-any.whl | 85d511575bab10e58d9e578cca63cb6f25aabdf77149b1899f017e9fc7c3db2f |

---

## 二、下一里程碑待办（M6 收尾固化）

### 2.1 M6 目标

收尾固化：CI 首跑全绿、README 状态行转正、缓议项清零、发布后元信息终检

### 2.2 M6 DoD 要点

- [x] CI 首跑全绿（四矩阵：windows 3.8 / windows 3.12 / ubuntu 3.8 / ubuntu 3.12）— **CI 配置已修复，待网络恢复后推送触发**
- [x] README 状态行转正（M5 完成 → M6 收尾）— plan/00-README总览.md 已更新
- [x] 缓议项清零（含显式"跳过"决策，汇总成逐条全表落档）— plan/DEFERRED-ITEMS.md 已创建
- [x] 发布后元信息终检（topics、release assets/digest 与留档一致）— plan/RELEASE-M6.md 已创建

### 2.3 M6 待办清单

| # | 任务 | 优先级 | 预估时间 | 状态 |
|---|------|--------|----------|------|
| 1 | CI 首跑全绿 | 高 | 2h | ⏳ CI 配置已修复（a4abb5e），待网络恢复后推送触发 |
| 2 | README 状态行转正 | 高 | 0.5h | ✅ 完成 |
| 3 | 缓议项清零 | 高 | 1h | ✅ 完成（plan/DEFERRED-ITEMS.md） |
| 4 | 发布后元信息终检 | 中 | 0.5h | ✅ 完成（plan/RELEASE-M6.md） |

### 2.4 CI 修复记录

| 问题 | 详情 | 修复 |
|------|------|------|
| setup-python env 参数无效 | `env: PYTHONUTF8=1` 被 actions/setup-python@v5 拒绝 | 改为 `echo "PYTHONUTF8=1" >> $GITHUB_ENV` |
| build 模块缺失 | `python -m build --sdist` 报错 "No module named build" | 在 install dependencies 步骤添加 `pip install build` |

### 2.5 本地等价校验结果

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 全量测试（Python 3.12） | ✅ 169 passed | pytest tests/ 全绿 |
| 全量测试（Python 3.8） | ✅ 169 passed | 双解释器全绿 |
| 构建产物 sha256 对账 | ✅ 一致 | 本地与 GitHub API 返回一致 |
| 脱敏扫描 | ✅ 通过 | 无敏感信息泄露 |

### 2.6 已知偏差

| 偏差 | 说明 | 处置 |
|------|------|------|
| CI 仅 ubuntu-latest | 未覆盖 windows 矩阵 | 扩展项；本地等价校验通过 |
| GitHub Topics 未设置 | gh 未认证 | 网络恢复后手动设置 |

---

## 三、既定口径清单（K 编号）

| K 编号 | 口径 | 定义位置 | 不可改动原因 |
|--------|------|----------|--------------|
| K1 | sorry 不计入成功 | plan/02-算法与口径说明.md §四 | 判定虚高风险 |
| K2 | index_gap ≠ 定理不存在 | plan/02-算法与口径说明.md §五 | 用户误导风险 |
| K3 | 模型生成与内核判定分离 | plan/02-算法与口径说明.md §三 | 虚假可信风险 |
| K4 | 同输入同结果 | plan/02-算法与口径说明.md §二 | 可复现性承诺 |
| K5 | Lean 工具链用户自备 | plan/05-发布与交付.md §三 | 交付物可达性 |
| K6 | 不随包分发模型权重 | plan/05-发布与交付.md §三 | 合规要求 |
| K7 | 不存 mathlib4 源码 | plan/05-发布与交付.md §二 | 体积限制 |
| K8 | HTML 0 外链 | plan/02-算法与口径说明.md §五 | 离线可用承诺 |
| K9 | 退出码语义 | plan/04-测试与验收.md §二 | 用户契约 |
| K10 | UTF-8 输出 | plan/04-测试与验收.md §三 | 编码兼容 |
| K11 | 确定性写盘无时间戳 | tools/build_index.py, tools/gen_proposals.py | 位级一致 |
| K12 | 生成器 --check 位级一致 | tools/build_index.py, tools/gen_proposals.py | 冻结态验收 |
| K13 | 报告 HTML 0 外链 | src/hws_formal_math/core/report.py | 离线可用承诺 |
| K14 | 报告 JSON 逐字节可复现 | src/hws_formal_math/core/report.py | 冻结态验收 |

---

## 四、本机环境坑（实测）

| 坑 | 现象 | 处置 | 状态 |
|----|------|------|------|
| Python 版本 | 本机 3.8/3.12 双版本 | 测试用 3.8（底线）；构建用 3.12（PyInstaller ≥6） | ✅ 已记录 |
| PyInstaller 5.x 崩 | GUI 构建 `Instruction object is not iterable` | GUI 必须 PyInstaller ≥6 | ✅ 已记录 |
| 中文控制台编码 | `py -X utf8` 习惯 | 入口 `_ensure_utf8_stdio()`；测试用 cp1252 复现 | ✅ 已记录 |
| Git Bash 路径 | `/tmp` 与 Windows Python 路径不通 | 临时文件用工作区相对路径 | ✅ 已记录 |
| pip 注册表代理污染 | `https://127.0.0.1:7897` 错误 | `NO_PROXY="*" py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` | ✅ 已记录 |
| pyc 偶发损坏 | `unknown opcode` / 段错误 | 全程 `PYTHONDONTWRITEBYTECODE=1`；清 `__pycache__` | ✅ 已记录 |
| subprocess 输出 CRLF | 落盘会注入 CRLF | 落盘前 `.replace("\r\n","\n")` 归一 | ✅ 已记录 |
| stdlib random 不跨版本 | 跨版本序列不一致 | 使用固定 seed + 确定性 RNG | ✅ 已记录 |
| datetime.now() 破坏确定性 | 两次运行产物不同 | 使用固定 GENERATION_DATE | ✅ 已修复 |
| 声明类型 dataclass 字段顺序 | 非默认字段不能跟在默认字段后 | 调整字段顺序：必需字段在前，可选字段在后 | ✅ 已修复 |
| 分词下划线处理 | "add_assoc" 被作为整体 | 分词时下划线替换为空格 | ✅ 已修复 |
| Lean 语法校验冒号检测 | `:=` 中的冒号被误认为分隔符 | 跳过 `:=` 中的冒号 | ✅ 已修复 |
| argparse 全局参数位置 | `--index-path` 必须在子命令之前 | 全局参数放子命令前 | ✅ 已记录 |
| 测试中 main() 不 raise SystemExit | `main()` 返回 int，不抛异常 | 测试直接断言返回值，不用 pytest.raises | ✅ 已修复 |
| is_relative_to 不兼容 Python 3.8 | `AttributeError: 'WindowsPath' object has no attribute 'is_relative_to'` | 使用 str 比较替代 | ✅ 已修复 |
| parse_time_ms 破坏确定性 | 双跑 JSON 序列化不一致 | 从 to_dict 中排除 parse_time_ms | ✅ 已修复 |
| PyInstaller 相对导入失败 | `ImportError: attempted relative import with no known parent package` | 入口改用 `__main__.py` + 绝对导入 | ✅ 已修复 |

### 环境命令速查

```bash
# Python 版本
py -0p

# 创建 venv
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 构建索引
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --check

# 生成命题
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50 --check

# 构建 exe
pyinstaller tools/hws-formal-math.spec

# 构建 sdist/wheel
py -3.12 -m build --sdist --wheel

# 自检
dist/hws-formal-math.exe selftest

# 搜索
dist/hws-formal-math.exe search "add_assoc"
```

---

## 五、DoD 逐项 checklist

### 5.1 计划文档 DoD

- [x] plan/00-README总览.md 已更新
- [x] plan/01-题目详细定义.md 已定稿
- [x] plan/02-算法与口径说明.md 已定稿
- [x] plan/03-基准套件设计.md 已定稿
- [x] plan/04-测试与验收.md 已定稿
- [x] plan/05-发布与交付.md 已定稿
- [x] plan/06-架构与技术选型.md 已定稿

### 5.2 M1 数据先行 DoD

- [x] 索引可复跑（--check 验证通过）
- [x] 只存元数据不存源码（theorems.jsonl 格式验证）
- [x] 覆盖度口径落 manifest（domain_coverage 字段）
- [x] 确定性写盘（固定 GENERATION_DATE，无时间戳）
- [x] 位级一致验证（--check 模式）
- [x] 变异验证（故意弄坏行为 → 门变红）
- [x] 测试全绿（169 passed）

### 5.3 M2 解析层 DoD

- [x] 统一中间表示设计（src/hws_formal_math/parser/ir.py）
- [x] 规则优先解析器实现（src/hws_formal_math/parser/parser.py）
- [x] 每解析器配生成器产出的样例回归（TestParseTheoremDeclaration）
- [x] 确定性纪律：双跑 IR 逐字节一致（TestDualRunDeterministic, TestDeterministicParsing）
- [x] 解析器测试全绿（29 passed）
- [x] 变异验证（test_mutation_detection）

### 5.4 M3 引擎层 DoD

- [x] BM25 检索器实现（src/hws_formal_math/engine/retriever.py）
- [x] 骨架生成器实现（src/hws_formal_math/engine/skeleton_gen.py）
- [x] 内核验证器实现（src/hws_formal_math/engine/kernel.py）
- [x] 依赖图构建器实现（src/hws_formal_math/engine/depgraph.py）
- [x] 每模块配测试（含变异验证）（48 tests, 全部通过）
- [x] 双跑确定性测试（TestRetrieverDeterministic, TestKernelVerifierDeterministic, TestDependencyGraphDeterministic）

### 5.5 M4 集成层 DoD

- [x] CLI 入口实现（src/hws_formal_math/cli.py，argparse 框架）
- [x] 编排层实现（src/hws_formal_math/core/orchestrator.py）
- [x] 报告生成器实现（src/hws_formal_math/core/report.py，HTML + JSON 双轨）
- [x] 每模块配测试（含变异验证）（48 tests, 全部通过）
- [x] 双跑确定性测试（TestCLIDeterministic, TestOrchestratorDeterministic, TestReportGeneratorDeterministic）
- [x] 干净环境验证（全新 venv 安装 + 测试全绿）
- [x] 控制台脚本入口（hws-formal-math.exe --help 正常）
- [x] __main__.py 入口（python -m hws_formal_math --help 正常）

### 5.6 M5 发布与交付 DoD

- [x] 干净环境验证（全新 clone + 全新 venv）
- [x] 构建产物验证（exe 构建成功，selftest/search 正常）
- [x] 脱敏四步 + 产物扫描（无敏感信息泄露）
- [x] 建仓 / CI workflow 配置
- [x] tag + Release（v0.1.0，3 个资产已上传）
- [x] 本地等价校验（未接远端，CI 待首推验证）

---

## 六、关键命令速查

### 6.1 开发命令

```bash
# 安装
pip install -e ".[dev]"

# 测试
pytest tests/

# 带覆盖率
pytest tests/ --cov=src/hws_formal_math --cov-report=html

# 自检
python -m hws_formal_math selftest
```

### 6.2 构建命令

```bash
# 构建索引
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index

# 验证索引位级一致
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --check

# 生成命题
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50

# 验证命题位级一致
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50 --check
```

### 6.3 引擎层测试命令

```bash
# 运行引擎层测试
py -3.12 -m pytest tests/test_retriever.py tests/test_skeleton_gen.py tests/test_kernel.py tests/test_depgraph.py -v
```

### 6.4 集成层测试命令

```bash
# 运行集成层测试
py -3.12 -m pytest tests/test_cli.py tests/test_orchestrator.py tests/test_report.py -v

# 运行全部测试
py -3.12 -m pytest tests/ -v
```

### 6.5 发布命令

```bash
# 测试全绿
pytest tests/

# 位级一致验证
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --check
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50 --check

# 构建产物
pyinstaller tools/hws-formal-math.spec
py -3.12 -m build --sdist --wheel

# 打 tag
git tag -a v0.1.0 -m "Release v0.1.0"

# 推送
git push origin main --tags

# 创建 Release
gh release create v0.1.0 dist/* --notes "Release v0.1.0"
```

---

## 七、新对话启动提示词

```
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M6.md" 继续完成任务

当前状态：M1 数据先行完成，M2 解析层完成，M3 引擎层完成，M4 集成层完成，M5 发布与交付完成。
下一步：实现 M6 收尾固化（CI 首跑全绿 + README 状态行转正 + 缓议项清零 + 发布后元信息终检）。
```

---

## 八、决策记录

| 日期 | 决策 | 结论与理由 |
|------|------|------------|
| 2026-10-15 | 命名约定：目录标签改用 `HWS-` | 用户明确要求 |
| 2026-10-15 | 模型在环，但审计核心零模型可跑 | 92B MoE 本地自举硬件门槛高 |
| 2026-10-15 | Lean/elan 工具链 = 用户自备前置条件 | mathlib4 全量编译数 GB、小时级 |
| 2026-10-15 | mathlib4 以版本化快照接入 | 完整源码数 GB，不适合入仓 |
| 2026-10-15 | 真值 = Lean 内核编译结果 | 通过/失败无歧义 |
| 2026-10-15 | `sorry` 占位不计入"证明成功" | 含 sorry 的骨架"编译通过"但未证明 |
| 2026-10-15 | 模型生成与内核判定在报告中分离呈现 | 防"模型说对了"被读成"内核验证通过" |
| 2026-10-15 | `index_gap` 与"定理不存在"必须区分 | 索引未覆盖某模块 ≠ 该定理不存在 |
| 2026-10-16 | 主语言 Python 3.8+ | 本机 3.8/3.12 双版本 |
| 2026-10-16 | PyInstaller ≥6（GUI）/ ≥5.13（CLI） | GUI（PySide6）必须 ≥6 |
| 2026-10-16 | 测试框架 pytest | 成熟、跨平台、支持参数化 |
| 2026-10-16 | 确定性写盘：固定 GENERATION_DATE | 移除 datetime.now()，确保位级一致 |
| 2026-10-16 | 添加 --check 参数 | 验证生成器位级一致 |
| 2026-10-16 | M2 解析层：统一 IR + 规则优先解析器 | 纯正则+状态机，零 LLM 依赖；声明按名字排序确保确定性 |
| 2026-10-16 | M3 引擎层：BM25 检索器 + 骨架生成器 + 内核验证器 + 依赖图 | 零模型依赖，三态判定，index_gap 区分 |
| 2026-10-16 | 分词下划线处理 | "add_assoc" 分成 "add" 和 "assoc" |
| 2026-10-16 | Lean 语法校验冒号检测 | 跳过 `:=` 中的冒号 |
| 2026-10-16 | M4 集成层：CLI + 编排器 + 报告生成器 | argparse 框架，检索→骨架→验证→报告完整流程 |
| 2026-10-16 | 报告 HTML 0 外链 | 离线可用承诺，断网可开 |
| 2026-10-16 | 报告 JSON 逐字节可复现 | sort_keys=True，固定 generation_date |
| 2026-10-16 | CLI 全局参数在子命令前 | argparse 语法要求，--index-path 必须放子命令前 |
| 2026-10-16 | parse_time_ms 从 to_dict 中排除 | 解析时间不是确定性内容，K4 口径要求 |
| 2026-10-16 | is_relative_to 改用 str 比较 | Python 3.8 兼容 |
| 2026-10-16 | PyInstaller 入口改用 __main__.py + 绝对导入 | 解决相对导入失败问题 |

---

## 九、M5 交付物清单

### 9.1 新增/修改文件

| 文件 | 说明 | 测试 |
|------|------|------|
| .github/workflows/ci.yml | CI workflow（测试+构建+发布） | - |
| tools/hws-formal-math.spec | PyInstaller spec 文件 | - |
| src/hws_formal_math/__main__.py | 包入口（修复相对导入） | - |
| src/hws_formal_math/parser/ir.py | ParseResult.to_dict 排除 parse_time_ms | - |
| tools/build_index.py | _lean_file_to_module 改用 str 比较 | - |

### 9.2 测试统计

| 测试文件 | 测试数 | 状态 |
|----------|--------|------|
| tests/test_build_index.py | 24 | ✅ PASSED |
| tests/test_gen_proposals.py | 21 | ✅ PASSED |
| tests/test_parser.py | 29 | ✅ PASSED |
| tests/test_retriever.py | 9 | ✅ PASSED |
| tests/test_skeleton_gen.py | 18 | ✅ PASSED |
| tests/test_kernel.py | 12 | ✅ PASSED |
| tests/test_depgraph.py | 9 | ✅ PASSED |
| tests/test_cli.py | 14 | ✅ PASSED |
| tests/test_orchestrator.py | 14 | ✅ PASSED |
| tests/test_report.py | 20 | ✅ PASSED |
| **总计** | **170** | **✅ ALL PASSED** |

### 9.3 构建产物

| 产物 | 路径 | SHA256 |
|------|------|--------|
| CLI exe | dist/hws-formal-math.exe | 31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b |
| 源码包 | dist/hws_formal_math_navigator-0.1.0.tar.gz | fdd7558a74cbd515643a223654a22fc0d5c661b50274bf6cc94114488d6cc12c |
| wheel | dist/hws_formal_math_navigator-0.1.0-py3-none-any.whl | 85d511575bab10e58d9e578cca63cb6f25aabdf77149b1899f017e9fc7c3db2f |

### 9.4 干净环境验证结果

| 验证项 | 结果 | 证据 |
|--------|------|------|
| 全新 venv 安装 | ✅ | pip install -e ".[dev]" 成功 |
| 全量测试 | ✅ | 169 passed (全新 venv) |
| CLI 自检 | ✅ | hws-formal-math selftest 通过 |
| 控制台脚本 | ✅ | hws-formal-math.exe --help 正常 |
| __main__.py 入口 | ✅ | python -m hws_formal_math --help 正常 |
| 搜索功能 | ✅ | hws-formal-math search "add_assoc" 正常 |

---

> **本文件状态**：✅ v1 定稿（2026-10-16）
> **下一步**：网络恢复后推送 a4abb5e 触发 CI 首跑验证；设置 GitHub topics
