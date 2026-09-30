"""B1: package, Schema 2.0 and repository snapshot contract review."""

import copy
import hashlib
import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from sysconfig import get_path

import pytest
from pydantic import ValidationError

from docsync import __version__
from docsync.cli import exit_code, main
from docsync.config import RepoSpec, ScanConfig, ScanOptions
from docsync.models import FileRecord, ScanReport
from docsync.pipeline import scan
from docsync.repository import analyze


def test_installed_and_module_cli_expose_the_same_commands():
    console = Path(get_path("scripts")) / ("docsync.exe" if os.name == "nt" else "docsync")
    assert console.is_file()
    assert version("docsync-core") == __version__

    module = subprocess.run(
        [sys.executable, "-m", "docsync", "--help"], capture_output=True, text=True, check=False
    )
    installed = subprocess.run(
        [str(console), "--help"], capture_output=True, text=True, check=False
    )
    assert module.returncode == installed.returncode == 0
    assert module.stdout == installed.stdout
    for command in ("scan", "patch", "apply", "schema", "benchmark"):
        assert command in installed.stdout
        help_result = subprocess.run(
            [str(console), command, "--help"], capture_output=True, text=True, check=False
        )
        assert help_result.returncode == 0
        assert f"docsync {command}" in help_result.stdout


@pytest.mark.parametrize(
    "kind,checked_in",
    [("report", "schemas/report.schema.json"), ("benchmark", "bench/schema/sample.schema.json")],
)
def test_generated_schema_matches_checked_in_contract(kind, checked_in, tmp_path):
    generated = tmp_path / f"{kind}.schema.json"
    assert main(["schema", "--kind", kind, "--out", str(generated)]) == 0
    actual = json.loads(generated.read_bytes())
    expected = json.loads(Path(checked_in).read_bytes())
    assert actual == expected
    assert actual["additionalProperties"] is False
    if kind == "report":
        assert actual["properties"]["schema_version"]["default"] == "2.0"


@pytest.mark.parametrize(
    "payload",
    [
        {"unexpected": True},
        {"scan": {"unexpected": True}},
        {"alignment": {"unexpected": True}},
        {"llm": {"unexpected": True}},
        {"ignores": [{"reason": "review", "unexpected": True}]},
    ],
)
def test_unknown_configuration_fields_are_rejected_at_every_level(payload):
    with pytest.raises(ValidationError):
        ScanConfig.model_validate(payload)


@pytest.mark.parametrize(
    "case",
    [
        "duplicate_entity",
        "duplicate_snapshot_path",
        "fact_entity",
        "fact_snapshot",
        "claim_snapshot",
        "candidate_claim",
        "candidate_fact",
        "judgment_claim",
        "judgment_fact",
        "finding_claim",
        "finding_fact",
        "evidence_head",
        "evidence_snapshot",
        "evidence_document",
        "evidence_code",
        "patch_finding",
    ],
)
def test_report_rejects_broken_foreign_keys_and_evidence(case, commit_files):
    repo = commit_files(
        {
            "client.py": "def connect(timeout=60):\n    return timeout\n",
            "README.md": "# `connect`\n\n`timeout` 默认值为 `30`。\n",
        }
    )
    payload = copy.deepcopy(scan(RepoSpec(repo=repo)).model_dump(mode="json"))
    if case == "duplicate_entity":
        payload["entities"].append(copy.deepcopy(payload["entities"][0]))
    elif case == "duplicate_snapshot_path":
        payload["snapshot"]["files"].append(copy.deepcopy(payload["snapshot"]["files"][0]))
    elif case == "fact_entity":
        payload["facts"][0]["entity_id"] = "missing"
    elif case == "fact_snapshot":
        payload["facts"][0]["span"]["blob_hash"] = "0" * 64
    elif case == "claim_snapshot":
        payload["claims"][0]["span"]["blob_hash"] = "0" * 64
    elif case == "candidate_claim":
        payload["candidates"][0]["claim_id"] = "missing"
    elif case == "candidate_fact":
        payload["candidates"][0]["candidates"][0]["fact_id"] = "missing"
    elif case == "judgment_claim":
        payload["judgments"][0]["claim_id"] = "missing"
    elif case == "judgment_fact":
        payload["judgments"][0]["fact_ids"] = ["missing"]
    elif case == "finding_claim":
        payload["findings"][0]["claim_id"] = "missing"
    elif case == "finding_fact":
        payload["findings"][0]["fact_ids"] = ["missing"]
    elif case == "evidence_head":
        payload["findings"][0]["evidence"]["head_sha"] = "0" * 40
    elif case == "evidence_snapshot":
        payload["findings"][0]["evidence"]["snapshot_hash"] = "missing"
    elif case == "evidence_document":
        payload["findings"][0]["evidence"]["document"]["start_line"] = 999
    elif case == "evidence_code":
        payload["findings"][0]["evidence"]["code"]["start_line"] = 999
    elif case == "patch_finding":
        payload["patches"][0]["finding_ids"] = ["missing"]
    with pytest.raises(ValidationError):
        ScanReport.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"path": "../README.md", "blob_hash": "0" * 64, "size": 1},
        {"path": "README.md", "blob_hash": "not-a-sha256", "size": 1},
        {"path": "README.md", "blob_hash": "0" * 64, "size": -1},
    ],
)
def test_file_records_reject_unsafe_or_impossible_metadata(payload):
    with pytest.raises(ValidationError):
        FileRecord.model_validate(payload)


