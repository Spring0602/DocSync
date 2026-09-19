import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from docsync.alignment import align
from docsync.cli import exit_code
from docsync.config import RepoSpec, ScanConfig, ScanOptions
from docsync.extractors.python_ast import extract_code
from docsync.llm import validate_response
from docsync.patches import apply_patch
from docsync.pipeline import scan
from docsync.repository import analyze
from docsync.utils import DocSyncError
from docsync.verification import verify

CODE = "def connect(timeout=60):\n    return timeout\n"
DOC = (
    "# Client\n\n## `connect`\n\n`timeout` 默认值为 `30`。\n\n```python\nconnect(timeout=30)\n```\n"
)


def test_real_default_conflict_patch_and_rescan(commit_files):
    repo = commit_files({"src/client.py": CODE, "README.md": DOC})
    before = (repo / "README.md").read_bytes()
    report = scan(RepoSpec(repo=repo))
    assert report.manifest.status == "COMPLETED"
    assert len(report.findings) == 1
    assert len(report.patches) == 1
    assert report.patches[0].validation == "VALIDATED"
    assert (repo / "README.md").read_bytes() == before
    assert len([j for j in report.judgments if j.reason_code == "CALL_ACCEPTED"]) == 1
    patch = report.patches[0]
    apply_patch(repo, patch, patch.diff)
    actual = (repo / "README.md").read_bytes()
    assert actual == before.replace("默认值为 `30`".encode(), "默认值为 `60`".encode())
    assert (repo / "src/client.py").read_text() == CODE
    assert not scan(RepoSpec(repo=repo, working_tree=True)).findings
    assert len(scan(RepoSpec(repo=repo)).findings) == 1  # HEAD remains immutable.
    with pytest.raises(DocSyncError, match="Preimage changed"):
        apply_patch(repo, patch, patch.diff)


@pytest.mark.parametrize(
    "code,doc,expected",
    [
        (CODE, DOC.replace("默认值为 `30`", "默认值为 `60`"), "CONSISTENT"),
        (CODE.replace("60", "factory()"), DOC, "UNCERTAIN"),
        (CODE, DOC.replace("## `connect`", "## 旧版 `connect`"), "UNCERTAIN"),
        (CODE, DOC.replace("默认值", "通常默认值"), "UNCERTAIN"),
        (CODE, DOC.replace("`connect`", "`other`"), "UNCERTAIN"),
        (CODE.replace("60", "True"), DOC.replace("`30`", "`1`"), "INCONSISTENT"),
    ],
)
def test_semantic_boundaries(commit_files, code, doc, expected):
    repo = commit_files({"client.py": code, "README.md": doc})
    report = scan(RepoSpec(repo=repo))
    default_ids = {c.claim_id for c in report.claims if c.kind == "DEFAULT_ASSERTION"}
    defaults = [j for j in report.judgments if j.claim_id in default_ids]
    assert len(defaults) == 1
    assert defaults[0].decision == expected
    assert len(report.findings) == int(expected == "INCONSISTENT")


def test_ambiguous_names_not_resolved_by_top_one(commit_files):
    repo = commit_files({"one.py": CODE, "two.py": CODE, "README.md": DOC})
    report = scan(RepoSpec(repo=repo))
    assert not report.findings
    assert report.uncertain_count == 2
    candidate = align(report.claims[:1], report.facts, top_k=1)[0]
    assert candidate.ambiguity
    assert len(candidate.candidates) == 1


def test_chinese_and_crlf_byte_offsets(commit_files):
    code = "def connect(名称='中文', timeout=60):\r\n    return 名称\r\n"
    repo = commit_files({"client.py": code, "README.md": DOC.replace("\n", "\r\n")})
    report = scan(RepoSpec(repo=repo))
    assert len(report.findings) == 1
    fact = next(f for f in report.facts if f.property == "timeout")
    raw = (repo / fact.span.path).read_bytes()
    assert raw[fact.span.start_byte : fact.span.end_byte] == b"60"
    patch = report.patches[0]
    apply_patch(repo, patch, patch.diff)
    raw = (repo / "README.md").read_bytes()
    assert raw.count(b"\r\n") == DOC.count("\n")


