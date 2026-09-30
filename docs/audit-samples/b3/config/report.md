# DocSync 扫描报告

- 状态：COMPLETED
- 提交：`710cd36a67a555fe29ff23f7973fb697cd418393`
- 快照：commit；工作树 dirty=False
- 模式：rules；实际能力：默认值、支持的调用绑定、简单配置
- 纳入文件：2；提取事实：1；声明/示例：1
- 已确认（未忽略）：1；已忽略：0；不确定：0
- 范围说明：未提取的文本不代表一致；实际模型调用量、降级原因见 manifest。

## 285d2cdfeabf7bc47b828d1d

类型：CONFIG；证据：VERIFIED；忽略：False

文档：README.md:5

    `timeout` defaults to `30`.

代码：settings.py:1

    settings.CONFIG.timeout = 60

规则：CONFIG/1；两侧 SHA-256 见 JSON。

## 诊断

支持范围内未出现扫描故障。

## 补丁

补丁仅为文档修改建议，需要人工审阅后显式 apply。
内存复扫通过只代表支持范围内的目标告警消失，不代表文档整体正确。
