# 2026-10-07 开发评测证据

来源：代码 ac8081d3de60f25b050d3ce6d1d5e7429ffe4f6c；已裁决开发集 seed-dev-v1。分类原始预测与指标同时保存；alignment.json 包含 gold hash、每条目标命中和排除理由。不是独立正式测试成绩。

重跑入口见 ../../../bench/frozen/seed-dev-v1/README.md。实际命令的输出目录为 runs/a-review-20261007/rebuilt、rules、keyword、alignment.json；测试记录 runs/a-review-20261007/targeted.xml。原始目标映射依据 B/C 标注及源码审核确定，未用预测反推 gold。
