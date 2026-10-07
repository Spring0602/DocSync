# seed-dev-v1：已裁决开发集

2026-10-07 基于 B/C 两份完整标注逐条接收，20/20 标签一致，分类为 11 INCONSISTENT、5 CONSISTENT、4 INSUFFICIENT。A 将本轮技术复核委托给助手；adjudication.jsonl 明确记录 AI 辅助身份，不伪造 A 人工签字。两份原始标注保留，来源哈希见 freeze.json。

范围：20 个自建、此前已用于开发的样本，全部 split=dev、annotation_status=adjudicated。独立性来自团队提交的标注记录，开发过程接触历史如实披露；不称为盲测或独立正式测试集。目标映射由源码及标注证据复核确定，非根据模型预测生成。

manifest.jsonl 的 SHA-256 为 fe5b4c21e3261de83137d1748651f9e54bc6b5fcb937eabee39108900f7dfab8。freeze.json 固定标注来源与三份数据文件 hash；标注来源统一 LF 后计算，冻结文件由 .gitattributes 固定 LF。任何修改需另建版本，禁止沿用本版本 hash。

不要直接对本目录运行 benchmark：仓库由重建脚本生成，manifest 必须与 repos 位于同一输出目录。

```powershell
.\.venv\Scripts\python.exe bench/builders/build_reviewed_seed.py --out runs/reviewed-seed-new
.\.venv\Scripts\python.exe -m docsync benchmark --manifest runs/reviewed-seed-new/manifest.jsonl --method rules --out runs/reviewed-rules-new
.\.venv\Scripts\python.exe bench/evaluate_alignment.py --gold bench/frozen/seed-dev-v1/alignment-gold.jsonl --reports runs/reviewed-rules-new --out runs/reviewed-retrieval-new.json
```

重建脚本校验原始标注、冻结文件和每个样本的固定 Git SHA，再替换成已裁决 manifest，不运行目标代码。原 build_seed.py 保持 provisional 行为，避免旧开发脚本自动授予人工审核状态。

## Recall@K 口径

预先限定“当前版本、可判定且实体可唯一归属”的 16 个样本。4 个 INSUFFICIENT 样本以理由单列（动态值、历史语境、歧义），不进入本项分母；这不是全数据集候选召回，也不意味着动态值没有可检索实体。

单位为人工目标事实坐标（代码路径、实体、属性、类型、起始行），文档用路径及声明起始行定位。围栏调用使用提取器的围栏起始行；表格声明为第 5 行，非整张表范围。无候选、声明未提取、坏报告、错误快照均计未命中，不删除样本。多目标按事实数微平均；零分母 null。候选按真实 rank<=K 命中，和分类 recall 分开。

本轮扫描 top_k=5，只报告 K=1/3/5；若以后设置更大 K，必须重新生成足够深度的候选，不能从截断报告推断未知排名。工具不执行检索，调用者须记录候选生成配置。

freeze.json 不把结果指标当成 gold。分类及候选结果见 docs/audit-samples/a-20261007。正式测试集仍须另收合法新数据、双标裁决及按 repo/group 划分，不把这 20 条改成 test。
