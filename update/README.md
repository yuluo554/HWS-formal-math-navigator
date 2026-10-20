# 交接索引：HWS-formal-math-navigator 二次迭代

> 诊断日 **2026-10-21**。诊断方只读，未改任何受控文件；唯一写入是本目录。
> 事实基线与缺陷编号以 `00-诊断报告.md` 为准。

## 一句话结论

**要迭代，而且必须迭代**：这个仓的**免安装 zip 是真实可用的**（我下载远端附件实跑了 `selftest`/`search`/`bench`/查看器自检四条，全 exit 0），但**三条独立的一级缺陷**把"可用性"和"真实性"各挖了一个洞——
① **pip 渠道装完即不可用**（wheel 与 sdist 里**一个 `data/` 文件都没有**，`selftest` 报"索引目录不存在" exit 1）；
② **内核验证的调用方式在上游 Lean 4 里根本不存在**（`lean --check` 不是合法选项，上游源码 `shell.cpp` 的选项表里没有；真装 Lean 后正确证明也会被判 FAIL，`PASS_NO_SORRY` 永远达不到）——而这条路径**没有任何测试覆盖**，CI 里也永远因为"无 Lean"而 `not_enabled`，所以它是"看起来有、实际没验过"的状态；
③ **发布形态门禁是假门**（`assert_release_shape.py` 用子串判 zip 是否含 CLI，而 CLI 名是查看器名的前缀 → 负控实测：一个**只含查看器、完全没有 CLI** 的 zip 被判 "✅ 含 CLI + 查看器"，exit 0）。

建议版本 **v0.1.2**（补丁迭代），范围限定为"补三洞 + 数据自证 + CI 换新 runner 拿绿证据"，不扩容、不实现模型端点、不上 PyPI。

## 文件索引

| 文件 | 内容 |
|---|---|
| `00-诊断报告.md` | 现状表（每条附命令）、**做得好的部分 8 条**、缺陷 D1–D15 + 16 条失效模式逐条交代（含 N/A 理由） |
| `01-迭代路线.md` | 总目标 G1–G6、批次 0–4、每批可粘贴门禁、范围边界、**这仓特有的 10 条坑** |
| `02-提示词-迭代对话.md` | **可直接复制到新对话执行的完整提示词** |
| `README.md` | 本文件 |

## 需要用户拍板的决策（执行方拿到答案再开工）

