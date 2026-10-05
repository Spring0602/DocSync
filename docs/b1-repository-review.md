# 成员 B：包、Schema 与仓库快照审核

日期：2026-09-28。范围：DocSync 0.2.0 的 B1 本地验收。本记录只说明实际执行过的本地检查；不代替 Linux/远程 CI，也不把 Windows 未获授权的真实文件系统符号链接用例写成通过。

## 结论

B1 已完成。包构建和隔离安装成功，安装版 CLI 与模块入口一致；代码生成的 report/benchmark Schema 与仓库文件一致；配置、报告外键、证据关联及仓库快照边界均有自动化回归测试。

本轮收紧了 `FileRecord` 的 Schema：路径必须是安全的仓库相对 POSIX 路径，`blob_hash` 必须是 64 位小写 SHA-256，`size` 不得为负；`ScanReport` 同时拒绝快照中的重复文件路径。两个已提交 JSON Schema 已从代码重新生成。

## 审核矩阵

| 审核项 | 自动化证据 | 结果 |
| --- | --- | --- |
| 包安装与 CLI | `test_installed_and_module_cli_expose_the_same_commands`；最终 wheel 隔离安装；`pip check` | `scan`、`patch`、`apply`、`schema`、`benchmark` 均可用，模块入口与安装入口帮助文本一致 |
| Schema 2.0 | `test_generated_schema_matches_checked_in_contract` | report/benchmark 生成结果与提交文件逐项相同；报告默认版本为 2.0 |
| 未知配置字段 | `test_unknown_configuration_fields_are_rejected_at_every_level`、`test_unknown_config_is_failed_without_echoing_input` | 顶层及 scan/alignment/llm/ignores 内未知字段均拒绝，CLI 不回显配置值 |
| 外键与证据关联 | `test_report_rejects_broken_foreign_keys_and_evidence` | 重复 ID/路径、丢失实体/事实/声明/发现引用及四类证据篡改均拒绝 |
| Git blob 与显式工作树 | `test_commit_snapshot_ignores_dirty_worktree_until_explicitly_selected`、`test_dirty_repo_and_snapshot_determinism` | 默认固定 HEAD blob；只有 `working_tree=True` 才读取未提交内容 |
| base/head 全量回退 | `test_base_records_changes_but_falls_back_to_all_head_blobs`、`test_changed_code_still_checks_unmodified_readme` | changed_paths 记录差异，同时保留并扫描未变化文档，产生 `FULL_SCAN_FALLBACK` 记录 |
| 文件过滤与大小限制 | `test_include_exclude_and_both_size_limits_are_auditable`、`test_bad_base_and_limits` | include/exclude、单文件和总字节上限均有稳定诊断 |
| hash 与 CRLF | `test_commit_snapshot_ignores_dirty_worktree_until_explicitly_selected`、`test_chinese_and_crlf_byte_offsets` | hash 来自原始字节；CRLF 与中文的字节定位及补丁保持正确 |
| 非 UTF-8 | `test_non_utf8_is_diagnostic_and_never_reported_complete` | 文件不进入快照，返回 `UNREADABLE_TEXT`，运行状态为 `PARTIAL`；要求完整时退出码为 3 |
| 符号链接 | `test_commit_symlink_is_skipped_without_os_symlink_privileges`、`test_external_symlink_is_rejected` | Git symlink blob 返回 `SYMLINK_SKIPPED`；补丁路径防护存在；真实 Windows 链接用例因当前权限跳过 |

## 实际执行结果

环境：Windows、Python 3.12.10、Git for Windows 2.55.0.windows.3。Git 使用工作区内便携版本；原始源码目录是 GitHub 下载快照，不含 `.git`，所有仓库行为测试均创建独立临时 Git 仓库并提交固定 fixture。

```powershell
python -m pytest tests/integration/test_b_repository_contracts.py -q
# 31 passed

python -m pytest -q --junitxml=runs/b1-review/pytest.xml
# 143 passed, 1 skipped

ruff check .
# All checks passed

ruff format --check .
# 39 files already formatted

mypy
# Success: no issues found in 20 source files

python -m build --no-isolation
# docsync_core-0.2.0.tar.gz and docsync_core-0.2.0-py3-none-any.whl built
```

最终 wheel 在新建 Python 3.12 环境中离线安装成功，`pip check` 返回 `No broken requirements found`；安装版导出的两个 Schema 与仓库文件 SHA-256 完全相同。wheel/sdist 清单检查未发现 `.env`、`.venv`、`runs` 或 `__pycache__`，wheel 含 CLI 入口，sdist 含测试和 Schema。

唯一跳过项为 `tests/unit/test_patch_guards.py::test_external_symlink_is_rejected`：当前 Windows 进程没有创建真实符号链接的权限。无需该权限的 Git symlink blob 集成测试实际通过，因此提交快照的拒绝路径已有自动化证据；真实文件系统链接仍保留给具备权限的 Windows 环境或 Linux CI 复验。
