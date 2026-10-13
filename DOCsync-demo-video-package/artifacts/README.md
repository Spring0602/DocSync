# 可验证演示工件

本目录工件由当前 DocSync 源码真实运行生成，用于验证网页默认演示数据和录屏中的技术表述。

| 文件 | 用途 |
|---|---|
| `before-report.json` | 补丁前完整 Schema 2.0 扫描报告 |
| `before-report.md` | 补丁前人类可读报告 |
| `fixes.patch` | 从报告导出的最小文档补丁 |
| `fixes.patch.json` | 补丁清单、preimage 与校验信息 |
| `after-report.json` | 应用补丁后的完整工作树复扫报告 |
| `after-report.md` | 复扫后人类可读报告 |
| `SHA256SUMS` | 上述工件的 SHA-256 校验值 |

生成结果：补丁前 1 条确认冲突，补丁后 0 条确认冲突；两次状态均为 `COMPLETED`，规则模式模型请求数均为 0。

这些工件仅证明受支持静态声明范围内的演示结果，不代表任意仓库中的所有文档语义都已验证。
