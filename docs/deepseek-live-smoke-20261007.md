# DeepSeek 首次真实调用验证（2026-10-07）

用户在持有密钥的本机终端执行，助手仅核验生成的报告，未接收或保存新密钥。

- 运行：runs/deepseek-retry-20261007-151326。
- 模型：deepseek-flash，服务实际返回名称相同；非思考模式，json_object，max_tokens=2048，单次请求、无重试。
- 状态：COMPLETED；模型调用 SUCCEEDED；requests=1，cache_hits=0。
- 实际用量：输入 1032、输出 133，共 1165 Token；unknown_usage_requests=0。
- 模型请求耗时约 5.77 秒，整个扫描约 6.06 秒。
- 模型确认默认值 30 与代码 60 冲突，独立 Verifier 通过，发布 1 条 Finding；补丁为 VALIDATED，但本次未应用。
- 合法显式调用由规则判定一致，未调用模型。因此不能将本次写成两个模型样本或多类别模型效果验证。

本次仅完成 A-N1 的连通性、结构化响应与单条冲突试运行。3—5 个已标注样本、证据不足边界、Full/LLM/消融、费用对账及正式实验仍未完成。

证据见 [脱敏摘要](audit-samples/deepseek-smoke-20261007/summary.json) 与同目录配置。调用时基于 ac8081d 的未提交修改，摘要保留关键代码 hash；不能只用该提交 SHA 代表实际运行代码。manifest.model.temperature 显示配置默认值 0，但 send_temperature=false，实际请求未发送 temperature。

上一轮 runs/deepseek-20261007-150519/result 在约 124.83 秒后超时/网络失败，unknown_usage_requests=1。失败记录保留；本轮成功不抹去前次失败，也不能证明其费用为零。两次差异包含禁用思考模式和降低输出上限，不能单凭此断言之前失败的唯一原因。
