import json
import subprocess
import sys
from datetime import date

import pytest

from docsync.cli import exit_code
from docsync.config import IgnoreRule, RepoSpec, ScanConfig, ScanOptions
from docsync.patches import apply_patch
from docsync.pipeline import scan


@pytest.mark.parametrize(
    "definition,call,decision",
    [
        ("def f(x): pass", "f()", "INCONSISTENT"),
        ("def f(x=1): pass", "f()", "CONSISTENT"),
        ("def f(x=1): pass", "f(y=2)", "INCONSISTENT"),
        ("def f(x=1, **kwargs): pass", "f(y=2)", "CONSISTENT"),
        ("def f(x, /): pass", "f(x=1)", "INCONSISTENT"),
        ("def f(x, /, **kwargs): pass", "f(1, x=2)", "CONSISTENT"),
        ("def f(*, x): pass", "f(1)", "INCONSISTENT"),
        ("def f(*args, **kwargs): pass", "f(1, a=2)", "CONSISTENT"),
        ("def f(x=1): pass", "f(1, x=2)", "INCONSISTENT"),
        ("def f(x): pass", "f(*args)", "UNCERTAIN"),
        ("@wrapped\ndef f(x): pass", "f()", "UNCERTAIN"),
        ("def f(x): pass\nf = replacement", "f()", "UNCERTAIN"),
    ],
)
def test_argument_binding(commit_files, definition, call, decision):
    repo = commit_files({"api.py": definition + "\n", "README.md": f"```python\n{call}\n```\n"})
    report = scan(RepoSpec(repo=repo))
    assert report.judgments[0].decision == decision
    assert report.confirmed_count == int(decision == "INCONSISTENT")
    assert all(f.drift_type == "SIGNATURE" for f in report.findings)
    assert not report.patches  # Cannot invent required argument values.


@pytest.mark.parametrize(
    "decorator,example,expected",
    [
        ("", "obj = Client()\nobj.connect()", "CONSISTENT"),
        ("", "Client.connect()", "INCONSISTENT"),
        ("@classmethod\n    ", "Client.connect()", "CONSISTENT"),
        ("@staticmethod\n    ", "Client.connect()", "INCONSISTENT"),
    ],
)
def test_method_receivers(commit_files, decorator, example, expected):
    code = f"class Client:\n    {decorator}def connect(self, timeout=60):\n        pass\n"
    repo = commit_files({"api.py": code, "README.md": f"```python\n{example}\n```\n"})
    report = scan(RepoSpec(repo=repo))
    claim = next(c for c in report.claims if c.subject.endswith("connect"))
    assert next(j for j in report.judgments if j.claim_id == claim.claim_id).decision == expected


