# external-v1 具体样本与 B/C 无标签交接（2026-10-11）

已从成员 A 确认的六个外部固定仓库提交中选出 **24 个声明单元**，每仓库四条。原文包、B/C 空表、独立接触声明、完整许可证、筛选/暂缓依据与哈希已准备好。**尚未得到人工标签，正式测试集尚未冻结。** 本轮没有 DocSync 扫描、规则试跑、第三方代码执行或实验 API 调用。

## 交付入口

- [包内操作说明](../bench/annotations/external-v1/README.md)：字段、独立填写和收表流程。
- [24 条样本导航](../bench/annotations/external-v1/SAMPLES.md)：每条问题、原文焦点和代码入口。
- [B 空表](../bench/annotations/external-v1/individual-B.csv)及 [B 接触声明](../bench/annotations/external-v1/exposure-B.md)。
- [C 空表](../bench/annotations/external-v1/individual-C.csv)及 [C 接触声明](../bench/annotations/external-v1/exposure-C.md)。
- [固定文件校验清单](../bench/annotations/external-v1/checksums.json)、[源码上下文索引](../bench/annotations/external-v1/context-index.json)、[许可范围记录](../bench/annotations/external-v1/rights-review.json)。
- 本地转交压缩包：`runs/external-v1-handoff/external-v1-unlabelled.zip`。这是完整原始空白包，B/C 收到同一版本；其中不存在已填答案。压缩包及下载缓存位于 Git 忽略的 runs，原文目录可正常入库。

| 样本 | 来源 | 本轮核对对象 |
| --- | --- | --- |
| external-01—04 | encode/httpx | 默认超时、顶层/客户端调用、禁用超时配置 |
| external-05—08 | Delgan/loguru | 初始输出配置、debug/add/remove 接口 |
| external-09—12 | theskumar/python-dotenv | 无参调用、默认查找策略、override、路径参数 |
| external-13—16 | Textualize/rich | print、pretty.install、Console 构造及方法调用 |
| external-17—20 | python-attrs/attrs | 装饰器生成构造、field、私有属性参数映射 |
| external-21—24 | rsalmei/alive-progress | total、返回句柄、关键字配置、ctrl_c 默认设置 |

分类、标签、实际实体和最终证据坐标均由标注者独立填写。表格只预填 ID、固定 SHA、原文路径。导航的代码入口是查阅提示，不是 gold 或候选召回坐标。动态/环境依赖保留上下文，不预先判定为 INSUFFICIENT。

## 筛选范围与独立性

[筛选规则](../bench/sources/external-v1/screening-policy.md)在本轮读取具体正文前写入：按既定文档顺序及行号筛选，每仓库至多四个声明单元，不按答案配额或工具结果挑选。后续段落达到上限只记暂缓，不声称已经穷尽筛查。[选择记录](../bench/sources/external-v1/selection.json)保留问题、坐标、上下文列表和每类跳过理由。python-dotenv 的 docs/index.md 仅为路径别名，没有重复算作独立文档。

本轮是目的性小样本，调用签名类入口较多；不保证三类或正/负/不足均衡，不声称发现了 24 个真实缺陷。若双标后不足以支持目标指标，先登记新的采集设计再补来源，不改造这些原文凑比例。同仓库条目相关，六仓库不自动等于六个无泄漏家族。

[重叠记录](../bench/annotations/external-v1/overlap-review.json)核对了两批已冻结开发集共 44 条 ID/repo/group，并通过其既有 reviewed builder 重建固定 Git 提交后比对代码/文档原文哈希；没有申报标识或完整文件字节重叠。它不能排除语义派生、模板家族或人的既往接触。来源发现阶段 `sources.jsonl` 的 0 样本/未读正文状态作为历史快照保留，当前状态由本说明与 selection/context-index 补充。

采集由已接触 DocSync 开发历史的 AI 辅助完成。A 已报告来源此前未使用；B/C 个人接触情况、是否使用 AI 辅助标注仍待分别填写，模型预训练暴露未知。不得自动称为纯人工盲测金标准。

## A 现在执行

在项目根目录运行（下面命令无需模型密钥）：

