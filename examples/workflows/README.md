# GitHub Actions 接入

`action/action.yml` 是 Linux runner 的 composite Action，目标仓库仅作为数据。下面固定到已通过双平台 Core CI 的合并提交 `7db2456a1ff955f72eab2504169b17409c5ab4fb`。这是经验证的开发提交，不是正式发布 tag；不能使用被扫描 PR 的工具版本。

```yaml
name: Documentation drift
on: [pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 0
          path: target
          persist-credentials: false
      - uses: Spring0602/DocSync/action@FULL_TRUSTED_COMMIT_SHA
        id: docsync
        with:
          repo-path: target
          head: ${{ github.event.pull_request.head.sha || github.sha }}
          base: ${{ github.event.pull_request.base.sha || '' }}
          mode: rules
          fail-on: none
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        if: always()
        with:
          name: docsync-report
          path: ${{ runner.temp }}/docsync-*/report.*
```

需要完整中间产物及补丁时上传 `docsync-*/` 内的报告文件；不要上传 `docsync-venv/`。fork PR 不需要也不接收模型密钥。禁止改为高权限 `pull_request_target` 并执行不可信 PR 代码。浅克隆缺少 base 时先取回固定对象，当前工具会明确返回 MISSING_REF。

核心 CI 配置 push / pull_request / workflow_dispatch；`.github/workflows/docsync.yml` 是项目自身的文档扫描工作流，PR 时从可信 base.sha 检出工具、从 head.sha 检出目标数据，两个目录分开，始终规则模式且无模型 Secrets。六类场景由本地测试覆盖，其中模型超时为受控传输；远程 Windows/Linux 矩阵尚待首次推送后验证，不能把本地通过写成 GitHub 运行成功。第三方 Action SHA 已通过官方仓库标签核对；升级时重新核对来源、审阅变更并重跑回归。