def test_commit_snapshot_ignores_dirty_worktree_until_explicitly_selected(commit_files):
    committed = b"def connect(timeout=60):\r\n    return timeout\r\n"
    working = committed.replace(b"60", b"30")
    repo = commit_files({"client.py": committed, "README.md": "# Client\n"})
    (repo / "client.py").write_bytes(working)

    fixed = analyze(RepoSpec(repo=repo), ScanConfig())
    live = analyze(RepoSpec(repo=repo, working_tree=True), ScanConfig())

    assert fixed.manifest.mode == "commit"
    assert live.manifest.mode == "working-tree"
    assert fixed.manifest.dirty and live.manifest.dirty
    assert fixed.blobs["client.py"] == committed
    assert live.blobs["client.py"] == working
    record = next(item for item in fixed.manifest.files if item.path == "client.py")
    assert record.blob_hash == hashlib.sha256(committed).hexdigest()
    assert record.size == len(committed)


def test_base_records_changes_but_falls_back_to_all_head_blobs(commit_files):
    repo = commit_files({"client.py": "VALUE = 1\n", "README.md": "# Stable documentation\n"})
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    commit_files({"client.py": "VALUE = 2\n"})

    snapshot = analyze(RepoSpec(repo=repo, base=base), ScanConfig())
    assert snapshot.manifest.base_sha == base
    assert snapshot.manifest.changed_paths == ["client.py"]
    assert set(snapshot.blobs) == {"README.md", "client.py"}
    assert any(item.code == "FULL_SCAN_FALLBACK" for item in snapshot.diagnostics)


def test_include_exclude_and_both_size_limits_are_auditable(commit_files):
    repo = commit_files(
        {
            "a.py": "a=1\n",
            "b.py": "b=2\n",
            "skip.py": "skip=3\n",
            "guide.md": "# Guide\n",
            "notes.txt": "not supported\n",
        }
    )
    filtered = analyze(
        RepoSpec(repo=repo),
        ScanConfig(scan=ScanOptions(include=["**/*.py"], exclude=["skip.py"])),
    )
    assert set(filtered.blobs) == {"a.py", "b.py"}
    assert {item.path for item in filtered.diagnostics if item.code == "EXCLUDED"} == {
        "guide.md",
        "skip.py",
    }

    per_file = analyze(
        RepoSpec(repo=repo), ScanConfig(scan=ScanOptions(max_file_bytes=3, max_total_bytes=100))
    )
    assert not per_file.blobs
    assert all(item.code == "LIMIT_EXCEEDED" for item in per_file.diagnostics)

    total = analyze(
        RepoSpec(repo=repo), ScanConfig(scan=ScanOptions(max_file_bytes=100, max_total_bytes=6))
    )
    assert set(total.blobs) == {"a.py"}
    assert any(item.code == "LIMIT_EXCEEDED" for item in total.diagnostics)


def test_non_utf8_is_diagnostic_and_never_reported_complete(commit_files):
    repo = commit_files({"good.py": "VALUE = 1\n", "bad.md": b"# invalid\n\xff\n"})
    cfg = ScanConfig(scan=ScanOptions(require_complete=True))
    report = scan(RepoSpec(repo=repo), cfg)

    assert "bad.md" not in {item.path for item in report.snapshot.files}
    assert report.manifest.status == "PARTIAL"
    diagnostic = next(item for item in report.manifest.diagnostics if item.path == "bad.md")
    assert diagnostic.code == "UNREADABLE_TEXT"
    assert diagnostic.affects_completeness
    assert exit_code(report, cfg) == 3
