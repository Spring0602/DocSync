# A 技术裁决摘要

完整原始 B/C 内容和机器可读裁决见 adjudication.jsonl；不代替 A 人工签字。

| 样本 | 标签 | 统一实体 / 属性 | 代码行 | 文档行 | 理由 |
| --- | --- | --- | --- | --- | --- |
| candidate-01 | INCONSISTENT | case01.PageReader.__init__ / encoding | 2 | 5 | 签名默认编码为 utf-8，文档声明 utf-16，字面值冲突。 |
| candidate-02 | CONSISTENT | case02.download_resource / retries | 1 | 5 | 异步函数的 keyword-only 参数 retries 默认整数 4，与文档一致。 |
| candidate-03 | INCONSISTENT | case03.emit_record / tags | 1 | 5 | 默认元组第二项为 public，文档为 internal，类型相同但值不同。 |
| candidate-04 | CONSISTENT | case04.MemoryBuffer.__init__ / capacity | 2 | 5 | 比较调用接口默认参数 None；函数体将 None 转换为 32 不改变签名默认值。 |
| candidate-05 | INCONSISTENT | case05.read_batch / limit | 1-6 | 5 | 默认参数在定义时绑定 BATCH_LIMIT=12；末行重绑定为 24 不改变已绑定默认值。 |
| candidate-06 | CONSISTENT | case06.encode_packet / codec | 1-4 | 5 | 按模块正常初始化完成后的接口比较：显式 __defaults__ 赋值使 codec 为 utf-8，与文档一致。 |
| candidate-07 | INSUFFICIENT | case07.flush_records / interval | 1-7 | 5 | 定义时调用读取环境变量的函数；无环境值证据，fallback 8 不能证明本次值为 8。 |
| candidate-08 | CONSISTENT | case08.export_records / format_name | 1-5 | 5 | 固定源码中的无参辅助函数无条件返回 json，定义时绑定该返回值；可由源码推理，与文档一致。 |
| candidate-09 | CONSISTENT | case09.attach_volume / signature | 1 | 6-8 | 字面量字典展开提供必需 readonly，位置参数绑定 name，签名合法。 |
| candidate-10 | INCONSISTENT | case10.send_notice / signature | 1 | 6-8 | 元组展开传入两个位置参数，但 channel 是 keyword-only；参数绑定不合法。 |
| candidate-11 | CONSISTENT | case11.place_marker / signature | 1 | 6-9 | 元组为 x/y 提供两个位置值，字典提供 color 关键字，满足 / 和 * 的约束。 |
| candidate-12 | INSUFFICIENT | case12.queue_notice / signature | 1-8 | 6-7 | 展开参数来自环境 JSON；不能证明字典类型、priority 是否存在及是否有多余键，保留证据不足。 |
| candidate-13 | CONSISTENT | case13.ArtifactStore.open / signature | 1-3 | 6-7 | classmethod 自动绑定 cls，显式 root 与 create 参数匹配；只判断绑定，不要求运行示例。 |
| candidate-14 | INCONSISTENT | case14.Formatter.render / signature | 1-3 | 6-7 | staticmethod 不自动注入接收者；width 是 keyword-only，示例却按位置传入，冲突。 |
| candidate-15 | INCONSISTENT | case15.Registry.register / signature | 1-2 | 6-8 | 实例自动绑定 self；name 为 positional-only，示例将 name 作为关键字，冲突。 |
| candidate-16 | INSUFFICIENT | case16.dispatcher().deliver / signature | 1-14 | 6-7 | 运行时可能选 LocalDispatcher 或 RemoteDispatcher，后者还要求 token；环境未知，不能唯一判断。 |
| candidate-17 | INCONSISTENT | case17.RETRY_WINDOW / value | 1-2 | 5 | 按顺序执行模块赋值后值为 14；文档仍声明 6，冲突。 |
| candidate-18 | CONSISTENT | case18.PORT / value | 1-2 | 5 | 固定整数字面量增强赋值 8020+3 的结果为 8023，与文档一致。 |
| candidate-19 | INSUFFICIENT | case19.ARCHIVE_LEVEL / value | 1-6 | 5 | 条件分支依赖 ARCHIVE_PROFILE，可能得到 2 或 7；未规定环境，保留证据不足。 |
| candidate-20 | CONSISTENT | case20.SERVICE_OPTIONS / workers | 1-2 | 5 | 字面量字典经明确 update 后 workers 为 6，与文档一致；不是只读首次赋值。 |
| candidate-21 | INCONSISTENT | case21.PIPELINE.export / compression | 1 | 5 | 嵌套字典的 compression 为 gzip，文档声明 zstd，冲突。 |
| candidate-22 | CONSISTENT | case22.RETRY_DELAYS / value | 1 | 5 | 元组类型、顺序和值均为 (1,3,9)，与文档一致。 |
| candidate-23 | INSUFFICIENT | case23.STORAGE.local / root | 1-3 | 5 | 路径值读取 STORAGE_ROOT，./cache 只是环境未设置时的分支；环境缺失，保留证据不足。 |
| candidate-24 | CONSISTENT | case24.CACHE / enabled | 1 | 5 | 未重绑定内置 dict，关键字构造明确给出 enabled=True；类型和值与文档一致。 |
