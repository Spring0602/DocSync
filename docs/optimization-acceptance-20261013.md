# 优化落地验收与补充修复

日期：2026 年 10 月 13 日。对象：本地 `DocSync-main`，不代表远程 main 已更新。

## 结论

优化说明中列为“已完成”的 13 个方向均有实际代码和检查依据，并非只有文档。再次按异常输入、分页操作和复扫失败等边界验收时，发现初版仍有遗漏，本次已修复下述 6 类问题并重跑测试。

这里的“落地”不表示软件已经支持所有语言、具备在线扫描后端或完成正式泛化评测；这些在原文中列为后续工作，仍未完成。

## 对照文档逐项核验

所有前端路径均相对于 `DOCsync-demo-video-package/demo-ui/`。

| 文档承诺 | 实际实现 | 验收依据 |
| --- | --- | --- |
| 跨页面使用同一报告 | `report-store.js` 的 save/load，`app.js` 与 `portal.js` 共用模型 | 导入、刷新、跨五页导航，保持同一运行标识 |
| 证据不伪造 | `app.js` 的 fillCode/renderFinding，`portal.js` 的证据渲染 | 无冲突时清除旧证据；不确定项不补造 Finding；外来文本不成为 HTML |
| 搜索、筛选、分页和定位 | `app.js` 的 filterRecords/renderRecords/applyDataset | 多记录、零匹配、分页、深链接与重置筛选检查 |
| 不确定项正确计数 | `report-store.js` 的 summarize/uncertainJudgments/records | rejected 与不确定判断按 claim_id 去重，缺字段不当零 |
| 异常报告不破坏当前报告 | normalize/validate 后再接入 UI | 坏 JSON、未知版本、异常嵌套对象导入被拒，当前报告保持 |
| 过期忽略规则可解释 | `app.js` 的 renderFinding | 保留原因、截止日期，有效告警仍计数，已忽略项不提供补丁 |
| 自行导入复扫报告 | `report-store.js` 的 compare 和 app.js 的 importFile/renderVerification | 不同仓库/基准/配置/范围/运行条件拒绝；失败或不完整结果不显示完成状态 |
| 导出真实数据与 diff | app.js 下载、portal.js exportJSON | 导出 JSON 重新解析后与原报告深比较；diff 与原始建议逐字相同 |
| CLI 环境预检 | `src/docsync/doctor.py`，`cli.py` 注册命令 | doctor 回归，包括无依赖运行、Git、配置、模型需要条件及不泄露密钥 |
| 补丁输出防覆盖 | `src/docsync/cli.py` 排他创建 | 拒绝既有文件、diff/manifest 同路径、检查后被其他进程创建的文件 |
| 本地启动不暴露工作区 | `scripts/serve_frontend.py`，启动前端.cmd | 127.0.0.1、资源白名单、禁止写入、父路径、异常 Host/Origin 和链接守卫 |
| 可独立交接打包 | `scripts/package_frontend.py` | 精确清单、缺文件失败、不覆盖、竞态保护、链接路径保护；新版 ZIP 独立检查 |
| 工程质量检查 | Python/Node/浏览器测试及 CI 配置 | 本轮实际结果如下；没有把本地检查称为远程 CI 成功 |

## 这次具体补了哪些漏洞

| 实际发现 | 已实施的修复 |
| --- | --- |
| mode=rules 但 analysis_method=llm/no_static 时，doctor 原先说无需模型 | 模型需求判定与扫描引擎一致，补 4 个参数化回归实例 |
| uncertainty_reason、drift_type 等嵌套字段可混入对象，后续文本或筛选转换会出错 | 读取时拒绝不合结构的字段，保留契约允许的 null；新增反例测试 |
| 主报告有效，但缓存的复扫损坏时会连主报告一并丢弃 | 保留有效主报告，只放弃损坏复扫，显示持久提示 |
| 第三页选中记录后筛选回第一页，详情仍可能对应看不见的记录 | 翻页、筛选、重置后，详情选择始终对应当前页的一条可见记录 |
| 只有起始坐标时会出现 L4–undefined 之类文字 | 只显示报告实际提供的位置，不补造终止位置 |
| PARTIAL/FAILED 复扫仍可能在时间线上打勾，零冲突易被误读为完成 | 明确显示“复扫未完成”，时间线不打完成勾，使用警示卡片；含未验证告警也不会标成完成 |

数据层新增 4 个反例在旧实现上全部失败，修复后通过。浏览器边界首轮也实际复现了分页选中和坐标显示两项失败，修复后再验收通过，不是只检查代码里有没有函数。

## 最新实测结果

| 检查 | 结果 |
| --- | --- |
| Python 全量回归 | **283 passed、3 skipped，250.24 秒** |
| Node 数据契约 | **23 passed、0 failed** |
| 真正本地服务 + Chromium 148 | **28 组通过、0 失败** |
| 响应式检查 | 五页分别检查 320、390、768、1024、1440 像素，无页面横向溢出 |
| 浏览器异常 / CSP 违规 / 外部请求 | 均为 0 |
| Ruff / 格式 / mypy | 检查通过；64 文件格式通过；27 个源文件类型检查通过 |
| 离线构建 | wheel 和 sdist 的 --no-isolation 构建成功，未安装新依赖 |

3 个跳过仍是本机 Windows 没有创建真实符号链接的权限，不算测试通过。需要在有权限环境或远程 CI 补验。本轮未重做或改写正式样本金标，未调用模型产生所谓正式成绩。

浏览器记录与截图见 [补充验收证据](audit-samples/optimization-recheck-20261013/browser-results.json)。原始首轮失败记录保留在工作区 `tmp/docsync-optimization-audit-boundaries/`；最终原始浏览器记录在 `tmp/docsync-optimization-audit-final-verified/`。首次补充浏览器检查还暴露过测试脚本使用 toast 而非 reportNotice 的选择器错误，仅修正该断言后再次全量验证。测试服务均已关闭。

![复核版报告工作区](audit-samples/optimization-recheck-20261013/reports-desktop.png)

## 你现在打开、发送哪一个

打开本地新版：`DocSync-main/DOCsync-demo-video-package/启动前端.cmd`。不要继续打开旧目录或旧压缩包里的页面；已有页面可关闭后重新启动。

发队友：`交付/DocSync-前端交接包-20261013-复核版.zip`。完整解压到新文件夹，保留目录层次。旧包保留作版本记录，没有覆盖。

新版包含 24 个白名单文件，SHA-256：

~~~text
ce681de7c6af8fa875b83e6c32e64b7bd617a3cf35e61742760aba5b52c4b392
~~~

已将包内全部 24 项与当前源码逐字节核对，并独立解压启动自带服务：首页、报告页与 report-store.js 返回 200；父目录及私人标注路径返回 404。此次验证服务及其子进程已停止，监听端口已确认关闭。

前端 ZIP 不含核心扫描引擎、个人标注或导入的真实报告。核心构建产物只用于本轮构建检查；sdist 包含仓库原有审计档案，发布范围仍待审查，不能当成已审查完成的公开发布包。

## 仍未完成的事项

独立正式评测、真实用户试用、远程 CI 与仓库合并、网页直接扫描的安全后端、更多语言支持、长期历史与多人权限，均不在本次已完成结论里。前端仍是本地报告审阅工具；扫描与应用补丁依然通过 CLI 显式执行。

本次实施和自动验收使用 AI 辅助，不能代替团队本人审核、独立标注或真实用户反馈。没有推送 GitHub，也没有发布网站。
