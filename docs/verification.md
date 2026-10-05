# 实际验收记录

## 成员 B：到期日契约与坏链接复核（B-N3，2026-10-04）

A 已确认保持 Schema 2.0，并以非必填 `ignore_expires: date | null` 扩展 Finding。B 已完成模型、忽略匹配、固定扫描日期、Schema 和真实 1.0/2.0 旧报告兼容测试；过期规则保留原因/日期但不忽略告警，多规则不会混用元数据。异常补丁目标现在稳定转换为 `UNSAFE_PATCH`，Git symlink blob 继续拒绝；本机真实越界/dangling symlink 因系统权限无法创建，保留给有权限环境复验。

B-N3 专项 **11 passed**；相关联合回归 **109 passed，2 skipped**；全量回归 **198 passed，2 skipped**。Ruff 检查及格式检查通过，mypy 检查 20 个源文件无类型错误，wheel/sdist 构建成功。完整契约、兼容边界、测试证据和 C 的剩余报告工作见 [B-N3 复核记录](b-n3-ignore-expiry-symlink-review.md)。

## 成员 B：英文默认句式修复（B-N2，2026-10-04）

针对 C1 缺陷 D-1，新增 `The default value of X is Y` 提取支持及 `tests/integration/test_b_n2_english_defaults.py`。测试按失败优先编写：修复前专项 **6 failed**，修复后 **6 passed**；覆盖一致/冲突、旧版限定、同名歧义、显式源码链接、合法调用及含中文 CRLF 文档的 UTF-8 精确字节证据。

原有流水线与静态扩展联合回归 **56 passed**；全量回归 **186 passed，1 skipped**，唯一跳过仍为当前 Windows 进程无符号链接创建权限。Ruff 检查及格式检查通过，mypy 检查 20 个源文件无类型错误，wheel/sdist 构建成功。完整复现、矩阵和交给 C 的复验命令见 [B-N2 修复记录](b-n2-english-defaults-review.md)；当前状态是 B 本地完成、等待 C 独立复验，不提前宣称 D-1 已验收关闭。

## A 接收与发布准备（2026-09-30）

基线为合并提交 7db2456a1ff955f72eab2504169b17409c5ab4fb。本轮契约/指标/benchmark/provider/Action 专项 **39 passed**（runs/a-review-20260930/targeted.xml）；未将其累加为新的全量测试数。合并时全量记录为 180 passed/1 skipped。两种开发基线各 20 例，失败或部分完成为 0，标签仍 provisional。

Apache 官方许可证原文已落地，wheel/sdist 构建成功，wheel 内 License-Expression: Apache-2.0 及 LICENSE 字节一致性检查通过。远程 Core CI 36683440902 的 Windows/Linux 作业均成功。标注接收、许可证范围、C2 超时证据更正及四类验收结论详见 [A 接收与裁决记录](a-acceptance-20260930.md)。


## 成员 B：对齐、规则与补丁回归（2026-09-28）

新增 `tests/integration/test_b_alignment_patches.py`，专项测试 **15 passed**；与既有对齐、流水线、补丁守卫和契约测试联合执行 **90 passed，1 skipped**；全量回归 **180 passed，1 skipped，0 failed，0 errors**。Ruff 检查通过，44 个 Python 文件格式正确；mypy 检查 20 个源文件无类型错误。测试 XML 位于 `runs/b3-review/pytest.xml`。

本轮增加 canonical 行号/字节区间校验及确定性 patch ID、非空/唯一 finding ID 校验；伪造行号/ID、篡改 diff/hash/旧文本、重叠编辑、过期补丁和重复应用均在写入前拒绝。默认值和配置补丁只替换目标文档值，工作树复扫确认冲突消失；签名规则不生成补丁并在 Markdown 报告中给出人工处理提示。完整矩阵见 [B3 审核记录](b3-alignment-patch-review.md)，三类固定提交报告见 [B3 审计样例](audit-samples/b3/README.md)。

## 成员 B：静态事实扩展与验证（2026-09-28）

新增 `tests/integration/test_b_static_facts.py`，专项测试 **22 passed**；与既有静态扩展及主流水线联合执行 **78 passed**；全量回归 **165 passed，1 skipped，0 failed，0 errors**。Ruff 检查通过，40 个 Python 文件格式正确；mypy 检查 20 个源文件无类型错误。测试 XML 位于 `runs/b2-review/pytest.xml`。

本轮修复继承/元类方法、动态字典键覆盖和重复定义仍可能产生 KNOWN 事实的问题；明确区分字面量 `None`、`False`、`0`、无默认值和动态 UNKNOWN。新增唯一模块顶层直接/链式/相对重导出及包 `__init__.py` 的静态事实，别名事实继续引用原始实体和源码 blob；星号、条件、重绑定和运行时导出保持拒答。正例、反例、歧义、字节级溯源及跨提交稳定 ID 的证据见 [B2 审核记录](b2-static-facts-review.md)。

## 成员 B：包、Schema 与仓库快照审核（2026-09-28）

新增 `tests/integration/test_b_repository_contracts.py`，专项测试 **31 passed**；全量回归 **143 passed，1 skipped，0 failed，0 errors**。Ruff 检查通过，39 个 Python 文件格式正确；mypy 检查 20 个源文件无类型错误。唯一跳过仍是当前 Windows 进程无权创建真实文件系统符号链接；无需该权限的 Git symlink blob 用例实际通过。

本轮收紧 `FileRecord` 的安全相对路径、SHA-256 和非负大小约束，并拒绝重复快照路径；report/benchmark Schema 已重新生成。最终 wheel/sdist 构建成功，wheel 在新 Python 3.12 环境离线安装后 `pip check` 无错误，安装版 CLI 可用且导出的两个 Schema 与仓库文件完全相同。完整矩阵、命令和边界见 [B1 审核记录](b1-repository-review.md)，测试 XML 位于 `runs/b1-review/pytest.xml`。

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
