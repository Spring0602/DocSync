import json

import pytest

from bench.evaluate_alignment import AlignmentGold, evaluate
from docsync.config import RepoSpec
from docsync.pipeline import scan


def test_retrieval_counts_missing_report_and_wrong_target_as_misses(commit_files, tmp_path):
    repo = commit_files(
        {
            "client.py": "def connect(timeout=60): pass\n",
            "README.md": "## connect\n\ntimeout defaults to 30\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    claim = report.claims[0]
    fact = next(f for f in report.facts if f.fact_kind == "DEFAULT_VALUE")
    base = dict(
        sample_id="one",
        head_sha=report.snapshot.head_sha,
        document_path="README.md",
        claim_line=claim.span.start_line,
        targets=[
            dict(
                path="client.py",
                subject=fact.subject,
                property="timeout",
                fact_kind="DEFAULT_VALUE",
                start_line=1,
            )
        ],
    )
    target = tmp_path / "one"
    target.mkdir()
    (target / "report.json").write_text(report.model_dump_json(), encoding="utf-8")
    gold = AlignmentGold.model_validate(base)
    result = evaluate([gold], tmp_path, [1, 3])
    assert result["recall_at_k"] == {"1": 1.0, "3": 1.0}
    missing = AlignmentGold.model_validate({**base, "sample_id": "missing"})
    assert evaluate([gold, missing], tmp_path, [1])["recall_at_k"]["1"] == 0.5
    wrong = AlignmentGold.model_validate({**base, "head_sha": "0" * 40})
    assert evaluate([wrong], tmp_path, [1])["recall_at_k"]["1"] == 0
    base["targets"][0]["property"] = "host"
    assert evaluate([AlignmentGold.model_validate(base)], tmp_path, [1])["hits"]["1"] == 0
    data = json.loads(report.model_dump_json())
    data["candidates"][0]["candidates"][0]["rank"] = 2
    (target / "report.json").write_text(json.dumps(data), encoding="utf-8")
    assert evaluate([gold], tmp_path, [1, 3])["recall_at_k"] == {"1": 0.0, "3": 1.0}


def test_retrieval_exclusions_and_empty_denominator(tmp_path):
    gold = AlignmentGold(
        sample_id="ambiguous",
        head_sha="0" * 40,
        document_path="README.md",
        claim_line=1,
        targets=[],
        excluded_reason="ambiguous owner",
    )
    result = evaluate([gold], tmp_path, [1])
    assert result["excluded_samples"] == 1
    assert result["recall_at_k"]["1"] is None
    with pytest.raises(ValueError):
        evaluate([gold, gold], tmp_path, [1])
    with pytest.raises(ValueError):
        evaluate([gold], tmp_path, [0])
    with pytest.raises(ValueError):
        AlignmentGold.model_validate({**gold.model_dump(), "excluded_reason": None})