def test_all_parameter_kinds_and_none(commit_files):
    repo = commit_files({"api.py": "def f(x, /, y=None, *args, z, w=1, **kwargs):\n    pass\n"})
    code = extract_code(analyze(RepoSpec(repo=repo), ScanConfig()))
    params = {p.name: p for p in code.entities[0].signature}
    assert params["x"].kind == "POSITIONAL_ONLY"
    assert params["x"].value_state == "ABSENT"
    assert params["y"].typed_value.type == "NoneType"
    assert params["args"].kind == "VAR_POSITIONAL"
    assert params["z"].kind == "KEYWORD_ONLY" and params["z"].required
    assert params["kwargs"].kind == "VAR_KEYWORD"


def test_syntax_error_and_hybrid_are_partial(commit_files):
    repo = commit_files({"good.py": CODE, "bad.py": "def broken(:\n", "README.md": DOC})
    cfg = ScanConfig(scan=ScanOptions(mode="hybrid", require_complete=True))
    report = scan(RepoSpec(repo=repo), cfg)
    assert report.manifest.status == "PARTIAL"
    assert len(report.findings) == 1
    assert {d.code for d in report.manifest.diagnostics} >= {"PYTHON_PARSE_ERROR", "AI_UNAVAILABLE"}
    assert report.manifest.usage["requests"] == 0
    assert exit_code(report, cfg) == 3


