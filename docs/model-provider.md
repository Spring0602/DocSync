# 模型适配器

通过 `examples/hybrid.toml` 配置完整 Chat Completions POST 地址、精确模型名和密钥环境变量名。真实服务尚未由团队配置，本轮只执行受控传输故障测试；测试响应不会进入生产 CLI。

```powershell
# 在本地环境中设置 DOCSYNC_API_KEY，不要把密钥写入配置或提交。
.\.venv\Scripts\docsync.exe scan --repo runs/demo-repo --config examples/hybrid.toml --out runs/model-check
```

先把示例中的占位 endpoint/model 改成实际值。适配器默认使用 `json_schema` 严格结构化输出；兼容服务只支持 JSON mode 时可显式设置 `response_format="json_object"`，本地仍进行同样严格的 Pydantic 和 ID 引用验证。模型不支持 `temperature` 时设置 `send_temperature=false`。`token_parameter` 可显式选 `max_completion_tokens` 或旧兼容服务的 `max_tokens`，不会静默切换模型或协议。

hybrid 对规则不能确定或提出冲突的声明调用模型复核；确定一致的支持声明直接保留规则结论。模型可以拒答，确认冲突仍需独立静态 Verifier 通过。无法静态证明的动态默认值、跨版本和歧义实体不会仅凭模型说法发布告警。当前未实现任意自由文本的 AI Claim 提取，模型输入限于已定位声明和候选。

网络防护：HTTPS（本机 localhost 测试服务允许 HTTP）、拒绝 URL 中凭据和查询串、不跟随重定向、不提供工具调用接口、单请求 30 秒默认超时、有限 2 次重试、2MB 响应限制。仅 429、指定 5xx 和网络/超时错误重试；错误 JSON、伪造引用、拒绝或截断直接返回不确定。仓库内容以 JSON 数据传入，不执行其中命令。

预算按**一次 scan**限制请求数和 Token。为避免未知 Tokenizer 或失败请求漏计，发送前采用“请求 UTF-8 字节数 + 输出额度 + 固定开销”作保守预算预留；这不是计费 Token。实际服务返回的 input/output usage 分开记录。失败且未返回 usage 的请求计入 `unknown_usage_requests`，不得把账单成本声明为零。Benchmark 每个样本使用独立 scan 预算；运行大实验前需乘以样本数估算总上限。

可选 `cache_dir` 缓存校验后的结构化判断。缓存键包含端点、模型/参数、提示词版本、Schema 和完整请求内容；输入/版本变化失效。命中单独记录，运行实际调用/Token 不重复计入。缓存含生成的理由文本，可能引用被分析文档，按项目数据政策保管。日志只保存哈希、状态、模型、Token 和耗时，不存 Authorization 或原始请求；若服务错误回显密钥会替换为 `[REDACTED]`。

接口依据：[官方 Structured Outputs 文档](https://developers.openai.com/api/docs/guides/structured-outputs)。结构符合 Schema 不代表语义正确，因此后续仍执行独立证据验证。
