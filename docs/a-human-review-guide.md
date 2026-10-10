# 成员A：人工复核怎么做

本轮成员A已提交指南五项的复核反馈，接收日期为 2026-10-10；实际审核日期原回复留空，未代填。完成范围如下：

| 项目 | 已记录范围 | 证据 |
| --- | --- | --- |
| 1 核心流程 | 本人演示，冲突 1→0，仅文档默认说明修改 | [流程](audit-samples/billing-review-20261010/core-flow-review/review.json) |
| 2 关键代码 | CLI；模型密钥/预算/响应/重试/未知用量；补丁路径、原文和 manifest 检查 | [CLI](audit-samples/billing-review-20261010/cli-review.json)、[模型](audit-samples/billing-review-20261010/provider-review.json)、[补丁](audit-samples/billing-review-20261010/patch-review.json) |
| 3 报告 | 结论与披露口径；rules 的 03/01/05 三条预测抽查 | [报告](audit-samples/billing-review-20261010/report-review.json) |
| 4 标注 | 05/06/07/13/19 五条；B/C 原表保留；标签一致不等于独立盲测 | [标注](audit-samples/billing-review-20261010/annotation-review.json) |
| 5 发布相关 | 授权范围、0.0824961 CNY 汇总账单及逐请求证据限制、未完成发布条件 | [许可/账单/发布](audit-samples/billing-review-20261010/license-billing-release-review.json) |

边界：补丁并发保护的“写入前检查、无写后检查或全程锁”是助手纠正，未代填用户确认。三条预测和五条标注不扩大为全量审核；11 条历史 AI 台账尚未统一签署，保留各记录实际覆盖范围。当前已有真实模型开发实验，待办是新独立正式测试集及其冻结后实验、其他人工复核缺项、最终材料和发布 SHA/CI/tag 一致性。

下一步见 [历史补审指南](a-historical-review-guide.md)：11 条日志已逐行映射为 11 条均已有指定范围复核记录（不等于全量签署），不重复已有检查。

## 1. 先亲自确认核心流程

在 G:\DocSync 的 PowerShell 运行下面的规则演示，不需要 API Key，也不会产生模型费用。只会修改新建的 runs 演示目录。

```powershell
cd G:\DocSync
$review = "runs/a-human-" + (Get-Date -Format "yyyyMMdd-HHmmss")
.\.venv\Scripts\python.exe scripts/create_demo.py --out "$review/repo"
.\.venv\Scripts\python.exe -m docsync scan --repo "$review/repo" --mode rules --out "$review/before"
.\.venv\Scripts\python.exe -m docsync patch --report "$review/before/report.json" --out "$review/fix.patch"
```

亲自打开生成的 before/report.md、fix.patch、repo/README.md 和 repo/src/client.py。你要确认：源码 timeout 默认值 60，文档默认说明 30；报告只有 1 条默认值冲突；合法 connect(timeout=30) 示例不应被改。此时源码和 README 应没有被 scan/patch 修改。

看过 diff 后再执行：

```powershell
.\.venv\Scripts\python.exe -m docsync apply --repo "$review/repo" --patch "$review/fix.patch" --manifest "$review/fix.patch.json"
.\.venv\Scripts\python.exe -m docsync scan --repo "$review/repo" --working-tree --mode rules --out "$review/after"
git -C "$review/repo" diff -- README.md src/client.py
```

确认 after 中冲突数为 0，git diff 只显示文档说明 30→60，源码未改。这一项可记录为“本人复核核心运行流程”，不代表已审全部安全代码。保留目录路径和看到的结果。

## 2. 看三处关键代码，每处回答一个问题

