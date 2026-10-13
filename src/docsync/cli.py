from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from docsync import __version__

if TYPE_CHECKING:
    from docsync.config import ScanConfig
    from docsync.models import ScanReport


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="docsync", description="Evidence-first Python/Markdown drift checks"
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser(
        "doctor", help="Check local setup without scanning or network calls"
    )
    doctor.add_argument("--repo", type=Path, help="Optionally check a Git repository root")
    doctor.add_argument("--config", type=Path, help="Validate explicit trusted TOML configuration")
    doctor.add_argument("--format", choices=["text", "json"], default="text")
    run = commands.add_parser("scan", help="Read a fixed snapshot and emit evidence reports")
    run.add_argument("--repo", type=Path, default=Path("."))
    run.add_argument("--head", default="HEAD")
    run.add_argument("--base")
    run.add_argument(
        "--working-tree", action="store_true", help="Explicitly include uncommitted files"
    )
    run.add_argument("--config", type=Path, help="Explicit trusted TOML configuration")
    run.add_argument("--mode", choices=["rules", "hybrid"])
    run.add_argument("--format", default="json,md")
    run.add_argument(
        "--out", type=Path, help="New/empty output directory; defaults to a unique runs/<id>"
    )
    run.add_argument("--fail-on", choices=["none", "warning"])
    run.add_argument("--require-complete", action="store_true", default=None)
    patch = commands.add_parser("patch", help="Export a reviewed report's validated document diff")
    patch.add_argument("--report", required=True, type=Path)
    patch.add_argument("--out", required=True, type=Path)
    patch.add_argument("--manifest", type=Path, help="Defaults to OUT.patch.json")
    apply = commands.add_parser(
        "apply", help="Explicitly apply a patch after all preimages are checked"
    )
    apply.add_argument("--repo", type=Path, default=Path("."))
    apply.add_argument("--patch", required=True, type=Path)
    apply.add_argument("--manifest", required=True, type=Path)
    schema = commands.add_parser("schema", help="Export the versioned report JSON Schema")
    schema.add_argument("--out", type=Path)
    schema.add_argument("--kind", choices=["report", "benchmark"], default="report")
    benchmark = commands.add_parser(
        "benchmark", help="Run fixed manifest samples; preserve failures and abstentions"
    )
    benchmark.add_argument("--manifest", type=Path, required=True)
    benchmark.add_argument("--config", type=Path)
    benchmark.add_argument("--out", type=Path, required=True)
    benchmark.add_argument(
        "--method",
        choices=["keyword", "rules", "llm", "full", "no_alignment", "no_verifier", "no_static"],
        default="rules",
    )
    return root


