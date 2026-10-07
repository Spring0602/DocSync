"""Run comparable benchmark methods, preserving failures and provenance.

No model is called without --run. Use --methods rules keyword for offline validation.
"""

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from docsync.benchmark import BenchmarkSample, run_benchmark
from docsync.config import ScanConfig, load_config
from docsync.metrics import evaluate
from docsync.utils import DocSyncError

METHODS = ["keyword", "rules", "llm", "full", "no_alignment", "no_verifier", "no_static"]
LOCAL = {"keyword", "rules"}


def provenance(project: Path) -> dict:
    files = sorted(
        [*project.glob("src/**/*.py"), *project.glob("bench/**/*.py"), project / "pyproject.toml"]
    )
    hashes = {
        p.relative_to(project).as_posix(): hashlib.sha256(
            p.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for p in files
    }
    commit = subprocess.check_output(
        ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "-C", str(project), "status", "--porcelain"], text=True
        ).strip()
    )
    return {"commit": commit, "dirty": dirty, "source_hashes_lf": hashes}


def verify_installed_source(project: Path) -> None:
    import docsync

    installed = Path(docsync.__file__).resolve().parent
    for path in (project / "src/docsync").rglob("*.py"):
        actual = installed / path.relative_to(project / "src/docsync")
        if not actual.exists() or actual.read_bytes().replace(b"\r\n", b"\n") != (
            path.read_bytes().replace(b"\r\n", b"\n")
        ):
            raise ValueError("Installed package differs from source; reinstall local project first")


def plan_suite(manifest: Path, cfg: ScanConfig, methods: list[str], max_requests: int) -> dict:
    if not methods or len(set(methods)) != len(methods) or any(m not in METHODS for m in methods):
        raise ValueError("Choose unique supported methods")
    samples = [
        BenchmarkSample.model_validate_json(line)
        for line in manifest.read_bytes().splitlines()
        if line.strip()
    ]
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Manifest must have unique samples")
    if any(s.annotation_status != "adjudicated" for s in samples):
        raise ValueError("Suite requires adjudicated labels; use benchmark for provisional samples")
    if cfg.llm.cache_dir is not None:
        raise ValueError("Disable local model cache for comparable live request accounting")
    bound = len(samples) * sum(m not in LOCAL for m in methods) * cfg.llm.max_requests
    if max_requests < 0 or bound > max_requests:
        raise ValueError(
            f"Configured request upper bound {bound} exceeds suite limit {max_requests}"
        )
    return {
        "methods": methods,
        "samples": len(samples),
        "sample_ids": [s.sample_id for s in samples],
        "split_counts": dict(Counter(s.split for s in samples)),
        "formal_test_claim": False,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256(cfg.model_dump_json().encode()).hexdigest(),
        "request_upper_bound": bound,
        "output_token_upper_bound": bound * cfg.llm.max_output_tokens,
        "request_limit": max_requests,
        "cost_amount": None,
        "cost_note": "Token reservation is not billed usage; provider invoice required.",
    }


def summarize_method(directory: Path, expected_ids: list[str]) -> dict:
    rows = [
        json.loads(line) for line in (directory / "predictions.jsonl").read_bytes().splitlines()
    ]
    if sorted(r["sample_id"] for r in rows) != sorted(expected_ids):
        raise ValueError("Prediction set differs from manifest")
    metrics = evaluate(rows)
    saved = json.loads((directory / "metrics.json").read_bytes())
    if any(saved.get(k) != value for k, value in metrics.items()):
        raise ValueError("Saved metrics do not match raw predictions")
    usage_keys = [
        "requests",
        "input_tokens",
        "output_tokens",
        "cache_hits",
        "unknown_usage_requests",
    ]
    usage = {key: sum(r.get("usage", {}).get(key, 0) for r in rows) for key in usage_keys}
    issues = []
    for row in rows:
        expected = "UNCERTAIN" if row["gold"] == "INSUFFICIENT" else row["gold"]
        if row["status"] != "COMPLETED" or row["prediction"] != expected:
            issues.append(
                {k: row.get(k) for k in ["sample_id", "gold", "prediction", "status", "errors"]}
            )
    return {
        "metrics": metrics,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "usage": usage,
        "elapsed_seconds": sum(r["elapsed_seconds"] for r in rows),
        "review_items": issues,
        "cost_amount": None,
    }


