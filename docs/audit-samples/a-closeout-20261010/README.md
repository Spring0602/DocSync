# A 收尾验收证据（2026-10-10）

suite.json、comparison.md 和各方法原始文件来自 runs/candidate-dev-offline-20261009；rules 保留 24 份报告与调用 manifest。输入为 candidate-dev-v1（24 个扩展开发样本），不与旧 seed-dev-v1 成绩混合。suite 状态 PARTIAL 是如实保留的扫描结果，不是单元测试失败。API 请求为 0。

validation.json 记录本轮实际 217 passed / 2 skipped，remote-ci.json 仅记录已推送的 0465c93。输入 manifest 的相对 repos 路径属于原运行目录；需用重建脚本得到真实仓库后才能再次扫描。裁决和冻结 hash 见 bench/frozen/candidate-dev-v1。
