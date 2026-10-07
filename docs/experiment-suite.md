# 统一实验操作说明

> 最新状态：七方法开发集真实实验已验收，85 次调用成功；[指标及差异分析](deepseek-suite-20261007.md)。后文准备步骤与历史待办保留作复现参考；当前待办以 tasks.md 为准。


当前数据 seed-dev-v1 是 20 例已裁决开发集，不能用于宣称独立测试效果。A-N1 小样本技术验证已通过；本步骤完成 A-N3 开发集方法比较。

在项目根目录、已设置 DOCSYNC_API_KEY 的 PowerShell 中运行。密钥不写入命令文件。若在新 clone 中操作，先按 README 安装项目，再重建固定数据：

```powershell
.\.venv\Scripts\python.exe bench/builders/build_reviewed_seed.py --out runs/a-review-20261007/rebuilt
```

现有目录已重建时跳过上述步骤。先只查看计划（不发起网络请求）：

```powershell
.\.venv\Scripts\python.exe -m bench.run_suite --manifest runs/a-review-20261007/rebuilt/manifest.jsonl --config examples/deepseek.toml
```

确认计划包含 20 个样本、7 个方法、request_upper_bound=100 后执行：

```powershell
$trial = "runs/deepseek-suite-" + (Get-Date -Format "yyyyMMdd-HHmmss")
.\.venv\Scripts\python.exe -m bench.run_suite --manifest runs/a-review-20261007/rebuilt/manifest.jsonl --config examples/deepseek.toml --out "$trial" --max-requests 100 --run
```

keyword/rules 不调用模型；其余五方法每个样本至多 1 次、不重试。总上限 100 次，实际可能更少。输出 Token 配置额度最多 204800，不是实际用量，也不是金额上限。输入用量和未知失败费用需结合账单核对。不要在运行中编辑源代码、配置或样本。

运行器核对已安装包与源码一致；若报版本不一致，先执行 `python -m pip install --no-deps --no-build-isolation .`（使用本项目虚拟环境解释器）。会保存提交 SHA、源码哈希、dirty 状态、manifest 与有效配置。正式对比应在已提交的固定版本运行。

输出包含 suite.json、comparison.md，以及各方法 predictions.jsonl、metrics.json 和逐样本报告。指标从预测重算核对；review_items 列出标签不符及非完整扫描。COMPLETED 仅表示流程完成，不代表全判对。退出 3 表示非完整结果；退出 2 表示校验或执行异常，先检查证据。INTERRUPTED 保留已完成方法；进程强制终止可能留下 RUNNING。暂不支持续跑，不要不查原因就重跑整个付费批次，也不要覆盖旧目录。

A 收到结果后逐项解释误报、漏报、拒答及用量；特别复核别名实体和动态值的解释。Recall@K 按 [评测说明](benchmark.md)另行计算，不能与分类 recall 混称。llm/no_static 仍受既定声明和候选范围限制，不是全文端到端模型基线。

离线验收已保存到 runs/a-suite-offline-20261007：rules、keyword 各 20 例完整结束，模型请求为 0。此记录不替代上述五种模型方法，也不证明新独立测试集表现。
