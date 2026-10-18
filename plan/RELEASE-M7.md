# RELEASE-M7（v0.1.1）发布留档

仓库 `HWS-formal-math-navigator`。发布日期 **2026-10-18**。
本文件在 **tag 之前**写好并进 tag 树；发布后才产生的事实列在 §五「tag 后追加事实」。

> **为什么有 v0.1.1**：出题技能回访（`ai-tool-topic-definer` 阶段 6）对 v0.1.0 做
> "承诺 vs 实物"评估，发现三类"题面写了、产物里没有"的缺陷。按 `check_release.py`
> 与 preflight ㉔㉕㉗ 逐条修复后出补丁版本。**v0.1.0 的 tag 与 Release 保留不动**。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.1.1` |
| 发布形态 | 源码仓库 + 三平台冻结产物 zip + sdist/wheel + `demo.gif` |
| 变更范围 | 查看器实现、索引溯源、文档与测试；**不改内核/检索/依赖图算法** |
| 测试 | 212 passed（Python 3.12；CI 四矩阵见 §五） |

---

## 二、修复清单（回访发现的缺陷 → 处置）

| # | 缺陷（v0.1.0 实况） | 级别 | 处置 |
|---|---|---|---|
| D1 | **查看器是死壳**：「检索定理」按钮无 `clicked.connect`；`viewer/ui/__init__.py` 只有 TODO | 出题级（㉕） | 重写 `viewer/controller.py`（零 Qt 业务层）+ `viewer/main.py`（窗口接线）；新增 `viewer/__main__.py` |
| D2 | **查看器不在发布物里**：spec 只产 CLI 单 exe，Release zip 内无 viewer | 出题级（㉕/㉖） | spec 改双产物（`hws-formal-math` + `hws-formal-math-viewer`）；CI 断言 zip 内含两者 |
| D3 | **索引溯源 `commit_hash: "unknown"`**，台账却称"含 commit hash ✅" | 出题级（㉗） | manifest 改 `index_kind=curated-sample` + `provenance_note`；`build_index_with_commit()` 拒绝 `unknown` |
| D4 | **索引规模未声明**：题面写 mathlib4"数万条定理"，随仓 35 条 | 出题级（㉗） | README 新增「索引：随包是样例，全量需自建」；manifest 显式 kind |
| D5 | **§三 承诺的技术报告 / 演示 GIF 不存在**（全仓 0 个图片、无 docs/） | 出题级（㉔） | 新增 `docs/技术报告.md`、`docs/demo/demo.gif`（查看器四步实拍）；GIF 进 Release 附件 |
| D6 | 缺「招牌动词表」 | 出题级（⑳） | `plan/00` §三之二 补 8 行表，每行都有命令 + 断言 |
| D7 | plan/04 无查看器验收口径 | 出题级（⑩/㉕） | plan/04 §二之二 补三层验收 + 形态四格表 |

---

## 三、验证（tag 时点）

```bash
# 全量测试
python -m pytest tests/ -q            # 212 passed

# 冻结产物原生冒烟（本机 Windows）
dist/hws-formal-math/hws-formal-math.exe selftest
dist/hws-formal-math/hws-formal-math-viewer.exe --selftest
# → 索引 35 条（curated-sample）/ 检索 5 条 / 依赖图 4 节点 8 边 / 导出 HTML 0 外链

# 打包 + 产物形态断言
python tools/package_release.py --dist dist --output release --tag v0.1.1
cp docs/demo/demo.gif release/
python tools/assert_release_shape.py --dist dist --release release
# → 冻结产物含双 exe / zip 内含 CLI + 查看器 / demo.gif 就位

# 门禁
python <skill>/scripts/check_topic.py .        # 0 FAIL
python <skill>/scripts/check_release.py .      # 0 FAIL（发布后）
```

**产物哈希（本机 Windows 构建，tag 时点）**：

| 文件 | 大小 | sha256 |
|---|---|---|
| `hws-formal-math-v0.1.1-win64.zip` | 62,680,134 字节 | 见 Release 附件回读（§五） |
| `demo.gif` | 42,636 字节 | 同上 |

> 冻结产物不承诺跨机字节一致（PyInstaller 特性）；可复跑的是**打包这一步**
> （`ZIP_STORED` + 条目排序 + 固定时间戳，双打逐字节一致）。

---

## 四、已知边界（未变）

- 随包索引是 35 条**样例**，检索召回仅代表样例域；
- 签名是便于演示的简化写法（`provenance_note` 已声明），非 mathlib4 逐字抽取；
- 内核验证需用户自备 Lean；未装时 `bench --suite skeleton` 报 `not_enabled` 且 exit 1；
- 查看器需 PySide6（`[gui]` extra）；缺依赖时 `--selftest` 仍可跑，窗口模式 exit 3。

---

## 五、tag 后追加事实

> 本节内容产生于 tag 之后，与 §一「tag 时点事实」分开记录（口径见 preflight ㉒）。

**tag 提交**：`93a5d91`（CI 绿）。tag 推送后 CI run `39120496486` **success**。

**Release 附件**（`gh release view v0.1.1 --json assets` 回读）：

| 附件 | 大小 |
|---|---|
| `hws-formal-math-v0.1.1-linux-x86_64.zip` | 54,058,762 B |
| `hws-formal-math-v0.1.1-macos-arm64.zip` | 38,109,444 B |
| `hws-formal-math-v0.1.1-win64.zip` | 21,794,184 B |
| `hws_formal_math_navigator-0.1.1-py3-none-any.whl` | 49,239 B |
| `hws_formal_math_navigator-0.1.1.tar.gz` | 69,411 B |
| `SHA256SUMS.txt` | 530 B |
| `demo.gif` | 42,636 B |

**真下载复核**（中立目录、`env -u PYTHONPATH -u PYTHONHOME`）：

| 命令 | 结果 |
|---|---|
| `hws-formal-math.exe selftest` | exit 0，冻结态数据目录随包 |
| `hws-formal-math-viewer.exe --selftest` | exit 0，索引 35 条 / 检索 / 4 节点 8 边 / 导出 HTML 0 外链 |

**zip 形态**：68 个条目，含 `hws-formal-math.exe` 与 `hws-formal-math-viewer.exe`（双 exe 同包）。
原 v0.1.0 的 Windows 包经 Qt 组件裁剪后由 112MB 降到 21.8MB。
