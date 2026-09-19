import json
import subprocess

import pytest

from docsync.benchmark import run_benchmark
from docsync.config import IgnoreRule, ScanConfig
from docsync.utils import DocSyncError


def manifest_for(repo, root, **overrides):
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    row = {
        "sample_id": "case-1",
        "repo_id": "r1",
        "repo_path": "repo",
        "head_sha": sha,
        "code_path": "api.py",
        "document_path": "README.md",
        "group_id": "g1",
        "split": "dev",
        "origin": "controlled",
        "gold": "INCONSISTENT",
        "drift_type": "DEFAULT_VALUE",
        "rights_status": "pending",
        "annotation_status": "provisional",
        "claim_line": None,
    }
    row.update(overrides)
    path = root / "manifest.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return path, row


def test_rules_benchmark_ignores_user_suppressions(commit_files, tmp_path):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    manifest, _ = manifest_for(repo, tmp_path)
    cfg = ScanConfig(ignores=[IgnoreRule(reason="Suppress all in user scans")])
    result = run_benchmark(manifest, cfg, tmp_path / "bench", "rules")
    assert result["failed_or_partial"] == 0 and result["provisional_labels"]
    prediction = json.loads((tmp_path / "bench/predictions.jsonl").read_text())
    assert prediction["prediction"] == "INCONSISTENT"
    assert json.loads((tmp_path / "bench/metrics.json").read_text())["counts"]["tp"] == 1


def test_pure_llm_without_provider_never_fakes_success(commit_files, tmp_path):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    manifest, _ = manifest_for(repo, tmp_path)
    result = run_benchmark(manifest, ScanConfig(), tmp_path / "llm", "llm")
    assert result["failed_or_partial"] == 1
    row = json.loads((tmp_path / "llm/predictions.jsonl").read_text())
    assert row["prediction"] == "UNCERTAIN" and row["status"] == "PARTIAL"


def test_missing_commit_kept_as_false_negative(commit_files, tmp_path):
    repo = commit_files({"api.py": "def f(): pass\n"})
    manifest, _ = manifest_for(repo, tmp_path, head_sha="0" * 40)
    run_benchmark(manifest, ScanConfig(), tmp_path / "bench", "rules")
    result = json.loads((tmp_path / "bench/metrics.json").read_text())
    assert result["counts"]["fn"] == 1 and result["counts"]["failed"] == 1


def test_split_leakage_rejected(commit_files, tmp_path):
    repo = commit_files({"api.py": "def f(): pass\n"})
    manifest, row = manifest_for(repo, tmp_path)
    with manifest.open("a") as stream:
        stream.write(json.dumps({**row, "sample_id": "case-2", "split": "test"}) + "\n")
    with pytest.raises(DocSyncError) as error:
        run_benchmark(manifest, ScanConfig(), tmp_path / "bench", "rules")
    assert error.value.code == "SPLIT_LEAKAGE"


def test_keyword_baseline_does_not_use_signature_or_type_verifier(commit_files, tmp_path):
    repo = commit_files({"api.py": "def f(x=60): pass\n", "README.md": "```python\nf(x=30)\n```\n"})
    manifest, _ = manifest_for(repo, tmp_path, gold="CONSISTENT", drift_type="SIGNATURE")
    result = run_benchmark(manifest, ScanConfig(), tmp_path / "keyword", "keyword")
    assert result["failed_or_partial"] == 0
    row = json.loads((tmp_path / "keyword/predictions.jsonl").read_text())
    assert row["prediction_stage"] == "keyword" and row["prediction"] == "INCONSISTENT"
    # This deliberately simple B1 makes the documented explicit-value false positive.
