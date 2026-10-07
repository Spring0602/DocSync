# A 本轮执行与接收（2026-10-07）

代码基线 ac8081d3de60f25b050d3ce6d1d5e7429ffe4f6c。本次由 A 委托助手进行技术复核；不代签 AI 日志或虚构人工审核过程。

## 已完成

- 两份标注均为 20 行，必填身份/时间/标签/理由/证据完整，sample_id 不重复，head_sha 与重建固定提交一致。20/20 标签一致，逐条理由与源码语义相符。
- 完成逐项技术裁决并冻结 [seed-dev-v1](../bench/frozen/seed-dev-v1/README.md)，明确仅为开发集。A 的技术复核身份在每行披露，B/C 原始标注不覆盖。
- 增加重建脚本并实际重建通过；源标注、标签、类型、路径、提交、分组和 split 可核对。所有样本维持 dev，未泄漏为 test。
- 完成候选 Recall@K 工具和反例测试；在 16 个预先限定的可判定样本上 Recall@1/3/5 均为 1.0，4 个证据不足样本按理由排除。不得将它表述为全体样本/正式测试召回。
- rules 和 keyword 各重跑 20 个已裁决开发样本，无 FAILED/PARTIAL；rules TP/FP/TN/FN=11/0/5/0、拒答4；keyword=4/1/4/7、拒答10、证据不足不当确认3。分类型及逐样本结果见 [证据目录](audit-samples/a-20261007/README.md)。
- 本轮专项 40 passed，覆盖新增指标、既有分类指标、A 契约、英文句式和忽略到期日；Ruff 检查及 46 文件格式检查通过。不是新全量测试数。

## B/C 交付接收

| 任务 | 接收结论 |
| --- | --- |
| B-N1/C-N1 | 两份标注已收到、逐项技术裁决完毕；无需重新标这 20 个开发样本 |
| B-N2/C-N2 英文句式 | 合并代码、专项回归和 C 确认齐全，D-1 关闭 |
| B-N3/C-N2 到期日 | 继续 Schema 2.0 的决策已执行；可选 ignore_expires、旧报告读取及渲染测试通过，接收 |
| B-N3 路径防护 | 合并已有守卫修复和测试；本机权限导致 2 个 symlink 用例跳过的限制保留，不宣称本机全部执行 |
| C-N3 | 真实 Documentation consistency 运行及工件已核验；受控超时证据与真实调用分开 |
| C-N4 | 接收团队认可的同机 fresh clone + fresh venv 独立复现；不要求另买/另找物理设备。最终材料仍需复查 |

## 远程证据

- 最新合并版 [Core CI 37582511244](https://github.com/Spring0602/DocSync/actions/runs/37582511244)：completed/success，SHA ac8081d3de60f25b050d3ce6d1d5e7429ffe4f6c。只覆盖该提交，不覆盖本轮未提交的指标工具。
- [Documentation consistency 37421932006](https://github.com/Spring0602/DocSync/actions/runs/37421932006)：completed/success，SHA 3f694ff19828945ac8a25a21ddc62ea4549b8944；docsync-evidence 工件存在且未过期。扫描 summary 按 C 的原记录为 PARTIAL、0 confirmed、1 uncertain；工作流成功不等于扫描完整或没有问题。

## A 剩余事项

1. DeepSeek 单例及 5 例试运行已通过，统一七方法运行器已完成。A 在持有密钥的终端按 experiment-suite.md 运行剩余模型方法，并按 model-cost-ledger-20261007.md 核对费用。
2. 正式独立测试集仍未收集和冻结；开发集版本完成不替代此项。A 确定样本范围与组划分，B/C 按需补新数据双标。
3. AI 日志 human_reviewer/human_changes 需实际成员补充，助手不代填。
4. 最终提交/tag、真实实验与材料一致性、匿名化和链接由 A/C 收尾。原始 B 标注带真实审核人姓名，不为掩盖历史而改写；面向匿名评审的导出材料须改用 B/C 标识并按要求复核，不声称整个当前仓库完全匿名。

A-N2 的开发集裁决、版本固定和指标工具部分完成；A-N1 小样本技术部分完成，费用核对、A-N3 模型批量实验、正式测试集及 A-N4 最终发布验收仍未完成。
