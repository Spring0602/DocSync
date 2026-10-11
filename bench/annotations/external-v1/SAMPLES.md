# 样本导航

坐标均为完整原文件行号。代码入口只是查阅提示，最终标签/类型/实体/证据坐标由标注者独立填写。

## external-01：默认超时数值

核对文档所述默认超时数值与库的默认配置；不评估真实网络是否在精确时刻抛异常。

来源：encode/httpx，固定提交 `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`。

文档：[docs/advanced/timeouts.md](external-01/document_path.txt)，焦点 3-4 行。

代码：[httpx/_config.py](external-01/code_path.txt)，查阅入口 246 行。

补充上下文：`context/external-source-01/`，索引见 context-index.json。

## external-02：顶层 get 调用

核对示例中位置参数和 timeout 关键字能否按该接口绑定。

来源：encode/httpx，固定提交 `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`。

文档：[docs/advanced/timeouts.md](external-02/document_path.txt)，焦点 10-12 行。

代码：[httpx/_api.py](external-02/code_path.txt)，查阅入口 174-186 行。

补充上下文：`context/external-source-01/`，索引见 context-index.json。

## external-03：客户端 get 调用

核对已构造 client 的 get 调用绑定，包括 timeout 关键字。

来源：encode/httpx，固定提交 `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`。

文档：[docs/advanced/timeouts.md](external-03/document_path.txt)，焦点 14-16 行。

代码：[httpx/_client.py](external-03/code_path.txt)，查阅入口 1036-1047 行。

补充上下文：`context/external-source-01/`，索引见 context-index.json。

## external-04：禁用请求超时的配置

核对示例 timeout=None 对超时配置的含义，沿调用链查看；不以实际外部网络行为作证。

来源：encode/httpx，固定提交 `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`。

文档：[docs/advanced/timeouts.md](external-04/document_path.txt)，焦点 19-23 行。

代码：[httpx/_config.py](external-04/code_path.txt)，查阅入口 86-130 行。

补充上下文：`context/external-source-01/`，索引见 context-index.json。

## external-05：初始日志输出配置

核对导入 logger 后文档所述初始输出位置；保留原文限定及配置/环境条件。

来源：Delgan/loguru，固定提交 `0412a60d6aff63a4ed009c7445993b42d294c2f1`。

文档：[README.md](external-05/document_path.txt)，焦点 64-66 行。

代码：[loguru/__init__.py](external-05/code_path.txt)，查阅入口 18-32 行。

补充上下文：`context/external-source-02/`，索引见 context-index.json。

## external-06：debug 调用

核对 logger.debug 示例的参数绑定；不评估实际日志内容或终端效果。

来源：Delgan/loguru，固定提交 `0412a60d6aff63a4ed009c7445993b42d294c2f1`。

文档：[README.md](external-06/document_path.txt)，焦点 68-72 行。

代码：[loguru/_logger.py](external-06/code_path.txt)，查阅入口 2205-2207 行。

补充上下文：`context/external-source-02/`，索引见 context-index.json。

## external-07：添加 sink 的调用

核对 logger.add 示例中 sink 和 format/filter/level 的绑定；sys.stderr 按示例引用处理。

来源：Delgan/loguru，固定提交 `0412a60d6aff63a4ed009c7445993b42d294c2f1`。

文档：[README.md](external-07/document_path.txt)，焦点 80-84 行。

代码：[loguru/_logger.py](external-07/code_path.txt)，查阅入口 273-288 行。

补充上下文：`context/external-source-02/`，索引见 context-index.json。

## external-08：移除 handler 的调用

核对 logger.remove() 无参数调用与文档所指移除范围，勿只按方法名称判断。

来源：Delgan/loguru，固定提交 `0412a60d6aff63a4ed009c7445993b42d294c2f1`。

文档：[README.md](external-08/document_path.txt)，焦点 88 行。

代码：[loguru/_logger.py](external-08/code_path.txt)，查阅入口 1072-1118 行。

补充上下文：`context/external-source-02/`，索引见 context-index.json。

## external-09：load_dotenv 无参调用

