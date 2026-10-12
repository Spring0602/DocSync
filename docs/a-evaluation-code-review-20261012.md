# A 评测新代码四项阅读复核（2026-10-12）

审查人：Codex（A 委托助手完成源码阅读）。日期：2026-10-12。范围：结项文件列出的 4 处新代码，对照 [工程收尾](a-evaluation-closeout-20261012.md) 的声称。未扫描 external-v1，未执行上游代码，未调用实验 API。此前 24 条标签确认不覆盖本批代码。本记录不是成员 A 的人工签署，也不关闭正式实验条件。

结论：**四项阅读完成；实现与结项口径一致，附 4 条使用时说明。** 不因本次阅读宣称最终扫描/预算已冻结。

---

## 1. `src/docsync/benchmark.py`

实际阅读：`run_benchmark` 的 `report_cache`、`usage`/`report_reused`/`report_run_id`、`ownership_keys` 与重叠区间循环；对照 `tests/integration/test_benchmark_scope.py` 的复用与重叠拒绝。

**首次/复用用量。** 缓存键是解析后的绝对仓库路径、`head_sha` 和当前有效配置 JSON，不是 `repo_id`。第一次命中写入 `report.manifest.usage`；复用行写空字典，并带同一 `report_run_id` 与 `report_reused=true`。`write_report` 仍写出完整扫描报告，其中 usage 是那一次扫描的原始用量。同仓库两个声明若各自把报告里的 `requests` 加总，会把同一次扫描算两次。正确归属是 predictions 行：只把首次行的 usage 计入，`unique_scan_count = len(report_cache)` 仅统计已缓存报告的唯一键数；抛异常而未生成报告的尝试不计入，不能当作所有实际扫描尝试次数。

**为何同组多个声明不能把请求数相加。** 检测管道按仓库快照运行一次，再对每个 sample 做声明级匹配。费用发生在 `scan()`，不在 `predict()`。两个 `claim_scope` 共享同一路径/提交/配置时只产生一次模型或规则扫描。

**重叠何时拒绝。** 旧检查仍按 `repo_id + sha + 文档/代码路径 + drift_type + claim_line + claim_scope 序列化` 拒绝完全重复坐标。新增检查在两边都有 `claim_scope` 时，用解析后的真实路径（可绕过不同 `repo_id`）、同一提交、同一文档、同一 `subject`/`predicate`，以及文档行区间是否相交。`entity_names` 别名不参与该判定，测试用 `another-label` 与别名列表仍被拒绝。这是保守的区间归属，不是任意主张的语义等价证明：不同主体、不相交区间、或缺 `claim_scope` 的样本级行不会走这条拒绝。

**意见。**

1. 当前 `pipeline.scan()` 只返回 COMPLETED 或 PARTIAL。benchmark 行上的 FAILED 来自异常，且异常路径不入缓存，后续同键样本会再试一次。结项“FAILED/PARTIAL 报告也复用”应读成：只要得到 `ScanReport` 对象（含 PARTIAL）就复用；没生成报告的抛错不缓存。`scoped_predict` 对 `status == FAILED` 返回 UNCERTAIN 是防御分支，本轮 runner 不会走到缓存里的 FAILED 报告。
2. 无 `claim_scope` 的旧样本仍只靠含 `repo_id` 的坐标去重。换 `repo_id`、指向同一物理仓库且都没有声明范围时，新的重叠检查不会触发。这与结项“声明区间”范围相符，评测清单不要混用两种单位来重复计同一发现。

---

## 2. `src/docsync/benchmark_scope.py`

实际阅读：`ClaimScope`、`scoped_predict` 全文；`keyword_predict` 在有 `claim_scope` 时直接 SKIPPED；`run_benchmark` 只把 `RepoSpec`/`ScanConfig` 交给 `scan`。

**完整声明范围。** 声明必须 `path` 对、`subject`/`predicate` 对，且整段行号落在某一个 `document_ranges` 闭区间内（不能跨多个区间拼起来）。对不上任何声明 → `SKIPPED`。

**主体/属性与实体映射。** 文档侧用 scope 的 subject/predicate 选 claim；代码侧用 `entity_names` ∩ `code_path` 选实体，再用实体、路径、`property == predicate`、`fact_kind == drift_type` 选事实。公开文档名与内部限定名不必字面相同，靠显式实体列表连接。判断引用的 `fact_ids` 必须是该事实集合的子集，否则 UNCERTAIN。rules 等还要求未忽略、类型匹配的 finding；`llm`/`no_verifier` 可用未验证判断。

**required_provenance。** 每个所需 `SourceSpan` 必须等于该事实的主 span 或 `provenance` 列表中的一项（路径、行、字节、哈希全等）。空列表时 `all([])` 为真，旧样本不受影响。缺失或伪造路径 → 事实集合为空或判断无法归属 → UNCERTAIN，而不是用 gold 改判。

**证据缺失为何拒答。** 声明抽到了但实体/事实/出处链对不上、判断混杂、有 `rejected`、报告 FAILED 或 head 不一致，一律 UNCERTAIN。这避免把“没对准目标”记成一致或冲突。

**gold 为什么不进 scan。** `gold` 只写入 predictions 行供 `evaluate`。`scan` 看不到 sample。`keyword_predict` 在声明模式下故意 SKIPPED，注释写明不借用 gold 证据补实体归属。符合结项：关键词 baseline 对 `claim_scope` 保持 SKIPPED。