def test_table_and_source_link_disambiguate(commit_files):
    doc = "## [connect](src/client.py)\n\n| 参数 | 默认值 | 说明 |\n| --- | --- | --- |\n| `timeout` | `30` | 等待秒数 |\n"
    repo = commit_files(
        {
            "src/client.py": "def connect(timeout=60): pass\n",
            "other.py": "def connect(timeout=30): pass\n",
            "README.md": doc,
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 1
    assert "link_match" in report.candidates[0].candidates[0].features
    patch = report.patches[0]
    apply_patch(repo, patch, patch.diff)
    assert (repo / "README.md").read_text(encoding="utf-8") == doc.replace("`30`", "`60`")


def test_import_alias_resolves_call(commit_files):
    repo = commit_files(
        {
            "pkg/client.py": "def connect(timeout): pass\n",
            "other.py": "def connect(timeout=1): pass\n",
            "README.md": "```python\nfrom pkg.client import connect as open_connection\nopen_connection()\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 1
    assert report.findings[0].evidence.code.path == "pkg/client.py"


@pytest.mark.parametrize(
    "code,subject,prop,value,expected",
    [
        ("TIMEOUT = 60", "settings", "TIMEOUT", "30", "INCONSISTENT"),
        ("CONFIG = {'timeout': 60}", "settings.CONFIG", "timeout", "30", "INCONSISTENT"),
        ("CONFIG = {'timeout': 60}", "settings.CONFIG", "timeout", "60", "CONSISTENT"),
        ("CONFIG = {'timeout': env()}", "settings.CONFIG", "timeout", "30", "UNCERTAIN"),
        (
            "CONFIG = {'timeout': 60}\nCONFIG.update(other)",
            "settings.CONFIG",
            "timeout",
            "30",
            "UNCERTAIN",
        ),
        ("TIMEOUT = 60\nTIMEOUT = 30", "settings", "TIMEOUT", "30", "CONSISTENT"),
    ],
)
def test_config_defaults(commit_files, code, subject, prop, value, expected):
    repo = commit_files(
        {
            "settings.py": code + "\n",
            "README.md": f"## 配置 `{subject}`\n\n`{prop}` 默认值为 `{value}`。\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.judgments[0].decision == expected
    assert report.confirmed_count == int(expected == "INCONSISTENT")
    if report.findings:
        assert report.findings[0].drift_type == "CONFIG"
        assert report.patches


def test_historical_call_and_table_are_uncertain(commit_files):
    repo = commit_files(
        {
            "api.py": "def f(x, timeout=60): pass\n",
            "README.md": "## Legacy `f`\n\n| parameter | default |\n|---|---|\n|timeout|30|\n\n```python\nf()\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.uncertain_count == 2 and not report.findings


def test_ignore_reason_expiry_and_threshold(commit_files):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    cfg = ScanConfig(
        scan=ScanOptions(fail_on="warning"),
        ignores=[IgnoreRule(rule_id="DEFAULT_VALUE/1", reason="Tracked migration")],
    )
    report = scan(RepoSpec(repo=repo), cfg)
    assert report.ignored_count == 1 and report.confirmed_count == 0
    assert not report.patches and exit_code(report, cfg) == 0
    expired = cfg.model_copy(
        update={"ignores": [IgnoreRule(reason="expired", expires=date(2000, 1, 1))]}
    )
    assert scan(RepoSpec(repo=repo), expired).confirmed_count == 1


def test_failure_run_and_previous_run_are_preserved(commit_files, tmp_path):
    repo = commit_files({"api.py": "def f(): pass\n"})
    out = tmp_path / "failed"
    command = [
        sys.executable,
        "-m",
        "docsync",
        "scan",
        "--repo",
        str(repo),
        "--head",
        "missing",
        "--out",
        str(out),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    failure = (out / "failure.json").read_bytes()
    assert json.loads(failure)["code"] == "MISSING_REF"
    repeat = subprocess.run(command, capture_output=True, text=True)
    assert json.loads(repeat.stderr)["code"] == "OUTPUT_EXISTS"
    assert (out / "failure.json").read_bytes() == failure


@pytest.mark.parametrize(
    "expression", ["{'timeout': 60, **other}", "{'timeout': 60, 'timeout': 30}"]
)
def test_unknown_dict_overrides_not_confirmed(commit_files, expression):
    repo = commit_files(
        {
            "settings.py": "CONFIG = " + expression + "\n",
            "README.md": "## `settings.CONFIG`\n`timeout` defaults to `10`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert not report.findings and report.uncertain_count == 1


def test_import_binding_order_is_preserved(commit_files):
    repo = commit_files(
        {
            "one.py": "def f(): pass\n",
            "two.py": "def f(required): pass\n",
            "README.md": "```python\nfrom one import f as g\ng()\nfrom two import f as g\ng()\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert [j.decision for j in report.judgments] == ["CONSISTENT", "INCONSISTENT"]
    assert report.confirmed_count == 1


def test_rebound_example_alias_is_uncertain(commit_files):
    repo = commit_files(
        {
            "one.py": "def f(required): pass\n",
            "README.md": "```python\nfrom one import f as g\ng = other\ng()\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.uncertain_count == 1 and not report.findings


def test_english_sentence_period_not_lost(commit_files):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\nx defaults to 30.\n"}
    )
    assert scan(RepoSpec(repo=repo)).confirmed_count == 1


def test_repeated_invalid_calls_keep_distinct_findings(commit_files):
    repo = commit_files({"api.py": "def f(x): pass\n", "README.md": "```python\nf()\nf()\n```\n"})
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 2
    assert len({f.finding_id for f in report.findings}) == 2
