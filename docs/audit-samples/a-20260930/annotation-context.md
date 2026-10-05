# C 标注材料补充：固定提交原文

工具生成的上下文，不是人工标注或最终标签。保留 C 原表；补齐表格、标题、同名实体和 import 上下文，供 B/C 独立复核。

## seed-01-default_drift

固定提交：e8701dddd7d559d0794afbcdd8b6ace8d8a1f2b0

### README.md

~~~~text
1: ## `connect`
2:
3: `timeout` 默认值为 `30`。
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-02-default_equal

固定提交：6f3876f25a59976d116eb80d1a0220e2f3132be6

### README.md

~~~~text
1: ## `connect`
2:
3: `timeout` 默认值为 `60`。
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-03-typed_bool

固定提交：8b42acebdad4fd16b1d02561228f27dc2c2ccc65

### README.md

~~~~text
1: ## `connect`
2:
3: `timeout` 默认值为 `1`。
~~~~

### client.py

~~~~text
1: def connect(timeout=True):
2:     return timeout
~~~~

## seed-04-factory_unknown

固定提交：a12996cb00b0bcc90c9458caf4a6db09838a0278

### README.md

~~~~text
1: ## `connect`
2:
3: `timeout` 默认值为 `30`。
~~~~

### client.py

~~~~text
1: def connect(timeout=factory()):
2:     return timeout
~~~~

## seed-05-historical

固定提交：8e407ba6cea6e8f58f3ccced86d81d7761f1c453

### README.md

~~~~text
1: ## 旧版 `connect`
2:
3: `timeout` 默认值为 `30`。
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-06-ambiguous

固定提交：6d9ed71fa83b3bf747a080dfaf33d411e968d2f7

### README.md

~~~~text
1: ## `connect`
2:
3: `timeout` 默认值为 `30`。
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

### other.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-07-table_drift

固定提交：c131e00fcf344e565a4a30648c2c53392d9b7428

### README.md

~~~~text
1: ## `connect`
2:
3: | parameter | default |
4: |---|---|
5: |timeout|30|
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-08-table_equal

固定提交：af9fbfe9d2715b403d7b37758863a238e9be56bb

### README.md

~~~~text
1: ## `connect`
2:
3: | parameter | default |
4: |---|---|
5: |timeout|60|
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-09-linked_owner

固定提交：5ec21f193f947e5c54490f1a3ebac57b9cc3c290

### README.md

~~~~text
1: ## [connect](client.py)
2:
3: `timeout` 默认值为 `30`。
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

### other.py

~~~~text
1: def connect(timeout=30):
2:     return timeout
~~~~

## seed-10-constant_drift

固定提交：ab57f9585b67276cead2e786f4aa4b4f94ac5c26

### README.md

~~~~text
1: ## 配置 `settings`
2:
3: `TIMEOUT` 默认值为 `30`。
~~~~

### settings.py

~~~~text
1: TIMEOUT = 60
~~~~

## seed-11-constant_equal

固定提交：dcce728ee423df7f969e31a1b124a21bc2f5e3fe

### README.md

~~~~text
1: ## 配置 `settings`
2:
3: `TIMEOUT` 默认值为 `60`。
~~~~

### settings.py

~~~~text
1: TIMEOUT = 60
~~~~

## seed-12-dict_drift

固定提交：2e4da1b56480b3a17927d6f8505911961e208a26

### README.md

~~~~text
1: ## `settings.CONFIG`
2:
3: `timeout` 默认值为 `30`。
~~~~

### settings.py

~~~~text
1: CONFIG = {'timeout': 60}
~~~~

## seed-13-dict_dynamic

固定提交：2524e5f3c443b08ba170875da8d20b2299808f42

### README.md

~~~~text
1: ## `settings.CONFIG`
2:
3: `timeout` 默认值为 `30`。
~~~~

### settings.py

~~~~text
1: CONFIG = {'timeout': env()}
~~~~

## seed-14-missing_required

固定提交：59f09b9d8efff70eaebce74ae46589a697b14959

### README.md

~~~~text
1: ```python
2: connect()
3: ```
~~~~

### client.py

~~~~text
1: def connect(host): pass
~~~~

## seed-15-unexpected_keyword

固定提交：a95d8228d35c88cae04b359c7c5e09cafa57fe3e

### README.md

~~~~text
1: ```python
2: connect(host='local')
3: ```
~~~~

### client.py

~~~~text
1: def connect(timeout=60):
2:     return timeout
~~~~

## seed-16-kwargs_legal

固定提交：4c5a8deb8d27ed524c548021d10ac812a46a0da2

### README.md

~~~~text
1: ```python
2: connect(host='local')
3: ```
~~~~

### client.py

~~~~text
1: def connect(**kwargs): pass
~~~~

## seed-17-positional_only

固定提交：42d6aa0bc5153528895ec510881d91d44f2c5b93

### README.md

~~~~text
1: ```python
2: connect(host='local')
3: ```
~~~~

### client.py

~~~~text
1: def connect(host, /): pass
~~~~

## seed-18-keyword_only

固定提交：ca392b5052c1ddfac069dad57a143a8132f53a26

### README.md

~~~~text
1: ```python
2: connect()
3: ```
~~~~

### client.py

~~~~text
1: def connect(*, host): pass
~~~~

## seed-19-optional_added

固定提交：8782f5c711d1427f3f2ef9580bdda56d2ebbab3c

### README.md

~~~~text
1: ```python
2: connect(timeout=30)
3: ```
~~~~

### client.py

~~~~text
1: def connect(timeout=60, retries=3): pass
~~~~

## seed-20-import_alias

固定提交：4fe77671790bed8a501719efabff9ebab4836e36

### README.md

~~~~text
1: ```python
2: from client import connect as open_connection
3: open_connection()
4: ```
~~~~

### client.py

~~~~text
1: def connect(host): pass
~~~~