**意见。** `required_provenance` 要求每条候选事实单独包含全部所需 span，不能把链拆到多个 fact 上凑齐。这与导出事实把链挂在同一 fact 的 `provenance` 上一致，但是保守约束。无法被提取器表达的跨段语义仍应拒答，不能靠填写 provenance 假装已支持。

---

## 3. `src/docsync/verification/__init__.py` 与 `src/docsync/models.py`

实际阅读：`valid_span`/`valid_provenance`/`verify`；`CodeFact.provenance`、`Evidence.code_provenance` 默认空列表；`ScanReport.references_exist`；导出链在 `extractors/python_ast.py`；对照 `test_a_contract_review.py` 旧报告补 `code_provenance: []`，以及 `test_forged_cross_file_provenance_is_rejected`。

**扫描时校验。** 仅对 `INCONSISTENT` 判断调用 `verify`。校验声明/事实主 span 的 blob 哈希、字节区间、由偏移重建的坐标，以及 quote/expression 与字节一致；provenance 逐段核哈希与坐标。再从同一 snapshot 重提取，要求 claim/fact 对象全等，然后重新 align+judge，决策与 `fact_ids` 必须仍是 INCONSISTENT。失败写入 `rejected`，不发布 finding。Finding 的 `code_provenance` 复制自当时的 `fact.provenance`。

**报告引用校验。** 读入 `ScanReport` 时检查：事实实体存在、主 span 与 provenance 的 path/hash 落在 snapshot 文件表、finding 的 document/code/provenance/entity/head/files_hash 与引用对象一致。这是结构完整性，不是再跑一遍 verifier。

**旧报告默认字段 vs 重新验证历史判断。** Schema 2.0 可选字段默认空列表。读 1.0 归档报告时补 `provenance`/`code_provenance` 为空，保留原 finding、补丁和标签，测试断言补丁导出仍用原证据。空 provenance 在引用检查中视为“没有额外链”，不会去重算决策。新程序读旧报告；不保证旧程序读新字段。伪造 head 或抽掉导出链会导致校验/重提取失败，与“补默认”不是同一条路径。

**意见。** `valid_provenance` 不把中间导出 span 的源文字面再和 quote 比对（主 span 才比对 quote）。强度来自哈希+坐标重建+全对象重提取。CONSISTENT 判断不做对称重证明；明确一致率依赖的是评测匹配，不是 verifier 对一致结论的二次证明。

---

## 4. `src/docsync/metrics.py`

实际阅读：`evaluate` 计数与四个比率；`tests/unit/test_metrics.py` 的 `test_explicit_consistency_does_not_count_abstention_as_correct`。

**TN 含拒答，明确一致率不含。** 可判定负例（gold=CONSISTENT）上，凡预测不是 INCONSISTENT 都进 TN，包括 UNCERTAIN/SKIPPED。因此历史 TN 不能读成“明确判对”。`explicit_consistency_rate` 分子只有 gold 与预测均为 CONSISTENT，分母是全部 gold=CONSISTENT 行。测试：四行 CONSISTENT gold，预测分别为 CONSISTENT/UNCERTAIN/SKIPPED/INCONSISTENT 时，`tn==3` 且明确一致率 `0.25`。拒答降低覆盖率，不抬明确一致率。

**无冲突正例为什么不能报冲突召回。** `recall = tp / (tp+fn)`。全部 gold 为 CONSISTENT 时 tp=fn=0，比率为 `None`，不写成 0 或 100%。全一致集可以看误报、明确一致、拒答和 `complete_run_rate`，不能证明冲突检出能力。与结项及正式资格结论一致。

**意见。** FAILED 且非确定预测的负例仍进 TN，同时 `failed` 另计；解读时要并列看 `complete_run_rate` 与 `abstention_rate`。`evaluate` 本身不算 usage；费用去重是 runner 的 predictions 归属，不要用 metrics 里的样本数去乘单次扫描请求。

---

## 使用时说明（不要求改代码）

1. 已知用量用 predictions 归属字段汇总，禁止把逐样本 `report.json` 的 usage 相加；预算沿用保守上界，unique_scan_count 只统计已生成并缓存报告的键。异常未返回用量不等于零费用。
2. 声明重叠拒绝不覆盖“无 claim_scope + 不同 repo_id + 同一物理仓库”的旧坐标。
3. 读取旧报告补空 provenance 不等于用新 verifier 重判历史 finding。
4. 当前全一致/无 INCONSISTENT gold 的集合不得填写冲突 recall。

## 仍未关闭

B 既往接触 unknown；正式 test=0；external-10 未决。最终扫描绑定最终 manifest、代码 SHA 与配置之前，不能宣称最终实验。关键词 baseline 保持 SKIPPED。成员 A 若需本人签署，在本记录上另填姓名与日期，不由助手代签。

## 成员 A 本人补充确认

反馈接收日期：2026-10-12。审核人：成员A。用户原话：“本人也已阅读四项并确认无异议”。据此登记上述 1—4 项本人源码阅读完成、未提出修改；实际阅读日期未另行提供，不用接收日期冒充。原 Codex 阅读记录保留其助手身份；本人确认不等于助手代签，也不关闭正式数据、实验和发布门槛。

接收审查补记：源码及 Schema 的八份哈希与本轮 verification.json 一致，无新增代码变化；此次仅修正文档 unique_scan_count 的范围表述，不另行声称用户审过新增代码。签署对应源码哈希和原话见本地 `runs/a-readiness-20261012/human-review.json`。
