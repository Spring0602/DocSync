# 七方法实验归档

来源 runs/deepseek-suite-20261007-222034；详细解释见 [验收报告](../../deepseek-suite-20261007.md)。suite.json 保留原始提交、dirty 状态和源码哈希；audit.json 保存逐报告文件 SHA-256 与调用用量核对。各方法含 predictions.jsonl、metrics.json；除 keyword 无逐样本扫描报告外，其他方法保留各样本 manifest.json/report.json。full-alignment.json 为本轮额外重算的候选指标。

input-manifest.jsonl 中相对仓库路径属于原运行目录，归档本身不能直接重跑；先用 bench/builders/build_reviewed_seed.py 重建固定数据，再按 docs/experiment-suite.md 运行。此为开发集证据，不是独立测试集。
