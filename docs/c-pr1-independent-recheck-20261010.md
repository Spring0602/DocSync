# C 独立复验记录：PR #1（B 收尾）

- 复验人：成员 C（2026-10-10）
- 复验对象：PR #1 `Member b release closeout final`，分支 `member-b-release-closeout-final` → `main`，head `bfd066e308e9f481abd7b1435479ed580f94b628`（基于 `main` `353527b`）
- 复验方式：全离线、全复现；未调用任何付费模型；**未修改 B 的本人复核记录**（`docs/audit-samples/b-release-coverage-20261010/human-review.json` 保持原样）
- 复验环境：Windows + `.venv`（本项目依赖）；本地检出 PR head 后逐项重跑

---

## 一、复验结论

**通过（实质验证全部复现）。** 同时发现 3 项**文档层面的可追溯性问题**，不影响功能结论，建议在 A 合并前或合并后由 B 修正。

---

## 二、逐项核验（对应复验要求 1—5）

### 1. Files changed 中的代码、测试和报告是否一致 ✅

PR 共 15 个文件（与 GitHub API 一致，+1081/−87）：代码 `src/docsync/extractors/{markdown,python_ast}.py`、`utils.py`；测试 `tests/integration/{test_b_release_coverage,test_static_extensions}.py`；报告 `docs/audit-samples/b-release-coverage-20261010/*` 与 3 篇说明文档。

独立复现结果：

| 核验项 | 我的复现 | 结论 |
|--------|----------|------|
| 冻结 manifest 可重建性 | `build_reviewed_candidates.py` 重建的 manifest 与 `bench/frozen/candidate-dev-v1/manifest.jsonl` **逐字节相同**（SHA-256 `c8fcf3cf…`） | ✅ |
| 逐样本预测 | 我用 `bench.run_suite --methods rules` 重跑，24/24 样本的 prediction **与证据文件 `after-predictions.jsonl` 完全一致**（含 4 个 PARTIAL） | ✅ |
| 指标 | 我用仓库 `src/docsync/metrics.py` 重算：`tp=8 fp=0 tn=11 fn=0 decidable=19 decided=18 insufficient=5 improper_confirmation=0 abstained=6`，与 `after-metrics.json` **完全一致** | ✅ |
| 报告前后对比表 | 修复前 `3/0/11/5`（与 `a-closeout-20261010/rules/metrics.json` 一致）、修复后 `8/0/11/0`；决策覆盖 `6/19 → 18/19`；拒答 `18/24 → 6/24`；不当确认 `0/5 → 0/5`；API 请求 `0` | ✅ |
| 代码是否"针对样本硬编码" | `git diff src/` 中**无** `candidate-*`、`seed-*`、`CONSISTENT/INCONSISTENT`、`gold` 等字面量；实现是通用的 `_UNKNOWN` 传播 | ✅ 无作弊 |
| 测试与报告对应 | `test_b_release_coverage.py` 5 个用例分别对应报告所述"构造方法、定义时绑定、字面量展开、顺序/嵌套配置、动态反例"五组；单跑 `5 passed` | ✅ |

### 2. candidate-06 是否仍保持拒答 ✅

- manifest：`candidate-06` 金标 `CONSISTENT`、类型 `DEFAULT_VALUE`；源码 `repos/candidate-family-02/case06.py`：
  ```python
  def encode_packet(payload, codec="latin-1"):
      return payload, codec

  encode_packet.__defaults__ = ("utf-8",)
  ```
  即函数定义后**在运行时改写 `__defaults__`**。
- 我重跑得到 `UNCERTAIN`（拒答），与证据文件一致；报告状态为 `PARTIAL`，并带 `DYNAMIC_FUNCTION` 诊断；B 报告与本 PR 文档均明确写"继续拒答、本轮不展开支持"。
- 该样本因此是本轮唯一"可判定但未回答"的样本（`decided=18/19`），不是被误判为一致。

### 3. 环境变量与运行时动态语义是否被错误判断为一致 ✅

金标为 `INSUFFICIENT` 的 5 个样本（07/12/16/19/23）我逐个复现，**全部 `UNCERTAIN`，无一个被确认为一致**；指标 `improper_confirmation = 0/5`。

- `candidate-07`：默认值取自读环境变量的函数调用 ——
  ```python
  def flush_interval():
      return int(os.environ.get("FLUSH_INTERVAL", "8"))

  def flush_records(interval=flush_interval()):
  ```
  存在 fallback 也**未**被当作保证值 ✅
- 新增测试文件中直接写入反例断言（我实跑通过）：
  - `("encode_packet","codec").decision == "UNCERTAIN"`（运行时改 `__defaults__`）
  - `("settings.STORAGE.local","root").decision == "UNCERTAIN"`（环境变量）
  - `("settings.OPTIONS","workers")`、`("settings","PORT")`、被重绑定 `dict(...)` 构造 → `UNCERTAIN`

### 4. 完整测试及 CI 是否通过 ✅