仅核对 load_dotenv() 调用绑定；此条不把示例后的环境变量实际值作为待评估事实。

来源：theskumar/python-dotenv，固定提交 `0b2880591780a426b0551436f47a17e7a76d954f`。

文档：[README.md](external-09/document_path.txt)，焦点 36-43 行。

代码：[src/dotenv/main.py](external-09/code_path.txt)，查阅入口 431-438 行。

补充上下文：`context/external-source-03/`，索引见 context-index.json。

## external-10：默认查找目录配置

核对文档所述默认查找起点/向上搜索策略，结合调用入口和上下文条件。

来源：theskumar/python-dotenv，固定提交 `0b2880591780a426b0551436f47a17e7a76d954f`。

文档：[README.md](external-10/document_path.txt)，焦点 45-47 行。

代码：[src/dotenv/main.py](external-10/code_path.txt)，查阅入口 376-428 行。

补充上下文：`context/external-source-03/`，索引见 context-index.json。

## external-11：override 默认设置

仅核对 override 的默认设置及其覆盖含义；不猜测外部 .env 内容。

来源：theskumar/python-dotenv，固定提交 `0b2880591780a426b0551436f47a17e7a76d954f`。

文档：[README.md](external-11/document_path.txt)，焦点 45-49 行。

代码：[src/dotenv/main.py](external-11/code_path.txt)，查阅入口 431-479 行。

补充上下文：`context/external-source-03/`，索引见 context-index.json。

## external-12：dotenv_values 路径参数调用

仅核对 dotenv_values(".env") 的调用绑定；不对注释示例中的 USER/EMAIL 实际值判定。

来源：theskumar/python-dotenv，固定提交 `0b2880591780a426b0551436f47a17e7a76d954f`。

文档：[README.md](external-12/document_path.txt)，焦点 86-90 行。

代码：[src/dotenv/main.py](external-12/code_path.txt)，查阅入口 482-488 行。

补充上下文：`context/external-source-03/`，索引见 context-index.json。

## external-13：rich.print 调用

核对示例 print 的三个位置参数绑定；不扩展为对全部 builtin print 行为的等价证明。

来源：Textualize/rich，固定提交 `9d8f9a372cc5916fd4781fec207ced7ddac2f08f`。

文档：[README.md](external-13/document_path.txt)，焦点 64-68 行。

代码：[rich/__init__.py](external-13/code_path.txt)，查阅入口 53-59 行。

补充上下文：`context/external-source-04/`，索引见 context-index.json。

## external-14：pretty.install 调用

核对 pretty.install() 无参调用绑定；不评估 REPL 的实际输出效果。

来源：Textualize/rich，固定提交 `9d8f9a372cc5916fd4781fec207ced7ddac2f08f`。

文档：[README.md](external-14/document_path.txt)，焦点 76-79 行。

代码：[rich/pretty.py](external-14/code_path.txt)，查阅入口 171-180 行。

补充上下文：`context/external-source-04/`，索引见 context-index.json。

## external-15：Console 构造调用

核对 Console() 无参构造的绑定。

来源：Textualize/rich，固定提交 `9d8f9a372cc5916fd4781fec207ced7ddac2f08f`。

文档：[README.md](external-15/document_path.txt)，焦点 87-91 行。

代码：[rich/console.py](external-15/code_path.txt)，查阅入口 619-672 行。

补充上下文：`context/external-source-04/`，索引见 context-index.json。

## external-16：Console.print 调用

核对已构造 console 的 print("Hello", "World!") 绑定，不评估终端渲染。

来源：Textualize/rich，固定提交 `9d8f9a372cc5916fd4781fec207ced7ddac2f08f`。

文档：[README.md](external-16/document_path.txt)，焦点 93-97 行。

代码：[rich/console.py](external-16/code_path.txt)，查阅入口 1652-1682 行。

补充上下文：`context/external-source-04/`，索引见 context-index.json。

## external-17：生成的 Empty 构造接口

核对 @define 后 Empty() 的构造绑定；需查看装饰器、生成逻辑及文档中类定义，不能将导出名直接当生成的类。

