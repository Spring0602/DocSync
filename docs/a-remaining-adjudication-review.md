# 成员A：其余 19 条开发集裁决复核

本页从冻结标注包的 code_path.txt/document_path.txt 直接生成带行号的完整原文；修复了上一版按标题切分导致部分文档截断的问题。原始包和冻结裁决不修改。

2026-10-10 助手已逐条静态技术复审，19 条均与既有裁决一致；没有运行目标代码或调用模型 API。这不是成员A的人工签署，也不是独立盲测。本页 19 条均已收到成员A反馈；连同此前五条，24/24 标签人工复核完成。见 [全量复核索引](audit-samples/release-readiness-20261010/candidate-human-review-complete.json)。

每次可审一组，回复样本 ID、同意/不同意/待查、代码与文档行号及理由。
组 1：01/02/03/04；组 2：08/09/10/11/12；组 3：14/15/16/17/18；组 4：20/21/22/23/24。

## candidate-01

固定提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`。

文件：`case01.py`

````text
  1 | class PageReader:
  2 |     def __init__(self, encoding: str = "utf-8"):
  3 |         self.encoding = encoding
````

文件：`case01.md`

````text
  1 | # API reference
  2 | 
  3 | ## `PageReader.__init__`
  4 | 
  5 | `encoding` 默认值为 `utf-16`。
````

助手技术复审：**INCONSISTENT**；构造函数签名 encoding=utf-8，文档第 5 行为 utf-16；比较接口默认值即可确认冲突。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-02

固定提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`。

文件：`case02.py`

````text
  1 | async def download_resource(url, *, retries: int = 4, decode: bool = False):
  2 |     return url, retries, decode
````

文件：`case02.md`

````text
  1 | # API reference
  2 | 
  3 | ## `download_resource`
  4 | 
  5 | `retries` 默认值为 `4`。
````

助手技术复审：**CONSISTENT**；async 不改变默认参数绑定；retries 是 keyword-only 且默认整数 4，与文档一致。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-03

固定提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`。

文件：`case03.py`

````text
  1 | def emit_record(payload, *, tags: tuple[str, ...] = ("audit", "public")):
  2 |     return payload, tags
````

文件：`case03.md`

````text
  1 | # API reference
  2 | 
  3 | ## `emit_record`
  4 | 
  5 | `tags` 默认值为 `("audit", "internal")`。
````

助手技术复审：**INCONSISTENT**；两个元组首项相同，第二项 public/internal 不同；类型一致不等于值一致。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-04

固定提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`。

文件：`case04.py`

````text
  1 | class MemoryBuffer:
  2 |     def __init__(self, capacity=None):
  3 |         self.capacity = 32 if capacity is None else capacity
````

文件：`case04.md`

````text
  1 | # API reference
  2 | 
  3 | ## `MemoryBuffer.__init__`
  4 | 
  5 | `capacity` 默认值为 `None`。
````

助手技术复审：**CONSISTENT**；签名默认 None；实例属性最终取 32 是函数体转换，不能将属性值冒充参数默认值。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-08

固定提交：`c41084643fa443a73111d1ce3940c5508ca4de31`。

文件：`case08.py`

````text
  1 | def choose_format():
  2 |     return "json"
  3 | 
  4 | def export_records(format_name=choose_format()):
  5 |     return format_name
````

文件：`case08.md`

````text
  1 | # API reference
  2 | 
  3 | ## `export_records`
  4 | 
  5 | `format_name` 默认值为 `json`。
````

助手技术复审：**CONSISTENT**；choose_format 无条件返回 json，无外部输入；定义时绑定该值。静态提取器不支持调用表达式不改变原文可推导的标签。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-09

固定提交：`16d3ac74221f2247c645ca1999d485bb9763d833`。

文件：`case09.py`

````text
  1 | def attach_volume(name, *, readonly):
  2 |     return name, readonly
````

文件：`case09.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case09 import attach_volume
  7 | options = {"readonly": True}
  8 | attach_volume("logs", **options)
  9 | ```
````

助手技术复审：**CONSISTENT**；options 是固定字典，展开后提供 readonly=True；name 由 logs 位置参数绑定，无多余参数。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-10

固定提交：`16d3ac74221f2247c645ca1999d485bb9763d833`。

文件：`case10.py`

````text
  1 | def send_notice(address, *, channel):
  2 |     return address, channel
````

文件：`case10.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case10 import send_notice
  7 | arguments = ("ops@example.invalid", "email")
  8 | send_notice(*arguments)
  9 | ```
````

助手技术复审：**INCONSISTENT**；arguments 展开成两个位置参数；channel 在 * 后，仅接受关键字，第二个位置参数不合法。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-11

固定提交：`16d3ac74221f2247c645ca1999d485bb9763d833`。

文件：`case11.py`

````text
  1 | def place_marker(x, y, /, *, color="red"):
  2 |     return x, y, color
````

文件：`case11.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case11 import place_marker
  7 | position = (3, 7)
  8 | style = {"color": "blue"}
  9 | place_marker(*position, **style)
 10 | ```
````

助手技术复审：**CONSISTENT**；position 展开成 x/y 两个位置参数，style 提供 color 关键字，符合 / 与 * 约束。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-12

固定提交：`16d3ac74221f2247c645ca1999d485bb9763d833`。

文件：`case12.py`

````text
  1 | import json
  2 | import os
  3 | 
  4 | def read_options():
  5 |     return json.loads(os.environ.get("NOTICE_OPTIONS", "{}"))
  6 | 
  7 | def queue_notice(topic, *, priority):
  8 |     return topic, priority
````

