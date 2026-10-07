# controlled-candidates-v1：24 条未标注受控候选

本批于 2026-10-07 由 A 委托助手编写，24 条候选、6 个合成仓库/技术家族，外部真实仓库为 0。来源是 AI 辅助原创代码及文档；团队对原创材料采用 Apache-2.0 的决定见 docs/license-scope.md。未复制第三方仓库，随快照附完整 LICENSE；最终发布仍需正常材料审核。

**这不是已经完成的独立正式测试集。** 创建者已读旧开发集及实验结果，无法宣称数据作者盲态。没有导入旧种子生成器，没有为候选执行 DocSync 扫描、规则预测或模型调用，也没有生成 gold。24 是实际候选数，不是通过独立性审查的样本数；人工标签和来源/模板审查均待完成。

## 分组与独立性风险

| 组 | 样本 | 主要结构 | 需要复核的旧数据相似性 |
| --- | --- | --- | --- |
| candidate-family-01 | 01—04 | 构造方法、异步函数、类型注解和复合默认值 | 仍涉及默认值文字声明，不能因换实体而自动认定新模板 |
| candidate-family-02 | 05—08 | 默认值绑定时间、函数默认值修改、调用表达式 | 07/08 尤需与旧 factory_unknown 模板比较；可能需归 dev |
| candidate-family-03 | 09—12 | *args / **kwargs 展开及来源值 | 与旧签名参数检查存在语义关联，需检查是否只是展开形式改写 |
| candidate-family-04 | 13—16 | 类方法、静态方法、实例绑定、运行时接收者 | 与旧参数绑定/歧义案例有关联，新增结构不等于独立来源 |
| candidate-family-05 | 17—20 | 注解变量、再赋值、分支和字典更新 | 与旧常量/动态配置有关联，需按代码模式审查 |
| candidate-family-06 | 21—24 | 嵌套字典、元组、环境值和 dict 构造 | 与旧配置字典有关联，需按派生关系审查 |

组不能跨 dev/test；同一技术家族保持整体归属。若发现与旧种子同族，整组保留为 dev/候选研究材料并记录原因，不能只重命名 group_id 绕过检查。当前只完成 ID 检查和代码/文档字节哈希对比：无旧开发 blob 完全相同；这不能证明语义独立。不是六个独立真实项目，也不保证三类最终标签配额。

## 版本与重建

spec.json 保存原始代码和文档，不含标签。freeze.json 固定规范、入库 packet、原始 intake 和 LICENSE 的 SHA-256；两个新目录的实际重建产生相同 intake 和 Git SHA。Git 使用固定的合成作者和提交时间，仅为重建复现，不是人工审核签名或真实历史变更。

在项目根目录、依赖已安装的环境执行：

```powershell
.\.venv\Scripts\python.exe bench/builders/build_candidates.py --out runs/candidate-v1-20261007
.\.venv\Scripts\python.exe -m bench.annotation_packet prepare --intake runs/candidate-v1-20261007/intake.jsonl --out runs/candidate-v1-packet-new
```

已存在目录不要重复创建，换新的 --out。构建只用 ast.parse 验证 Python 语法，不执行候选源码。原始 intake 中 repos 路径相对重建目录；bench/annotations/test-intake/intake.jsonl 指向上面指定的本地重建位置，所以字节 hash 不同，不要与原始 intake hash 混用。

B/C 无需重建即可阅读 [入库标注包](../../annotations/candidate-v1/README.md)。这一版本内容不再直接修改；勘误/补充文件请另建候选版本并记录排除/替代关系。未来是否冻结 test-v1，取决于人工独立性审查、双标及 A 裁决，不由工具自动设置。
