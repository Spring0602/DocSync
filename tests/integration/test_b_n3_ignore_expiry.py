import json
from datetime import date
from pathlib import Path

import pytest

import docsync.pipeline as pipeline
from docsync.cli import exit_code
from docsync.config import IgnoreRule, RepoSpec, ScanConfig, ScanOptions
from docsync.models import ScanReport
from docsync.patches import apply_patch
from docsync.pipeline import scan
from docsync.reporting import markdown_report
from docsync.utils import DocSyncError

SCAN_DATE = date(2026, 10, 4)
ARCHIVED_REPORTS = [
    Path(__file__).parents[1] / "fixtures/reports/v1-default.json",
    Path(__file__).parents[2] / "docs/audit-samples/b3/default/report.json",
]


class FixedDate(date):
    calls = 0

    @classmethod
    def today(cls):
        cls.calls += 1
        return SCAN_DATE


@pytest.fixture(autouse=True)
def fixed_scan_date(monkeypatch):
    FixedDate.calls = 0
    monkeypatch.setattr(pipeline, "date", FixedDate)


def drift_repo(commit_files):
    return commit_files(
        {
            "api.py": "def f(x=60): pass\n",
            "README.md": "## `f`\n\n`x` defaults to `30`.\n",
        }
    )


@pytest.mark.parametrize(
    ("rules", "ignored", "reason", "expires"),
    [
        ([IgnoreRule(path="other.md", reason="not matched")], False, None, None),
        ([IgnoreRule(reason="no deadline")], True, "no deadline", None),
        (
            [IgnoreRule(reason="future", expires=date(2026, 10, 5))],
            True,
            "future",
            date(2026, 10, 5),
        ),
        (
            [IgnoreRule(reason="boundary", expires=SCAN_DATE)],
            True,
            "boundary",
            SCAN_DATE,
        ),
        (
            [IgnoreRule(reason="expired", expires=date(2026, 10, 3))],
            False,
            "expired",
            date(2026, 10, 3),
        ),
    ],
)
def test_ignore_expiry_contract(commit_files, rules, ignored, reason, expires):
    cfg = ScanConfig(scan=ScanOptions(fail_on="warning"), ignores=rules)
    report = scan(RepoSpec(repo=drift_repo(commit_files)), cfg)
    finding = report.findings[0]

    assert finding.ignored is ignored
    assert finding.ignore_reason == reason
    assert finding.ignore_expires == expires
    assert report.ignored_count == int(ignored)
    assert report.confirmed_count == int(not ignored)
    assert bool(report.patches) is not ignored
    assert exit_code(report, cfg) == int(not ignored)
    assert FixedDate.calls == 1


def test_one_scan_uses_one_date_for_all_findings(commit_files, monkeypatch):
    class MovingDate(date):
        calls = 0

        @classmethod
        def today(cls):
            cls.calls += 1
            return date(2026, 10, 4) if cls.calls == 1 else date(2026, 10, 6)

    monkeypatch.setattr(pipeline, "date", MovingDate)
    repo = commit_files(
        {
            "api.py": "def f(x=60): pass\ndef g(x=60): pass\n",
            "README.md": ("## `f`\n`x` defaults to `30`.\n\n## `g`\n`x` defaults to `30`.\n"),
        }
    )
    cfg = ScanConfig(ignores=[IgnoreRule(reason="same scan", expires=date(2026, 10, 5))])

    report = scan(RepoSpec(repo=repo), cfg)

    assert report.ignored_count == 2
    assert {finding.ignore_expires for finding in report.findings} == {date(2026, 10, 5)}
    assert MovingDate.calls == 1


def test_active_rule_wins_without_mixing_expired_metadata(commit_files):
    cfg = ScanConfig(
        ignores=[
            IgnoreRule(reason="old", expires=date(2026, 10, 3)),
            IgnoreRule(reason="current", expires=date(2026, 10, 5)),
        ]
    )

    finding = scan(RepoSpec(repo=drift_repo(commit_files)), cfg).findings[0]

    assert finding.ignored
    assert finding.ignore_reason == "current"
    assert finding.ignore_expires == date(2026, 10, 5)


@pytest.mark.parametrize("archive", ARCHIVED_REPORTS)
def test_old_reports_default_missing_expiry_without_recomputing(archive):
    raw = json.loads(archive.read_bytes())
    report = ScanReport.model_validate(raw)

    assert all(finding.ignore_expires is None for finding in report.findings)
    assert [finding.finding_id for finding in report.findings] == [
        finding["finding_id"] for finding in raw["findings"]
    ]
    assert [patch.patch_id for patch in report.patches] == [
        patch["patch_id"] for patch in raw.get("patches", [])
    ]
    assert [patch.diff for patch in report.patches] == [
        patch["diff"] for patch in raw.get("patches", [])
    ]


def test_ignore_expiry_schema_is_optional_date_or_null():
    finding = ScanReport.model_json_schema()["$defs"]["Finding"]
    expires = finding["properties"]["ignore_expires"]

    assert "ignore_expires" not in finding["required"]
    assert expires["default"] is None
    assert {item.get("type") for item in expires["anyOf"]} == {"string", "null"}
    assert (
        next(item for item in expires["anyOf"] if item.get("type") == "string")["format"] == "date"
    )


def test_disappeared_patch_target_returns_structured_error(commit_files):
    repo = drift_repo(commit_files)
    proposal = scan(RepoSpec(repo=repo)).patches[0]
    (repo / "README.md").unlink()

    with pytest.raises(DocSyncError) as error:
        apply_patch(repo, proposal, proposal.diff)

    assert error.value.code == "UNSAFE_PATCH"
    assert error.value.stage == "apply"


@pytest.mark.parametrize(
    ("rules", "expected", "unexpected"),
    [
        ([IgnoreRule(path="other.md", reason="not matched")], "忽略状态：未忽略", "到期日"),
        (
            [IgnoreRule(reason="no deadline")],
            "忽略状态：当前忽略；原因：no deadline；无期限",
            "到期日",
        ),
        (
            [IgnoreRule(reason="future", expires=date(2026, 10, 5))],
            "忽略状态：当前忽略；原因：future；到期日：2026-10-05",
            None,
        ),
        (
            [IgnoreRule(reason="expired", expires=date(2026, 10, 3))],
            "忽略状态：规则已过期，告警未忽略；原因：expired；到期日：2026-10-03",
            None,
        ),
    ],
)
def test_markdown_report_explains_ignore_expiry_states(commit_files, rules, expected, unexpected):
    report = scan(RepoSpec(repo=drift_repo(commit_files)), ScanConfig(ignores=rules))

    markdown = markdown_report(report)

    assert expected in markdown
    if unexpected is not None:
        assert unexpected not in markdown
