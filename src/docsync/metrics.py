"""Compute metrics from actual per-sample predictions; never synthesize predictions."""

import argparse
import json
from pathlib import Path


def evaluate(rows: list[dict]) -> dict:
    ids = set()
    counts = dict(
        tp=0,
        fp=0,
        tn=0,
        fn=0,
        decidable=0,
        decided=0,
        insufficient=0,
        improper_confirmation=0,
        failed=0,
        abstained=0,
    )
    for row in rows:
        sample = row["sample_id"]
        if not isinstance(sample, str) or not sample or sample in ids:
            raise ValueError("Sample IDs must be unique, nonempty strings")
        ids.add(sample)
        gold, prediction, status = row["gold"], row["prediction"], row["status"]
        if gold not in {"INCONSISTENT", "CONSISTENT", "INSUFFICIENT"}:
            raise ValueError("Unknown gold label")
        if prediction not in {"INCONSISTENT", "CONSISTENT", "UNCERTAIN", "SKIPPED"}:
            raise ValueError("Unknown prediction")
        if status not in {"COMPLETED", "PARTIAL", "FAILED"}:
            raise ValueError("Unknown run status")
        if status == "FAILED" and prediction in {"INCONSISTENT", "CONSISTENT"}:
            raise ValueError("Failed sample cannot carry a definite prediction")
        positive = prediction == "INCONSISTENT"
        counts["failed"] += int(status == "FAILED")
        counts["abstained"] += int(prediction in {"UNCERTAIN", "SKIPPED"})
        if gold == "INSUFFICIENT":
            counts["insufficient"] += 1
            counts["improper_confirmation"] += int(positive)
            continue
        counts["decidable"] += 1
        counts["decided"] += int(prediction in {"INCONSISTENT", "CONSISTENT"})
        if gold == "INCONSISTENT":
            counts["tp" if positive else "fn"] += 1
        else:
            counts["fp" if positive else "tn"] += 1

    def ratio(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    tp, fp, tn, fn = (counts[key] for key in ("tp", "fp", "tn", "fn"))
    return {
        "sample_count": len(rows),
        "counts": counts,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "false_positive_rate": ratio(fp, fp + tn),
        "decision_coverage": ratio(counts["decided"], counts["decidable"]),
        "abstention_rate": ratio(counts["abstained"], len(rows)),
        "improper_confirmation_rate": ratio(
            counts["improper_confirmation"], counts["insufficient"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        rows = [
            json.loads(line)
            for line in args.input.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        metrics = evaluate(rows)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
