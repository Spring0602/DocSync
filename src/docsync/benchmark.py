"""Reproducible manifest runner. Gold labels never enter the detection pipeline."""

import json
import re
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from docsync.config import RepoSpec, ScanConfig
from docsync.metrics import evaluate
from docsync.models import Model, ScanReport
from docsync.pipeline import scan
from docsync.reporting import write_report
from docsync.repository import analyze
from docsync.utils import DocSyncError, digest


class BenchmarkSample(Model):
    sample_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    repo_id: str
    repo_path: str
    head_sha: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    document_path: str
    code_path: str
    group_id: str
    split: Literal["dev", "test"]
    origin: Literal["real", "controlled"]
    gold: Literal["CONSISTENT", "INCONSISTENT", "INSUFFICIENT"]
    drift_type: Literal["DEFAULT_VALUE", "SIGNATURE", "CONFIG"]
    rights_status: Literal["cleared", "manifest_only", "pending"]
    annotation_status: Literal["provisional", "adjudicated"] = "provisional"
    claim_line: int | None = Field(default=None, ge=1)


def predict(report: ScanReport, sample: BenchmarkSample, method: str) -> str:
    claims = {
        c.claim_id
        for c in report.claims
        if c.span.path == sample.document_path
        and (sample.claim_line is None or c.span.start_line == sample.claim_line)
    }
    if method in {"no_verifier", "llm"}:
        if any(j.claim_id in claims and j.decision == "INCONSISTENT" for j in report.judgments):
            return "INCONSISTENT"
    elif any(f.claim_id in claims and f.drift_type == sample.drift_type for f in report.findings):
        return "INCONSISTENT"
    decisions = [j.decision for j in report.judgments if j.claim_id in claims]
    if decisions and all(d == "CONSISTENT" for d in decisions):
        return "CONSISTENT"
    return "UNCERTAIN" if decisions else "SKIPPED"


def keyword_predict(
    spec: RepoSpec, sample: BenchmarkSample, cfg: ScanConfig
) -> tuple[str, list[str]]:
    """B1: exact token matching only, without AST, ownership or type verification."""
    snapshot = analyze(spec, cfg)
    errors = [d.code for d in snapshot.diagnostics if d.affects_completeness]
    source = "\n".join(
        data.decode() for path, data in snapshot.blobs.items() if path.endswith(".py")
    )
    document = snapshot.blobs.get(sample.document_path, b"").decode()
    if sample.claim_line is not None:
        lines = document.splitlines()
        document = lines[sample.claim_line - 1] if sample.claim_line <= len(lines) else ""
    values = re.findall(r"\b([A-Za-z_]\w*)\s*=\s*([^,)\n#]+)", source)
    matched = False
    for name, value in values:
        pattern = rf"\b{re.escape(name)}\b`?\s*(?:defaults?\s+to|默认值?为|=)\s*`?([^`\s。;,)]+)"
        for match in re.finditer(pattern, document, re.I):
            matched = True
            if match.group(1).rstrip(".") != value.strip():
                return "INCONSISTENT", errors
    return ("CONSISTENT" if matched else "SKIPPED"), errors


def run_benchmark(manifest: Path, cfg: ScanConfig, out: Path, method: str) -> dict:
    if out.exists() and any(out.iterdir()):
        raise DocSyncError("OUTPUT_EXISTS", "Choose an empty benchmark directory", "benchmark")
    raw = manifest.read_bytes()
    samples = [
        BenchmarkSample.model_validate_json(line) for line in raw.splitlines() if line.strip()
    ]
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise DocSyncError("INVALID_MANIFEST", "Manifest must contain unique samples", "benchmark")
    for grouping in ("group_id", "repo_id"):
        groups: dict[str, set[str]] = {}
        for sample in samples:
            groups.setdefault(getattr(sample, grouping), set()).add(sample.split)
        if any(len(splits) > 1 for splits in groups.values()):
            raise DocSyncError(
                "SPLIT_LEAKAGE", "Same repository/group occurs across splits", "benchmark"
            )
    mode = "rules" if method in {"rules", "keyword"} else "hybrid"
    cfg = cfg.model_copy(
        update={
            "scan": cfg.scan.model_copy(
                update={"mode": mode, "analysis_method": "rules" if method == "keyword" else method}
            ),
            "ignores": [],
        }
    )
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for sample in samples:
        started = time.perf_counter()
        row: dict[str, Any] = {
            "sample_id": sample.sample_id,
            "gold": sample.gold,
            "origin": sample.origin,
            "split": sample.split,
            "drift_type": sample.drift_type,
            "method": method,
            "annotation_status": sample.annotation_status,
            "manifest_hash": digest(raw),
            "prediction_stage": "keyword"
            if method == "keyword"
            else ("unverified_judge" if method in {"no_verifier", "llm"} else "verified"),
        }
        try:
            repo = (manifest.parent / sample.repo_path).resolve()
            if not repo.is_relative_to(manifest.parent.resolve()):
                raise DocSyncError(
                    "UNSAFE_SAMPLE_PATH",
                    "Repository must be inside manifest directory",
                    "benchmark",
                )
            spec = RepoSpec(repo=repo, head=sample.head_sha)
            if method == "keyword":
                prediction, errors = keyword_predict(spec, sample, cfg)
                row.update(
                    prediction=prediction,
                    status="PARTIAL" if errors else "COMPLETED",
                    usage={"requests": 0},
                    errors=errors,
                )
            else:
                report = scan(spec, cfg)
                write_report(report, out / sample.sample_id, {"json", "md"})
                row.update(
                    prediction=predict(report, sample, method),
                    status=report.manifest.status,
                    usage=report.manifest.usage,
                    errors=[d.code for d in report.manifest.diagnostics if d.affects_completeness],
                )
        except (DocSyncError, OSError, ValueError) as exc:
            row.update(
                prediction="UNCERTAIN",
                status="FAILED",
                errors=[exc.code if isinstance(exc, DocSyncError) else "SAMPLE_ERROR"],
            )
        row["elapsed_seconds"] = time.perf_counter() - started
        rows.append(row)
        with (out / "predictions.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    metrics = evaluate(rows)
    metrics["by_type"] = {
        kind: evaluate([r for r in rows if r["drift_type"] == kind])
        for kind in sorted({s.drift_type for s in samples})
    }
    metrics["provisional_labels"] = any(s.annotation_status != "adjudicated" for s in samples)
    metrics["manifest_hash"] = digest(raw)
    metrics["config_hash"] = digest(cfg.model_dump_json().encode())
    metrics["method"] = method
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {
        "method": method,
        "samples": len(samples),
        "out": str(out),
        "failed_or_partial": sum(r["status"] != "COMPLETED" for r in rows),
        "provisional_labels": metrics["provisional_labels"],
    }