文件：`case12.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case12 import queue_notice, read_options
  7 | queue_notice("maintenance", **read_options())
  8 | ```
````

助手技术复审：**INSUFFICIENT**；NOTICE_OPTIONS 未知，可能缺 priority、含多余键、不是映射或无效 JSON；不能把默认 {} 当实际输入。

人工复核：**成员A已确认 INSUFFICIENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-14

固定提交：`9638d576f474294bbcb2ec37e34e998306f13cab`。

文件：`case14.py`

````text
  1 | class Formatter:
  2 |     @staticmethod
  3 |     def render(text, *, width):
  4 |         return text, width
````

文件：`case14.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case14 import Formatter
  7 | Formatter.render("status", 72)
  8 | ```
````

助手技术复审：**INCONSISTENT**；staticmethod 不注入 self/cls；width 仅限关键字，72 却作为第二位置参数传入。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-15

固定提交：`9638d576f474294bbcb2ec37e34e998306f13cab`。

文件：`case15.py`

````text
  1 | class Registry:
  2 |     def register(self, name, /, *, replace=False):
  3 |         return name, replace
````

文件：`case15.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case15 import Registry
  7 | registry = Registry()
  8 | registry.register(name="worker")
  9 | ```
````

助手技术复审：**INCONSISTENT**；self 由实例绑定，但 name 仍是 / 前的位置专用参数；name=worker 不合法。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-16

固定提交：`9638d576f474294bbcb2ec37e34e998306f13cab`。

文件：`case16.py`

````text
  1 | import os
  2 | 
  3 | class LocalDispatcher:
  4 |     def deliver(self, message):
  5 |         return message
  6 | 
  7 | class RemoteDispatcher:
  8 |     def deliver(self, message, *, token):
  9 |         return message, token
 10 | 
 11 | def dispatcher():
 12 |     if os.environ.get("REMOTE_DELIVERY"):
 13 |         return RemoteDispatcher()
 14 |     return LocalDispatcher()
````

文件：`case16.md`

````text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case16 import dispatcher
  7 | dispatcher().deliver("ready")
  8 | ```
````

助手技术复审：**INSUFFICIENT**；环境可选 Local 或 Remote，Remote 还需 token；当前环境缺证据，不能断言所有路径绑定都有效或都无效。

人工复核：**成员A已确认 INSUFFICIENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-17

固定提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`。

文件：`case17.py`

````text
  1 | RETRY_WINDOW: int = 6
  2 | RETRY_WINDOW = 14
````

文件：`case17.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case17`
  4 | 
  5 | `RETRY_WINDOW` 默认值为 `6`。
````

助手技术复审：**INCONSISTENT**；顺序初始化后 RETRY_WINDOW=14，注解和首赋值 6 不阻止后续重赋值；文档 6 过期。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-18

固定提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`。

文件：`case18.py`

````text
  1 | PORT: int = 8020
  2 | PORT += 3
````

文件：`case18.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case18`
  4 | 
  5 | `PORT` 默认值为 `8023`。
````

助手技术复审：**CONSISTENT**；固定整数增强赋值 8020+3 得 8023；无未知输入，文档一致。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-20

固定提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`。

文件：`case20.py`

````text
  1 | SERVICE_OPTIONS = {"workers": 2}
  2 | SERVICE_OPTIONS.update({"workers": 6})
````

文件：`case20.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case20.SERVICE_OPTIONS`
  4 | 
  5 | `workers` 默认值为 `6`。
````

助手技术复审：**CONSISTENT**；字典 update 明确覆盖 workers 为 6；应比较模块初始化完成后的值，而非初始 2。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-21

固定提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`。

文件：`case21.py`

````text
  1 | PIPELINE = {"export": {"compression": "gzip", "level": 3}}
````

文件：`case21.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case21.PIPELINE.export`
  4 | 
  5 | `compression` 默认值为 `zstd`。
````

助手技术复审：**INCONSISTENT**；层级路径 PIPELINE.export.compression 精确对应 gzip，文档 zstd 不同；不能用工具不支持嵌套键否定真值。

人工复核：**成员A已确认 INCONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-22

固定提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`。

文件：`case22.py`

````text
  1 | RETRY_DELAYS = (1, 3, 9)
````

文件：`case22.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case22`
  4 | 
  5 | `RETRY_DELAYS` 默认值为 `(1, 3, 9)`。
````

助手技术复审：**CONSISTENT**；固定元组 (1,3,9) 的类型、次序、数值与文档一致。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-23

固定提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`。

文件：`case23.py`

````text
  1 | import os
  2 | 
  3 | STORAGE = {"local": {"root": os.environ.get("STORAGE_ROOT", "./cache")}}
````

文件：`case23.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case23.STORAGE.local`
  4 | 
  5 | `root` 默认值为 `./cache`。
````

助手技术复审：**INSUFFICIENT**；STORAGE_ROOT 的实际值未知；./cache 仅为未设置分支，不能保证文档在实际环境成立。

人工复核：**成员A已确认 INSUFFICIENT**（反馈接收 2026-10-10；实际审核日期未填）。

## candidate-24

固定提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`。

文件：`case24.py`

````text
  1 | CACHE = dict(enabled=True, capacity=128)
````

文件：`case24.md`

````text
  1 | # API reference
  2 | 
  3 | ## `case24.CACHE`
  4 | 
  5 | `enabled` 默认值为 `True`。
````

助手技术复审：**CONSISTENT**；模块内无 dict 重绑定；关键字构造给出布尔 True，与文档布尔值一致，不混同整数 1。

人工复核：**成员A已确认 CONSISTENT**（反馈接收 2026-10-10；实际审核日期未填）。

