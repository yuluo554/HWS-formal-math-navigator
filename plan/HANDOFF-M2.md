# plan/HANDOFF-M2.md

> **跨会话交接快照（M2 续接用）**
>
> **已过时仅作历史** — 当前状态请参考 plan/00-README总览.md 最新版

---

## 一、当前进度 + 证据

### 1.1 已完成

| 项目 | 状态 | 证据位置 |
|------|------|----------|
| plan/00-README总览.md | ✅ v1 定稿 | plan/00-README总览.md |
| plan/01-题目详细定义.md | ✅ v1 定稿 | plan/01-题目详细定义.md |
| plan/02-算法与口径说明.md | ✅ v1 定稿 | plan/02-算法与口径说明.md |
| plan/03-基准套件设计.md | ✅ v1 定稿 | plan/03-基准套件设计.md |
| plan/04-测试与验收.md | ✅ v1 定稿 | plan/04-测试与验收.md |
| plan/05-发布与交付.md | ✅ v1 定稿 | plan/05-发布与交付.md |
| plan/06-架构与技术选型.md | ✅ v1 定稿 | plan/06-架构与技术选型.md |
| 索引构建器 | ✅ 完成 | tools/build_index.py |
| 命题生成器 | ✅ 完成 | tools/gen_proposals.py |
| 索引文件 | ✅ 生成 | data/index/theorems.jsonl (35 定理) |
| 命题集 | ✅ 生成 | data/proposals/v1/proposals.json (50 命题) |
| 索引构建器测试 | ✅ 完成 | tests/test_build_index.py (24 tests) |
| 命题生成器测试 | ✅ 完成 | tests/test_gen_proposals.py (21 tests) |
| 确定性写盘修复 | ✅ 完成 | 移除 datetime.now()，使用固定日期 |
| --check 参数 | ✅ 完成 | 验证位级一致 |
| 变异验证测试 | ✅ 完成 | 故意弄坏行为 → 门变红 |

### 1.2 M1 DoD 验证结果

| DoD 项 | 状态 | 验证方式 |
|--------|------|----------|
| 索引可复跑 | ✅ | `tools/build_index.py --check` 通过 |
| 只存元数据不存源码 | ✅ | theorems.jsonl 只含 name/signature/deps |
| 覆盖度口径落 manifest | ✅ | manifest.json 含 domain_coverage |
| 测试全绿 | ✅ | 45 passed |
| 确定性写盘 | ✅ | 固定 GENERATION_DATE，无时间戳 |
| 位级一致验证 | ✅ | --check 模式验证通过 |

---

## 二、下一里程碑待办（M2 解析层）

### 2.1 M2 目标

统一中间表示 + 规则优先解析器（LLM 只兜底）

### 2.2 M2 DoD 要点

- [ ] 设计统一中间表示（参数卡）
- [ ] 实现规则优先解析器
- [ ] 每解析器配生成器产出的样例回归
- [ ] 确定性纪律：双跑 IR 逐字节一致

### 2.3 M2 待办清单

| # | 任务 | 优先级 | 预估时间 |
|---|------|--------|----------|
| 1 | 设计统一中间表示 IR | 高 | 2h |
| 2 | 实现定理解析器 | 高 | 2h |
| 3 | 实现依赖解析器 | 高 | 1h |
| 4 | 实现签名解析器 | 高 | 1h |
| 5 | 编写解析器测试 | 中 | 2h |
| 6 | 添加双跑确定性测试 | 中 | 1h |

---

## 三、既定口径清单（K 编号）

> **动了会打挂测试的约定，改动前必读**

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

### 口径变更流程

```
1. 提出变更 → 2. 评估影响面 → 3. 更新代码 → 4. 更新测试 → 5. 更新文档 → 6. 登记决策记录
```

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
| datetime.now() 破坏确定性 | 两次运行产物不同 | 使用固定 GENERATION_DATE | ✅ 已记录 |

### 环境命令速查

```bash
# Python 版本
py -0p

# 创建 venv
py -3.12 -m venv .venv
\.\.venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 带覆盖率
pytest tests/ --cov=src/hws_formal_math --cov-report=html

# 构建索引
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --commit-hash <commit>

# 验证索引位级一致
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --check

# 生成命题
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50

# 验证命题位级一致
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50 --check
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
- [x] 测试全绿（45 passed）

### 5.3 待验证（M2）

- [ ] 统一中间表示设计
- [ ] 规则优先解析器实现
- [ ] 双跑确定性测试

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

### 6.3 发布命令

```bash
# 测试全绿
pytest tests/

# 位级一致验证
py -3.12 tools/build_index.py --mathlib4-path data/raw --output data/index --check
py -3.12 tools/gen_proposals.py --output data/proposals/v1 --num-cases 50 --check

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
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M2.md" 继续完成任务

当前状态：M1 数据先行完成，M2 解析层待启动。
下一步：设计统一中间表示 + 实现规则优先解析器。
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

---

> **本文件状态**：✅ v1 定稿（2026-10-16）
> **下一步**：启动 M2 对话，设计统一中间表示 + 实现规则优先解析器
