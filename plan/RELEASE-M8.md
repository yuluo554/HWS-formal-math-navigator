# RELEASE-M8（v0.1.2）发布留档

仓库 `HWS-formal-math-navigator`。发布日期 **2026-10-21**。
本文件在 **tag 之前**写好并进 tag 树；发布后才产生的事实列入 §五「tag 后追加事实」。

> **为什么有 v0.1.2**：二次迭代诊断（`update/00-诊断报告.md`，2026-10-21）发现
> 三条一级缺陷把"可用性"和"真实性"各挖了一个洞——① pip 渠道装完即不可用；
> ② 内核验证调用了 Lean 4 里根本不存在的 `--check` 选项；③ 发布形态门禁用子串判定，
> 放行了只含查看器的 zip。本版为补丁迭代：**只补洞 + 数据自证 + CI 换新口径拿绿证据**，
> 不扩容索引、不实现模型端点、不上 PyPI。**v0.1.0 / v0.1.1 的 tag 与 Release 保留不动。**

---

## 决策记录（DEC1–DEC5，用户 2026-10-21 拍板）

| 编号 | 决策点 | 选项 | **决定** | 落地 |
|---|---|---|---|---|
| **DEC1** | Python floor | A 保持 3.8 / B 抬 3.12 / C 抬 3.10 | **B（>=3.12）** | `pyproject.toml` / classifiers / CI 矩阵 / README / RELEASE-NOTES 五处同步；`setuptools>=68`→`>=77`，license 转 PEP 639 SPDX；删 3.8 绕行（`STDLIB_ALLOWLIST`、`str.startswith` 前缀比较）；GUI extra 下限 `PySide6>=6.0`→`>=6.6` |
| **DEC2** | 随包数据位置 | A `data/` + MANIFEST.in / B 移进 `src/.../data/` / C 承认 pip 不可用 | **A** | 用 `[tool.setuptools.data-files]` 装到 `<prefix>/share/hws-formal-math/`；`config.default_data_dir()` 在装态回落查找；冻结态（zip）零影响 |
| **DEC3** | 内核验证怎么调 Lean | A `lean <file>` 看 rc / B `lean --json` / C 降级为"需自备" | **A + 实测** | `KernelVerifier.build_command()` 产 `[lean, <file>]`；实测记录见 §三 |
| **DEC4** | `update/` 与本地 `release/` | A 都忽略 / B `update/` 入仓 + `release/` 忽略 / C 反向 | **B（先脱敏）+ 删除本地 `release/`** | `update/` 3 处本机绝对路径替换为占位；`release/` 已删除（其 62,680,134 B 版本与远端 21,794,184 B 不是同一字节，留着会让复核得出假缺陷） |
| **DEC5** | 测试数写哪 + jinja2 | A README + 删 185 + 删 jinja2 / B 只改 RELEASE-NOTES / C 都不写 | **A** | README 新增「验证与质量」写实测数；`RELEASE-NOTES.md` 的 185 删除；`jinja2>=3.0` 从核心依赖移除（全仓 0 处 import） |

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.1.2` |
| 起点 HEAD | `5df59b6b96a72518cfc76dc30cc94348e352e6fc`（2026-10-18） |
| 起点 tag | `v0.1.1` = `93a5d913c62c6e17215aa27b2391ee249fc714b1`（annotated）；`v0.1.1..HEAD` = 1 个提交（只改 `plan/RELEASE-M7.md`） |
| 发布形态 | 源码仓库 + 三平台冻结产物 zip + sdist/wheel + `demo.gif` |
| 变更范围 | pip 可用性、内核调用形态、发布形态门禁、数据自证、floor/CI、文档一致性；**不改检索 / 依赖图 / 报告算法** |
| 测试 | **266 passed**（Python 3.12.10，本机；自指数由守门对撞，见 §三） |
| Python floor | `>=3.12` |

### 1.1 数据字节

| 文件 | 大小 | sha256 | 与 manifest |
|---|---|---|---|
| `data/index/theorems.jsonl` | 5,613 B | `74b58d138f3e466917ed9f2056ec16177534fa59231273d523fccf7f8b3d3855f` | = `index/manifest.json` ✅ |
| `data/snapshots/v1/snapshots.json` | 2,150 B | `fcf7aaf7a075f09d2a578b5ddb69ada4b5a9ad83c9bb9cd36afcda5e30d6012b` | = 两个 snapshot manifest ✅ |
| `data/proposals/v1/proposals.json` | 11,270 B（LF） | `8029bdf202353ce03bb5c85694b3b8a80212cbb37a59baf76c562c727754ce33` | **本批新增登记** ✅ |

> `theorems.jsonl` 与 `snapshots.json` 的**内容未改**（与 v0.1.1 逐字节相同）。
> `proposals.json` 由 11,776 B（CRLF）归一为 11,270 B（LF）——这是 D4 的**已发生漂移**
> 的修复，不是内容改动：`git` 里的 blob 一直是 LF 的 11,270 B，只有工作树被 autocrlf 改写成 CRLF。

---

## 二、修复清单（D1–D15 → 处置）

| # | 缺陷 | 级别 | 处置（本批实做） |
|---|---|---|---|
| **D1** | pip 渠道装完不可用：wheel/sdist 里零 `data/` | P1 | `[tool.setuptools.data-files]` 收 12 条数据 + 3 条 fixtures；`default_data_dir()` 装态回落 `<prefix>/share/hws-formal-math/data`；`default_fixtures_dir()` 同款回落；`MANIFEST.in` 让 sdist 自带 `data/` `tests/` `tools/` |
| **D2** | `lean --check` 不是合法选项，正确证明也判 FAIL | P1 | 改 `lean <file>`（`build_command()` 单一构造点）；新增 12 项**真子进程**测试（可注入假 lean 夹具）；`errors`/`command` 进 `VerificationResult` 便于复核 |
| **D3** | 形态门禁子串判定（CLI 是 VIEWER 前缀）→ 只含查看器的 zip 判通过 | P1 | 改 `PurePosixPath(n).name` 精确比较（`== stem` 或 `== stem+'.exe'`）；新增 `tests/test_release_shape.py` 9 项（正控 + 4 条负控 + 4 项匹配器直判） |
| **D4** | 冻结属性漏二级目录，3 个文件已 CRLF 漂移且无人发现 | P1 | `.gitattributes` 改 `data/**`；`tools/check_data_integrity.py` 新门（`--strict`）；`selftest` 运行时校验；`gen_proposals` 给 proposals manifest 补 `sha256`；正反两向负控已验 |
| **D5** | `gen_snapshots --check` 先写盘再比对，抹掉篡改痕迹 | P2 | 拆出纯函数 `_build_snapshot_bytes()`；`--check` 只算不写。**同类缺陷 `gen_proposals --check` 一并修**（原实现也是先写后比） |
| **D6** | 模型端点三支全是 `NotImplementedError` 且未披露 | P2 | **只补披露不实现**：README「已知环境问题」加行、前置条件表加 ⚠️、RELEASE-NOTES 同步、`plan/DEFERRED-ITEMS.md` D6 更新 |
| **D7a** | README 写退出码 4，实现里 `CONFIG_ERROR` 无任何 return | P2 | `main()` 捕获 `ModelConfigError` → `ExitCode.CONFIG_ERROR`(4)；实测「模型启用无端点」→ exit 4 |
| **D7b** | README 写 `hws-formal-math-viewer`，`[project.scripts]` 无此项 | P2 | 注册 console script；干净 venv 实测该 exe 可跑 `--selftest` |
| **D7c** | `--version` 未实装（exit 2） | P2 | argparse `action="version"`；实测 `hws-formal-math 0.1.2` exit 0 |
| **D8** | 领域覆盖度算得出但既不判定也不打印 | P2 | **打印**（`[coverage]` 段）但**不接进 `all_passed`**；口径与理由写在函数 docstring 与 README |
| **D9** | `export` 忽略 `-o` 文件名、命题写死 | P2 | `-o` 决定输出文件名（临时目录生成后 `shutil.move`）；新增 `--proposition`（不给时**明示**"使用内置示例命题"） |
| **D10** | `sorry` 检测对块注释/行尾注释假阳性 | P2 | `_strip_comments()` 逐行状态机（支持块注释嵌套 + 行尾 `--`）；4 项新测覆盖（含"真 sorry 仍被抓"阴性对照） |
| **D11** | 版本双源（pyproject 0.1.1 / `__init__` 0.1.0） | P2 | `__version__` 改为"仓内 pyproject → 安装元数据 → 兜底常量"；`tests/test_repo_gate.py` 加对撞断言 |
| **D12** | floor 3.8 EOL + CI 绿证据早于 runner 迁移 | P2 | DEC1=B：floor 抬 3.12；CI 矩阵 `{ubuntu,windows} × {3.12, 3.13}`；actions 升 v7 家族；`setuptools>=77` + SPDX license |
| **D13** | `RELEASE-NOTES.md:58` 写 185、开头写 212 | P2 | 按 DEC5=A：删 185，改为实测数；README 同步写同一数 |
| **D14** | 本地 `release/` 与远端附件不同字节，M7 台账同文件名两个值 | P2 | 按 DEC4 删除本地 `release/`；M7 的历史台账**不改**（那是历史事实），在本文件 §二 记录处置 |
| **D15** | 两个 TODO 占位模块 + 未用依赖 jinja2 | P3 | 删除 `src/hws_formal_math/templates/` 与 `viewer/ui/`（全仓 0 引用）；jinja2 从 `dependencies` 移除；README 项目结构同步 |

### 2.1 与诊断结论的差异（更正 + 证据）

诊断纪律要求"发现诊断结论有错，新增文件写更正 + 证据"。本批发现 **2 处**：

| # | 诊断原文 | 实测更正 |
|---|---|---|
| C1 | `03?` 「`data/index/manifest.json` 与 `data/proposals/v1/manifest.json` 工作树比 index 大」被归为"GitHub 侧"问题 | **实际是本机 `core.autocrlf=true` 的单向改写**：`git ls-files --eol` 显示 `i/lf w/crlf`。仓库 blob 一直是 LF（11,270 B），只有工作树被写成 CRLF（11,776 B）。所以 D4 的修法不只是"加 `-text`"，还要把**已漂移的工作树**归一，否则首次 `git add` 会把 CRLF 固化进历史 |
| C2 | D5 只点了 `gen_snapshots.py --check` | **同款缺陷在 `gen_proposals.py --check` 也存在**（`generate_proposals()` 真写盘后再读回来比）。本批一并修，并补 `tests/test_gen_proposals.py` 之外的只读语义（见 §三 的负控） |

---

## 三、验证（tag 时点）

### 3.1 全量测试

```bash
python -m pytest tests/ -q
# → 266 passed（Python 3.12.10，本机）
#   注：本数由 tests/test_repo_gate.py::TestSelfReportedTestCount 与 README/RELEASE-NOTES 自指对撞
```

分项（本批新增 51 项）：

| 文件 | 项数 | 覆盖 |
|---|---|---|
| `tests/test_kernel_subprocess.py` | 12 | 真子进程三态（新增） |
| `tests/test_release_shape.py` | 9 | 形态门禁正控 + 4 负控（新增） |
| `tests/test_cli_contracts.py` | 12 | `--version` / 退出码 4 / `export -o` / coverage 打印（新增） |
| `tests/test_repo_gate.py` | +21 | floor 五处一致 / 版本单源 / 数据自证（含负控）/ gitattributes 实查 / **自述测试数自指对撞** |

### 3.2 内核调用形态实测（DEC3=A，**关键证据**）

**本机无 Lean 工具链**（`command -v lean` 无输出、`~/.elan` 不存在），
故用**可注入的假 lean 夹具**（`tests/test_kernel_subprocess.py` 内联生成，
行为按真 Lean 语义模拟：编译失败 → rc 1 + stderr；`sorry` → rc 0 + warning；
未知长选项 → rc 1 + `Unknown command line option`）。
**这不是真 Lean 实测** —— 真 Lean 的验收留给下一轮（见 §六 遗留）。

| 输入 | **旧实现** `lean --check <file>` | **新实现** `lean <file>` |
|---|---|---|
| `theorem add_zero (n : Nat) : n + 0 = n := by simp` | rc **1**，`Unknown command line option '--check'` → **FAIL（错误判定）** | rc **0** → `PASS_NO_SORRY` ✅ |
| `theorem bad : 1 = 2 := by rfl #error` | rc **1**（但原因是选项非法，不是证明错） | rc **1** + stderr 错误行 → `FAIL` ✅ |
| `theorem s : 1 = 2 := by sorry` | rc **1**（同上，永远达不到 PASS_WITH_SORRY） | rc **0** + warning → `PASS_WITH_SORRY` ✅（K1：不计入成功） |

**结论**：旧实现下 rc 恒为 1，`PASS_NO_SORRY` 与 `PASS_WITH_SORRY` **永远不可达**——
诊断 D2 的核心判断成立。新实现三态映射全部正确。

### 3.3 pip 渠道"装完能用"（G1）

干净 venv（**新建**，非 `.venv_test`）+ **中立目录**（不是仓根）：

| 命令 | 结果 |
|---|---|
| `hws-formal-math selftest` | **exit 0**，索引 35 条，数据自证通过 |
| `hws-formal-math search "加法结合律"` | **exit 0**，9 条 |
| `hws-formal-math bench --suite retrieval` | **exit 0**，Recall@10 0.9 / MRR 0.9 |
| `hws-formal-math bench --suite depgraph` | **exit 0**，完整率 1.0 / 断链 1.0 / index_gap 1.0 |
| `hws-formal-math export --format html -o r/x.html` | **exit 0**，`r/x.html` 存在 |
| `hws-formal-math-viewer --selftest` | **exit 0**，35 条 / 5 命中 / 4 节点 8 边 / 3,092 B HTML |

包内容：wheel **43** 条目（其中 `data/` **12** 条、`fixtures/` **3** 条，此前均为 **0**）。

### 3.4 sdist 自足

```bash
tar xzf hws_formal_math_navigator-0.1.2.tar.gz && cd hws_formal_math_navigator-0.1.2
pip install -e ".[dev]" && python -m pytest tests/ -q
# → 260 passed, 3 skipped（此前是 2 个 collection error，exit 2）
```

> 3 项 skip 是依赖 `.git` 的门（`git check-attr` / `git ls-files`），
> 源码包内没有 `.git` 属预期。**反向锚**：`test_git_attr_gates_are_active_in_repo`
> 断言"仓库内必须有 .git"，防止这两条门在仓库里被永久 skip 变成假门。

### 3.5 门禁负控（逐条贴 rc）

| 门 | 负控构造 | 期望 | 实测 |
|---|---|---|---|
| `assert_release_shape.py` | zip **只放查看器** | ≠0 | **EXIT=1**（`❌ 内缺 CLI`） |
| 同上 | zip **只放 CLI** | ≠0 | **EXIT=1**（`❌ 内缺查看器`） |
| 同上 | 双 exe 齐备 | 0 | **EXIT=0** |
| `tools/check_data_integrity.py` | `snapshots.json` 追加 1 空格 | ≠0 | **EXIT=1**（2 处不一致） |
| 同上 | 改 `proposals` manifest 的 sha256 | ≠0 | **EXIT=1** |
| 同上 | 未篡改 | 0 | **EXIT=0** |
| `gen_snapshots.py --check` | 追加 1 空格后跑 | ≠0 且**文件保持 2,151 B** | **EXIT=1**，大小仍 2,151 B ✅（旧实现会恢复成 2,150 B） |
| `gen_proposals.py --check` | 未篡改 | 0 | **EXIT=0**，sha256 `8029bdf2…` |

### 3.5.1 自述测试数（D13 的复发与守门）

本批第一次提交时，README / RELEASE-NOTES 里的测试数被写成 **227**（当时实测 263）——
**这是 D13 的同款缺陷复发**，且因为 tag 已打，错误的数字进了 tag 树与 Release 正文。
处置：

1. 修正为实测数（现已 266，含新增的自指守门本身）；
2. **补自指守门**：`tests/test_repo_gate.py::TestSelfReportedTestCount`（3 项）
   用 `pytest --collect-only` 的**真实收集数**对撞 README 与 RELEASE-NOTES 里的数字，
   改测试数量而不同步文档 → 立刻红。这比"再写一次数字"更可靠；
3. tag `v0.1.2` **重指**到修正后的提交（旧 tag 提交已被替换，CI 与 Release 重新生成）。

> 教训（与本组其它仓一致）：**"数字写进文档"必须配"数字与实物对撞的门"**，
> 否则下一次改测试还会漂移；而一旦漂移发生在 tag 之后，就需要移动 tag 才能修好发布物。

### 3.6 字节冻结实查

```
$ git check-attr -a data/index/theorems.jsonl data/snapshots/manifest.json \
    data/snapshots/v1/snapshots.json data/snapshots/v1/manifest.json \
    data/proposals/v1/proposals.json data/proposals/v1/manifest.json
→ 全部 text: unset
```

---

## 四、已知边界（未变 / 新增）

- 随包索引是 35 条**样例**（`curated-sample`），检索召回仅代表样例域；
- 签名是便于演示的简化写法（`provenance_note` 已声明），非 mathlib4 逐字抽取；
- 内核验证需用户自备 Lean；未装时 `bench --suite skeleton` 报 `not_enabled` 且 exit 1；
- 查看器需 PySide6（`[gui]` extra）；缺依赖时 `--selftest` 仍可跑，窗口模式 exit 3；
- **新增**：模型端点三条仍为 `NotImplementedError`（本批只披露，见 §二 D6）；
- **新增**：领域覆盖度 **只打印不判定**（`analysis` 4/5、`number_theory` 0/5）；
  根因是随包模块名为 `Mathlib.Data.*`，`domain in module` 分类对 `number_theory` 恒为 0。
  把它接进门禁会让基准恒红，静默降级成 verified 则是开后门——本批选择如实打印。

---

## 五、tag 后追加事实

> 本节内容产生于 tag 之后，与 §一 分开记录。
> **注意**：本节在 tag 树里保存的是当时快照；tag 之后又发生过一次**重指**（见下），
> 故**最终事实以本节当前版本为准**（tag 树内的版本是较早的一次快照）。

### 5.1 tag 重指（诚实记录）

| 次 | tag 提交 | 触发的 run | 为什么重指 |
|---|---|---|---|
| 第 1 次 | `32b5cb1` | `39482520223`（push main）/ `39483233797`（tag）均 success | — |
| **第 2 次（最终）** | **`f82ccad`** | `39519879201`（push main）/ `39520358078`（tag）均 success | 首发把自述测试数写成 **227**（实测 263），改正并补自指守门后重指（见 §3.5.1） |

重指前推送过一次 `main`（`f82ccad`）并确认 CI 全绿，之后才 `git push --force` 覆盖 tag，
随后 publish job 重建 Release（附件哈希随之变化）。

### 5.2 最终 CI 证据

| run | 触发 | 结论 |
|---|---|---|
| `39519879201` | push `main`（`f82ccad`） | ✅ 4 测试腿 + 3 平台 build success；publish skipped |
| `39520358078` | push tag `v0.1.2`（同提交） | ✅ 7 job success + **publish success** |

**注解**：Node20 弃用告警 **0 条**。仅剩 GitHub 平台级 notice 4 条
（3 条 `ubuntu-latest → Ubuntu 26` 迁移提示、1 条 macOS arm64 容量提示），与本仓代码无关。

### 5.3 最终 Release 附件（`gh release view v0.1.2 --json assets` 回读）

| 附件 | 大小 | sha256（API digest，去前缀） |
|---|---|---|
| `hws-formal-math-v0.1.2-win64.zip` | 21,870,552 B | `45551ef867a005e9a54a2593f620c85c256dacfd8f5f74d6f2fbc1181c7d9473` |
| `hws-formal-math-v0.1.2-linux-x86_64.zip` | 54,797,077 B | `9f4800eff57f0d238abc4b378a9185ad36988cdefbc400b34ca1a9b1c7c6be5b` |
| `hws-formal-math-v0.1.2-macos-arm64.zip` | 38,271,266 B | `053821af3434b2b27b688ad12e79a3dac2d363b9a679b80b2775234faa1018c3` |
| `hws_formal_math_navigator-0.1.2-py3-none-any.whl` | 68,812 B | `746b099cce448a200514974cc5153668009ac317b69707c3cd0aa6d40f62cd07` |
| `hws_formal_math_navigator-0.1.2.tar.gz` | 181,623 B | `9e809f8784f540ede3d3b5eb050eba3b18847e823c03ff3ed0f9cec5ef3a8537` |
| `SHA256SUMS.txt` | 530 B | `49dc16bfdf096e71da4131f4a039755fa92ec47cd4a6fed85441810c4b7a5cb2` |
| `demo.gif` | 42,636 B | `1ea75122d338bce5c2b27f024c65310517e1633c67254b0f4d89df0f2f3edb2c` |

> 三次 zip 的大小完全相同（21,870,552 / 54,797,077 / 38,271,266 B）而 sha256 不同 ——
> 这是 PyInstaller 产物**不承诺跨次构建字节一致**的已知特性（CI 注释已声明），
> 与"打包这一步"（`ZIP_STORED` + 条目排序 + 固定时间戳）的可复现性不冲突。

**Release 正文**：读的是 tag 树里的 `RELEASE-NOTES.md`，已确认含 `266 tests passed`（不再是 227）。

### 5.4 真下载复核（中立目录，直连 GitHub）

| 命令 | 结果 |
|---|---|
| 下载全部 7 附件后 `sha256sum -c SHA256SUMS.txt` | **5/5 OK** |
| `unzip` win64 zip → 双 exe | `hws-formal-math.exe` + `hws-formal-math-viewer.exe` |
| `hws-formal-math.exe selftest` | **exit 0**（索引 35 条 / **数据自证通过** / 冻结态数据目录随包） |
| `hws-formal-math.exe search "加法结合律"` | **exit 0** |
| `hws-formal-math.exe bench --suite retrieval` | **exit 0** |
| `hws-formal-math-viewer.exe --selftest` | **exit 0** |
| 干净 venv 装 Release **wheel**（`selftest` / `search` / `bench --suite retrieval` / `bench --suite depgraph` / `export --format json -o o/custom.json` / `viewer --selftest`） | **全部 exit 0** |
| `hws-formal-math --version` | **exit 0**，`hws-formal-math 0.1.2` |

> 注：CI 构建的 wheel/sdist 与本机构建的字节不同（68,812 B vs 69,011 B；181,623 B vs 174,625 B），
> 系数 setuptools 版本与构建平台差异；本仓不对 sdist/wheel 承诺跨机字节一致。

## 六、遗留（交给下一轮）

| # | 项 | 说明 |
|---|---|---|
| L0 | ~~写 RELEASE-M8 / 提交推送 / CI 绿 / 打 tag / 发 Release~~ | ✅ **已完成**（见 §五；run `39482520223` 与 `39483233797` 全绿，Release 7 附件真下载复核通过） |
| L1 | **真 Lean 实测** | 本机无 Lean，D2 的修复只有"假 lean 夹具"证据。需在装了 Lean 4 的机器上跑三种输入并记录 `lean --version` 与 rc/stdout |
| L2 | macOS / Linux 实机目检 | 附件 sha256 可核，但两平台的原生运行只在 CI runner 跑过；若打包器变了需重新确认 |
| L3 | `vector` extra 从未被 import | 与 jinja2 同类（"声明了但没实现"）；本批只清了 jinja2 |
| L4 | 领域覆盖度是否进判定 | 需要先修分类规则（按 `Mathlib.Data.*` 的实际语义映射），否则接进门禁只会恒红 |
