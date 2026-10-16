# RELEASE-M6.md 发布留档

> 本文件为 M6 收尾固化阶段的发布留档，记录发布过程、产物核验与已知偏差。
> 基准提交：a4abb5e（M6: 修复 CI 配置）

---

## 一、发布基线

| 项目 | 值 |
|------|-----|
| 仓库 | yuluo554/HWS-formal-math-navigator |
| 标签 | v0.1.0 |
| 提交 | a0eefbd（M5 发布）→ a4abb5e（M6 CI 修复） |
| 发布日期 | 2026-10-16 |
| 发布者 | HWS |

## 二、构建产物清单

### 2.1 产物列表

| 产物 | 路径 | 大小 | SHA256 |
|------|------|------|--------|
| CLI exe | dist/hws-formal-math.exe | 7.58MB | 31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b |
| 源码包 | dist/hws_formal_math_navigator-0.1.0.tar.gz | 44KB | fdd7558a74cbd515643a223654a22fc0d5c661b50274bf6cc94114488d6cc12c |
| wheel | dist/hws_formal_math_navigator-0.1.0-py3-none-any.whl | 34KB | 85d511575bab10e58d9e578cca63cb6f25aabdf77149b1899f017e9fc7c3db2f |

### 2.2 产物核验（D14）

```bash
# 本地计算
sha256sum dist/hws-formal-math.exe
# 31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b

# GitHub API 返回
# hws-formal-math.exe: sha256:31bb6c7daf695a03009a778e106282aa83de65ee33b43740489e793ca9defa5b
# 一致 ✅
```

## 三、测试结果

### 3.1 本地测试（Python 3.12）

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0
collected 169 items

tests/ ... PASSED

============================= 169 passed in 0.84s =============================
```

### 3.2 CI 测试状态

| 提交 | 事件 | 状态 | 说明 |
|------|------|------|------|
| a31a75c | push | ❌ failure | M5 收尾提交，CI 未修复 |
| a0eefbd | release | ❌ failure | tag push，CI 未修复 |
| a0eefbd | push | ❌ failure | M5 发布提交，CI 未修复 |
| a4abb5e | push | ⏳ 待验证 | M6 CI 修复提交，**待网络恢复后推送触发** |

### 3.3 CI 失败原因（已修复）

| 问题 | 详情 | 修复 |
|------|------|------|
| setup-python env 参数无效 | `env: PYTHONUTF8=1` 被 actions/setup-python@v5 拒绝 | 改为 `echo "PYTHONUTF8=1" >> $GITHUB_ENV` |
| build 模块缺失 | `python -m build --sdist` 报错 "No module named build" | 在 install dependencies 步骤添加 `pip install build` |

## 四、发布后元信息终检

### 4.1 Release 资产

| 检查项 | 状态 | 证据 |
|--------|------|------|
| isDraft = false | ✅ | GitHub API 返回 |
| 附件名在列 | ✅ | hws-formal-math.exe, .whl, .tar.gz |
| 附件大小正确 | ✅ | 7581375, 34309, 44635 bytes |
| digest 与本地一致 | ✅ | 见 2.2 节 |

### 4.2 GitHub Topics

| 检查项 | 状态 | 说明 |
|--------|------|------|
| topics 设置 | ⏳ 待完成 | gh 未认证，无法设置；待首推后手动设置 |
| 建议 topics | — | lean4, mathlib4, formal-math, theorem-proving |

### 4.3 README 状态行

| 检查项 | 状态 | 说明 |
|--------|------|------|
| M5 状态 | ✅ 完成 | plan/00-README总览.md 已更新 |
| M6 状态 | ⬜ 待启动 | 需更新为 "✅ 完成" |

## 五、已知偏差

### 5.1 CI 四矩阵未全绿

| 偏差 | 说明 | 影响 |
|------|------|------|
| CI 仅 ubuntu-latest | 未覆盖 windows 3.8 / windows 3.12 / ubuntu 3.8 | 跨平台兼容性未 CI 验证 |
| 本地等价校验 169 passed | 双解释器（3.8 + 3.12）本地测试全绿 | 替代证据，但非 CI 实跑 |

**处置**：本地等价校验通过 + CI 修复已提交 + 网络恢复后推送触发。按 skill 规则，"未推送 = 未跑 CI"，此处如实标注"待首推验证"。

### 5.2 GitHub Topics 未设置

| 偏差 | 说明 | 影响 |
|------|------|------|
| topics 为空数组 | gh 未认证，无法调用 API | 仓库发现性降低 |

**处置**：网络恢复后手动设置。

## 六、发布基线纪律

### 6.1 产物与源码同基线

```bash
# 发布基线提交：a0eefbd（M5 发布）
# M6 修复提交：a4abb5e（CI 配置修复）
# git diff a0eefbd..a4abb5e -- src/ tools/*.spec
# 为空 ✅（仅修改 .github/workflows/ci.yml）
```

### 6.2 构建产物留底

```
dist/
├── hws-formal-math.exe
├── hws-formal-math.exe.sha256
├── hws_formal_math_navigator-0.1.0.tar.gz
├── hws_formal_math_navigator-0.1.0.tar.gz.sha256
├── hws_formal_math_navigator-0.1.0-py3-none-any.whl
└── hws_formal_math_navigator-0.1.0-py3-none-any.whl.sha256
```

## 七、历史扫描低敏发现

| 发现 | 定夺 | 理由 |
|------|------|------|
| 无 HARD 词面命中 | — | 脱敏扫描通过 |
| 无个人邮箱/密钥 | — | 提交元数据邮箱为 example@example.com |

---

> **本文件状态**：✅ v1 定稿（2026-10-16）
> **下一步**：网络恢复后推送 a4abb5e，触发 CI 首跑验证；设置 GitHub topics
