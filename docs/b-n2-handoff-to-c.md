# B-N2 交付成员 C 复验说明

成员 C 你好，成员 B 已完成 B-N2，现将代码和复验材料交给你验收。

## 一、B-N2 基本信息

- 项目：DocSync
- 分支：`member-b-tasks`
- B-N2 提交：`f561b9c`
- 提交说明：`fix: support English default statements for B-N2`
- 对应缺陷：C1 缺陷 D-1
- 缺陷内容：英文句式 `The default value of X is Y` 原来不会被提取
- B 的修复报告：`docs/b-n2-english-defaults-review.md`
- 新增测试：`tests/integration/test_b_n2_english_defaults.py`
- 修改的提取器：`src/docsync/extractors/markdown.py`

## 二、B 已完成的修改

B 已增加对以下明确英文默认值句式的支持：

```text
The default value of `timeout` is `60`.
```

该句式现在会生成 `DEFAULT_ASSERTION`，并继续复用原来的：

- 符号归属逻辑
- 源码链接归属逻辑
- 历史版本识别
- 同名符号歧义判断
- 字面量类型判断
- 文件 hash
- 行号
- UTF-8 精确字节范围

B 没有把动态值、历史语境或歧义情况强行判断为一致。

## 三、请 C 复验以下场景

请重点检查这 6 类场景：

1. 文档默认值为 60，代码默认值为 60：

   - 应为 `CONSISTENT`
   - 原因应为 `LITERAL_EQUAL`

2. 文档默认值为 30，代码默认值为 60：

   - 应为 `INCONSISTENT`
   - 应生成一条 finding

3. 标题包含 `Old version`：

   - 应为 `UNCERTAIN`
   - 原因应为 `VERSION_UNRESOLVED`
   - 不应生成 finding

4. 两个文件中存在同名 `connect`：

   - 应为 `UNCERTAIN`
   - 原因应为 `AMBIGUOUS`
   - 不应选择 top-1 强行判断

5. Markdown 标题显式链接到 `client.py`：

   - 应归属到 `client.py`
   - 代码证据也应指向 `client.py`

6. 文档中同时存在合法调用 `connect(timeout=30)`：

   - 调用应为 `CONSISTENT / CALL_ACCEPTED`
   - 不应因为调用参数和函数默认值不同而误报

另外请检查：

- claim 的所属符号是否正确
- 文档路径是否正确
- 行号是否正确
- `span` 和 `value_span` 是否正确
- UTF-8 字节范围是否能定位到具体的数值
- blob hash 是否对应固定文档内容

## 四、专项复验命令

请在 DocSync 项目根目录执行：

```powershell
python -m pytest tests/integration/test_b_n2_english_defaults.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n2-c-review"
```

B 本地的预期结果是：

```text
6 passed
```

然后执行相关回归：

```powershell
python -m pytest tests/integration/test_pipeline.py tests/integration/test_static_extensions.py -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n2-c-related"
```

B 本地的预期结果是：

```text
56 passed
```

如果需要执行全量测试：

```powershell
python -m pytest -q -p no:cacheprovider --basetemp "$env:TEMP/pytest-b-n2-c-full"
```

B 本地全量结果是：

```text
186 passed, 1 skipped
```

唯一跳过项是当前 Windows 进程没有创建文件系统符号链接的权限，与 B-N2 英文句式修复无关。

## 五、请 C 留下的验收记录

复验完成后，请在 `docs/c1-markdown-evidence-review.md` 中追加真实复验记录，包括：

- 复验日期
- 完整提交 SHA
- 实际执行的命令
- 测试通过/失败数量
- 英文一致样例结果
- 英文冲突样例结果
- 历史语境结果
- 同名歧义结果
- 源码链接归属结果
- 行号、字节范围和 blob hash 检查结果
- C 的最终结论

如果全部通过，请明确回复：

```text
C 已复验 B-N2 提交 f561b9c。
专项测试和相关回归通过，英文默认值声明能够正确提取；
历史语境和同名歧义仍保持 UNCERTAIN；
证据的文件、行号、字节范围和 blob hash 可以追溯。
同意关闭 C1 缺陷 D-1。
```

如果没有通过，请不要关闭 D-1，请把以下内容发给 B：

- 失败的测试名称
- 完整错误信息
- 使用的操作系统和 Python 版本
- 实际测试命令
- 出错样例
- 预期结果
- 实际结果

## 六、B-N3 协作提醒

B 接下来准备开始 B-N3。B-N3 涉及“忽略到期日”字段，按照任务分工：

- B 负责数据模型、匹配逻辑、Schema 和兼容测试
- C 负责 JSON/Markdown 报告展示和报告测试
- A 负责确认 Schema 兼容性和最终字段契约

请 C 暂时不要和 B 同时修改 B 负责的数据模型、Schema 和忽略匹配文件，避免代码冲突。请先确认愿意参与 B-N3 字段契约讨论，并说明你计划修改的报告文件。

## 七、访问说明

提交 `f561b9c` 当前尚未推送到 GitHub。如果 C 不和 B 共用当前本地仓库，需要先将 `member-b-tasks` 分支推送到 GitHub，C 才能取得该提交并进行复验。
