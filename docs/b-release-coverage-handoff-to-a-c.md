# B 扩展覆盖收尾交接给 A/C

## 交付内容

- 技术实现提交：`7a16354f0ff1ad4c6ed544cd19a926c867848897`
- 实现与范围报告：`docs/b-release-coverage-review-20261010.md`
- 原始离线证据：`docs/audit-samples/b-release-coverage-20261010/`
- 新增回归：`tests/integration/test_b_release_coverage.py`
- B 本人复核指南：`docs/b-ai-human-review-guide-20261010.md`

## 复验结论请求

请 A/C 在正式最新 `main` 上移植技术提交和随后的审计文档提交后确认：

1. 构造方法和裸字符串文档值的提取没有引入同名实体误对齐。
2. 字面量 tuple/list/dict 展开能正确验证 09—11，运行时展开仍返回 UNCERTAIN。
3. 明确重赋值、数字 `+=`/`-=`、固定 mapping update 和嵌套字典按初始化顺序计算。
4. 环境值、动态 update、函数 `__defaults__` 修改和被重绑定的 `dict` 没有被静默确认。
5. candidate-dev-v1 离线结果为 8 TP、0 FP、11 TN、0 FN；18/19 可判定样本得到明确决定；0/5 INSUFFICIENT 被不当确认。
6. 四个 PARTIAL 均只来自共享仓库的 `case06.py:DYNAMIC_FUNCTION`，不得描述成四次独立运行失败。

复验建议命令：

```powershell
python -m pytest tests/integration/test_b_release_coverage.py tests/integration/test_b_static_facts.py tests/integration/test_static_extensions.py tests/integration/test_pipeline.py -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build --no-isolation
```

## 合并边界

由于 GitHub Git 连接在 B 工作时被重置，本地分支前一提交 `6997ff6` 只是把用户下载的最新 ZIP 接到旧远端历史上，**不要合并或 cherry-pick 该同步基线**。只移植 `7a16354` 和其后的 B 审计文档提交。最终远端 CI 必须对应 A 合并后的真实 main SHA。

B 的技术调查、实现、本地验证和交接已完成。成员 B 已于 2026-10-10 完成本人 AI 人工复核，确认五项内容均无异议，同意进入 A/C 复验；记录见 [复核指南及结果](b-ai-human-review-guide-20261010.md)。A/C 仍需在正式最新 main 上独立复验，不能把 B 的确认代替接收方结论。
