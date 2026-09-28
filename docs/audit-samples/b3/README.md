# B3 规则审计样例

本目录保存 2026-09-28 使用 DocSync 0.2.0 规则模式生成的三类完整报告。样例均来自本项目自建的最小 Git fixture，不包含第三方代码、密钥或模型响应。

| 目录 | 固定 fixture 提交 | 规则 | Finding | 补丁 |
| --- | --- | --- | --- | --- |
| `default/` | `6c0b6246151b40bf3ee0bc08e76a0548c79efe3e` | `DEFAULT_VALUE/1` | 文档 30、代码 60 | `fix.patch` + `patch.json` |
| `config/` | `710cd36a67a555fe29ff23f7973fb697cd418393` | `CONFIG/1` | 文档 30、配置 60 | `fix.patch` + `patch.json` |
| `signature/` | `2ec5c7505464e42d0232e2d6a99fac8f5f09e283` | `SIGNATURE/1` | 缺少必选参数 | 无自动补丁；`report.md` 含人工处理提示 |

每个目录保留 `report.json`、`report.md`、manifest、snapshot 及各阶段 JSONL，便于从 Finding 追溯 claim、fact、entity、原始路径、字节区间和 blob hash。默认值与配置补丁由公开 `docsync patch` 命令从对应报告导出；签名规则不会编造必选参数值。

fixture 源文件保存在本地忽略目录 `runs/b3-review/fixtures/`，全量测试证据为 `runs/b3-review/pytest.xml`。这些本地运行产物用于复核，不随发布包分发；本目录中的审计报告会随 sdist 保留。
