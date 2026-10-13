# 产品体验优化验证记录

日期：2026 年 10 月 13 日。对象是当前本地源码，不是新的远程提交或 CI 运行。当前下载目录没有 .git 元数据，源文件 SHA-256 记录在 cli-evidence.json，不能据此宣称已同步远程最新 main。

## 最终结果

| 检查 | 实际结果 |
| --- | --- |
| Python 全量测试 | 279 passed、3 skipped，117.63 秒 |
| Node 数据层测试 | 19 passed |
| 浏览器交互 | Chromium 148.0.7778.96，21 组检查通过 |
| 真正本地启动器 | 在 serve_frontend.py 服务下完成浏览器全流程 |
| 响应式布局 | 五页分别检查 320、390、768、1024、1440 像素，无页面横向溢出 |
| 浏览器运行 | 无未捕获异常、无 CSP 违规、无外部请求 |
| Ruff | 检查通过，64 个文件格式通过 |
| mypy | src 和 scripts 共 27 个源文件通过 |
| 核心构建 | wheel 和 sdist 的 --no-isolation 构建成功 |
| 规则模式端到端 | 1 条冲突 → 0 条冲突，前后均 COMPLETED，模型请求均为 0 |
| 补丁前像保护 | 重复应用退出 2 / STALE_PATCH，README 哈希未变 |

Python 3.12.14；pydantic 2.11.7；markdown-it-py 3.0.0。运行时显式设置 PYTHONPATH 指向当前 src，并设置 PYTHONUTF8=1，避免旧 editable 安装和 Windows 中文路径默认编码干扰。

跳过的是 test_frontend_server.py 的真实符号链接用例与 test_patch_guards.py 的两个用例，原因是当前 Windows 进程不允许创建符号链接。免权限的链接守卫测试通过；3 个 skip 仍不能算系统分支已通过。

## 可复核文件

- [cli-evidence.json](cli-evidence.json)：命令、源码哈希、真实运行 ID、依赖与构建摘要。移除了本机环境目录字段；原报告文件字节未改动。
- [cli-before-report.json](cli-before-report.json) 和 [cli-after-report.json](cli-after-report.json)：本轮当前源码在受控演示仓库产生的真实报告。
- [fixes.patch](fixes.patch) 和 [fixes.patch.json](fixes.patch.json)：对应建议及校验清单。目标临时仓库已修复，不应重复应用。
- [browser-results.json](browser-results.json)：21 项测试名称和异常计数，使用真实 Python 本地服务；临时服务已关闭。
- [桌面截图](reports-desktop.png) 和 [手机截图](reports-mobile.png)：本轮真实浏览器截图，页面默认展示的是旧归档演示工件。

报告 SHA-256：

~~~text
cli-before-report.json  ef5d72bbc725a61dcb0e6217072b423a572242b5402b26e031d0a6ea26777110
cli-after-report.json   f183bca2fbadf9eef1d57e825a93e0b72a3c679c2e2018579f53485e881e9d7d
~~~

这里的哈希按当前文件原始字节计算，不是任意 CRLF/LF 转换后的工作区内容。传输后应先核对字节；不要改动报告后继续引用旧哈希。

## 复跑

在安装开发依赖的 Python 3.12 环境和具有 node:test 的 Node 环境中，从仓库根执行：

~~~powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = "$PWD\src"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src scripts
node --test DOCsync-demo-video-package/demo-ui/tests/report-store.test.cjs
python -m build --no-isolation --outdir runs/product-build
~~~

浏览器检查需要本机已安装的 Playwright 与 Chromium；脚本不自动下载，不是软件日常使用依赖。先运行本地服务，按输出的地址给测试脚本传参：

~~~text
python scripts/serve_frontend.py --no-browser
node scripts/qa_frontend.cjs --browser PATH_TO_CHROMIUM --playwright PATH_TO_PLAYWRIGHT --base-url http://127.0.0.1:PORT/ --out runs/frontend-qa
~~~

测试脚本使用临时合成记录检查界面边界，不是新制作正式金标。--base-url 指向外部服务时脚本不会关闭它，完成后在服务终端 Ctrl+C。

## 证据边界

这是工程回归和功能冒烟，不是独立准确率评测。没有调用付费模型，没有修改人工标注或冻结测试集，也没有推送 GitHub。CI 配置已增加前端数据测试和脚本类型检查，但本轮没有新的远程 CI 结果。

核心 wheel 不包含静态前端。前端通过单独的白名单交接 ZIP 分发；完整源码、核心安装包和前端包需要区分。更广泛的语言、框架、多人协作和网页扫描后端仍未实现。

源码分发 sdist 已显式纳入前端 HTML/CSS/JS、数据契约测试、启动入口、说明和原始演示工件，避免解压源码包后只有启动脚本却缺少页面。独立前端交接 ZIP 为 24 个文件，实际解压启动后首页与主要资源均返回 200，父目录与非公开工件路径返回 404。

注意：sdist 沿用仓库原有范围，包含 bench/annotations 和 docs/audit-samples 中的历史标注、复核归档，不能称为“不含个人标注的公开发布包”。本轮未重新确认这些既有档案的分发授权，且部分重建工具与回归测试依赖它们；未改动原始记录或为减小包而跳过来源核验。当前可交给队友的是另行验证的白名单前端 ZIP；核心源码公开发布前仍须审查分发边界。

前端交接 ZIP：DocSync-前端交接包-20261013.zip，24 个文件，71,145 字节。SHA-256：

~~~text
7e37d7a0fe56d7a60b795cf1473b0b5ee991307f7b01186e30fcd9a2be91a744
~~~
