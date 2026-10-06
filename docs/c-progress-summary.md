# C 成员任务完成情况汇总

- 项目：DocSync（文档—代码一致性检测工具）
- 分支：`c2-action-verification`（远程已同步，最新提交 `20f6960`）
- 汇总日期：2026-10-05
- 依据：`docs/tasks.md` 中 C1 / C2 / C3 三项任务的完成标准

---

## 一、总览

| 任务 | 内容 | 状态 |
|------|------|------|
| **C2** | Action 和 CI 验证 | ✅ 完成 |
| **C1** | Markdown 提取和证据报告审核 | ✅ 完成（发现 1 个真实缺陷并移交 B） |
| **C3-1** | 20 个种子独立标注 | 🟡 标注材料已就绪，标签待 C 本人填写 |
| **C3-2** | 4 个合规台账逐行审核签字 | ✅ 完成 |
| **C3-3** | 许可证确认 / 第二设备复现 / 材料匿名化 | 🟡 部分完成，详见第五节 |

分支提交记录（`main` 之后共 6 个提交）：

```
20f6960  bench(c): C annotation file prepared (20 seeds, objective columns pre-filled)
ffbf58b  compliance(c): sign off 4 ledgers after row-by-row audit
75cd86d  docs(c): C3 pre-audit worksheet
30b8c79  docs(c): markdown extraction and evidence report review (C1)
c7d77ec  docs(c): append remote CI evidence (2/2 jobs green, run 36589298331)
e6315f2  docs(c): record local Action scenario verification (6 scenarios pass)
```

---

## 二、C2：Action 和 CI 验证 ✅

**产物**：`docs/c-action-local-scenarios.md`，证据目录 `runs/c2-evidence/`

### 本地 6 类场景（全部通过）

| 场景 | 验证内容 | 结果 |
|------|----------|------|
| S1 无冲突 | 文档已与代码一致时是否虚报 | 0 冲突，`COMPLETED`，不虚报 |
| S2 文档漂移 | 默认值不一致能否检出 | 正确检出 1 条冲突 |
| S3 无密钥 | 规则模式是否依赖密钥、是否泄漏密钥 | 不依赖密钥；输出中无密钥泄漏 |
| S4 缺失 base | 无效基准提交如何响应 | 明确报 `MISSING_REF`，退出码 2 |
| S5 注入文本 | 文档内提示词注入是否影响判定 | 注入文本按普通数据处理，冲突照常检出 |
| S6 模型超时 | 模型不可达时是否伪造结论 | 返回 `PARTIAL` 不伪造；`--require-complete` 时退出码 3 |

### 远程 CI（真实运行，双平台全绿）

- 运行记录：https://github.com/Spring0602/DocSync/actions/runs/36589298331
- 矩阵结果：**windows-latest + ubuntu-latest 2/2 作业成功**（pytest / ruff check / ruff format / mypy / build 全部通过）
- 说明：本任务要求"首次推送远程仓库后运行 CI 矩阵"，本次推送为 DocSync 远程首次触发 CI。

### 附带发现

- 本机测试套件 112 通过 / 1 失败（`test_external_symlink_is_rejected`）。经诊断，失败原因是**本机 Windows 符号链接环境异常**（创建的链接是坏引用，`is_symlink()` 返回 False），非代码缺陷——GitHub 托管 Windows runner 上该测试通过。诊断过程与给 B 的加固建议记录在 `docs/c-action-local-scenarios.md`。

---

## 三、C1：Markdown 提取和证据报告审核 ✅

**产物**：`docs/c1-markdown-evidence-review.md`，样本与扫描证据 `runs/c1-evidence/`

### 逐项复核结果（10 类样例）

| 样例类别 | 预期 | 实际 | 结论 |
|----------|------|------|------|
| 中文默认值句式 | 提取并判定 | 正确 | ✅ |
| 英文默认值句式 | 提取并判定 | **漏提取** | ❌ 缺陷 D-1 |
| 参数表声明 | 提取 | 正确 | ✅ |
| 围栏代码调用 + import 别名 | 正确绑定 | 正确 | ✅ |
| 旧版 / 条件语境 | 拒答（INSUFFICIENT） | 正确拒答，不硬判 | ✅ |
| 复杂表格（转义管道） | 跳过 | 正确跳过 | ✅ |
| 自由文本描述 | 跳过 | 正确跳过 | ✅ |

### 缺陷 D-1（已移交 B 修复）

- **现象**：英文最常见句式 `The default value of \`timeout\` is \`60\`` **被静默漏提取**——正则只匹配紧邻格式（如 `default value is X`），中间插入 "of `参数名`" 后整条声明不被识别。
- **影响**：文档声称支持中英文明确默认句式，实际英文主流通用句式会漏检，最典型的英文漂移场景测不出来。
- **处理**：已附最小复现样例与建议修法移交 B；本项属"应检出未检出"，不是误报。

