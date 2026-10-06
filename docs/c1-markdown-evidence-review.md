# C1 验收记录：Markdown 提取与证据报告审核

- 执行人：C（AI 助手代为执行样例与扫描，C 复核签字后生效）
- 执行日期：2026-09-29
- 环境：Windows 11，Python 3.12.1，docsync-core 0.2.0（editable），基线提交 `1be73fe`
- 样本仓库与产物：`runs/c1-evidence/`（fixture `demo-md`、扫描输出、ignore 配置；本地保留不入库）

## 一、提取与判定逐项复核（10 类样例）

代码基线 `src/client.py`：`connect(timeout=60)`、`fetch(retries=3, timeout=None)`、`open(cache=128)`。

| # | 样例 | 声明位置（span 可定位） | 预期 | 实际 | 结论 |
|---|------|------------------------|------|------|------|
| 1 | 中文默认句（`## \`connect\`` 标题语境） | docs/defaults-zh.md:5 | CONSISTENT（60=60） | CONSISTENT / LITERAL_EQUAL，fact_ids 指向代码事实 | ✅ |
| 2 | 中文默认句（fetch.retries=3） | docs/defaults-zh.md:9 | CONSISTENT | CONSISTENT / LITERAL_EQUAL | ✅ |
| 3 | 中文默认句（fetch 未传 timeout 为 None） | docs/defaults-zh.md:9 | 与 None 代码事实区分，不误判 | 未生成 30/5 类冲突，行为保守正确 | ✅ |
| 4 | **英文默认句** "The default value of `timeout` is `60`" | docs/defaults-en.md | 提取并判定 | **未提取（漏检）** | ❌ **缺陷 D-1** |
| 5 | **英文漂移句** "The default value of `timeout` is `5`"（代码 None） | docs/defaults-en.md | 应报冲突或明确 UNKNOWN | **未提取，静默漏检** | ❌ **缺陷 D-1** |
| 6 | 中文参数表（参数/默认值列） | docs/params-table.md:7 | 提取并判定 | CONSISTENT / LITERAL_EQUAL | ✅ |
| 7 | 围栏内 import 别名 + 调用（`import client as c; c.connect(timeout=60)`） | docs/fence-alias.md:3-6 | CALL_ACCEPTED | CONSISTENT / CALL_ACCEPTED，subject=client.connect | ✅ |
| 8 | 旧版/迁移语境（"旧版 0.9（已废弃）"标题下声明 30） | docs/legacy-context.md:5 | 拒绝确定结论 | UNCERTAIN / VERSION_UNRESOLVED，version_scope=unresolved | ✅ |
| 9 | 条件语境（"如果启用兼容模式…"） | docs/conditional.md:3 | 拒绝确定结论 | UNCERTAIN / QUALIFIED_ASSERTION，qualifiers=[conditional] | ✅ |
| 10 | 含转义管道的复杂表格 / 无法归属的自由文本 | docs/complex-table.md、docs/free-text.md | 不提取，且不得计为"一致" | 均未提取；报告明示"未提取的文本不代表一致" | ✅ |

### 缺陷 D-1：英文 "default value of X is Y" 句式漏提取

- 现象：`docs/defaults-en.md` 两条声明全部未进入 claims（报告"声明/示例：6"中不含任何英文句）。
- 根因：`src/docsync/extractors/markdown.py:18` 的默认句正则
  `default(?:\s+value)?\s*(?:is|:|=)\s*{VALUE}` 要求 "default (value)" 与 be 动词紧邻，
  不兼容英语中最常见的 **"The default value of `X` is `Y`"**（中间隔 "of X"）。
- 影响：英文文档的漂移会**静默漏检**，且没有 UNKNOWN 记录，违反"没提取出声明不是一致"的
  可审计要求中最小化静默区的精神（尽管报告有范围说明，用户无法知道哪些常见句式没扫到）。
- 最小复现：`runs/c1-evidence/demo-md/docs/defaults-en.md` + 扫描输出 `runs/c1-evidence/scan/`。
- 建议（B 评估）：正则扩展为允许 `default(?:\s+value)?\s+of\s+`{IDENT}`\s+(?:is|:|=)\s*{VALUE}`
  并将反引号内主语与标题/链接归属逻辑复用 `subject_from`；同时为该句式补正例与反例测试。

## 二、报告展示项检查