| 打开的代码位置 | 先看什么 | 你要能说明的事 |
| --- | --- | --- |
| [cli.py](../src/docsync/cli.py) 的 parser、exit_code、main | scan / patch / apply 分支及退出码 | 为什么扫描不会自动应用补丁？退出 0 是否等于没有问题？ |
| [provider.py](../src/docsync/llm/provider.py) 的初始化和 _request | 环境变量取密钥、max_requests 判断、响应校验、未知用量处理 | 密钥从哪来？预算用完和服务超时会发生什么？不会凭空生成成功结果的依据在哪里？ |
| [patches/__init__.py](../src/docsync/patches/__init__.py) 的 safe_target、apply_patch | Markdown 限制、路径边界、原文/哈希检查 | 为什么补丁不能随便改源码、越界文件或已变更的文档？ |

不用先逐行读所有实现。用编辑器搜索上述函数名定位；先读条件分支和抛出的错误，再对照自己的演示。确实理解的检查点写到审核意见；不理解的条件发给我解释，保留该项待审。

可辅助跑下列已有测试，再打开对应测试阅读输入和断言；命令通过只算测试结果，不能自动代表你理解了全部代码：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_provider.py tests/unit/test_patch_guards.py tests/unit/test_contracts.py -q
```

Windows 符号链接权限不足的跳过项应如实记录，不强行写全部场景通过。不需要重新运行付费模型实验。

补丁复核记录见 [patch-review.json](audit-samples/billing-review-20261010/patch-review.json)。助手纠正：实现是在整体应用前、每个文件写入前检查，未在写入后复核，也没有覆盖检查至替换期间的文件锁。因此不能宣称能发现所有并发修改；此纠正单独记录，未代填用户确认。

## 3. 复核报告是否夸大效果

读 [七方法实测](deepseek-suite-20261007.md) 和 [扩展集收尾](a-closeout-20261010.md)。逐一确认：旧集 Full 与 rules 结果一致，不能据此宣称 AI 更强；扩展集 rules 只有 3/8 冲突被检出，且有 4 次 PARTIAL；TN 中包含一致样本的拒答，不能全部当成明确判对。

打开证据目录里的 predictions.jsonl，至少选一条冲突、一条拒答、一条 PARTIAL 与报告核对。记录你实际抽查的 sample_id 和发现的问题。只抽查了三条就写“三条抽查”，不要写“全部原始结果逐条审核”。

## 4. 复核标注与独立性决定

读 [24 条裁决摘要](../bench/frozen/candidate-dev-v1/adjudication.md)，对照 [带行号原文](../bench/annotations/candidate-v1/context.md)。建议先检查 05（定义时默认值绑定）、06（显式修改默认值）、07（环境变量）、13（classmethod）、19（环境分支），再按需要补完剩余条目。

看 B/C 原表是否被保留，最终标签是否有理由，5 条 INSUFFICIENT 是否没有因“fallback”被擅自改成一致。阅读 group-review.jsonl，理解为什么六组保留 dev：AI 辅助和旧材料接触已披露，不能冒充独立盲测。若只审核部分条目，明确列出，不签整批。

## 5. 最后核对许可和账单

读 [授权范围](license-scope.md)、[发布清单](release-checklist.md) 和 [账单核对](provider-bill-reconciliation-20261010.md)。确认原创材料授权与外部竞赛文件范围；知道目前没有独立正式测试集和最终发布 tag。你已确认账单 91 次请求均属于 DocSync，该确认已作为账单归属依据，不等于代码复核。

## 审完怎么回复

不要先填“全通过”。每次可只交一部分，按以下空白格式填写真实事实：

```text
审核人：成员A
实际审核日期：
完成项（1—5）：
查看的文件/函数/样本：
亲自执行的命令与产物目录（如有）：
实际看到的结果：
发现的问题或修改：
仍没看懂/未审核的部分：
```

收到后我按具体范围写回人工台账：流程测试、代码审查、报告抽查分开。若未修改，就在确实检查后写“该范围未发现需修改项”；不是由助手默认生成。11 条原台账的逐条映射见 [原复核入口](billing-and-human-review-20261010.md)，未覆盖的行继续 pending。
