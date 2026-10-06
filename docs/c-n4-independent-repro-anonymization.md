# C-N4 同机独立环境复现与匿名化核查记录

- 记录日期：2026-10-06
- 复现性质：同机独立环境复现，不称为第二台物理设备复现
- 说明：队友于 2026-10-06 确认，本项验收目的在于验证独立环境复现；全新 clone + 全新 venv 已满足当前复现验收目的。记录中仍按事实注明本次不是第二台物理设备复现。

## 一、环境与版本

| 项 | 记录 |
| --- | --- |
| 设备/环境 | C 本人电脑，同机独立目录与独立虚拟环境 |
| 系统 | Microsoft Windows 10.0.26200 |
| Python | 3.12.1 |
| Git | 2.55.0.windows.3 |
| 来源 | 从 GitHub 全新 clone `https://github.com/Spring0602/DocSync.git` |
| 分支 | `c2-action-verification` |
| 固定提交 | `002b076efe145d0c35ea26669aff516eb4e09990` |
| 复现目录 | `runs/c-n4-independent-repro/checkout`（本地忽略目录，不入库） |
| 虚拟环境 | `runs/c-n4-independent-repro/checkout/.venv`，全新创建 |
| 模型范围 | 未配置真实模型；按 README 默认 rules 模式验证安装与基础使用流程 |

## 二、执行命令与结果