def run_suite(
    manifest: Path, cfg: ScanConfig, out: Path, methods: list[str], max_requests: int = 100
) -> dict:
    plan = plan_suite(manifest, cfg, methods, max_requests)
    if any(m not in LOCAL for m in methods):
        if cfg.llm.provider == "none" or not os.environ.get(cfg.llm.api_key_env):
            raise ValueError("Model configuration/key unavailable in this terminal; no run started")
    if out.exists():
        raise ValueError("Choose a new output directory; existing evidence is never overwritten")
    project = Path(__file__).resolve().parents[1]
    verify_installed_source(project)
    source = provenance(project)
    out.mkdir(parents=True)
    (out / "input-manifest.jsonl").write_bytes(manifest.read_bytes())
    (out / "effective-config.json").write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    state = {**plan, "provenance": source, "status": "RUNNING", "results": {}}

    def save() -> None:
        (out / "suite.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    save()
    for method in methods:
        print(f"Starting {method}: {plan['samples']} samples", flush=True)
        try:
            if provenance(project)["source_hashes_lf"] != source["source_hashes_lf"]:
                raise ValueError("Source changed during suite")
            if hashlib.sha256(manifest.read_bytes()).hexdigest() != plan["manifest_sha256"]:
                raise ValueError("Manifest changed during suite")
            run_benchmark(manifest, cfg, out / method, method)
            result = summarize_method(out / method, plan["sample_ids"])
            state["results"][method] = result
            print(f"Finished {method}: {result['status_counts']}", flush=True)
        except (OSError, ValueError, DocSyncError) as exc:
            # No raw service message/config value is echoed.
            state["results"][method] = {"suite_method_error": type(exc).__name__}
            state["status"] = "INTERRUPTED"
            save()
            raise
        save()
    state["status"] = (
        "PARTIAL"
        if any(
            any(status != "COMPLETED" for status in r["status_counts"])
            for r in state["results"].values()
        )
        else "COMPLETED"
    )
    state["actual_requests"] = sum(r["usage"]["requests"] for r in state["results"].values())
    if state["actual_requests"] > plan["request_upper_bound"]:
        state["status"] = "ACCOUNTING_ERROR"
    save()
    lines = [
        "# Benchmark suite",
        "",
        "Development data results do not establish independent test performance.",
        "",
        "| Method | TP | FP | TN | FN | Abstained | Failed/partial | Requests | Input | Output |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for method, result in state["results"].items():
        c, u = result["metrics"]["counts"], result["usage"]
        failed = sum(v for k, v in result["status_counts"].items() if k != "COMPLETED")
        lines.append(
            f"| {method} | {c['tp']} | {c['fp']} | {c['tn']} | {c['fn']} | "
            f"{c['abstained']} | {failed} | {u['requests']} | "
            f"{u['input_tokens']} | {u['output_tokens']} |"
        )
    (out / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--methods", nargs="+", default=METHODS, choices=METHODS)
    parser.add_argument("--max-requests", type=int, default=100)
    parser.add_argument(
        "--run", action="store_true", help="Execute; without this only show the plan"
    )
    args = parser.parse_args()
    try:
        cfg = load_config(args.config)
        if not args.run:
            print(
                json.dumps(
                    plan_suite(args.manifest, cfg, args.methods, args.max_requests), indent=2
                )
            )
            return
        if args.out is None:
            parser.error("--out is required with --run")
        state = run_suite(args.manifest, cfg, args.out, args.methods, args.max_requests)
        print(
            json.dumps(
                {
                    "status": state["status"],
                    "out": str(args.out),
                    "requests": state["actual_requests"],
                }
            )
        )
        if state["status"] != "COMPLETED":
            raise SystemExit(3)
    except (OSError, ValueError, DocSyncError):
        parser.exit(2, "Suite input/environment validation failed; check paths, budget and key.\n")


if __name__ == "__main__":
    main()
