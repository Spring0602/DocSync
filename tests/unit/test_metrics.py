import importlib.util
from pathlib import Path

import pytest

from docsync.metrics import evaluate

spec = importlib.util.spec_from_file_location(
    "bench_evaluate", Path(__file__).parents[2] / "bench/evaluate.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_abstained_positive_is_false_negative():
    result = module.evaluate(
        [
            {
                "sample_id": "a",
                "gold": "INCONSISTENT",
                "prediction": "UNCERTAIN",
                "status": "FAILED",
            },
            {
                "sample_id": "b",
                "gold": "CONSISTENT",
                "prediction": "UNCERTAIN",
                "status": "COMPLETED",
            },
            {
                "sample_id": "c",
                "gold": "INSUFFICIENT",
                "prediction": "INCONSISTENT",
                "status": "COMPLETED",
            },
        ]
    )
    assert result["counts"]["fn"] == 1
    assert result["precision"] is None
    assert result["decision_coverage"] == 0
    assert result["improper_confirmation_rate"] == 1


def test_empty_metrics_not_perfect():
    result = module.evaluate([])
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["f1"] is None


def test_failed_definite_prediction_rejected():
    with pytest.raises(ValueError):
        module.evaluate(
            [
                {
                    "sample_id": "a",
                    "gold": "CONSISTENT",
                    "prediction": "CONSISTENT",
                    "status": "FAILED",
                }
            ]
        )


def test_explicit_consistency_does_not_count_abstention_as_correct():
    rows = [
        dict(sample_id=str(i), gold="CONSISTENT", prediction=p, status="COMPLETED")
        for i, p in enumerate(["CONSISTENT", "UNCERTAIN", "SKIPPED", "INCONSISTENT"])
    ]
    result = evaluate(rows)
    assert result["counts"]["tn"] == 3
    assert result["explicit_consistency_rate"] == 0.25
    assert result["recall"] is None
