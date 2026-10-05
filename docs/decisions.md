# 实现决策

依据：项目根目录《DocSync项目策划案与开发执行规格.docx》，第 8—19、28 章。本文保留首轮 S0 决策并在文末记录第二轮演进；首轮表格不代表当前能力清单，当前状态以 tasks/limitations 为准。

| 决策 | 当前选择 | 原因与后续 |
| --- | --- | --- |
| 技术基线 | Python 3.12、src 单包、Pydantic 2、argparse | 与开发机一致，避免服务化和额外 CLI 框架 |
| 首个真实链路 | 明确默认值声明 DEFAULT_VALUE | 按首轮验收例跑通快照、对齐、判断、验证、补丁；签名和配置为后续独立规则 |
| 判定边界 | 带函数归属的中文/英文单行默认声明 | 任意自然语言、参数表 default 列、链接与 import 对齐尚未支持 |
| 快照 | 默认从 Git blob 读取 | 不 checkout、不导入目标、不执行其测试；工作树必须显式选择 |
| 字节定位 | UTF-8 原始字节，SHA-256，行号 1 基 | 兼容中文、CRLF；非 UTF-8 返回诊断，暂不做编码转换 |
| 候选 | 精确符号及点分后缀，歧义拒答 | top-K 截断前检查歧义；不引入 embedding |
| base/head | 记录差异，全量回退 | 保证未变 README 仍检查；增量优化延后 |
| AI | Protocol、严格响应校验、提示词草案 | 未选择未经团队确认的模型服务；hybrid 显式 PARTIAL，禁止模拟成功 |
| 补丁 | 仅明确字面值替换，内存复扫 | 默认只导出；显式 apply 才写入；保留代码示例、编码和换行 |
| 多文件应用 | 全部预检、逐文件原子替换、异常回滚 | 非跨文件系统事务；并发编辑及磁盘故障仍需谨慎处理 |
| 配置 | 仅显式 --config，拒绝未知字段 | 不自动执行或加载被扫描项目插件 |
| Action | 从调用方固定的可信 Action 提交安装工具 | 不从目标 PR 安装；仅规则模式，不自动评论或发 PR |
| 许可 | 拟 Apache-2.0，确认前不授予整体资料许可 | 原始附件和承诺书与新建代码分离；权利审核为发布前任务 |

依赖版本为本轮选择的明确版本，非“最新版”声明。开发检查与真实执行结果见 [verification.md](verification.md)。

实现参考：[Python AST](https://docs.python.org/3.12/library/ast.html)、[markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html)、[Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/)。实际兼容性以锁定版本测试为准。

## 第二轮演进 2026年9月18日

- 工具升至 0.2.0，新增签名/配置事实及模型/耗时字段，Schema 升至 2.0，兼容旧报告读取。
- 增加参数表、源码链接、代码围栏 import/实例别名与静态参数绑定；复杂动态定义/装饰器/重绑定采取拒答。
- HTTP Provider 使用标准库 urllib，不增加网络 SDK 依赖；endpoint/model/key 环境变量显式配置，默认规则模式。用户确认模型服务暂未准备，真实试运行保留待办。
- 预算为每次 scan 的保守 Token 预留，与实际 API usage 分开；失败用量未知单列。缓存可选，模型状态持久化，不把格式正确当语义正确。
- 增加 20 个受控开发种子和统一 Baseline/消融运行入口，标签标 provisional；不伪造人工双标和真实数据来源。
- 确认项目远程地址为 `https://github.com/Spring0602/DocSync.git`，只读 ls-remote 返回空 refs。远程 CI 需要首次提交后才能验证。

## 2026-09-30 A 接收决定

用户确认全员同意 Apache-2.0，落地原创代码/自建样本授权；原始附件排除。合并版 Core CI 已成功，更新此前空仓库结论。C 的预填表不视为人工标签，正式数据冻结暂不通过。具体证据及 C2 超时记录更正见 [A 接收记录](a-acceptance-20260930.md)。