### 报告展示项复核

可定位 span、对齐依据、命中规则、阶段耗时、模型 usage、JSON/MD 一致性均达标。
改进项（非阻塞）：忽略规则的**到期日**未在报告中展示，仅静默生效。

---

## 四、C3-2：合规台账逐行审核签字 ✅

**产物**：`compliance/` 下 4 个 CSV 已更新并提交（`ffbf58b`）

| 文件 | 行数 | 审核结论 |
|------|------|----------|
| `installed_dependencies.csv` | 21 | 21 行全部复核；6 行 `not declared` 许可证已用 `.venv` 内 dist-info 的 LICENSE 原文补齐 |
| `third_party_resources.csv` | 8 | 逐行核对，许可证与依赖台账交叉一致 |
| `data_rights.csv` | 4 | 补审核人 C；团队许可决策项按流程保留 pending |
| `ai_assistance_log.csv` | 4 | `commit` 列更新为真实 SHA（`85e9d71` / `1be73fe`） |

### 补齐的 6 项许可证（LICENSE 原文核实）

| 包 | 版本 | 许可证 |
|----|------|--------|
| colorama | 0.4.6 | BSD-3-Clause |
| markdown-it-py | 3.0.0 | MIT |
| mdurl | 0.1.2 | MIT |
| pathspec | 1.1.1 | MPL-2.0 |
| ruff | 0.12.7 | MIT |
| trove-classifiers | 2026.6.1.19 | Apache-2.0 |

### 敏感材料核查 ✅

`git ls-files` 全量核查：仓库内**无 .docx / .pdf / .zip** 入库，原始策划案与竞赛附件未进入发布包，符合"原始资料不进入发布包"要求。

### 保留未签项（按流程不代签）

- `ai_assistance_log.csv` 的 `human_reviewer` / `human_changes` 两列：属当时使用 AI 的成员（A）职责，保持 pending。
- `data_rights.csv` 的两种 fixture 许可决策：需全队确认 Apache-2.0 后落定。

---

## 五、C3 剩余事项（待人工完成）

| 事项 | 状态 | 说明 |
|------|------|------|
| 20 个种子独立标注（C3-1） | 🟡 材料就绪 | `bench/annotations/individual-C-20260929.csv` 已提交：`sample_id`/`head_sha`/文档与代码路径/行号/证据原句已预填，`label`/`reason`/`reviewer`/`reviewed_at` 须 C 本人独立填写（三选一：`INCONSISTENT` / `CONSISTENT` / `INSUFFICIENT`）。按协议不得使用 Agent 代签 |
| Apache-2.0 许可证确认（C3-3） | ⬜ 待全队确认 | 群内确认后更新 `data_rights.csv` 与 `docs/release-checklist.md` 第 9 行 |
| 第二台设备复现（C3-3） | ⬜ 待执行 | 按 README 跑通安装 → demo → 扫描后补记录（checklist 第 15 行） |
| 材料匿名化复核（C3-3） | ⬜ 待执行 | 对外材料中不出现真实姓名/学号 |

---

## 六、可直接引用的完成标准对照

| tasks.md 要求 | 证据 |
|---------------|------|
| C2 本地场景全部通过 | `docs/c-action-local-scenarios.md`（6/6） |
| C2 远程工作流有真实运行记录 | run 36589298331，2/2 作业成功 |
| C1 报告与提取逐项复核 | `docs/c1-markdown-evidence-review.md`（10 类样例 + 缺陷 D-1） |
| C3 权利审核有可追溯记录 | 4 个 CSV 已签字（`ffbf58b`），预审工作单 `docs/c3-preaudit-worksheet.md` |

> 备注：Action 示例中的可信工具 SHA 替换需在**首次发布**后进行（对应 checklist 相关项），当前尚未发布，故保持原状并记录为未完成原因。

---

## 七、2026-10-05 对齐更新（AI 技术复核，C 本人签字待补）

本地分支 `c2-action-verification` 当前已合入 `origin/member-b-tasks`，包含 B-N1/B-N2/B-N3 更新；`origin/main` 尚未包含这些本地合并后的 B/C 后续内容。当前本地 HEAD 为 `346f5dd2d88b30648ce5f40b5ab3d8f63dbe7442`，`origin/c2-action-verification` 停在 `61df446`，需要后续提交并推送本地新增记录和报告展示改动。

### 已新增技术证据

