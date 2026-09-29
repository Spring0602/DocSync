# C3 预审工作单：人工标注、权利与发布审查

- 预审人：C 的 AI 助手，2026-09-29；基线提交 `1be73fe`，C 审核分支 `c2-action-verification`
- 用途：把 C3 中可机械核实的事项先做掉，**需要人工签字/独立判断的事项集中列出**，由 C 本人完成后勾选 `docs/release-checklist.md`。

## 一、AI 助手已完成的机械核实

### 1. 敏感材料入库检查 ✅
- `git ls-files` 全量核查：**无 .docx/.pdf/.zip 入库**；`.gitignore` 已排除根目录 docx/pdf。
- 结论：原始策划案与竞赛附件未进入仓库，符合"原始资料不进入发布包"要求。

### 2. "未声明许可证"依赖的本地元数据核实 ✅
`installed_dependencies.csv` 中 6 项 `license_metadata=not declared`，已用
`.venv` 内 dist-info 的 LICENSE 原文逐一核实：

| 包 | CSV 现状 | 实际许可证（LICENSE 原文核实） | 建议 CSV 填写 |
|----|----------|-------------------------------|----------------|
| colorama 0.4.6 | not declared | BSD-3-Clause（Copyright (c) 2010 Jonathan Hartley） | BSD-3-Clause |
| markdown-it-py 3.0.0 | not declared | MIT | MIT |
| mdurl 0.1.2 | not declared | MIT（Copyright (c) 2015 Vitaly Puzrin, Alex Kocharin / 2021 Taneli Hukkinen） | MIT |
| pathspec 1.1.1 | not declared | MPL-2.0（Mozilla Public License Version 2.0） | MPL-2.0 |
| ruff 0.12.7 | not declared | MIT（Copyright (c) 2022 Charles Marsh） | MIT |
| trove-classifiers 2026.6.1.19 | not declared | Apache-2.0 | Apache-2.0 |

以上 6 项仅补"license_metadata"字段；`review_status` 仍须 C 本人复核后改为已审。

### 3. 台账交叉一致性 ✅
- `third_party_resources.csv` 与 `requirements-dev.lock` / pyproject 依赖一致，版本号无冲突。
- `data_rights.csv`：planning_docx / competition_attachments 标记 "not cleared for public
  redistribution" 且未入库，与第 1 项核查互相印证。

## 二、必须由 C 本人完成的事项（不可代做）

### 1. 20 个种子第二份独立标注（对应 tasks.md C3-1）
- 先**不要**看 B 的标注和 A 的裁决记录。
- 用 `bench/annotations/individual.template.csv` 填写，证据、标签、疑问、时间戳四列都要填。
- 完成后交给 A 与 B 的标注对照裁决；存在分歧是正常流程，不要事后对齐。

### 2. 合规台账签字（对应 tasks.md C3-2）
逐行复核后把 `review_status=pending` 改为已审并署名：
- [ ] `installed_dependencies.csv` 21 行（6 行的许可证可参考本单第一节的核实结果）
- [ ] `third_party_resources.csv` 8 行
- [ ] `data_rights.csv` 4 行——**"team ownership confirmation pending" 需要全队确认**
- [ ] `ai_assistance_log.csv` 4 行——注意 `commit` 列仍是 `uncommitted`，已过时，
      应更新为实际提交 SHA（当前 main=`1be73fe`，分支提交见下）；`human_reviewer`/
      `human_changes` 需要当时使用 AI 的成员补充。

### 3. 发布决策与复现（对应 tasks.md C3-3）
- [ ] Apache-2.0 许可证最终选择需全队确认后勾选 checklist 第 9 行
- [ ] 第二台设备按 README 复现安装、demo、扫描流程（checklist 第 15 行）
- [ ] 材料匿名化复核（对外材料中不出现真实姓名/学号等）

## 三、与 C2 成果的衔接

- checklist 第 13 行"首次推送 + CI 记录"：分支 `c2-action-verification` 已推送，
  CI 双平台运行记录见 `docs/c-action-local-scenarios.md` 第三节（run 36589298331，
  SHA e6315f2/c7d77ec）。main 的推送由团队决定合入时机。
