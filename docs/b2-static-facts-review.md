# 成员 B：静态事实扩展与验证

日期：2026-09-28。范围：DocSync 0.2.0 的 B2 本地验收。本记录核对静态事实的类型、参数绑定、接收者、配置、来源和稳定身份，并明确支持与拒答边界；不执行或导入目标项目。

## 结论

B2 已完成。新增的专项测试先锁定继承/元类、动态字典键、重复定义和不安全导出的拒答行为，再验证有限且可证明的直接重导出、参数及接收者、字典覆盖顺序、事实溯源和稳定 ID。复杂运行时语义不会被静默简化为 `CONSISTENT`。

本轮修复四个保守性缺口：

1. 带基类或元类的类方法现在标记为 `UNKNOWN`，避免忽略类创建阶段的运行时改写。
2. 动态字典键位于显式键之后时，之前的显式键标记为 `UNKNOWN`，因为运行时键可能覆盖它。
3. 同一作用域中的重复函数/类定义视为重绑定，相应默认值及签名不再作为确定事实。
4. `KNOWN` 使用 `value is not None` 判定，明确保留 `None`、`False`、`0`、空字符串和空容器等合法字面量。

新增的安全能力仅限模块顶层、唯一绑定的 `from module import name [as alias]`。支持直接、链式、相对导入和包 `__init__.py` 重导出；别名事实仍指向原始实体、源码 span 和 blob hash。星号导入、条件导入、缺失模块或任何重绑定都不生成别名事实。

## 审核矩阵

| 审核项 | 自动化证据 | 结果 |
| --- | --- | --- |
| 默认值及递归类型 | `test_defaults_distinguish_types_none_absent_and_unknown`、既有 `test_literals_retain_nested_types` | bool/int/float/str/list 等类型分离；`False` 不等于 `0` |
| `None`、缺失和 `UNKNOWN` | `test_defaults_distinguish_types_none_absent_and_unknown`、`test_all_parameter_kinds_and_none` | `None` 为 KNOWN/NoneType；无默认值为 ABSENT；动态工厂为 UNKNOWN |
| 调用参数绑定 | 既有 `test_argument_binding`、`test_dynamic_call_unpacking_is_never_simplified_to_a_valid_call` | positional-only、keyword-only、重复绑定、`*args`/`**kwargs` 接口可判定；调用侧动态解包拒答 |
| 接收者 | `test_receivers_and_parameter_kinds_are_preserved`、既有 `test_method_receivers` | instance/class/none 分离；classmethod、staticmethod 与实例方法绑定正确 |
| 顶层常量与字典 | `test_explicit_dict_key_after_dynamic_entries_is_known`、`test_dynamic_dict_key_after_explicit_key_is_unknown`、既有配置测试 | 字面量可确认；显式键位于动态项之后可安全覆盖；反向顺序、重复键、后续 update 和动态值拒答 |
| 装饰器及继承 | `test_inheritance_and_metaclasses_make_method_facts_unknown`、动态边界参数测试、既有 method 测试 | 仅无装饰器、staticmethod、classmethod 的简单无继承类方法可确定；其他情况 UNKNOWN |
| 重绑定 | `test_duplicate_function_definition_is_a_rebinding_boundary`、动态边界参数测试、既有别名顺序测试 | 赋值、删除、重复定义及调用示例别名重绑定均不会沿用旧事实 |
| 跨文件导出 | `test_safe_direct_and_chained_exports_keep_original_evidence`、`test_safe_relative_export_is_supported`、`test_package_init_export_uses_public_package_name`、不安全导出参数测试 | 唯一顶层直接/链式/相对重导出受支持；星号和重绑定导出拒答 |
| 歧义 | `test_same_named_symbols_remain_ambiguous`、既有 top-K 测试 | 多个同名事实不会因排序或截断变成确定结论 |
| 证据溯源 | `test_fact_provenance_points_back_to_the_exact_blob`、重导出证据测试 | 每条事实保留路径、行号、原始字节区间、实体 ID 和 SHA-256；字节切片可还原 expression |
| 稳定 ID | `test_fact_ids_are_stable_across_repeated_scans_and_unrelated_commits` | 重复扫描及只修改文档的新提交不会改变未变代码事实的 ID 和定位 |

## 实际执行结果

环境：Windows、Python 3.12.10、Git for Windows 2.55.0.windows.3。测试使用独立临时 Git 仓库和固定提交，不读取工作区未提交内容。

```powershell
python -m pytest tests/integration/test_b_static_facts.py -q
# 22 passed

python -m pytest tests/integration/test_b_static_facts.py `
  tests/integration/test_static_extensions.py tests/integration/test_pipeline.py -q
# 78 passed

python -m pytest -q --junitxml=runs/b2-review/pytest.xml
# 165 passed, 1 skipped

ruff check .
# All checks passed

ruff format --check .
# 40 files already formatted

mypy
# Success: no issues found in 20 source files
```

全量回归唯一跳过仍是当前 Windows 进程无权创建真实文件系统符号链接，与 B2 静态事实逻辑无关。JUnit 证据位于 `runs/b2-review/pytest.xml`。

## 保留边界

- 不支持星号导出、条件导出、运行时 `__getattr__`、猴子补丁、继承解析、元类和复杂对象别名。
- 后续任意 `dict.update`、下标赋值/删除或无法证明顺序的配置修改仍整体保守为 `UNKNOWN`。
- 动态默认值和动态调用不会执行；没有候选、歧义或证据不足返回 `UNCERTAIN`，而不是“一致”。
- 别名事实的 `subject` 是公开导出名，`entity_id`、源码 span 和 hash 始终属于原始定义，便于回到固定 blob 审核。
