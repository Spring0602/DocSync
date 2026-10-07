import json
from pathlib import Path

import pytest

from bench.run_suite import plan_suite, run_suite, summarize_method
from docsync.config import LLMOptions, ScanConfig
from docsync.metrics import evaluate


@pytest.fixture
def manifest(tmp_path):
    source = Path("bench/frozen/seed-dev-v1/manifest.jsonl").read_bytes().splitlines()[0]
    p = tmp_path / "manifest.jsonl"
    p.write_bytes(source + b"\n")
    return p


def test_suite_budget_and_provisional_rejection(manifest):
    cfg = ScanConfig(llm=LLMOptions(max_requests=1))
    assert plan_suite(manifest, cfg, ["rules", "full", "llm"], 2)["request_upper_bound"] == 2
    with pytest.raises(ValueError):
        plan_suite(manifest, cfg, ["full", "llm"], 1)
    with pytest.raises(ValueError):
        plan_suite(manifest, cfg, ["full", "full"], 2)
    row = json.loads(manifest.read_bytes())
    row["annotation_status"] = "provisional"
    manifest.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError):
        plan_suite(manifest, cfg, ["rules"], 0)


def test_missing_key_never_starts_run(manifest, tmp_path, monkeypatch):
    monkeypatch.delenv("DOCSYNC_TEST_MISSING", raising=False)
    cfg = ScanConfig(
        llm=LLMOptions(
            provider="chat-completions", api_key_env="DOCSYNC_TEST_MISSING", max_requests=1
        )
    )
    out = tmp_path / "suite"
    with pytest.raises(ValueError):
        run_suite(manifest, cfg, out, ["full"], 1)
    assert not out.exists()


def test_summary_preserves_partial_and_rechecks_metrics(tmp_path):
    row = dict(
        sample_id="one",
        gold="INCONSISTENT",
        prediction="UNCERTAIN",
        status="PARTIAL",
        usage={"requests": 1, "unknown_usage_requests": 1},
        errors=["MODEL_TIMEOUT_OR_NETWORK_ERROR"],
        elapsed_seconds=1.2,
    )
    (tmp_path / "predictions.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(evaluate([row])), encoding="utf-8")
    result = summarize_method(tmp_path, ["one"])
    assert result["metrics"]["counts"]["fn"] == 1
    assert result["status_counts"] == {"PARTIAL": 1}
    assert result["usage"]["unknown_usage_requests"] == 1
    assert len(result["review_items"]) == 1
    with pytest.raises(ValueError):
        summarize_method(tmp_path, ["missing"])
    path.write_text(json.dumps({"sample_count": 0}), encoding="utf-8")
    with pytest.raises((ValueError, KeyError)):
        summarize_method(tmp_path, ["one"])


def test_runner_preserves_method_failure(manifest, tmp_path, monkeypatch):
    import bench.run_suite as suite
    from docsync.utils import DocSyncError

    monkeypatch.setattr(suite, "verify_installed_source", lambda _: None)
    monkeypatch.setattr(suite, "provenance", lambda _: {"source_hashes_lf": {}})

    def fail(*args):
        raise DocSyncError("MISSING_REF", "fixture failure")

    monkeypatch.setattr(suite, "run_benchmark", fail)
    out = tmp_path / "failed-suite"
    with pytest.raises(DocSyncError):
        run_suite(manifest, ScanConfig(), out, ["rules"], 0)
    state = json.loads((out / "suite.json").read_bytes())
    assert state["status"] == "INTERRUPTED"
    assert state["results"]["rules"]["suite_method_error"] == "DocSyncError"