| 步骤 | 命令 | 结果 |
| --- | --- | --- |
| 全新 clone | `git clone --branch c2-action-verification https://github.com/Spring0602/DocSync.git runs/c-n4-independent-repro/checkout` | 成功 |
| 固定提交 | `git checkout 002b076efe145d0c35ea26669aff516eb4e09990` | 成功，detached HEAD |
| 创建 venv | `python -m venv .venv` | 成功 |
| 安装依赖 | `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | 成功，安装 `docsync-core-0.2.0` 及 dev 依赖 |
| CLI help | `.\.venv\Scripts\docsync.exe --help` | 成功，显示 `scan/patch/apply/schema/benchmark` 子命令 |
| 创建 demo | `.\.venv\Scripts\python.exe scripts/create_demo.py --out runs/demo-repo` | 成功，输出 `runs\demo-repo` |
| 首次扫描 | `.\.venv\Scripts\docsync.exe scan --repo runs/demo-repo --out runs/demo` | 成功，`COMPLETED`，`confirmed_count=1` |
| 补丁预览 | `.\.venv\Scripts\docsync.exe patch --report runs/demo/report.json --out runs/fixes.patch` | 成功，生成 `runs\fixes.patch` 和 `runs\fixes.patch.json`，`requires_review=true` |
| 显式应用 | `.\.venv\Scripts\docsync.exe apply --repo runs/demo-repo --patch runs/fixes.patch --manifest runs/fixes.patch.json` | 成功，`APPLIED`，修改 `README.md` |
| working-tree 复扫 | `.\.venv\Scripts\docsync.exe scan --repo runs/demo-repo --working-tree --out runs/after` | 成功，`COMPLETED`，`confirmed_count=0` |

## 三、关键产物

| 产物 | 路径 | 说明 |
| --- | --- | --- |
| 首次扫描 JSON 报告 | `runs/c-n4-independent-repro/checkout/runs/demo/report.json` | `status=COMPLETED`，初扫确认 1 条冲突 |
| 首次扫描 Markdown 报告 | `runs/c-n4-independent-repro/checkout/runs/demo/report.md` | 人类可读报告 |
| 补丁文件 | `runs/c-n4-independent-repro/checkout/runs/fixes.patch` | 补丁预览产物 |
| 补丁 manifest | `runs/c-n4-independent-repro/checkout/runs/fixes.patch.json` | 应用前校验依据 |
| 复扫 JSON 报告 | `runs/c-n4-independent-repro/checkout/runs/after/report.json` | `status=COMPLETED`，确认冲突降为 0 |
| 复扫 Markdown 报告 | `runs/c-n4-independent-repro/checkout/runs/after/report.md` | 人类可读复扫报告 |

## 四、结论

README 中的安装、CLI help、demo 构建、扫描、补丁预览、显式应用和 working-tree 复扫流程，已在同机独立 clone 与全新 venv 中跑通。该复现证明安装与基础使用流程可从干净工作副本完成。

限制：本次不是第二台物理设备复现，不把同一台电脑称为第二设备。未配置真实模型，验证范围限于默认 rules 模式和基础 CLI 流程。

## 五、匿名化核查表

| 项 | 状态 | 记录 |
| --- | --- | --- |
| 原始 DOCX/PDF/ZIP 是否入库 | 通过 | 既有 C3 审核确认仓库无 `.docx` / `.pdf` / `.zip` 入库；根目录 `.gitignore` 继续排除原始私有材料。 |
| 复现产物是否入库 | 通过 | 复现目录位于 `runs/`，该目录被 `.gitignore` 忽略，不进入提交。 |
| 对外文档是否含学号 | 待最终材料阶段复核 | 当前仓库文档未专门扫描最终演示/视频/截图材料；最终提交前需复核。 |
| 对外文档是否含真实姓名/账号/本机路径 | 待最终材料阶段复核 | 当前记录含本机复现目录作为本地证据路径；若对外发布材料截图或视频，应打码本机用户名、绝对路径、浏览器账号和终端提示符。 |
| 链接是否有效 | 部分完成 | GitHub workflow run 链接已保存；最终材料链接需在发布前统一复核。 |
| 许可证和署名 | 保留 | 不因匿名化删除 Apache-2.0、第三方许可证和必要权利声明。 |

## 六、后续待办

- 独立环境复现已按当前队友反馈满足验收目的；如后续最终验收临时要求严格“第二台物理设备”，再换另一台电脑重复 README 流程并补记录。
- 最终演示、截图、视频和提交链接确定后，再做一次匿名化与链接可访问性复核。

## 七、当前仓库匿名化与缺项汇总（2026-10-06）

### 已执行的仓库扫描

- `git ls-files`：已跟踪文件中未发现 `.docx`、`.pdf`、`.zip` 原始材料入库。
- 敏感词/路径/密钥模式扫描范围：`docs compliance README.md bench .github action examples src tests`。
- 命中项复核：
  - `.github`、`action`、`examples/workflows` 中的长 SHA 为固定 GitHub Action 版本，不是密钥。
  - `tests@example.invalid`、`fixture@example.invalid` 为测试用假邮箱。
  - `DOCSYNC_API_KEY`、`OPENAI_API_KEY`、`sk-fake-dummy` 为文档或测试中的变量名/假值，不是真实密钥。
  - `C:/README.md`、`C:\Users\...` 等为测试路径或本地复现记录；对外截图/视频仍需打码本机用户名和绝对路径。
  - `学号`、`真实姓名` 等命中来自待办/核查说明本身，不是实际个人信息。

当前仓库材料可作为代码仓库提交；最终演示、截图、视频、压缩包或外部提交链接确定后，仍需再做一次面向最终材料的匿名化核查。

### AI assistance log 缺项汇总

`compliance/ai_assistance_log.csv` 当前仍有 5 行 `human_reviewer` / `human_changes` 为 `pending`：

| 日期 | 阶段 | commit | 当前状态 |
| --- | --- | --- | --- |
| 2026-09-17 | framework | `85e9d71` | pending，需实际参与成员补人工复核 |
| 2026-09-18 | core extensions | `85e9d71` | pending，需实际参与成员补人工复核 |
| 2026-09-19 | release verification | `85e9d71` | pending，需实际参与成员补人工复核 |
| 2026-09-20 | member A contract review | `1be73fe` | pending，需实际参与成员补人工复核 |
| 2026-09-30 | A acceptance and license | `uncommitted` | pending，需 A 按真实经历补人工复核和修改说明 |

C 的处理结论：已汇总缺项，不代 A/B 或历史 AI 使用者填写人工复核意见。该项仍是最终发布前待关闭事项。