```powershell
.\.venv\Scripts\python.exe -m bench.builders.build_external_packet --verify bench/annotations/external-v1
Get-FileHash bench/annotations/external-v1/packet.json -Algorithm SHA256
Get-FileHash bench/annotations/external-v1/checksums.json -Algorithm SHA256
```

查看筛选问题、原文与许可证后，把同一原始包和各自表交给 B/C；本轮新增准备工作的人工签署仍待 A 实际复核，不借用历史完成记录。B/C 复制表后在私有工作目录填写，不覆盖原包；收到完整两表且各自冻结后，按真实交付路径执行：

```powershell
.\.venv\Scripts\python.exe -m bench.annotation_packet check `
  --packet bench/annotations/external-v1/packet.json `
  --b <B实际交付.csv> `
  --c <C实际交付.csv>
```

`<...>` 必须替换为真实路径，不能原样运行。空表执行 check 会因待填字段退出 2，这是预期；原包完整性用前面的 --verify。

A 再逐条复核一致项与分歧、审核接触/家族/许可、固定实验扫描范围及声明级计分映射，再另建正式 test manifest。多个单元共享同一 README/源码，不能简单重复整仓扫描并把任意一条 Finding 算成所有样本命中。此阶段不改提取器来迎合待测样本。

## 新机器离线重建准备

检验现有包不需要源缓存；重新生成才需要下面的固定 Git 对象。只拉固定 SHA，不安装或执行上游代码：

```powershell
$sourceRows = Get-Content bench/sources/external-v1/sources.jsonl -Encoding UTF8 | ForEach-Object { $_ | ConvertFrom-Json }
foreach ($source in $sourceRows) {
    $cachePath = Join-Path 'runs/external-v1-repos' $source.source_id
    if (-not (Test-Path -LiteralPath $cachePath)) {
        git init --bare --quiet $cachePath
        if ($LASTEXITCODE -ne 0) { throw '初始化缓存失败' }
    }
    git -C $cachePath fetch --depth=1 --no-tags ($source.source_url + '.git') $source.head_sha
    if ($LASTEXITCODE -ne 0) { throw '获取固定快照失败' }
}
.\.venv\Scripts\python.exe -m bench.builders.build_external_packet --out runs/external-v1-new-copy
```

输出目录必须不存在。新脚本复用既有 prepare 工具，另外补原文上下文、两批开发集核对、哈希和空表校验；Windows CSV 双重换行已在新脚本中规范为单次 CRLF。重建需要项目原有的冻结开发集及标注证据完整，以通过旧集的自校验。

## 验证结果与交接哈希

[验证记录](audit-samples/external-v1-preparation-20261011/verification.json)：5 项标注专项通过，Ruff 通过；独立重建 101 个文件逐字节一致。4 个负向检查分别覆盖篡改原文、删除文件、新增文件和重算清单后插入标签，均拒绝。B/C 表格工具预览与记录顺序检查通过；压缩包解包字节一致。没有重复运行整个业务测试集，当前工作未改变扫描/修复实现。

上游代码/文档继续适用各自 MIT 或 BSD-3-Clause；完整原文许可证已附，不包含 README 链接的图片、logo 或外站资源。最终发布许可与家族裁决仍由 A/C 实际复核，脚本没有代签。

- packet.json SHA-256：`d2e30c933b2a31dd06c192b5f2834b51164220fb7fb8ec0dd08b29d0921cdf89`
- checksums.json SHA-256：`ba1be2574191267018f66c08b33b51553ff2886c5a72470ca3ec4796cd6cce3f`
- 压缩包 SHA-256：`f8e6dc1e3a55b5f52e3b76b0ab29a31cd50335c28c6c78b0edd11be2a3cb582c`

## 2026-10-12 接收及技术裁决更新

B/C external-v1 原表和接触声明已接收并冻结，双表结构检查通过，不再重复派发标注。24 条技术复查完成：23 条在限定范围内一致，external-10 的文档场景范围未决；原表不改。详见[逐条裁决及 A 复核指南](external-adjudication-20261012.md)。成员A已确认本轮 24/24 条技术裁决（10 认可保留未决），反馈接收于 2026-10-12；正式 test 仍为 0，独立性与计分/扫描方案仍待完成。本页早期等待交付的说明保留为历史，不代表最新状态。