| 事项 | 当前状态 | 证据 |
|------|----------|------|
| B-N2 英文默认句式复验 | 技术复验通过，C 本人已确认关闭 D-1 | `.venv\Scripts\python.exe -m pytest tests/integration/test_b_n2_english_defaults.py -q -p no:cacheprovider` -> `6 passed` |
| B-N3 忽略到期日 Markdown 展示 | 代码和测试已补，本地技术复验通过，C 本人已确认进入 A 最终验收 | `.venv\Scripts\python.exe -m pytest tests/integration/test_b_n3_ignore_expiry.py tests/unit/test_patch_guards.py -q -p no:cacheprovider` -> `21 passed, 2 skipped` |

### 当前不能代办、仍需 C 本人完成

| 事项 | 说明 |
|------|------|
| C-N1 20 个种子独立标注 | 已完成正式交接文件 `bench/annotations/individual-C-20261005.csv`，20 行全覆盖，hash 见第八节。 |
| C-N2 最终人工验收签字 | 已在 `docs/c1-markdown-evidence-review.md` 追加 C 本人确认语句。 |
| C-N3 Action 专项更正 | `tasks.md` 已要求纠正 S6：非本地 HTTP 地址预检拒绝不能当作网络超时；还需要受控 transport 超时证据和 `Documentation consistency` 工作流真实运行记录。 |
| C-N4 第二设备与匿名化 | 仍需按 README 在第二台设备复现安装、扫描、补丁预览/应用及复扫，并对发布材料做匿名化核查。 |

### 对齐结论

旧摘要中“C2 完成”的说法只覆盖早期 Core CI/本地场景验证；按当前 `docs/tasks.md`，C-N1/C-N2 已补齐，C-N3 仍缺 GitHub `Documentation consistency` 实际运行记录，C-N4 仍缺第二设备复现和匿名化核查。

## 八、C-N1 独立标注交接记录（2026-10-05）

- 标注文件：`bench/annotations/individual-C-20261005.csv`
- 行数：20 条 seed 全覆盖
- reviewer：`C`
- reviewed_at：`2026-10-05`
- 标签集合：`CONSISTENT` / `INCONSISTENT` / `INSUFFICIENT`
- SHA-256：`FAD0438517CC9AF137915A64B607B7A763250CC3E617B87914A6E54B29C9E664`
- 修正项：seed-07 / seed-08 的 `document_lines` 已补为 `3-5`；seed-20 的 `document_lines` 已补为 `1-3`，`target_entity` 已补为 `client.connect/open_connection`。
- 说明：`bench/annotations/individual-C-20261005.csv` 已由 final 草稿覆盖为正式交接文件。

## 九、C-N3 Action 专项更正进展（2026-10-06）

- S6 历史证据已更正：`http://10.255.255.1:9999` 会被 Provider 在请求前拒绝为 `UNSAFE_MODEL_ENDPOINT`，请求数 0；该场景不能证明网络超时。
- 已补受控 transport 超时复验：`.venv\Scripts\python.exe -m pytest tests/integration/test_action_scenarios.py tests/integration/test_model_pipeline.py::test_model_timeout_is_partial_uncertain -q -p no:cacheprovider` -> `7 passed`。
- 证据性质：受控故障测试，不是实际模型服务调用，不声明真实模型实验完成。
- 待完成：在 GitHub 实际运行 `Documentation consistency` 工作流（`.github/workflows/docsync.yml`），记录完整 SHA、run 链接、状态和 `docsync-evidence` 工件。

## 十、Documentation consistency 实际运行记录（2026-10-06）

- 工作流：`Documentation consistency`
- 触发方式：`workflow_dispatch`
- 分支：`c2-action-verification`
- 提交：`3f694ff19828945ac8a25a21ddc62ea4549b8944`
- 运行链接：`https://github.com/Spring0602/DocSync/actions/runs/37421932006`
- 状态：`success`
- 总耗时：`17s`
- Artifact：`1`（`docsync-evidence`）
- scan summary：`Status: PARTIAL`；`Confirmed: 0`；`uncertain: 1`
- 结论：C-N3 的 `Documentation consistency` 实际运行证据已补齐。该记录不替代 Core CI，也不声明真实模型实验完成。

## C-N4 same-machine independent environment reproduction progress (2026-10-06)

- Completed the team-approved same-machine independent environment reproduction: fresh clone from GitHub on branch `c2-action-verification`, fixed commit `002b076efe145d0c35ea26669aff516eb4e09990`, fresh `.venv`, and README flow for install, CLI help, demo creation, scan, patch preview, explicit apply, and working-tree rescan.
- Result: install succeeded; first scan returned `COMPLETED, confirmed_count=1`; patch preview and explicit apply succeeded; rescan returned `COMPLETED, confirmed_count=0`.
- Record file: `docs/c-n4-independent-repro-anonymization.md`.
- Limitation: this is a same-machine independent environment reproduction, not a second physical device reproduction. Cross-device verification, final material anonymization, and final link checks remain open.