来源：python-attrs/attrs，固定提交 `644b4e165bfbeee7e127de6fcbda08b64014316f`。

文档：[docs/examples.md](external-17/document_path.txt)，焦点 7-13 行。

代码：[src/attr/_make.py](external-17/code_path.txt)，查阅入口 2030-2096 行。

补充上下文：`context/external-source-05/`，索引见 context-index.json。

## external-18：生成的 Coordinates 构造接口

核对文档同一 Coordinates 类的两种构造调用（位置及关键字），限定为该类的参数绑定。

来源：python-attrs/attrs，固定提交 `644b4e165bfbeee7e127de6fcbda08b64014316f`。

文档：[docs/examples.md](external-18/document_path.txt)，焦点 24-44 行。

代码：[src/attr/_make.py](external-18/code_path.txt)，查阅入口 2187-2448 行。

补充上下文：`context/external-source-05/`，索引见 context-index.json。

## external-19：field 无参调用

仅核对类体中的 field() 调用绑定，Coordinates 构造已在上一条评估，不重复计数。

来源：python-attrs/attrs，固定提交 `644b4e165bfbeee7e127de6fcbda08b64014316f`。

文档：[docs/examples.md](external-19/document_path.txt)，焦点 51-58 行。

代码：[src/attr/_next_gen.py](external-19/code_path.txt)，查阅入口 434-455 行。

补充上下文：`context/external-source-05/`，索引见 context-index.json。

## external-20：私有属性对应的构造参数

核对示例 C(x=1) 中关键字与生成构造接口的对应关系，结合文档类定义。

来源：python-attrs/attrs，固定提交 `644b4e165bfbeee7e127de6fcbda08b64014316f`。

文档：[docs/examples.md](external-20/document_path.txt)，焦点 66-74 行。

代码：[src/attr/_make.py](external-20/code_path.txt)，查阅入口 2451-2459 行。

补充上下文：`context/external-source-05/`，索引见 context-index.json。

## external-21：alive_bar 的 total 参数

仅核对 alive_bar(120000) 的调用绑定；下一条单独评估返回句柄。

来源：rsalmei/alive-progress，固定提交 `69d9bf0aba6276e2434a3a595cceca55040d64d7`。

文档：[README.md](external-21/document_path.txt)，焦点 126-132 行。

代码：[alive_progress/core/progress.py](external-21/code_path.txt)，查阅入口 22-22 行。

补充上下文：`context/external-source-06/`，索引见 context-index.json。

## external-22：bar 句柄调用

核对同一 with 上下文中的 bar(60000, skipped=True) 与 bar() 的绑定；根据上下文判断目标，不预设为某一内部函数。

来源：rsalmei/alive-progress，固定提交 `69d9bf0aba6276e2434a3a595cceca55040d64d7`。

文档：[README.md](external-22/document_path.txt)，焦点 126-134 行。

代码：[alive_progress/core/progress.py](external-22/code_path.txt)，查阅入口 181-202 行。

补充上下文：`context/external-source-06/`，索引见 context-index.json。

## external-23：alive_bar 关键字配置调用

核对 alive_bar(26, dual_line=True, title=...) 的关键字入口及配置接收；不评估显示效果或 bar.text 赋值。

来源：rsalmei/alive-progress，固定提交 `69d9bf0aba6276e2434a3a595cceca55040d64d7`。

文档：[README.md](external-23/document_path.txt)，焦点 194-203 行。

代码：[alive_progress/core/progress.py](external-23/code_path.txt)，查阅入口 22-22 行。

补充上下文：`context/external-source-06/`，索引见 context-index.json。

## external-24：ctrl_c 默认配置

仅核对文档所述 ctrl_c 默认值；保留历史版本小节上下文，以当前固定提交为代码对照，不实测键盘中断。

来源：rsalmei/alive-progress，固定提交 `69d9bf0aba6276e2434a3a595cceca55040d64d7`。

文档：[README.md](external-24/document_path.txt)，焦点 238-241 行。

代码：[alive_progress/core/configuration.py](external-24/code_path.txt)，查阅入口 145-175 行。

补充上下文：`context/external-source-06/`，索引见 context-index.json。
