# candidate-dev-v1：已技术裁决的扩展开发集

2026-10-09 完成逐项技术裁决，2026-10-10 收尾验收。24 条样本来自 6 个受控仓库组：11 CONSISTENT、8 INCONSISTENT、5 INSUFFICIENT。B/C 的 24 条标签一致；统一了 16 处实体写法、7 处源码范围、8 处文档范围差异，原始表不改动。

adjudication.jsonl 每行保留 B/C 原始记录、最终标签、统一实体/属性、源码与文档证据、判定理由及代理身份。目标统一为模块限定实体，参数或键单列 property；文档证据不包含围栏标记，但 manifest 中签名类 claim_line=5 对应提取器围栏起始行。其余明确声明也在第 5 行。证据范围与 claim_line 用途不同，不要求相同。

语义口径：判断固定模块正常初始化后的 API 和配置；函数默认值在定义时绑定，显式 __defaults__ 修改与配置后续赋值必须考虑；默认参数 None 不等于函数体中的替换值。完整源码能推出的纯常量辅助函数/字面量展开可技术判定，不因当前提取器不支持而改为证据不足。环境或外部输入未确定时，fallback 不是保证值，07/12/16/19/23 保持 INSUFFICIENT。仅阅读源码推理，未导入/执行目标代码。

## 数据性质与边界

全部 split=dev，annotation_status=adjudicated 表示已完成披露身份的技术裁决，不表示 A 本人人工签字。human_signoff=pending。团队原创代码/自建样本 Apache-2.0 决定沿用现有授权，不代签人工 AI 审核。

六组均排除出独立正式 test，逐组依据见 group-review.jsonl：作者已接触旧开发集/实验结果，B 披露 AI 辅助及旧模板接触，且各组与旧默认值、签名、配置家族有联系；现有证据不足以宣称独立盲测。不是对 B/C 标签工作的否定，也不应为满足预设数量重新换组名。原候选包继续保留，原文与 SHA 未变；这份新冻结版本记录裁决结果。

## 重建与验证

freeze.json 记录原始来源的 LF 归一化 SHA-256 和三个裁决产物的原始字节哈希。修改源表、原文或标签必须另建版本。

```powershell
.\.venv\Scripts\python.exe -m bench.builders.build_reviewed_candidates --out runs/candidate-dev-rebuilt-new
.\.venv\Scripts\python.exe -m bench.run_suite --manifest runs/candidate-dev-rebuilt-new/manifest.jsonl --config examples/deepseek.toml --methods rules keyword --max-requests 0 --out runs/candidate-dev-offline-new --run
```

同组仓库包含 4 对样本文件，每次 scan 会读取整个仓库；PARTIAL 可能来自同组其他文件。模型每扫描最多 1 次的旧 DeepSeek 配置不适合直接宣称覆盖这批所有目标声明。未来模型实验应先明确文档范围/预算，不直接复用旧付费批次命令。当前只执行两种离线基线。

扩展集未建立与当前提取器 Fact 完全对应的独立 Recall@K gold，尤其动态值和复杂配置；不得复制旧 16/16 候选召回数到本集。这里的实体与证据坐标是人工表裁决结果，不伪造提取器事实 ID。

验收与离线失败分析见 docs/a-closeout-20261010.md。
