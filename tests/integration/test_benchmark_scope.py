import json

import pytest

import docsync.benchmark as benchmark
from docsync.benchmark import BenchmarkSample, predict, run_benchmark
from docsync.benchmark_scope import ClaimScope, LineRange
from docsync.config import RepoSpec, ScanConfig
from docsync.pipeline import scan


def test_scope_isolates_shared_document_and_entity(commit_files):
    repo = commit_files(
        {
            "api.py": "def f(x=60): pass\ndef g(x=30): pass\n",
            "README.md": "## `f`\n`x` defaults to `30`.\n\n## `g`\n`x` defaults to `30`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo), ScanConfig())
    fact = next(
        f for f in report.facts if f.typed_value and f.typed_value.canonical == '["int",60]'
    )
    entity = next(e for e in report.entities if e.entity_id == fact.entity_id)
    scope = ClaimScope(
        document_ranges=[LineRange(start=2, end=2)],
        code_path="api.py",
        entity_names=[entity.qualified_name],
        subject="f",
        predicate="x",
    )
    sample = BenchmarkSample(
        sample_id="synthetic",
        repo_id="synthetic",
        repo_path="repo",
        head_sha=report.snapshot.head_sha,
        document_path="README.md",
        code_path="api.py",
        group_id="synthetic",
        split="dev",
        origin="controlled",
        gold="INCONSISTENT",
        drift_type="DEFAULT_VALUE",
        rights_status="pending",
        claim_scope=scope,
    )
    assert predict(report, sample, "rules") == "INCONSISTENT"
    wrong_entity = scope.model_copy(update={"entity_names": ["unrelated.g"]})
    assert (
        predict(report, sample.model_copy(update={"claim_scope": wrong_entity}), "rules")
        == "UNCERTAIN"
    )
    absent = scope.model_copy(update={"document_ranges": [LineRange(start=99, end=99)]})
    assert predict(report, sample.model_copy(update={"claim_scope": absent}), "rules") == "SKIPPED"
    assert predict(report, sample.model_copy(update={"head_sha": "0" * 40}), "rules") == "UNCERTAIN"
    judgment = next(j for j in report.judgments if j.decision == "INCONSISTENT")
    contradictory = report.model_copy(
        update={
            "judgments": [*report.judgments, judgment.model_copy(update={"decision": "CONSISTENT"})]
        }
    )
    assert predict(contradictory, sample, "rules") == "UNCERTAIN"
    unverified = report.model_copy(update={"findings": []})
    assert predict(unverified, sample, "rules") == "UNCERTAIN"
    assert predict(unverified, sample, "llm") == "INCONSISTENT"
    missing = scope.model_copy(
        update={"required_provenance": [fact.span.model_copy(update={"path": "missing.py"})]}
    )
    assert (
        predict(report, sample.model_copy(update={"claim_scope": missing}), "rules") == "UNCERTAIN"
    )
    present = scope.model_copy(update={"required_provenance": [fact.span]})
    assert (
        predict(report, sample.model_copy(update={"claim_scope": present}), "rules")
        == "INCONSISTENT"
    )


def test_benchmark_reuses_report_for_samples_from_same_repository(
    commit_files, tmp_path, monkeypatch
):
    repo = commit_files(
        {
            "api.py": "def f(x=60): pass\ndef g(x=30): pass\n",
            "README.md": "## `f`\n`x` defaults to `30`.\n\n## `g`\n`x` defaults to `30`.\n",
        }
    )
    head_sha = benchmark.analyze(
        benchmark.RepoSpec(repo=repo), benchmark.ScanConfig()
    ).manifest.head_sha
    manifest = tmp_path / "manifest.jsonl"
    samples = [
        BenchmarkSample(
            sample_id=name,
            repo_id="shared",
            repo_path="repo",
            head_sha=head_sha,
            document_path="README.md",
            code_path="api.py",
            group_id=name,
            split="dev",
            origin="controlled",
            gold="INCONSISTENT",
            drift_type="DEFAULT_VALUE",
            rights_status="pending",
            claim_scope={
                "document_ranges": [{"start": line, "end": line}],
                "code_path": "api.py",
                "entity_names": [entity],
                "subject": subject,
                "predicate": "x",
            },
        ).model_dump_json()
        for name, line, entity, subject in (
            ("f-sample", 2, "api.f", "f"),
            ("g-sample", 5, "api.g", "g"),
        )
    ]
    manifest.write_text("\n".join(samples) + "\n", encoding="utf-8")
    calls = 0
    original_scan = benchmark.scan

    def counted_scan(*args, **kwargs):
        nonlocal calls
        calls += 1
        report = original_scan(*args, **kwargs)
        return report.model_copy(
            update={
                "manifest": report.manifest.model_copy(
                    update={"usage": {"requests": 3, "input_tokens": 21}}
                )
            }
        )

    monkeypatch.setattr(benchmark, "scan", counted_scan)
    run_benchmark(manifest, benchmark.ScanConfig(), tmp_path / "out", "rules")
    assert calls == 1
    rows = [
        json.loads(line) for line in (tmp_path / "out/predictions.jsonl").read_text().splitlines()
    ]
    assert sum(r["usage"].get("requests", 0) for r in rows) == 3
    assert [r["report_reused"] for r in rows] == [False, True]
    assert [r["prediction"] for r in rows] == ["INCONSISTENT", "CONSISTENT"]
    metrics = json.loads((tmp_path / "out/metrics.json").read_text(encoding="utf-8"))
    assert metrics["evaluation_unit"] == "declaration"
    assert metrics["declaration_count"] == 2


def test_benchmark_rejects_duplicate_discovery_ownership(commit_files, tmp_path):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    head_sha = benchmark.analyze(
        benchmark.RepoSpec(repo=repo), benchmark.ScanConfig()
    ).manifest.head_sha
    sample = BenchmarkSample(
        sample_id="one",
        repo_id="shared",
        repo_path="repo",
        head_sha=head_sha,
        document_path="README.md",
        code_path="api.py",
        group_id="shared",
        split="dev",
        origin="controlled",
        gold="INCONSISTENT",
        drift_type="DEFAULT_VALUE",
        rights_status="pending",
    ).model_dump_json()
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(sample + "\n" + sample.replace('"one"', '"two"') + "\n", encoding="utf-8")
    with pytest.raises(benchmark.DocSyncError, match="same repository discovery coordinate"):
        run_benchmark(manifest, benchmark.ScanConfig(), tmp_path / "out", "rules")


def test_overlapping_scope_aliases_cannot_double_count(tmp_path):
    base = dict(
        sample_id="first",
        repo_id="r",
        repo_path="repo",
        head_sha="a" * 40,
        document_path="README.md",
        code_path="api.py",
        group_id="g",
        split="dev",
        origin="controlled",
        gold="CONSISTENT",
        drift_type="DEFAULT_VALUE",
        rights_status="pending",
        claim_scope=dict(
            document_ranges=[dict(start=2, end=5)],
            code_path="api.py",
            entity_names=["api.f"],
            subject="f",
            predicate="x",
        ),
    )
    other = {
        **base,
        "sample_id": "second",
        "repo_id": "another-label",
        "claim_scope": {
            **base["claim_scope"],
            "entity_names": ["public.f", "api.f"],
            "document_ranges": [dict(start=3, end=6)],
        },
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(base) + "\n" + json.dumps(other) + "\n")
    with pytest.raises(benchmark.DocSyncError, match="Overlapping declaration"):
        run_benchmark(manifest, ScanConfig(), tmp_path / "out", "rules")
    assert not (tmp_path / "out").exists()
