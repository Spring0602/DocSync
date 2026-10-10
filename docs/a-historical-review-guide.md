# 成员A：历史 AI 日志补审

2026-10-10 整理。历史 CSV 共 11 条，已有反馈映射为 11 条均已有指定范围复核记录（不等于全量签署）；尚无整条历史阶段的全范围签署。原 CSV 原样保留，快照及机器可读范围见 [映射](audit-samples/billing-review-20261010/historical-review-map.json)。部分复核不要求重做已检查内容，也不把当前版本审查倒填为旧提交验收。

## 逐行缺口

| 原台账行 / 阶段 | 已有复核 | 保留边界 | 状态 |
| --- | --- | --- | --- |
| 2 framework | 核心演示、CLI、补丁主要检查点；H1 快照/未提取声明/模型降级与拒答/并发边界已反馈；确认不导入或执行目标项目 | 本组指定检查点已完成；不声称重装、重跑测试或历史提交全量验收 | 指定范围已记录 |
| 3 core extensions | 模型密钥、预算、校验、重试及未知用量；H1 快照/未提取声明/模型降级与拒答/并发边界已反馈；确认不导入或执行目标项目 | 本组指定检查点已完成；不声称重装、重跑测试或历史提交全量验收 | 指定范围已记录 |
| 4 release verification | 历史验证的时点/版本/范围，skip 不算 pass，远程 CI 的 SHA 边界，LICENSE/元数据与自有材料范围一致 | 指定文档/许可/构建配置检查点已完成；未声称检查实际发行包或重跑验证 | 指定范围已记录 |
| 5 member A contract review | CLI 退出码和显式应用、补丁检查；旧报告不重算、新字段兼容边界、FAILED 信封及输出覆盖差异 | 本组指定检查点已完成；不声称重装、重跑测试或历史提交全量验收 | 指定范围已记录 |
| 6 A acceptance and license | 历史验证的时点/版本/范围，skip 不算 pass，远程 CI 的 SHA 边界，LICENSE/元数据与自有材料范围一致 | 指定文档/许可/构建配置检查点已完成；未声称检查实际发行包或重跑验证 | 指定范围已记录 |
| 7 A development adjudication | 限定 16 样本事实级候选召回、5 样本实际 4 次调用、seed-04 拒答与错误附带解释的区分 | 汇总口径复核完成；未声称逐条核验全部 gold 或原始模型响应 | 指定范围已记录 |
| 8 live smoke verification | 限定 16 样本事实级候选召回、5 样本实际 4 次调用、seed-04 拒答与错误附带解释的区分 | 汇总口径复核完成；未声称逐条核验全部 gold 或原始模型响应 | 指定范围已记录 |
| 9 A experiment readiness | 七方法开发结果解释及汇总账单；默认仅计划、实际调用与上界有别、执行前输出/源码检查；乘法预算上界和 suite 限额判断已确认 | 指定运行器检查点已完成；无付费重跑 | 指定范围已记录 |
| 10 A annotation handoff tooling | B/C 原表及交接保留、标签一致不等于独立性；Git blob 固定、无预填答案、结构检查边界、合成组来源及冻结重建校验 | 工具与来源检查点已提交；保留哈希不证明独立性的助手澄清，不扩大为 24 条全量裁决签署 | 指定范围已记录 |
| 11 A controlled candidate collection | 五条标注及来源独立性原则；Git blob 固定、无预填答案、结构检查边界、合成组来源及冻结重建校验 | 工具与来源检查点已提交；保留哈希不证明独立性的助手澄清，不扩大为 24 条全量裁决签署 | 指定范围已记录 |
| 12 A technical closeout | 报告解释、3 条预测、5 条标注及 dev 判断；Git blob 固定、无预填答案、结构检查边界、合成组来源及冻结重建校验 | 工具与来源检查点已提交；保留哈希不证明独立性的助手澄清，不扩大为 24 条全量裁决签署 | 指定范围已记录 |

## H1：使用说明、支持边界和并发限制（行 2、3）

进度：H1 指定检查点已完成；不代表重新安装或历史提交全量验收。原子性指逐文件替换，不是跨文件原子回滚。

阅读 [README](../README.md) 的安装/快速开始与 [limitations](limitations.md)，再对照 [CLI](../src/docsync/cli.py) 的 `--head`、`--working-tree`。

请反馈：
1. 默认扫描 HEAD 还是未提交修改？要检查工作区改动应加什么参数？
2. 没有提取出声明能否算“一致”？工具会不会导入并执行目标项目？
3. hybrid 没有模型服务时与纯 LLM 基线如何处理？
4. 补丁只在整体应用前和逐文件写入前检查；无全程锁、无写后复核，所以不应与编辑器并发写入。这是否与你对代码的检查一致？

不需要重装、不调用 API。安装流程未实际重跑时写“文档审查，未重装”，不声称独立环境复现。

