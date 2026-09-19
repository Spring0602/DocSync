# 开发与验证

使用 Python 3.12 虚拟环境。常规开发安装 `python -m pip install -e '.[dev]'`。所有目标仓库只作为测试数据，不导入它们的模块或执行它们的安装脚本。

已提交 `requirements-dev.lock` 和 `requirements-runtime.lock`，锁定全部对应依赖及 Windows x64 / manylinux x86_64 的 wheel SHA-256。runtime 锁包含安装源码包所需的固定构建后端。更新流程：修改明确版本、下载两个目标平台的 wheel 到新目录、运行 `python scripts/lock_dependencies.py --wheels <目录>`，审阅变更后进行隔离安装测试；不要手工填写哈希。

提交前运行：

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build --no-isolation
```

当前支持 DEFAULT_VALUE、SIGNATURE 和 CONFIG 的明确子集。扩展类型必须同时修改模型、提取器、判定器、独立验证器、范围说明和正反例，不允许依靠模型置信分绕过证据门控。

新增第三方资源填写 `compliance/third_party_resources.csv`，新增评测数据填写 `compliance/data_rights.csv`。不要提交密钥、运行产物、虚拟环境、个人承诺书信息或未经授权的第三方仓库片段。AI 辅助修改需补充台账并由团队成员审核。

发布前在 Windows 和 Linux 验证锁文件安装，固定 Action 的完整提交 SHA，导出 Schema、生成 wheel/sdist 并检查包内文件。所有原始 DOCX/PDF 资料应保留在本地，公开仓库前单独确认再分发范围；构建包仅包含核心源码与必要元数据。
