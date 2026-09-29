# C2 验收记录：Action 本地场景与 CI 验证

- 执行人：C（由 AI 助手代为执行，C 复核）
- 执行日期：2026-09-29
- 环境：Windows 11，Python 3.12.1（venv），docsync-core 0.2.0（editable install）
- 提交基线：`1be73fe`（Add member A contract review and evaluation preparation）

## 一、本地基线检查

| 命令 | 结果 |
|------|------|
| `python -m pytest -q` | **112 passed, 1 failed**（5 分 09 秒） |
| 失败项 | `tests/unit/test_patch_guards.py::test_external_symlink_is_rejected` |

### 失败诊断（环境问题，非产品缺陷）

在该 Windows 设备上，`Path.symlink_to()` 创建的条目处于异常状态：
`link.is_symlink() == False`，`os.lstat(link)` 抛 `FileNotFoundError (WinError 2)`，
`resolve()` 不追踪到目标。此时 `safe_target` 的三个守卫（resolve 越界检查、
`target.is_symlink()`、父目录 symlink 检查）均无从触发，测试期望的
`DocSyncError` 未抛出。

证据：非管理员进程；`fsutil behavior query symlinkevaluation` 显示本地到本地已启用；
同样的守卫在真实符号链接上有效（Linux CI 将验证）。

**给 B 的加固建议**：`apply_patch` 中 `target.read_bytes()` 对此类坏引用会抛
`FileNotFoundError` 而非 `DocSyncError`，建议捕获并转换为 `UNSAFE_PATCH`，
使错误面收敛到统一的错误模型。

## 二、Action 本地六类场景复跑

演示仓库由 `scripts/create_demo.py` 生成（fixture：代码 `connect(timeout=60)`，
文档声明默认值 30）。全部产物在 `runs/c2-evidence/`（本地保留，不入库）。

| # | 场景 | 命令 | 结果 | 退出码 | 产物路径 |
|---|------|------|------|--------|----------|
| S1 | 无冲突 | `docsync scan --repo runs/c2-evidence/demo-clean --head HEAD --out runs/c2-evidence/s1-no-conflict` | `COMPLETED, confirmed=0` | 0 | `runs/c2-evidence/s1-no-conflict/` |
| S2 | 文档漂移 | `docsync scan --repo runs/c2-evidence/demo-drift --head HEAD --out runs/c2-evidence/s2-drift` | `COMPLETED, confirmed=1` | 0 | `runs/c2-evidence/s2-drift/` |
| S3 | 无密钥 | 同 S2 加 `--mode rules`，环境注入 `DOCSYNC_API_KEY=sk-fake-dummy OPENAI_API_KEY=sk-fake-dummy` | `COMPLETED, confirmed=1`；全产物 `grep sk-fake` 无泄漏 | 0 | `runs/c2-evidence/s3-no-secret/` |
| S4 | 缺失 base | 同 S2 加 `--base 0000000000000000000000000000000000000000` | 结构化失败 `FAILED / MISSING_REF`（"Cannot resolve reference; fetch the required commit first"） | 2 | `runs/c2-evidence/s4-missing-base/` |
| S5 | 注入文本 | 在 demo-drift README 追加提示词注入文本并提交后扫描（`--mode rules`） | 注入文本被当作数据，仍 `confirmed=1`，无指令被采纳 | 0 | `runs/c2-evidence/s5-injection/` |
| S6 | 模型超时 | hybrid 模式，endpoint 指向不可路由地址 `http://10.255.255.1:9999`，`timeout_seconds=2`（配置：`runs/c2-evidence/timeout-config.toml`） | `PARTIAL`，静态规则仍确认 1 条冲突，报告记录 timeout 失败；模型超时未被记为成功 | 0 | `runs/c2-evidence/s6-timeout/` |
| S6b | 部分扫描+要求完整 | 同 S6 加 `--require-complete` | `PARTIAL` | **3** | `runs/c2-evidence/s6-require-complete/` |

结论：六类场景全部符合预期——无冲突不虚报、漂移必报、规则模式不依赖密钥、
缺失引用明确报错、注入文本不改变判定、模型超时返回 PARTIAL 且不伪造结论。

## 三、远程 CI

- 触发方式：本记录随分支 `c2-action-verification` 推送，`ci.yml`（`on: push`）自动触发。
- **运行链接**：https://github.com/Spring0602/DocSync/actions/runs/36589298331
- **提交 SHA**：`e6315f2`（父提交 `1be73fe`）
- **结果：2/2 作业全部成功** ✅
  - `check (ubuntu-latest)`：success（pytest / ruff check / ruff format / mypy / build）
  - `check (windows-latest)`：success——`test_external_symlink_is_rejected` 在远程正常
    Windows 环境下通过，进一步证实本地失败为环境问题而非产品缺陷
- 无失败日志需要修复；此前 main 与 member-b-tasks 分支也已有真实 CI 运行记录
  （run 35489771490 / 36451523193 等），"远程 CI 尚未执行"的 README 描述已过时。

## 四、待办

- [x] 补充远程 CI 运行链接、SHA（2026-09-29 完成，见第三节）
- [ ] B 确认符号链接加固建议（apply 建议把 FileNotFoundError 转为 UNSAFE_PATCH）
- [ ] Action 示例中的第三方 Action 已使用固定 SHA；待首次真实发布后替换为实际发布提交