## H2：报告兼容和失败信封（行 5）

进度：H2 指定检查点已完成，见 [复核记录](audit-samples/billing-review-20261010/historical-h2-review.json)。H3—H6 也已记录。

阅读 [契约审查](a-contract-review.md) 的“版本与失败报告边界”、[当前限制](limitations.md) 的 ignore_expires 段，并对照 [契约测试](../tests/integration/test_a_contract_review.py)。旧日期记录中的未完成状态须与当前状态区分。

请反馈：新程序读取旧 1.0/2.0 报告是否重新计算历史 ignored/Finding/补丁？旧程序是否保证读取新增字段？全局 FAILED 的错误信封为什么不能直接当完整 ScanReport？`patch` 同名输出和 `scan` 非空输出目录的行为是否相同？

## H3：历史验证、许可落地及版本证据（行 4、6）

进度：指定检查点已完成，见 [H3 记录](audit-samples/billing-review-20261010/historical-h3-review.json)。范围为文档、许可证和构建配置；未声称亲自检查实际发行包或重新运行测试。

阅读 [验证记录](verification.md) 的 2026-09-19 段、[LICENSE](../LICENSE)、[pyproject](../pyproject.toml) 的 license 与构建配置，以及 [收尾记录](a-closeout-20261010.md) 的工程证据。

请反馈：98 passed/1 skipped 与 217 passed/2 skipped 为什么不能相加？符号链接跳过是未执行还是通过？历史 CI 成功能否覆盖当前未推送修改？许可声明及打包范围是否与已审授权范围一致？记录实际查看的段落；未检查发行包本体就不要写“已检查包内容”。

## H4：旧开发集指标与真实小样本（行 7、8）

进度：汇总口径反馈已记录，见 [H4 记录](audit-samples/billing-review-20261010/historical-h4-review.json)。未扩大为全部 gold 坐标或原始响应逐条审核。

阅读 [seed-dev-v1 说明](../bench/frozen/seed-dev-v1/README.md) 和 [五例实测](deepseek-smoke5-20261007.md)，对照其链接的原始预测/汇总。

请反馈：Recall@1/3/5 的分母为何是 16 而不是 20？排除了哪类样本，候选 recall 与分类 recall 是否相同？五例为什么只有四次模型请求？seed-04 的拒答结果与附带解释问题分别是什么？不得把开发集改称正式测试。

## H5：实验运行器安全与口径（行 9）

进度：默认不执行、调用计数与上界区别、输出/源码检查已反馈。预算公式已由本人补充确认：样本数 × 非本地方法数 × 每扫描最大请求数；再与 suite 总上限比较，不做除法。见 [H5 记录](audit-samples/billing-review-20261010/historical-h5-review.json)。输出路径即使是空目录也必须不存在；源码一致性不等于 Git 必须 clean。

查看 [run_suite.py](../bench/run_suite.py) 的 `plan_suite`、`run_suite`、`main`，以及 [test_suite.py](../tests/unit/test_suite.py) 对应断言。

请反馈：不带 `--run` 会不会调用模型？请求预算上界怎么算、是否等于实际调用数？输出目录已存在或安装源码不匹配时怎样处理？这些检查只需读代码，不能为补审重跑付费实验。

## H6：标注工具、来源与重建（行 10—12）

进度：反馈已记录，见 [H6 记录](audit-samples/billing-review-20261010/historical-h6-review.json)。哈希等检查保证冻结版本的一致性和可重建性，不自动识别同源改写或证明独立性；来源与模板关系仍需人工审查。

查看 [annotation_packet.py](../bench/annotation_packet.py) 的 `prepare`、`check_annotations`，[候选来源](../bench/candidates/controlled-v1/README.md)，以及 [重建脚本](../bench/builders/build_reviewed_candidates.py)。

请反馈：标注包如何固定原文、是否包含预填标签？双表结构通过为什么不能代替标签正确性和盲态证据？六组合成样本是否来自六个真实项目？重建前的哈希检查为何必要？

24 条裁决现均已获成员A反馈，见 [全量复核索引](audit-samples/release-readiness-20261010/candidate-human-review-complete.json)；标签不变、仍为 dev，冻结时的 pending 字段由补充记录说明，不篡改原始哈希。

## 反馈格式与记录规则

每次回复一组即可：`组号；实际查看文件/函数；对问题的理解；问题或修改；未检查范围`。沿用审核人“成员A”，实际审核日期若未填写继续留空，另记反馈接收日期。助手负责技术比对与整理；只有用户实际反馈的范围能进入人工记录，不把自动测试通过变成人工签署。

六组是合并后的缺口入口，不是六项新的整仓库审计。本次以逐行 JSON 补充台账保存实际 reviewer、范围及证据，历史 CSV 作为原始记录保留。查阅当前人工复核状态必须同时查看补充台账；不替 B/C 签字，24 条后续实际反馈另见全量复核索引。