def exit_code(report: ScanReport, cfg: ScanConfig) -> int:
    if report.manifest.status == "FAILED":
        return 2
    if report.manifest.status == "PARTIAL" and cfg.scan.require_complete:
        return 3
    if report.confirmed_count and cfg.scan.fail_on == "warning":
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "doctor":
        from docsync.doctor import check_environment, render_text

        result = check_environment(args.repo, args.config)
        print(json.dumps(result.to_dict()) if args.format == "json" else render_text(result))
        return result.exit_code

    # Doctor and --help stay available when runtime dependencies need repair.
    from pydantic import ValidationError

    from docsync.config import RepoSpec, load_config
    from docsync.models import PatchProposal, ScanReport
    from docsync.patches import apply_patch
    from docsync.pipeline import scan
    from docsync.reporting import write_report
    from docsync.utils import DocSyncError

    failure_dir: Path | None = None
    try:
        if args.command == "scan":
            args.out = args.out or Path("runs") / uuid.uuid4().hex
            if args.out.exists() and any(args.out.iterdir()):
                raise DocSyncError(
                    "OUTPUT_EXISTS", "Choose a new output directory; existing run preserved", "cli"
                )
            args.out.mkdir(parents=True, exist_ok=True)
            failure_dir = args.out
            cfg = load_config(args.config)
            overrides = {
                key: getattr(args, key)
                for key in ("mode", "fail_on", "require_complete")
                if getattr(args, key) is not None
            }
            cfg = cfg.model_copy(update={"scan": cfg.scan.model_copy(update=overrides)})
            formats = set(args.format.split(","))
            if not formats <= {"json", "md"}:
                raise DocSyncError("INVALID_FORMAT", "Supported formats: json,md", "cli")
            report = scan(
                RepoSpec(
                    repo=args.repo, head=args.head, base=args.base, working_tree=args.working_tree
                ),
                cfg,
            )
            write_report(report, args.out, formats)
            print(
                json.dumps(
                    {
                        "status": report.manifest.status,
                        "confirmed_count": report.confirmed_count,
                        "ignored_count": report.ignored_count,
                        "uncertain_count": report.uncertain_count,
                        "out": str(args.out),
                    },
                    ensure_ascii=True,
                )
            )
            return exit_code(report, cfg)
        if args.command == "benchmark":
            from docsync.benchmark import run_benchmark

            summary = run_benchmark(args.manifest, load_config(args.config), args.out, args.method)
            print(json.dumps(summary))
            return 3 if summary["failed_or_partial"] else 0
        if args.command == "patch":
            report = ScanReport.model_validate_json(args.report.read_bytes())
            patches = [p for p in report.patches if p.validation == "VALIDATED"]
            if len(patches) != 1:
                raise DocSyncError(
                    "NO_VALIDATED_PATCH",
                    "Report must contain one validated patch proposal",
                    "patch",
                )
            proposal = patches[0]
            manifest = args.manifest or args.out.with_suffix(args.out.suffix + ".json")
            if args.out.resolve() == manifest.resolve():
                raise DocSyncError(
                    "OUTPUT_COLLISION", "Patch and manifest need different output paths", "patch"
                )
            for target in (args.out, manifest):
                if target.exists() or target.is_symlink():
                    raise DocSyncError(
                        "OUTPUT_EXISTS",
                        "Choose new output files; existing files preserved",
                        "patch",
                    )
            args.out.parent.mkdir(parents=True, exist_ok=True)
            manifest.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation protects existing files even if they appear after preflight.
            with args.out.open("xb") as diff_stream, manifest.open("xb") as manifest_stream:
                diff_stream.write(proposal.diff.encode("utf-8"))
                manifest_stream.write(proposal.model_dump_json(indent=2).encode("utf-8"))
            print(
                json.dumps(
                    {"patch": str(args.out), "manifest": str(manifest), "requires_review": True}
                )
            )
        elif args.command == "apply":
            proposal = PatchProposal.model_validate_json(args.manifest.read_bytes())
            changed = apply_patch(args.repo, proposal, args.patch.read_bytes().decode("utf-8"))
            print(json.dumps({"status": "APPLIED", "paths": changed}))
        elif args.command == "schema":
            from docsync.benchmark import BenchmarkSample

            schema_model = ScanReport if args.kind == "report" else BenchmarkSample
            schema = json.dumps(schema_model.model_json_schema(), indent=2, ensure_ascii=False)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(schema + "\n", encoding="utf-8")
            else:
                print(schema)
        return 0
    except (DocSyncError, OSError, ValueError, ValidationError) as exc:
        # Avoid echoing target text, arbitrary validation input or absolute host paths.
        code = exc.code if isinstance(exc, DocSyncError) else "INVALID_INPUT"
        stage = exc.stage if isinstance(exc, DocSyncError) else "cli"
        message = (
            str(exc)
            if isinstance(exc, DocSyncError)
            else "Cannot read or validate input; check paths and schema"
        )
        failure = {
            "schema_version": "2.0",
            "status": "FAILED",
            "code": code,
            "message": message,
            "stage": stage,
            "retryable": False,
        }
        if failure_dir is not None:
            try:
                serialized = json.dumps(failure, indent=2)
                for name in ("failure.json", "manifest.json", "report.json"):
                    (failure_dir / name).write_text(serialized, encoding="utf-8")
                (failure_dir / "report.md").write_text(
                    "# DocSync scan failed\n\n" + code + ": " + message + "\n", encoding="utf-8"
                )
            except OSError:
                pass  # Preserve the original failure; stderr remains authoritative.
        print(json.dumps(failure), file=sys.stderr)
        return 2
