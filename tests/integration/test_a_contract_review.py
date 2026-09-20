"""A1: exercise public contracts with an actual archived 0.1.0 report."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from docsync.cli import exit_code, main
from docsync.config import RepoSpec, ScanConfig, ScanOptions
from docsync.models import ScanReport
from docsync.pipeline import scan
from docsync.reporting import write_report

ARCHIVE = Path(__file__).parents[1] / "fixtures/reports/v1-default.json"


@pytest.fixture(params=["1.0", "2.0"])
def versioned_report(request, commit_files):
    if request.param == "1.0":
        return json.loads(ARCHIVE.read_bytes())
    repo = commit_files(
        {
            "client.py": "def connect(timeout=60): pass\n",
            "README.md": "# `connect`\n\n`timeout` 默认值为 `30`。\n",
        }
    )
    return scan(RepoSpec(repo=repo)).model_dump(mode="json")


def test_report_read_render_and_patch_export(versioned_report, tmp_path):
    original = versioned_report
    report = ScanReport.model_validate(original)
    assert report.schema_version == original["schema_version"]
    assert report.confirmed_count == 1
    out = tmp_path / "rendered"
    write_report(report, out, {"json", "md"})
    reread = ScanReport.model_validate_json((out / "report.json").read_bytes())
    assert reread.findings == report.findings
    for before, after in zip(original["findings"], reread.findings, strict=True):
        assert before["evidence"] == after.evidence.model_dump(mode="json")
    for claim in report.claims:
        assert claim.span == next(c.span for c in reread.claims if c.claim_id == claim.claim_id)
    assert report.findings[0].finding_id in (out / "report.md").read_text(encoding="utf-8")
    diff = tmp_path / "fix.patch"
    assert main(["patch", "--report", str(out / "report.json"), "--out", str(diff)]) == 0
    assert diff.read_bytes() == report.patches[0].diff.encode("utf-8")
    assert json.loads(diff.with_suffix(".patch.json").read_bytes())["requires_review"] is True


def test_tampered_evidence_rejected_for_both_versions(versioned_report, tmp_path, capsys):
    versioned_report["findings"][0]["evidence"]["head_sha"] = "forged"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(versioned_report), encoding="utf-8")
    target = tmp_path / "bad.patch"
    assert main(["patch", "--report", str(path), "--out", str(target)]) == 2
    assert json.loads(capsys.readouterr().err)["code"] == "INVALID_INPUT"
    assert not target.exists()


def test_failure_envelope_is_not_a_scan_report(tmp_path, capsys):
    out = tmp_path / "failure"
    assert main(["scan", "--out", str(out), "--format", "xml"]) == 2
    failure = json.loads((out / "report.json").read_bytes())
    assert failure["status"] == "FAILED"
    assert failure["code"] == "INVALID_FORMAT"
    assert json.loads(capsys.readouterr().err) == failure
    with pytest.raises(ValidationError):
        ScanReport.model_validate(failure)
    assert (
        main(
            [
                "patch",
                "--report",
                str(out / "report.json"),
                "--out",
                str(tmp_path / "failure.patch"),
            ]
        )
        == 2
    )


@pytest.mark.parametrize(
    "status,require_complete,fail_on,expected",
    [
        ("FAILED", True, "warning", 2),
        ("PARTIAL", True, "warning", 3),
        ("PARTIAL", False, "warning", 1),
        ("PARTIAL", False, "none", 0),
        ("COMPLETED", True, "warning", 1),
        ("COMPLETED", True, "none", 0),
    ],
)
def test_scan_exit_precedence(status, require_complete, fail_on, expected):
    report = ScanReport.model_validate_json(ARCHIVE.read_bytes())
    report = report.model_copy(
        update={"manifest": report.manifest.model_copy(update={"status": status})}
    )
    cfg = ScanConfig(scan=ScanOptions(require_complete=require_complete, fail_on=fail_on))
    assert exit_code(report, cfg) == expected


@pytest.mark.parametrize("kind", ["report", "benchmark"])
def test_public_schema_export(kind, tmp_path):
    path = tmp_path / f"{kind}.json"
    assert main(["schema", "--kind", kind, "--out", str(path)]) == 0
    schema = json.loads(path.read_bytes())
    assert schema["additionalProperties"] is False
    assert schema["required"]


def test_unknown_config_is_failed_without_echoing_input(tmp_path, capsys):
    config = tmp_path / "bad.toml"
    config.write_text('[llm]\nsecret = "must-not-echo"\n', encoding="utf-8")
    assert main(["scan", "--config", str(config), "--out", str(tmp_path / "out")]) == 2
    error = capsys.readouterr().err
    assert "must-not-echo" not in error
    assert json.loads(error)["code"] == "INVALID_INPUT"
