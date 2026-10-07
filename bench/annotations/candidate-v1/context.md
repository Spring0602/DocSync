# 固定候选原文（无答案）

以下行号对应代码/文档原文件；不要执行代码或向模型询问标签。

## candidate-01

提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`；组：`candidate-family-01`。

文件：`case01.py`

```text
  1 | class PageReader:
  2 |     def __init__(self, encoding: str = "utf-8"):
  3 |         self.encoding = encoding
```

文件：`case01.md`

```text
  1 | # API reference
  2 | 
  3 | ## `PageReader.__init__`
  4 | 
  5 | `encoding` 默认值为 `utf-16`。
```

## candidate-02

提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`；组：`candidate-family-01`。

文件：`case02.py`

```text
  1 | async def download_resource(url, *, retries: int = 4, decode: bool = False):
  2 |     return url, retries, decode
```

文件：`case02.md`

```text
  1 | # API reference
  2 | 
  3 | ## `download_resource`
  4 | 
  5 | `retries` 默认值为 `4`。
```

## candidate-03

提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`；组：`candidate-family-01`。

文件：`case03.py`

```text
  1 | def emit_record(payload, *, tags: tuple[str, ...] = ("audit", "public")):
  2 |     return payload, tags
```

文件：`case03.md`

```text
  1 | # API reference
  2 | 
  3 | ## `emit_record`
  4 | 
  5 | `tags` 默认值为 `("audit", "internal")`。
```

## candidate-04

提交：`97978fc406e9a2b05717d9ed6e55a747a94be41c`；组：`candidate-family-01`。

文件：`case04.py`

```text
  1 | class MemoryBuffer:
  2 |     def __init__(self, capacity=None):
  3 |         self.capacity = 32 if capacity is None else capacity
```

文件：`case04.md`

```text
  1 | # API reference
  2 | 
  3 | ## `MemoryBuffer.__init__`
  4 | 
  5 | `capacity` 默认值为 `None`。
```

## candidate-05

提交：`c41084643fa443a73111d1ce3940c5508ca4de31`；组：`candidate-family-02`。

文件：`case05.py`

```text
  1 | BATCH_LIMIT = 12
  2 | 
  3 | def read_batch(limit=BATCH_LIMIT):
  4 |     return limit
  5 | 
  6 | BATCH_LIMIT = 24
```

文件：`case05.md`

```text
  1 | # API reference
  2 | 
  3 | ## `read_batch`
  4 | 
  5 | `limit` 默认值为 `24`。
```

## candidate-06

提交：`c41084643fa443a73111d1ce3940c5508ca4de31`；组：`candidate-family-02`。

文件：`case06.py`

```text
  1 | def encode_packet(payload, codec="latin-1"):
  2 |     return payload, codec
  3 | 
  4 | encode_packet.__defaults__ = ("utf-8",)
```

文件：`case06.md`

```text
  1 | # API reference
  2 | 
  3 | ## `encode_packet`
  4 | 
  5 | `codec` 默认值为 `utf-8`。
```

## candidate-07

提交：`c41084643fa443a73111d1ce3940c5508ca4de31`；组：`candidate-family-02`。

文件：`case07.py`

```text
  1 | import os
  2 | 
  3 | def flush_interval():
  4 |     return int(os.environ.get("FLUSH_INTERVAL", "8"))
  5 | 
  6 | def flush_records(interval=flush_interval()):
  7 |     return interval
```

文件：`case07.md`

```text
  1 | # API reference
  2 | 
  3 | ## `flush_records`
  4 | 
  5 | `interval` 默认值为 `8`。
```

## candidate-08

提交：`c41084643fa443a73111d1ce3940c5508ca4de31`；组：`candidate-family-02`。

文件：`case08.py`

```text
  1 | def choose_format():
  2 |     return "json"
  3 | 
  4 | def export_records(format_name=choose_format()):
  5 |     return format_name
```

文件：`case08.md`

```text
  1 | # API reference
  2 | 
  3 | ## `export_records`
  4 | 
  5 | `format_name` 默认值为 `json`。
```

## candidate-09

提交：`16d3ac74221f2247c645ca1999d485bb9763d833`；组：`candidate-family-03`。

文件：`case09.py`

```text
  1 | def attach_volume(name, *, readonly):
  2 |     return name, readonly
```

文件：`case09.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case09 import attach_volume
  7 | options = {"readonly": True}
  8 | attach_volume("logs", **options)
  9 | ```
```

## candidate-10

提交：`16d3ac74221f2247c645ca1999d485bb9763d833`；组：`candidate-family-03`。

文件：`case10.py`

```text
  1 | def send_notice(address, *, channel):
  2 |     return address, channel
```

文件：`case10.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case10 import send_notice
  7 | arguments = ("ops@example.invalid", "email")
  8 | send_notice(*arguments)
  9 | ```
```

## candidate-11

提交：`16d3ac74221f2247c645ca1999d485bb9763d833`；组：`candidate-family-03`。

文件：`case11.py`

```text
  1 | def place_marker(x, y, /, *, color="red"):
  2 |     return x, y, color
