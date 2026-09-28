# 成员 B：对齐、规则与补丁回归

日期：2026-09-28。范围：DocSync 0.2.0 的 B3 本地验收。本记录核对确定性对齐、三类规则证据、补丁预览/应用/复扫及篡改拒绝；补丁仍需人工审阅后显式应用。

## 结论

B3 已完成。精确符号、参数归属、import 别名、源码链接、截断前歧义和重复调用稳定性均有直接测试；默认值与配置规则只修改目标值，应用后通过工作树复扫证明冲突消失；签名规则只报告证据和人工处理提示，不生成或猜测必选参数。

本轮修复两个补丁校验缺口：

1. `edited_blobs` 现在根据当前 blob 重新计算 canonical `SourceSpan`，行号与字节区间不一致的伪造编辑会返回冲突。
2. `apply_patch` 现在要求非空且不重复的 finding ID，并重新计算确定性 `patch_id`；伪造、空或重复 ID 在写文件前拒绝。

签名 Finding 的 Markdown 报告新增明确提示：“签名问题不自动生成参数值”，要求用户根据文档和代码证据人工修正调用示例。

## 审核矩阵

| 审核项 | 自动化证据 | 结果 |
| --- | --- | --- |
| 精确符号与参数归属 | `test_exact_symbol_and_parameter_owner_win_over_suffix_matches` | 完整符号优先于后缀同名项；候选事实的参数和源码归属一致 |
| import 别名 | `test_import_alias_keeps_signature_parameter_ownership`、既有别名顺序/重绑定测试 | 简单 import alias 解析到原实体；顺序变化和重绑定不会沿用旧别名 |
| 源码链接 | `test_source_link_resolves_name_collision_and_top_k_never_hides_ambiguity` | 唯一 `.py` 链接消解同名项，并在候选特征中记录 `link_match` |
| top-K 歧义 | 同上、既有 `test_ambiguous_names_not_resolved_by_top_one` | 先计算全部候选歧义再截断；`top_k=1` 不会制造确定结论 |
| 重复调用稳定性 | `test_repeated_calls_have_distinct_but_repeatable_claim_and_finding_ids` | 同一围栏中的重复调用 ID 互不碰撞，重复扫描 ID 和顺序稳定 |
| 默认值/配置最小补丁 | `test_default_and_config_patches_are_minimal_and_proven_by_rescan` | 只替换 Markdown 中目标值；代码 blob 和其余文档字节不变 |
| 预览、hash 与复扫 | 同上、既有 patch CLI/CRLF/同一行多编辑测试 | diff 与 manifest 一致；base hash 绑定原文；内存及工作树复扫均证明目标冲突消失且无新增冲突 |
| 原子写入与回滚 | 既有 `test_multifile_apply_rolls_back_when_later_write_fails` | 临时文件 fsync 后原子替换；后续文件失败时已写文件逆序恢复 |
| 重复应用 | `test_patch_cannot_be_applied_twice` | 首次成功，第二次因 preimage/hash 变化返回 `STALE_PATCH`，文件不再变化 |
| 篡改拒绝 | `test_apply_rejects_tampered_patch_metadata_without_writing`、既有 overlap/伪造证据测试 | patch ID、空/重复 finding ID、行号、diff、base hash、old text、重叠区间、伪造证据全部在写入前拒绝 |
| 签名人工处理 | `test_signature_rule_emits_evidence_and_manual_guidance_without_patch` | 保留 VERIFIED 文档/代码证据，不生成 PatchProposal，报告含人工处理提示 |
| 三类规则样例 | [`audit-samples/b3`](audit-samples/b3/README.md) | DEFAULT_VALUE、CONFIG、SIGNATURE 各有固定提交的完整 JSON/Markdown 报告 |

## 可审计规则样例

- [`DEFAULT_VALUE/1`](audit-samples/b3/default/report.md)：文档默认值 30、代码默认值 60；保留 `fix.patch` 和 `patch.json`。
- [`CONFIG/1`](audit-samples/b3/config/report.md)：文档配置值 30、代码配置值 60；保留 `fix.patch` 和 `patch.json`。
- [`SIGNATURE/1`](audit-samples/b3/signature/report.md)：调用缺少必选参数；无自动补丁，保留 VERIFIED 证据和人工提示。

每个样例目录同时保存 `report.json`、manifest、snapshot、entities/facts/claims/candidates/judgments/findings JSONL 和 summary，能够从 Finding 追溯到固定提交、原始 blob hash、字节区间和规则 ID。

## 实际执行结果

环境：Windows、Python 3.12.10、Git for Windows 2.55.0.windows.3。规则样例来自三个本项目自建的固定 Git fixture，不含第三方数据或模型响应。

```powershell
python -m pytest tests/integration/test_b_alignment_patches.py -q
# 15 passed

python -m pytest tests/integration/test_b_alignment_patches.py `
  tests/integration/test_pipeline.py tests/integration/test_static_extensions.py `
  tests/unit/test_patch_guards.py tests/integration/test_a_contract_review.py -q
# 90 passed, 1 skipped

python -m pytest -q --junitxml=runs/b3-review/pytest.xml
# 180 passed, 1 skipped

ruff check .
# All checks passed

ruff format --check .
# 44 files already formatted

mypy
# Success: no issues found in 20 source files
```

全量回归唯一跳过仍是当前 Windows 进程无权创建真实文件系统符号链接；Git symlink、安全路径及补丁逻辑的其他测试均通过。JUnit 证据位于 `runs/b3-review/pytest.xml`。

## 保留边界

- 补丁 ID 是一致性校验，不是数字签名；补丁必须来自已审核报告，并与导出的 manifest/diff 成对使用。
- 自动补丁仅用于已验证且未忽略的 DEFAULT_VALUE/CONFIG 文档值；SIGNATURE 始终交给人工决定参数或示例如何修改。
- 原子替换与异常回滚不是掉电安全的跨文件事务，也不支持与编辑器并发写入；apply 前后仍需保留版本控制和人工审阅。
