# B 扩展样本覆盖调查与修复（2026-10-10）

本轮完成 `docs/tasks.md` 中“B：扩展样本覆盖调查与修复交接”的技术部分。实现提交为 `7a16354f0ff1ad4c6ed544cd19a926c867848897`。没有调用付费模型，没有修改冻结标签或原始 B/C 标注。

## 范围决定

| 样本范围 | 决定 | 结果 |
| --- | --- | --- |
| candidate-01/04 | `__init__` 是需要公开提取的构造方法；其他私有/双下划线方法仍默认跳过 | 两例从 UNCERTAIN 变为正确的 INCONSISTENT / CONSISTENT |
| candidate-05 | 默认参数在函数定义时绑定；只解析此前已有的静态字面量绑定 | 正确识别默认值仍为 12，而不是后来重绑定的 24 |
| candidate-06 | 函数对象 `__defaults__` 属性可在运行时任意改变，本轮不展开支持 | 继续 UNCERTAIN，并保留 DYNAMIC_FUNCTION |
| candidate-07 | 返回值依赖环境变量，即使存在 fallback 也不能假定实际环境 | 继续 UNCERTAIN |
| candidate-08 | 无参数、无装饰器、函数体只有一个字面量 `return` 时，可证明定义时调用结果 | 正确识别 `json` |
| candidate-09—11 | 仅展开代码块中先前直接赋值的字面量 tuple/list/dict；运行时函数返回值不展开 | 09/11 正确接受，10 正确拒绝；12 继续拒答 |
| candidate-17/18 | 按模块初始化顺序处理明确重赋值和安全的数字 `+=`/`-=` | 正确得到 14 和 8023 |
| candidate-20 | 只支持显式字面量 mapping 的 `dict.update` | 正确得到 workers=6；动态 update 继续 UNKNOWN |
| candidate-21/23 | 递归保留字符串键嵌套路径；动态叶值保持 UNKNOWN | 21 正确判冲突，23 继续拒答 |
| candidate-24 | 仅在内建 `dict` 未被重绑定时支持纯关键字构造 | 正确识别布尔 True；重绑定后的 `dict(...)` 不回答 |

## 反例边界

新增测试先覆盖以下“应拒答”情况：

- 运行时 `*args` / `**kwargs` 不被当作已知参数。
- 环境或普通函数调用产生的默认值保持 UNKNOWN。
- 函数定义后修改 `__defaults__` 保持 DYNAMIC_FUNCTION。
- 动态 `dict.update(...)`、动态增强赋值和被重绑定的 `dict` 构造保持 UNKNOWN。
- 文档中的 `factory()` 等表达式不被误当成普通字符串；只有受限的代码样式裸字符串值（例如 `utf-8`、`json`、`./cache`）被按字符串比较。

## 最小复现与回归

回归文件：[test_b_release_coverage.py](../tests/integration/test_b_release_coverage.py)。它独立覆盖构造方法、定义时绑定、字面量展开、顺序配置和动态反例五组行为。

实际验证：

- 新增专项：`5 passed`。
- B 收尾与静态/流水线联合回归：`93 passed`。
- 完整 pytest：`222 passed, 2 skipped`；两个 skip 均为当前 Windows 进程没有 symlink 创建权限。
- Ruff：通过。
- Ruff format：22 个相关 Python 文件格式正确。
- mypy：20 个源文件通过。
- wheel/sdist：构建成功。wheel SHA-256 为 `bb9bbfb25a91e1b66989fcb70e7a9761dec5424ae314e2dec9a414a821827727`；sdist SHA-256 为 `505dd55e15ef8ef7f99879fff3796fb4f08fc461536441c58ef7b52586442f85`。
- candidate-dev-v1 rules 离线重跑：24 个样本，0 API 请求；4 个 PARTIAL 均由共享仓库中的同一个 `case06.py:DYNAMIC_FUNCTION` 引起。

命令：

```powershell
$env:PYTHONPATH = "$PWD;$PWD\src"
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
python bench\builders\build_reviewed_candidates.py --out runs\b-release-closeout-candidates
python -m docsync benchmark --manifest runs\b-release-closeout-candidates\manifest.jsonl --method rules --out runs\b-release-closeout-rules
```

离线指标和逐样本原始预测见 [证据目录](audit-samples/b-release-coverage-20261010/README.md)。benchmark 命令因保留 4 个 PARTIAL 返回非零退出码，这是 `--require-complete` 语义，不是运行中断；24 行预测和指标均已写出。

## 版本边界

早期工作区曾以用户下载的 `main` ZIP 建立本地承接基线 `6997ff6`，该提交仅用于网络不可用时继续开发。2026-10-10 已重新获取正式 `origin/main` `353527b`，并从它创建干净分支 `member-b-release-closeout-final`；`6997ff6` 不是该分支祖先。

原始提交 `7a16354`、`656ecc0`、`1498206` 在正式最新 main 上依次移植为 `0ccbecb`、`2ab8ed3`、`3a34706`。移植后完整测试为 `222 passed, 2 skipped`，两个 skip 仍为 Windows symlink 权限；Ruff、格式检查、mypy 和构建均通过。当前构建产物 SHA-256：wheel `efda69cd1eda5460ee0d65abdab09b5623dbdef4e822a57009f0bb97771b77b4`；sdist `70e1e94fc1cef6a9b700a7b82b74792069ae5f2b7ff14a7a3232696300dbb854`。远程 CI 仍需以推送后的分支 SHA 为准。