```

文件：`case11.md`

```text
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
```

## candidate-12

提交：`16d3ac74221f2247c645ca1999d485bb9763d833`；组：`candidate-family-03`。

文件：`case12.py`

```text
  1 | import json
  2 | import os
  3 | 
  4 | def read_options():
  5 |     return json.loads(os.environ.get("NOTICE_OPTIONS", "{}"))
  6 | 
  7 | def queue_notice(topic, *, priority):
  8 |     return topic, priority
```

文件：`case12.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case12 import queue_notice, read_options
  7 | queue_notice("maintenance", **read_options())
  8 | ```
```

## candidate-13

提交：`9638d576f474294bbcb2ec37e34e998306f13cab`；组：`candidate-family-04`。

文件：`case13.py`

```text
  1 | class ArtifactStore:
  2 |     @classmethod
  3 |     def open(cls, root, *, create=False):
  4 |         return cls(), root, create
```

文件：`case13.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case13 import ArtifactStore
  7 | ArtifactStore.open("artifacts", create=True)
  8 | ```
```

## candidate-14

提交：`9638d576f474294bbcb2ec37e34e998306f13cab`；组：`candidate-family-04`。

文件：`case14.py`

```text
  1 | class Formatter:
  2 |     @staticmethod
  3 |     def render(text, *, width):
  4 |         return text, width
```

文件：`case14.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case14 import Formatter
  7 | Formatter.render("status", 72)
  8 | ```
```

## candidate-15

提交：`9638d576f474294bbcb2ec37e34e998306f13cab`；组：`candidate-family-04`。

文件：`case15.py`

```text
  1 | class Registry:
  2 |     def register(self, name, /, *, replace=False):
  3 |         return name, replace
```

文件：`case15.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case15 import Registry
  7 | registry = Registry()
  8 | registry.register(name="worker")
  9 | ```
```

## candidate-16

提交：`9638d576f474294bbcb2ec37e34e998306f13cab`；组：`candidate-family-04`。

文件：`case16.py`

```text
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
```

文件：`case16.md`

```text
  1 | # Usage
  2 | 
  3 | 以下示例展示当前版本的调用方式，仅检查参数绑定，不要求执行示例。
  4 | 
  5 | ```python
  6 | from case16 import dispatcher
  7 | dispatcher().deliver("ready")
  8 | ```
```

## candidate-17

提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`；组：`candidate-family-05`。

文件：`case17.py`

```text
  1 | RETRY_WINDOW: int = 6
  2 | RETRY_WINDOW = 14
```

文件：`case17.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case17`
  4 | 
  5 | `RETRY_WINDOW` 默认值为 `6`。
```

## candidate-18

提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`；组：`candidate-family-05`。

文件：`case18.py`

```text
  1 | PORT: int = 8020
  2 | PORT += 3
```

文件：`case18.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case18`
  4 | 
  5 | `PORT` 默认值为 `8023`。
```

## candidate-19

提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`；组：`candidate-family-05`。

文件：`case19.py`

```text
  1 | import os
  2 | 
  3 | if os.environ.get("ARCHIVE_PROFILE") == "compact":
  4 |     ARCHIVE_LEVEL = 2
  5 | else:
  6 |     ARCHIVE_LEVEL = 7
```

文件：`case19.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case19`
  4 | 
  5 | `ARCHIVE_LEVEL` 默认值为 `2`。
```

## candidate-20

提交：`8a8b003a0089b42edd4e692e76b5adaa5f52151d`；组：`candidate-family-05`。

文件：`case20.py`

```text
  1 | SERVICE_OPTIONS = {"workers": 2}
  2 | SERVICE_OPTIONS.update({"workers": 6})
```

文件：`case20.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case20.SERVICE_OPTIONS`
  4 | 
  5 | `workers` 默认值为 `6`。
```

## candidate-21

提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`；组：`candidate-family-06`。

文件：`case21.py`

```text
  1 | PIPELINE = {"export": {"compression": "gzip", "level": 3}}
```

文件：`case21.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case21.PIPELINE.export`
  4 | 
  5 | `compression` 默认值为 `zstd`。
```

## candidate-22

提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`；组：`candidate-family-06`。

文件：`case22.py`

```text
  1 | RETRY_DELAYS = (1, 3, 9)
```

文件：`case22.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case22`
  4 | 
  5 | `RETRY_DELAYS` 默认值为 `(1, 3, 9)`。
```

## candidate-23

提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`；组：`candidate-family-06`。

文件：`case23.py`

```text
  1 | import os
  2 | 
  3 | STORAGE = {"local": {"root": os.environ.get("STORAGE_ROOT", "./cache")}}
```

文件：`case23.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case23.STORAGE.local`
  4 | 
  5 | `root` 默认值为 `./cache`。
```

## candidate-24

提交：`05e0224c9d9b66564f45b228f7374f4e083f0f76`；组：`candidate-family-06`。

文件：`case24.py`

```text
  1 | CACHE = dict(enabled=True, capacity=128)
```

文件：`case24.md`

```text
  1 | # API reference
  2 | 
  3 | ## `case24.CACHE`
  4 | 
  5 | `enabled` 默认值为 `True`。
```