| 编号 | 决策点 | 方案 | 收益 / 代价 | 建议 |
|---|---|---|---|---|
| **DEC1** | **Python floor** | A. 保持 `>=3.8`（现状）；B. 抬到 `>=3.12`；C. 抬到 `>=3.10` | A：零改动成本，但 3.8 已 EOL（2024-10）、CI 最近一次绿（2026‑10‑18）早于 `ubuntu-latest → Ubuntu 26`（2026‑10‑19 起），且为兼容 3.8 写了 `STDLIB_ALLOWLIST`/字符串前缀比较等绕行；`gui` extra 在 3.8 上最多装 PySide6 6.6.3.1。B：与另外两个 HWS 仓（若也抬）口径统一、能转 PEP 639 SPDX license、能删绕行代码；代价是源码安装的最低门槛变高（但免安装 zip 不受影响，本机与 CI 都已是 3.12）。C：折中，能装到 PySide6 6.11+，但 `setuptools>=77` 的 `>=3.10` 已经踩线，收益不明显。 | **B**。理由：本组三个仓都是"Windows 本机 + GitHub CI"两处跑，抬到 3.12 是唯一能让"CI 绿证据"与"本机实测"同一口径的选择，且能顺带解决 D12（actions 升级 + SPDX）。**但这是用户的技术选型，必须问。** |
| **DEC2** | **随包数据放在哪** | A. 数据留在仓根 `data/`，用 `MANIFEST.in` + `[tool.setuptools.package-data]` 把 `data/**` 塞进 wheel/sdist，`default_data_dir()` 增加"装态回落"；B. 把数据 `git mv` 进 `src/hws_formal_math/data/`，用 `importlib.resources`；C. 不把数据放进 wheel，改为**在 README 正面声明"pip 安装后需 `--index-path` 或 `cd` 仓根"**并把 `selftest` 的报错文案改成指引 | A：改动小（不用动 spec 的相对路径、不用改冻结态断言），但 `data/` 在仓根的"双重身份"（既是仓内资源又是包数据）要继续维护；B：最"干净"，但 `tools/*.spec` 的 `DATAS`、`default_data_dir()` 的冻结态分支、`tests` 里的路径都要跟着改，风险最高；C：改动最小、最诚实，但**等于承认 pip 装完不可用**。 | **A**。理由：冻结态（zip）是唯一被实测证明可用的渠道，任何改动都不能让它退化；A 对它零影响。B 的风险（spec + 冻结态 + 21.8 MB 附件重打）在这个批次里不成比例。C 会把"pip 装完能用"从目标里删掉，与 G1 冲突——**只有用户认为"pip 渠道不重要"时才选 C**。 |
| **DEC3** | **内核验证怎么调 Lean**（本批最关键） | A. 用 `lean <file>` 并检查退出码（上游 `shell.cpp` 的 `g_opt_str` 支持裸文件参数）；B. 用 `lean --json <file>` 解析结构化消息；C. **不装/不调 Lean**，把 `skeleton` 套件与 `PASS_NO_SORRY` 从"能力"降级为"需用户自备 Lean 才启用"，并在 README 正面写"本批未在真 Lean 上验证过" | A：最小改动、语义最接近原意（rc=0 即编译通过）；但上游的 `sorry` 在 Lean 4 里是否影响退出码**必须实测**（不要靠推断）——若 `sorry` 也返回 0，`PASS_WITH_SORRY` 只能靠现有的正则 `_detect_sorry` 判定（D10 的假阳性要先修）。B：能得到"哪些是 warning vs error"，但解析成本高、跨版本易变。C：最诚实，但把卖点砍掉一半。 | **A + 实测**：先用 `lean <file>`，把"正确/错误/含 sorry 三种输入的 rc 与 stdout"实测记录下来（这就是 G2 的验收证据）；若发现 `sorry` 不影响 rc，就用正则判 `PASS_WITH_SORRY` 并修 D10。**在拿到实测结果前不许写"已修复"。** |
| **DEC4** | **`update/` 与本地 `release/` 怎么处置** | A. 两者都加进 `.gitignore`；B. `update/` 入仓（作为交接物）、`release/` 忽略；C. `update/` 忽略、`release/` 入仓 | A：最省事，但交接物不入仓、下一轮审计看不到；B：与另一个仓（agent-rework-lens 的 `update/` 只踩 C01）的经验一致，交接物可追溯；代价是 `update/` 内含本机绝对路径（`<本地仓根>`、`<TEMP 目录>`），若仓是公开的需先脱敏。C：无收益。 | **待定，须用户回答**。若选 B，请先决定是否接受 `update/` 里的本机路径（本仓是**公开仓**）。另外**无论选哪个**：本地 `release/`（62,680,134 B，sha `62c391ef…`）与远端附件（21,794,184 B，sha `3d5ce4e9…`）**不是同一字节**，留着会让任何人拿它对账得出假缺陷——建议直接删本地 `release/`。 |
| **DEC5** | **测试数写进哪里 + `jinja2` 去留** | A. 把实测数（212）写进 `README.md` 的"验证与质量"、删掉 `RELEASE-NOTES.md` 的 185；B. 只改 `RELEASE-NOTES.md`；C. 两者都不写数字 | `RELEASE-NOTES.md:58` 的「185 tests passed」已经进了 Release 正文，是**已发布的不一致**（同一文件开头写 212）。`jinja2>=3.0` 是核心依赖但全仓 **0 处 import**（`grep -rn jinja src tools tests` 空）。 | **A**，且顺手在 `pyproject.toml` 里**按用户决定**去掉或保留 `jinja2`：若去掉，属于"删未使用依赖"（合法）；若保留，需在 plan 里写明未来用途。**不要为了省事把它从 README 抹掉而不动 pyproject**。 |

## 本次迭代的边界（摘要，详见 `01-迭代路线.md` §三）

- 不实现模型端点、不扩容索引、不上 PyPI、不动 `v0.1.0`/`v0.1.1` tag 与 Release。
- 不改 `tests/test_bench_probe.py` 的双向探活结构，不降低任何阈值常量。
- 唯一允许改内容的受控数据文件是 `data/proposals/v1/manifest.json`（补 `sha256` 字段）。
- 完成后写回执行记录并标 **「待复验」**，不自宣完成。