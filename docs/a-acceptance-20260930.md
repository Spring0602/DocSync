# A 接收与裁决记录（2026-09-30）

基线：合并提交 `7db2456a1ff955f72eab2504169b17409c5ab4fb`。执行者：成员 A 的 AI 助手；技术裁决基于当前代码及产物，人员签字不由助手代填。用户已明确确认全员同意 Apache-2.0。

## 一、C3 逐项处理结论

| 事项 | 现有证据 | A 的处理结论 | 下一步 |
| --- | --- | --- | --- |
| C 的 20 条标注 | ID 无重复，20 个 head_sha 与重建种子全部一致；reviewer/reviewed_at/label/reason 全空 | 接收为待标注材料，完整标注为 0/20；不能作为第二份金标准 | C 独立填写 20 行并署名，不先看其他标签 |
| B 的独立标注 | 仓库中未收到 individual-B 文件 | 不能进行双人分歧裁决；不以 B1—B3 测试代替标注 | B 按同一 manifest 单独提交 |
| C 的定位预填 | seed-07/08/20 无 document_lines，原表包含“文档[0]”；历史标题和同名实体需要更多上下文 | 不篡改 C 原表；补充固定提交的完整文档/代码材料 | B/C 对照补充材料填写行范围、证据和明确实体 |
| 依赖台账 | C 于 09-29 署名审核直接依赖 8 项、安装依赖 21 项 | 接收已有审核记录，不冒签或覆盖 C 意见 | 分发方式变化时重新核对 LICENSE/NOTICE |
| 原创成果许可证 | 用户本轮回复“已全员确认采用 Apache-2.0” | 同意落地；已替换 LICENSE、更新包元数据和 data_rights | 原始附件继续排除，第三方许可证不变 |
| AI 使用日志 | C 已填历史提交；human_reviewer/human_changes 仍 pending | 接收机器日志，不认定已完成人工复核 | 当时使用 AI 的成员按真实经历填写审核及修改说明 |
| 第二设备和匿名化 | 未收到覆盖最终发行材料的记录 | 不通过最终发布验收 | C 保存第二设备命令、版本、结果和逐项匿名化记录 |

逐样本检查见 [annotation-readiness.csv](audit-samples/a-20260930/annotation-readiness.csv)，补充材料见 [固定提交原文](audit-samples/a-20260930/annotation-context.md)。保留原表 hash、manifest hash 和本轮指标于 [review-summary.json](audit-samples/a-20260930/review-summary.json)。

**数据裁决：保持 provisional/dev，不改 adjudicated、不冻结正式测试集。** 这是明确的不满足冻结条件结论，不是用自动审核替代两人的判断。

## 二、C1/C2 争议处理

- C1 英文句式缺口：接受缺陷报告，“The default value of X is Y” 不在当前覆盖范围。先补 limitations；由 B/C 补实现及正反例回归后再申请关闭。A 本轮不修改静态扫描逻辑。
- 忽略到期日：接受报告展示缺口。到期日参与匹配不等于报告存有该字段，不声明已满足完整展示要求。
- C2 S6 的超时证据：当前 Provider 初始化即拒绝非本地 HTTP，使用其记录的 `http://10.255.255.1:9999` 实测得到 `UNSAFE_MODEL_ENDPOINT`，请求数 0。该场景仅支持“不安全地址拒绝/部分扫描”结论，不能证明网络超时。原记录保留，本文为复核更正；真正超时路径由现有受控 transport 测试覆盖，仍不冒充线上服务实验。
- C 的历史 symlink 失败：记录为该设备待复现问题。合并版本机 180 passed/1 skipped，远程 Core CI 双平台成功；不能凭本机跳过宣布所有坏链接环境问题已解决。
- Core CI 与 Documentation consistency 是不同工作流。已核验前者，不把它写成后者已实跑。

## 三、A3 当前可完成的评测

在同一重建 manifest 上分别运行 rules 和 keyword，全部 20 样本，失败/部分完成均为 0：

| 方法 | TP | FP | TN | FN | 拒答 | 证据不足样本 | 不当确认 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rules | 11 | 0 | 5 | 0 | 4 | 4 | 0 |
| keyword | 4 | 1 | 4 | 7 | 10 | 4 | 3 |

以上为自建开发样本、临时标签下的流程验证，不是正式准确率或泛化结论。拒答包括证据不足样本；证据不足不进入 TP/FP/TN/FN。逐样本预测已保存，可由指标脚本重算。分类 recall 不能当成 Recall@K：人工目标实体映射及候选命中评估仍待完成。

重跑命令（输出目录需使用新名称）：

```powershell
.\.venv\Scripts\python.exe bench/builders/build_seed.py --out runs/a-review-20260930/seed
.\.venv\Scripts\python.exe -m docsync benchmark --manifest runs/a-review-20260930/seed/manifest.jsonl --method rules --out runs/a-review-20260930/rules
.\.venv\Scripts\python.exe -m docsync benchmark --manifest runs/a-review-20260930/seed/manifest.jsonl --method keyword --out runs/a-review-20260930/keyword
```

## 四、A4 四类验收状态

| 类别 | 结论及证据 |
| --- | --- |
| 本地 | 合并时全量 180 passed/1 skipped；本轮契约/指标/模型故障专项另见 verification；带许可证的 wheel/sdist 构建成功，wheel 的 License-Expression 和 LICENSE 原文核对通过 |
| 真实模型 | 未配置，未完成 A2，不运行或伪造正式 Full/LLM/消融实验 |
| 远程 CI | 合并 SHA 的 [Core CI 36683440902](https://github.com/Spring0602/DocSync/actions/runs/36683440902) 已核验 success；Windows/Linux 两个作业的安装、测试、Ruff、mypy、build 均 success；仅针对该 SHA |
| 人工 | 已取得用户转达的团队 Apache-2.0 同意；C 依赖台账已有署名；独立标注、AI 人工复核和最终材料审核仍未齐全 |

Action 消费示例已固定到上述完整合并 SHA，作为经验证的开发版本；这不是发布 tag。A1 技术核对可接受，A3 完成接收审计及开发基线部分，A4 完成当前证据汇总；A2 和最终发布验收继续保留阻塞。
