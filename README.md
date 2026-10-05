# DocSync

团队后续开发请先阅读 [三位成员任务清单](docs/tasks.md)：明确 A/B/C 当前优先事项、交付物与依赖；最新裁决见 [A 接收记录](docs/a-acceptance-20260930.md)。

面向 Python 与 Markdown 的代码—文档一致性检测工具。当前 0.2.0：读取固定 Git 快照，检测明确默认值、支持的调用签名和简单配置冲突，独立验证证据，生成报告和最小文档补丁。

**已实现：三类静态规则、可配置 AI 适配器、评测运行器和 Action 包装。** 默认规则模式不需要密钥。真实模型服务暂未配置，20 例自建种子标签待人工复核，远程 CI 尚未执行；详细范围见 [能力边界](docs/limitations.md)、[验收记录](docs/verification.md) 和 [开发任务](docs/tasks.md)。

## 安装

需要 Python **3.12** 和 Git。Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\docsync.exe --help
```

Linux/macOS：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/docsync --help
```

后续示例的 `docsync`、`python`、`pytest` 均指虚拟环境内命令；可先激活环境。Windows x64 / Linux x86_64 的 Python 3.12 可用 `python -m pip install --require-hashes -r requirements-dev.lock` 安装完整锁定依赖，再执行 `python -m pip install --no-deps --no-build-isolation .`。其他平台暂使用常规安装，哈希锁需补对应 wheel。见 [贡献指南](docs/contributing.md)。本地原始策划案、承诺书和竞赛附件不属于软件包或默认公开资产。

## 五分钟跑通

```powershell
.\.venv\Scripts\python.exe scripts/create_demo.py --out runs/demo-repo
.\.venv\Scripts\docsync.exe scan --repo runs/demo-repo --out runs/demo
.\.venv\Scripts\docsync.exe patch --report runs/demo/report.json --out runs/fixes.patch
```

打开 `runs/demo/report.md` 和 `runs/fixes.patch`。演示源代码为 `connect(timeout=60)`，文档明确声明默认值为 30，同时包含合法的 `connect(timeout=30)` 示例。应当只确认 **1 条**默认值冲突，补丁只替换默认说明中的数字。

审阅后显式应用，并扫描工作树：

```powershell
.\.venv\Scripts\docsync.exe apply --repo runs/demo-repo --patch runs/fixes.patch --manifest runs/fixes.patch.json
.\.venv\Scripts\docsync.exe scan --repo runs/demo-repo --working-tree --out runs/after
```

复扫应为 0 条确认冲突。再次应用原补丁会报 `STALE_PATCH`。默认扫描读取提交对象，**不会包含未提交的修复**；只有 `--working-tree` 才包含它们。

## 检查自己的项目

```bash
docsync scan --repo /path/to/git-root --head HEAD --out runs/check
docsync scan --repo /path/to/git-root --base BASE_SHA --head HEAD_SHA --fail-on warning
docsync scan --repo /path/to/git-root --config docsync.toml --mode hybrid --require-complete
```

配置仅通过 `--config` 显式加载。`base/head` 当前保留变更清单并全量检测，以覆盖“代码变了而文档未变”；缺失引用明确报错。`hybrid` 可通过 [模型配置示例](examples/hybrid.toml) 接入服务，无配置时返回规则结果和 `AI_UNAVAILABLE/PARTIAL`。服务故障返回不确定，不产生模拟 AI 结论。细节见 [模型适配器](docs/model-provider.md)。

每次运行使用新的 `--out` 目录，不覆盖已有实验；不指定时自动创建 `runs/<id>`。扫描失败也会在新目录写入结构化失败工件。可在配置的 `[[ignores]]` 中指定规则/路径/原因/到期日，报告单列忽略计数。

退出码：`0` 未触发阻断；`1` 确认问题触发 `--fail-on warning`；`2` 输入/运行失败；`3` 部分扫描且要求完整。默认 `fail-on=none`，退出 0 不代表没有告警。`COMPLETED` 仅表示当前声明支持范围内完成。

## 目录

```text
src/docsync/       数据模型、配置、CLI、核心流水线
  repository/     只读 Git / 显式工作树快照
  extractors/     Python AST、Markdown 明确声明
  alignment/      确定性候选与歧义处理
    llm/            规则判定、HTTP Provider、预算/缓存/响应校验
  verification/   原始 blob 重定位与独立复核
  patches/        最小 diff、内存复扫、哈希防护应用
  reporting/      JSON、JSONL、Markdown
tests/            单元测试与真实 Git 仓库集成测试
examples/         自建演示仓库、CI 接入说明
bench/            20 例受控种子构建器、评测契约和指标（正式实验待完成）
action/           复用 CLI 的只读 composite Action
docs/             架构、决策、限制、任务与验收
compliance/       资源、数据权利、AI 辅助台账
scripts/          演示构建、Schema 导出等开发工具
```

## 开发检查

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build
docsync schema --out schemas/report.schema.json
docsync schema --kind benchmark --out bench/schema/sample.schema.json
```

Schema 已升级至 2.0，并兼容读取首轮 1.0 报告。运行受控开发评测：

```bash
python bench/builders/build_seed.py --out runs/my-seed
docsync benchmark --manifest runs/my-seed/manifest.jsonl --method rules --out runs/my-rules
docsync benchmark --manifest runs/my-seed/manifest.jsonl --method keyword --out runs/my-keyword
```

真实模型准备后可用 `--method full/llm/no_alignment/no_verifier/no_static` 的相应单个值，配合 `--config` 运行。方法边界、失败计分和人工标注要求见 [评测说明](docs/benchmark.md)。

项目原创代码及自建样本采用 Apache-2.0（团队于 2026-09-30 确认）。原始策划案、竞赛附件和个人承诺书不在授权范围内；第三方资源遵循各自许可证。参见 [LICENSE](LICENSE)、[授权范围](docs/license-scope.md)和[第三方台账](compliance/third_party_resources.csv)。