| 检查项 | 结果 |
|--------|------|
| 声明可定位（path+行号+字节范围+blob_hash） | ✅ span 四元组齐全，凭报告可回到固定源码 blob |
| 代码事实与对齐依据 | ✅ judgments 附 fact_ids；facts.jsonl 含定义位置 |
| 规则展示 | ✅ reason_code（LITERAL_EQUAL / CALL_ACCEPTED / QUALIFIED_ASSERTION / VERSION_UNRESOLVED） |
| 忽略原因 | ✅ finding.ignored=True + ignore_reason 落报告（rule=DEFAULT_VALUE/1 验证） |
| 忽略到期日 | ⚠️ 到期日仅用于匹配时静默生效，报告不展示到期日（改进建议：finding 补 ignore_expires 字段） |
| 阶段耗时 | ✅ manifest.stage_seconds |
| 模型 usage | ✅ manifest.usage / model_calls（rules 模式为 0，如实记录） |
| 失败原因 | ✅ C2 已验证 MISSING_REF / 超时等结构化失败 |
| JSON ↔ Markdown 对应 | ✅ report.md 的状态/计数/待核查 claim_id 与 report.json 一致 |
| 拒答而非"一致" | ✅ 2 条 UNCERTAIN 有明确 reason；无凭空 CONSISTENT |

## 三、结论与移交

- 10 类样例中 8 类行为符合声明；**1 个真实缺陷（D-1 英文句式漏提取）移交 B 修复**，修复前
  不应将 limitations 中"中英文明确默认句式"表述为已完全支持，或应在 limitations 明确当前
  仅支持 "defaults to / default value is" 紧邻句式。
- 1 个展示改进（忽略到期日不入报告）记录在案。
- 全部产物路径与命令可复现；本记录待 C 人工复核签字。

## 四、B-N2 英文默认句式修复技术复验（2026-10-05）

- 执行人：AI 助手代为执行命令并整理证据；C 本人复核签字待补。
- 复验基线：`346f5dd2d88b30648ce5f40b5ab3d8f63dbe7442`（已合入 B-N2 提交 `f561b9c`）
- 环境：Windows 11，Python 3.12.1，项目 `.venv`
- 命令：`.venv\Scripts\python.exe -m pytest tests/integration/test_b_n2_english_defaults.py -q -p no:cacheprovider`
- 结果：`6 passed`

技术复验结论：

- 英文 `The default value of X is Y` 正例已能提取，并分别覆盖一致和冲突样例。
- 旧版标题语境仍保持 `UNCERTAIN / VERSION_UNRESOLVED`，不会强行确认。
- 同名符号歧义仍保持 `UNCERTAIN / AMBIGUOUS`，不会选择 top-1 硬判。
- 显式源码链接归属、合法调用样例、行号、字节范围和 blob hash 由专项测试覆盖并通过。

待 C 本人复核后，可据此判断是否关闭 C1 缺陷 D-1。

## 五、B-N3 忽略到期日展示技术复验（2026-10-05）

- 执行人：AI 助手代为执行命令并整理证据；C 本人复核签字待补。
- 复验基线：`346f5dd2d88b30648ce5f40b5ab3d8f63dbe7442`（已合入 B-N3 提交 `1edda88`）
- C 展示修改：`src/docsync/reporting/__init__.py`
- C 展示测试：`tests/integration/test_b_n3_ignore_expiry.py::test_markdown_report_explains_ignore_expiry_states`
- 命令：`.venv\Scripts\python.exe -m pytest tests/integration/test_b_n3_ignore_expiry.py tests/unit/test_patch_guards.py -q -p no:cacheprovider`
- 结果：`21 passed, 2 skipped`
- 跳过说明：`tests/unit/test_patch_guards.py` 中两个真实 symlink 场景因当前 Windows 进程没有创建文件系统符号链接权限而跳过；不能写成已通过。

Markdown 展示复验结果：

- 无匹配规则：显示 `忽略状态：未忽略`，不编造原因或到期日。
- 匹配无期限规则：显示 `当前忽略`、规则原因和 `无期限`。
- 匹配有效到期日规则：显示 `当前忽略`、规则原因和到期日。
- 匹配已过期规则：显示 `规则已过期，告警未忽略`、规则原因和到期日。

技术复验显示：JSON 字段含义由 B-N3 契约测试覆盖，Markdown 能区分无期限、有效期、规则已过期和无匹配四种状态；过期规则显示“规则已过期，告警未忽略”，未按阅读日期重新计算历史报告。专项测试和补丁守卫测试通过；真实 symlink 场景因权限跳过，保留为后续有权限环境复核项。待 C 本人复核后，可提交给 A 做最终验收。

C 本人已复核上述 B-N2/B-N3 技术复验记录，确认同意关闭 C1 缺陷 D-1，并同意 B-N3 字段、匹配和报告展示进入 A 的最终验收。
