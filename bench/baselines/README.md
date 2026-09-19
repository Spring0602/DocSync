# Baseline 计划

统一入口为 `docsync benchmark --method <方法>`，实现位于 `src/docsync/benchmark.py` 和共享 pipeline。可选 keyword、rules、llm、full、no_alignment、no_verifier、no_static。具体输入/验证边界见 `docs/benchmark.md`；模型未配置时保留 PARTIAL/拒答，不用规则替充纯 LLM 结果。
