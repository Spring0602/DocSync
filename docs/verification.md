# 实际验收记录

## 成员 A 契约审查（2026-09-20）

新增 `tests/integration/test_a_contract_review.py`，使用实际 0.1.0 归档报告和新生成的 2.0 报告验证读取、渲染、证据保留、补丁导出、篡改拒绝、失败格式、退出码优先级及 Schema/配置边界。实际执行 **14 passed**，证据为 `runs/a-review/contracts.xml`。这不是重新执行全量测试后的总数，不能直接覆盖下面的历史回归记录。

另复跑指标与 benchmark 测试 **8 passed**，证据为 `runs/a-review/metrics.xml`；新增测试文件 Ruff 检查与格式检查通过。本轮共执行 22 项且全部通过，未重复运行全量回归。契约解释、评测准备及本地/真实模型/远程 CI/人工审核四类状态见 [A 的审查记录](a-contract-review.md)。本轮没有真实模型请求、人工代签或远程推送。

## 0.2.0 收尾验收

记录日期：2026-09-19。Windows 本地执行；测试 XML 时间为 2026-09-18。以下记录取代首轮中已完成事项的待办状态，首轮记录保留供追溯。

| 检查 | 实际结果 |
| --- | --- |
| 完整 pytest 回归 | **98 passed，1 skipped，0 failed，0 errors**；57.903 秒；`runs/verification-v2-release/pytest.xml` |
| Ruff 检查及格式检查 | 通过，37 个 Python 文件格式正确 |
| mypy | 20 个源文件，无类型错误 |
| 0.2.0 wheel / sdist | 最终代码重新构建成功 |
| 隔离环境安装最终 wheel | 离线、无依赖重装成功；`pip check` 无错误 |
| 已安装 CLI 实际扫描 | COMPLETED，确认冲突 1，待核查 0；`runs/installed-v2-release/report.json` |
| Action 本地场景 | 无冲突、文档漂移、无密钥、缺失 base、注入文本、受控模型超时均通过；未冒充远程 CI |
| 开发种子集及规则评测 | 20 例逐样本运行，无失败/部分完成；TP=11、FP=0、TN=5、FN=0，另 4 例证据不足均拒答 |
| 关键词基线 | 20 例逐样本运行，TP=4、FP=1、TN=4、FN=7；保留拒答和证据不足误判记录 |
| 未配置模型的 LLM 方法 | 20 例均记录 PARTIAL，未发起真实模型请求，不生成虚假成功预测 |

新增回归覆盖签名绑定、实例/类接收者、配置常量及字典、顺序敏感的导入别名、重绑定、表格和源码链接、重复调用的稳定 ID、结构化响应、预算、缓存、超时重试、模型用量审计、忽略规则、评测数据划分及失败计数。模型测试采用受控传输，不等于线上服务验证。

唯一跳过仍是 Windows 文件系统符号链接权限用例，Git symlink blob 用例已通过。开发种子集是自建且标签待双人复核，以上结果不能作为正式测试集准确率。评测产物位于 `runs/bench-rules-v2-final`、`runs/bench-keyword-v2-final` 和 `runs/bench-llm-unconfigured`。

尚待实际验收：用户确认暂未准备的真实模型服务、团队双人标注/权利审核、远程 GitHub Actions、Linux/第二设备执行。GitHub 工作流已编写，但没有远程成功运行记录。任务范围及责任见 [tasks.md](tasks.md)。

## 首轮实际验收记录

日期：2026-09-17。环境：Windows、Python 3.12.2、Git 2.52.0.windows.1。全部结果来自本地实际执行；不代表完整 P0、Linux 远程 CI、真实模型实验或社区验证完成。

| 检查 | 实际结果 |
| --- | --- |
| 安装开发包 `pip install -e '.[dev]'` | 成功，CLI 可用 |
| `pytest -q --junitxml=runs/verification/pytest.xml` | **41 passed，1 skipped，0 failed**；25.96 秒 |
| `mypy` | 17 个源文件，无类型错误 |
| `ruff check .` | 通过 |
| `ruff format --check .` | 27 个 Python 文件格式通过 |
| `python -m build --no-isolation` | wheel 和 sdist 构建成功 |
| `docsync schema --out schemas/report.schema.json` | 1.0 报告 Schema 已导出 |
| 新虚拟环境 + `--require-hashes --no-index` 安装 | runtime 锁和本地 wheel 安装成功 |
| 隔离环境安装后的 `docsync --help` / `scan` | 成功，默认值冲突数为 1 |
| 隔离环境从源码 `--no-deps --no-build-isolation` 安装 | 成功；`pip check` 无缺失/冲突依赖 |
| 真实最小演示 | 检测 1 条默认值冲突；合法调用示例不告警 |
| 显式应用演示补丁 + working-tree 复扫 | 仅 README 默认值由 30 改为 60；复扫确认冲突为 0 |
| Action Python 包装器本地测试 | 输出报告/补丁路径及计数，与 CLI 一致 |

回归覆盖：固定快照与 dirty 隔离、缺失 base、仅代码变化、大小上限、Git blob 符号链接、中文/CRLF 字节偏移、全部参数形态、None 与动态工厂默认值、bool/int 类型差异、同名歧义和 top-K 截断、旧版/条件语境、合法显式参数、损坏围栏、语法错误隔离、hybrid 降级、伪造 ID/行号/指令字段、只允许 Markdown、重叠/过期补丁、重复应用、多编辑偏移、多文件回滚、补丁复扫必须重新找到一致声明、指标中的拒答/失败/零分母。

唯一跳过：Windows 当前进程没有创建文件系统符号链接的权限，`test_external_symlink_is_rejected` 自动跳过。另一个不需要操作系统链接权限的 Git symlink blob 集成测试已通过；真实文件系统链接用例待 Linux CI 补验。

迭代中曾发现的失败已修复：带“通常”的默认句式没有生成待核查声明；初始类型标注和格式问题。最终失败项为 0。安装时移除了不存在的可选类型存根包，markdown-it-py 自带类型信息已足够完成检查。

可查看本机证据：`runs/demo/report.json`、`runs/demo/report.md`、`runs/fixes.patch`、`runs/after/report.json`、`runs/installed-demo/report.json`、`runs/verification/pytest.xml`。这些是本地生成产物，已被 Git 忽略。测试用例使用自建内容，不是历史开源评测数据。

未验收：生产模型请求、超时/限流网络适配、真实模型样本、完整签名和配置检测、20 例人工标注种子集、Benchmark/消融运行器、远程 GitHub Actions、完整传递资源人工许可核查、团队版权确认、Linux/第二设备实际执行。责任与后续步骤见 [tasks.md](tasks.md)。
