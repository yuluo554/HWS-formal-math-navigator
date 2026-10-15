# plan/HANDOFF-M1.md

> **跨会话交接快照（M1 续接用）**
> 
> **已过时仅作历史** — 当前状态请参考 plan/00-README总览.md 最新版

---

## 一、当前进度 + 证据

### 1.1 已完成

| 项目 | 状态 | 证据位置 |
|------|------|----------|
| plan/00-README总览.md | ✅ v1 定稿 | plan/00-README总览.md |
| plan/01-题目详细定义.md | ✅ v1 定稿 | plan/01-题目详细定义.md |
| plan/02-算法与口径说明.md | ✅ v1 定稿（2026-10-16） | plan/02-算法与口径说明.md |
| plan/03-基准套件设计.md | ✅ v1 定稿（2026-10-16） | plan/03-基准套件设计.md |
| plan/04-测试与验收.md | ✅ v1 定稿（2026-10-16） | plan/04-测试与验收.md |
| plan/05-发布与交付.md | ✅ v1 定稿（2026-10-16） | plan/05-发布与交付.md |
| plan/06-架构与技术选型.md | ✅ v1 定稿（2026-10-16） | plan/06-架构与技术选型.md |
| 项目骨架 | ✅ 已创建 | src/hws_formal_math/ |
| pyproject.toml | ✅ 已创建 | pyproject.toml |
| README.md | ✅ 已创建 | README.md |
| 基础模块 | ✅ 已创建 | src/hws_formal_math/{cli.py,config.py,logging.py,exceptions.py} |
| 引擎骨架 | ✅ 已创建 | src/hws_formal_math/engine/{retriever.py,skeleton_gen.py,kernel.py,depgraph.py} |
| 编排层骨架 | ✅ 已创建 | src/hws_formal_math/core/{orchestrator.py,model_gateway.py} |
| 测试骨架 | ✅ 已创建 | tests/test_*.py |
| 数据文件 | ✅ 已创建 | data/index/manifest.json, data/snapshots/manifest.json, data/proposals/manifest.json |
| 测试用例 | ✅ 已创建 | tests/fixtures/{retrieval_cases.json,skeleton_cases.json,depgraph_cases.json} |

### 1.2 未完成

| 项目 | 状态 | 原因 |
|------|------|------|
| 索引构建器实现 | ⬜ 待实现 | 需要 mathlib4 源码 |
| BM25 检索算法 | ⬜ 待实现 | 需要索引数据 |
| 骨架生成逻辑 | ⬜ 待实现 | 需要模型端点 |
| 内核验证逻辑 | ⬜ 待实现 | 需要 Lean 工具链 |
| 依赖图算法 | ⬜ 待实现 | 需要索引数据 |
| 桌面查看器 | ⬜ 待实现 | 需要 PySide6 |
| 基准测试 | ⬜ 待实现 | 需要核心功能 |
| CI 配置 | ⬜ 待实现 | 需要 GitHub Actions |

---

## 二、下一里程碑待办（M1 数据先行）

### 2.1 M1 目标

mathlib4 索引抽取器、版本化快照（commit hash + sha256）、合成命题生成器

### 2.2 M1 DoD 要点

- [ ] 索引可复跑
- [ ] 只存元数据不存源码
- [ ] 覆盖度口径落 manifest

### 2.3 M1 待办清单

| # | 任务 | 优先级 | 预估时间 |
|---|------|--------|----------|
| 1 | 实现 `tools/build_index.py` 索引构建器 | 高 | 2h |
| 2 | 从 mathlib4 抽取索引元数据 | 高 | 1h |
| 3 | 生成 `data/index/theorems.jsonl` | 高 | 1h |
| 4 | 实现 `tools/gen_proposals.py` 合成命题生成器 | 中 | 1h |
| 5 | 生成 `data/proposals/v1/` 命题集 | 中 | 30m |
| 6 | 更新 `data/index/manifest.json` 覆盖度 | 中 | 15m |
| 7 | 编写索引构建器测试 | 中 | 1h |
| 8 | 编写命题生成器测试 | 中 | 30m |

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

# 带覆盖率
pytest tests/ --cov=src/hws_formal_math
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

### 5.2 骨架 DoD

- [x] 目录结构已创建
- [x] pyproject.toml 已创建
- [x] README.md 已创建
- [x] .gitignore 已创建
- [x] .gitattributes 已创建
- [x] 基础模块已创建（cli, config, logging, exceptions）
- [x] 引擎骨架已创建（retriever, skeleton_gen, kernel, depgraph）
- [x] 编排层骨架已创建（orchestrator, model_gateway）
- [x] 测试骨架已创建
- [x] 数据文件已创建

### 5.3 待验证（M1）

- [ ] 索引构建器可复跑
- [ ] 只存元数据不存源码
- [ ] 覆盖度口径落 manifest
- [ ] 测试全绿
- [ ] 基准达标

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

# 基准
python -m hws_formal_math bench
```

### 6.2 构建命令

```bash
# 构建索引
python tools/build_index.py --mathlib4-path /path/to/mathlib4 --output data/index

# 生成命题
python tools/gen_proposals.py --output data/proposals/v1 --num-cases 50

# 打包
python tools/package.py
```

### 6.3 发布命令

```bash
# 测试全绿
pytest tests/

# 基准达标
python -m hws_formal_math bench

# 构建产物
python tools/package.py

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
/goal 读取 "<项目绝对路径>\plan\HANDOFF-M1.md" 继续完成任务

当前状态：M0 计划先行完成，M1 数据先行待启动。
下一步：实现索引构建器、合成命题生成器。
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

---

> **本文件状态**：✅ v1 定稿（2026-10-16）
> **下一步**：启动 M1 对话，实现索引构建器与合成命题生成器