def test_dirty_repo_and_snapshot_determinism(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    (repo / "client.py").write_text(CODE.replace("60", "30"))
    first = analyze(RepoSpec(repo=repo), ScanConfig())
    second = analyze(RepoSpec(repo=repo), ScanConfig())
    assert first.manifest == second.manifest
    assert first.manifest.dirty
    assert len(scan(RepoSpec(repo=repo)).findings) == 1
    assert not scan(RepoSpec(repo=repo, working_tree=True)).findings
    assert (repo / "client.py").read_text() == CODE.replace("60", "30")


def test_bad_base_and_limits(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    with pytest.raises(DocSyncError) as error:
        analyze(RepoSpec(repo=repo, base="missing-ref"), ScanConfig())
    assert error.value.code == "MISSING_REF"
    snapshot = analyze(RepoSpec(repo=repo), ScanConfig(scan=ScanOptions(max_file_bytes=10)))
    assert not snapshot.blobs
    assert all(d.code == "LIMIT_EXCEEDED" for d in snapshot.diagnostics)


def test_stale_patch_does_not_modify_any_file(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC, "guide.md": DOC})
    patch = scan(RepoSpec(repo=repo)).patches[0]
    (repo / "guide.md").write_text("changed", encoding="utf-8")
    before = (repo / "README.md").read_bytes()
    with pytest.raises(DocSyncError):
        apply_patch(repo, patch, patch.diff)
    assert (repo / "README.md").read_bytes() == before
    assert (repo / "guide.md").read_text() == "changed"


def test_forged_evidence_is_rejected(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    snapshot = analyze(RepoSpec(repo=repo), ScanConfig())
    report = scan(RepoSpec(repo=repo))
    claim = report.claims[0]
    judgment = report.judgments[0]
    facts = {f.fact_id: f for f in report.facts}
    bad_span = claim.span.model_copy(update={"start_line": 999})
    rejected = verify(judgment, claim.model_copy(update={"span": bad_span}), facts, snapshot)
    assert rejected.reason == "EVIDENCE_MISMATCH"
    fake = judgment.model_copy(update={"fact_ids": ["invented-id"]})
    assert verify(fake, claim, facts, snapshot).reason == "INVALID_REFERENCE"
    with pytest.raises(ValueError):
        validate_response(fake.model_dump_json(), claim, set(facts))
    payload = json.loads(judgment.model_dump_json())
    payload["execute"] = "arbitrary command"
    with pytest.raises(ValueError):
        validate_response(json.dumps(payload), claim, set(facts))


def test_cli_exit_codes_and_artifacts(commit_files, tmp_path):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    out = tmp_path / "run"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "docsync",
            "scan",
            "--repo",
            str(repo),
            "--out",
            str(out),
            "--fail-on",
            "warning",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["confirmed_count"] == 1
    assert (out / "report.json").is_file()
    assert (out / "report.md").is_file()
    assert (out / "claims.jsonl").is_file()
    failure = subprocess.run(
        [
            sys.executable,
            "-m",
            "docsync",
            "scan",
            "--repo",
            str(repo),
            "--base",
            "missing",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert failure.returncode == 2
    assert json.loads(failure.stderr)["status"] == "FAILED"


def test_changed_code_still_checks_unmodified_readme(commit_files):
    repo = commit_files({"client.py": CODE.replace("60", "30"), "README.md": DOC})
    base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    commit_files({"client.py": CODE})
    report = scan(RepoSpec(repo=repo, base=base))
    assert len(report.findings) == 1
    assert report.snapshot.changed_paths == ["client.py"]


def test_unclosed_fence_has_diagnostic(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC.rsplit("```", 1)[0]})
    report = scan(RepoSpec(repo=repo))
    assert any(d.code == "UNCLOSED_FENCE" for d in report.manifest.diagnostics)


def test_patch_rejects_disappeared_claim(commit_files):
    repo = commit_files(
        {"client.py": CODE.replace("60", "[1, 2]"), "README.md": DOC.replace("`30`", "30")}
    )
    report = scan(RepoSpec(repo=repo))
    assert len(report.findings) == 1
    assert not report.patches  # Unsupported unquoted list must not silently remove the claim.


def test_same_line_two_edits_survive_offset_shift(commit_files):
    repo = commit_files(
        {
            "client.py": "def connect(timeout=600, retries=5):\n    pass\n",
            "README.md": "## `connect`\n\n`timeout` 默认值为 `30`。`connect` 的 `retries` 默认值为 `1`。\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert len(report.findings) == 2
    assert len(report.patches) == 1
    apply_patch(repo, report.patches[0], report.patches[0].diff)
    assert not scan(RepoSpec(repo=repo, working_tree=True)).findings


def test_commit_symlink_is_skipped_without_os_symlink_privileges(commit_files):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    oid = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
        input="../../outside.md",
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "-C", str(repo), "update-index", "--add", "--cacheinfo", f"120000,{oid},linked.md"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "--quiet", "-m", "symlink fixture"], check=True
    )
    snapshot = analyze(RepoSpec(repo=repo), ScanConfig())
    assert "linked.md" not in snapshot.blobs
    assert any(d.code == "SYMLINK_SKIPPED" for d in snapshot.diagnostics)


def test_action_wrapper_reuses_cli(commit_files, tmp_path):
    repo = commit_files({"client.py": CODE, "README.md": DOC})
    output = tmp_path / "action-output"
    summary = tmp_path / "action-summary"
    environment = {
        **os.environ,
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_OUTPUT": str(output),
        "GITHUB_STEP_SUMMARY": str(summary),
        "DOCSYNC_REPO": str(repo),
        "DOCSYNC_HEAD": "HEAD",
        "DOCSYNC_MODE": "rules",
        "DOCSYNC_FAIL_ON": "none",
    }
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parents[2] / "action/run.py")],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert values["scan-status"] == "COMPLETED"
    assert values["confirmed-count"] == "1"
    assert Path(values["report-path"]).is_file()
    assert Path(values["patch-path"]).is_file()


def test_multifile_apply_rolls_back_when_later_write_fails(commit_files, monkeypatch):
    import docsync.patches as patches

    repo = commit_files({"client.py": CODE, "README.md": DOC, "guide.md": DOC})
    proposal = scan(RepoSpec(repo=repo)).patches[0]
    before = {name: (repo / name).read_bytes() for name in ("README.md", "guide.md")}
    original_write = patches.atomic_write

    def fail_second(path, data):
        if path.name == "guide.md":
            raise OSError("Controlled write failure")
        original_write(path, data)

    monkeypatch.setattr(patches, "atomic_write", fail_second)
    with pytest.raises(OSError):
        patches.apply_patch(repo, proposal, proposal.diff)
    assert {name: (repo / name).read_bytes() for name in before} == before