- 本地完整 pytest（PR head）：**222 passed, 2 skipped in 245.12s**；两个 skip 均为 `OS does not grant symlink creation to this process`（Windows 权限），与 B 声称一致。
- 新增回归单跑：`5 passed`。
- 远程 CI（head `bfd066e3`）：
  - `Core CI` #38063572306：`check (ubuntu-latest)` 与 `check (windows-latest)` **均 success**，步骤含 `pytest` / `ruff check` / `ruff format --check` / `mypy` / `build`；
  - `Documentation consistency` #38063572299：success；
  - 同 SHA 另有一次 `Core CI` #38063014580 success。

### 5. candidate-dev-v1 是否仍明确标为开发集 ✅

- `bench/frozen/candidate-dev-v1/manifest.jsonl`：24 行 `split=dev`、`origin=controlled`、`annotation_status=adjudicated`（**无一行标为 test**）。
- `freeze.json`：`formal_test_ready=false`、`human_signoff=pending`。
- 文字表述：冻结集 README、`docs/audit-samples/b-release-coverage-20261010/README.md`、`docs/b-ai-human-review-guide-20261010.md` 三处均写明"**仍是开发集，不是独立正式测试集**"，并说明六组已排除出独立正式 test 的依据。
- `compliance/ai_assistance_log.csv` 新增行也注明"no model calls; human review pending"，未夸大为正式评测。

---

## 三、发现的问题（3 项，文档/可追溯性层面，不阻塞功能结论）

**问题 1：证据 README 中"修复后指标文件"的哈希是 63 位，不是合法 SHA-256**

`docs/audit-samples/b-release-coverage-20261010/README.md` 第 11 行声明
`6c59ea53103f6cd72339e16c336d1e2ee14c79bdfee69d013f9c787e8f1eee8`，只有 **63** 个十六进制字符（疑似漏抄 1 个字符）。按仓库存储字节，该文件正确哈希为
`89686d460b6b870fb899de01499e04d518e19bfac836c129b4281905f0ef7949`。

**问题 2：同一 README 内两个哈希口径不一致（CRLF 工作区副本 vs 仓库字节）**

- 第 11、13 行（修复后指标 / 修复后预测）的声明值对应 **Windows 默认检出后 CRLF 副本**的哈希：
  - 预测：声明 `7f585f08…`（CRLF 副本），仓库存储字节（LF）实为 `6c424d160b07d56d866acb5d19e3c99a3216641cdb7e46a4730ac5e3370775d5`；
  - 指标：声明值即 CRLF 副本 `6c59ea53…`（且见问题 1，缺 1 字符），仓库字节为 `89686d46…`。
- 而第 7、9 行（manifest / 修复前指标）用的是 **LF 仓库字节**哈希。
- 后果：复验者**只按仓库（LF）字节**去做，无法一致复现第 11/13 行的哈希。建议统一为"仓库存储字节"口径，或显式标注"CRLF 工作区副本"。
- 注：该问题不影响功能结论——我已按仓库字节重建 manifest、重跑预测并重算指标，结果与报告完全一致。

**问题 3：引用的实现提交 `7a16354…` 在仓库中不可解析**

`docs/b-release-coverage-review-20261010.md`、`docs/tasks.md` 新增段落、`docs/audit-samples/b-release-coverage-20261010/README.md` 第 14 行、以及 `compliance/ai_assistance_log.csv` 新增行均引用 `7a16354f0ff1ad4c6ed544cd19a926c867848897`。我在已拉取全部远程分支（`main`、`c2-action-verification`、`member-b-tasks`、`member-b-release-closeout-final`）后确认：该提交**在任何引用中都不存在**。评审文档已说明它是移植前提交、已在 `353527b` 上移植为 `0ccbecb`，建议统一改引可解析的 `0ccbecb`，否则外部复验者无法定位代码版本。

**附带提示（不算问题）**：`compliance/ai_assistance_log.csv` 新增行的 `human_reviewer` / `human_changes` 仍为 `pending`，而 `human-review.json` 记载 B 已本人完成五项复核。若这是刻意保留给 A/C 复验，建议在台账里写明口径，避免两处记录被读成矛盾。

---

## 四、未越界声明

- 本记录**未修改** B 的本人复核记录（`human-review.json`）与其原始标注、冻结标签、冻结 CSV/表：PR 差异中不含 `bench/frozen/**`、`bench/annotations/**`、`compliance/data_rights.csv`、`compliance/installed_dependencies.csv`、`compliance/third_party_resources.csv`，也未改动 C 的 `individual-C-*.csv` 与 `docs/c3-preaudit-worksheet.md`。
- 未做合并操作；是否合并由 A 决定。
- 复验产生的临时产物在 `runs/c3-repro-candidates/`、`runs/c3-repro-out/`、`runs/pr1-pytest.txt`（`runs/` 已被 `.gitignore` 排除，不入库）。

## 五、建议给 A 的结论

1. 五项复验要求 **全部通过**，可进入 A 的合并决策。
2. 建议 A 在合并前请 B 修正上述 3 项文档问题（哈希位数/口径、引用不可解析的提交 SHA）；因这些不影响代码行为与指标，A 也可选择合并后以补充提交修正，但**不应**在修正前对外引用第 11/13 行哈希作为可复现依据。
3. candidate-06 的拒答属**已知且已文档化的覆盖缺口**（金标 CONSISTENT 但系统弃权），不应被解读为"通过"；如需提升该点，属后续实现范围，且按既定原则"不得为通过开发集放宽动态值证据要求"。
