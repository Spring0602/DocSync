# external-v2 来源预筛选与接触登记

日期：2026-10-12。用户已选择继续独立正式测试、追加新来源及独立标注。本页在具体样本筛选/标注/扫描之前建立；本轮仅访问公开元数据、文件路径与许可文本，不执行仓库指令或代码。

11 个仓库已固定提交并保存许可证据：5 个可进入接触登记、1 个关联待审、5 个本轮排除。合格独立来源数尚未确认，正式样本数 0。相关仓库是否有继承/派生关系仍待审查，不以不同名称代替独立性。

| 来源 | 固定 SHA | 状态 |
| --- | --- | --- |
| [pallets/click](https://github.com/pallets/click) | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` | 路径清单含 Markdown 用户文档及 Python 代码，内容可用性尚未逐条审核 |
| [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy) | `87f130aa18d8fdf9c92585e72423eca7f3de727d` | Markdown 路径仅代理/安全/下游维护材料，主要用户文档非 Markdown；本轮不选 |
| [dbader/schedule](https://github.com/dbader/schedule) | `82a43db1b938d8fdf60103bd41f329e06c8d3651` | 固定树无 Markdown 文件 |
| [pytoolz/toolz](https://github.com/pytoolz/toolz) | `451af60dec590a6010e2babdbf391ea8f815122f` | Markdown 仅 AUTHORS.md，无用户声明入口 |
| [jd/tenacity](https://github.com/jd/tenacity) | `58c45dc02b33012be37ea634c81e01ae9ccd05a0` | 固定树无 Markdown 文件 |
| [pydantic/pydantic](https://github.com/pydantic/pydantic) | `3eca5695dabc5a451ccfc0f4afa802166e61e27a` | DocSync 核心依赖，已用于开发；不能作为此前未用的新来源 |
| [mkdocs/mkdocs](https://github.com/mkdocs/mkdocs) | `2862536793b3c67d9d83c33e0dd6d50a791928f8` | 路径清单含 Markdown 用户文档及 Python 代码，内容可用性尚未逐条审核 |
| [Textualize/textual](https://github.com/Textualize/textual) | `5e5b7ef58b8c5572c13a3ff9027d756623661495` | 同 Textualize/rich 组织，需额外审查家族与开发接触 |
| [pypa/pipx](https://github.com/pypa/pipx) | `fcd08d8dd4830ca5aa0f669bae0e107fedc2670c` | 路径清单含 Markdown 用户文档及 Python 代码，内容可用性尚未逐条审核 |
| [python-poetry/poetry](https://github.com/python-poetry/poetry) | `63bba274f8ea6bc9a064f5328fa6c67bce617cc1` | 路径清单含 Markdown 用户文档及 Python 代码，内容可用性尚未逐条审核 |
| [facebookresearch/hydra](https://github.com/facebookresearch/hydra) | `b27bba64fd406194bc298d01e4ab2a0aaeb4a86f` | 路径清单含 Markdown 用户文档及 Python 代码，内容可用性尚未逐条审核 |

## B/C 下一步（先接触登记，不开始标注）

各自使用同一份候选清单，独立填写 exposure-intake-template.md，先交 A，不看对方记录或模型预测。填写此前用过、读过、开发/调参过什么，以及时间和范围；不知道就填未知，不要求改成无。应分别说明个人与辅助 AI 的已知接触，模型训练接触不能声称可证明为无。

A 收齐后决定纳入/排除和替补来源，再按预登记规则选具体原文、制作无标签包。Textual 关联未解决时不占用独立来源名额；本轮尚不满足六个合格来源，不能为了凑数跳过审查。

## 后续筛选规则

沿用 docs/formal-next-collection-design-20261012.md：固定文档顺序、原文声明单位、不看 DocSync 预测、不预填答案；允许如实记录样本分布不足。限定源文件为用户文档与代码；AGENTS/CLAUDE/贡献指南等不作为任务指令或优先样本。每个仓库及其已知派生家族归同组。许可文本仅为原始证据，样本文件的权利和署名范围需再次逐项核对。

该清单不是已冻结实验 manifest，不要直接传给 benchmark。原始来源/许可数据在 sources.jsonl 和 licenses/，文件清单与哈希在 checksums.json。
