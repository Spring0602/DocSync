"""Evaluate fixed, independently specified target coordinates against candidate reports."""

import argparse
import json
from pathlib import Path

from pydantic import Field, model_validator

from docsync.models import Model, ScanReport, SourceSpan


class Target(Model):
    path: str
    subject: str
    property: str
    fact_kind: str
    start_line: int = Field(ge=1)


class AlignmentGold(Model):
    sample_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    head_sha: str
    document_path: str
    claim_line: int = Field(ge=1)
    targets: list[Target]
    excluded_reason: str | None = None

    @model_validator(mode="after")
    def target_policy(self):
        if bool(self.targets) == bool(self.excluded_reason):
            raise ValueError("Provide targets or an exclusion reason, exclusively")
        for path in [self.document_path, *(target.path for target in self.targets)]:
            SourceSpan(
                path=path, start_line=1, end_line=1, start_byte=0, end_byte=0, blob_hash="0" * 64
            )
        if len({t.model_dump_json() for t in self.targets}) != len(self.targets):
            raise ValueError("Duplicate targets")
        return self


def evaluate(golds: list[AlignmentGold], reports: Path, ks: list[int]) -> dict:
    if not ks or any(k < 1 for k in ks) or len(set(ks)) != len(ks):
        raise ValueError("K values must be unique positive integers")
    if len({g.sample_id for g in golds}) != len(golds):
        raise ValueError("Duplicate sample IDs")
    rows = []
    total = 0
    hits = {str(k): 0 for k in ks}
    for gold in golds:
        row = {"sample_id": gold.sample_id, "excluded_reason": gold.excluded_reason}
        if gold.excluded_reason:
            rows.append(row)
            continue
        total += len(gold.targets)
        matched = {str(k): 0 for k in ks}
        try:
            report = ScanReport.model_validate_json(
                (reports / gold.sample_id / "report.json").read_bytes()
            )
            if report.snapshot.head_sha != gold.head_sha:
                raise ValueError("Snapshot mismatch")
            if report.manifest.status == "FAILED":
                raise ValueError("Failed report")
            claims = [
                c
                for c in report.claims
                if c.span.path == gold.document_path and c.span.start_line == gold.claim_line
            ]
            if len(claims) != 1:
                raise ValueError("Missing or ambiguous claim location")
            candidates = [c for c in report.candidates if c.claim_id == claims[0].claim_id]
            if len(candidates) != 1:
                raise ValueError("Missing or ambiguous candidate set")
            facts = {f.fact_id: f for f in report.facts}
            for target in gold.targets:
                ranks = [
                    c.rank
                    for c in candidates[0].candidates
                    if (
                        facts[c.fact_id].span.path,
                        facts[c.fact_id].subject,
                        facts[c.fact_id].property,
                        facts[c.fact_id].fact_kind,
                        facts[c.fact_id].span.start_line,
                    )
                    == (
                        target.path,
                        target.subject,
                        target.property,
                        target.fact_kind,
                        target.start_line,
                    )
                ]
                for k in ks:
                    matched[str(k)] += int(bool(ranks) and min(ranks) <= k)
            row["status"] = report.manifest.status
        except (OSError, ValueError) as exc:
            row["status"] = "UNAVAILABLE"
            row["error_type"] = type(exc).__name__
        row["target_count"] = len(gold.targets)
        row["hits"] = matched
        for k in ks:
            hits[str(k)] += matched[str(k)]
        rows.append(row)
    return {
        "sample_count": len(golds),
        "excluded_samples": sum(bool(g.excluded_reason) for g in golds),
        "target_count": total,
        "hits": hits,
        "recall_at_k": {k: v / total if total else None for k, v in hits.items()},
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--k", nargs="+", type=int, default=[1, 3, 5])
    args = parser.parse_args()
    golds = [
        AlignmentGold.model_validate_json(line)
        for line in args.gold.read_bytes().splitlines()
        if line.strip()
    ]
    result = evaluate(golds, args.reports, args.k)
    import hashlib

    result["gold_sha256"] = hashlib.sha256(args.gold.read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
