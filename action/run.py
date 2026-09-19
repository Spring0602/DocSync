"""Trusted Action wrapper; inputs are argument values, never interpolated shell code."""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


def main() -> int:
    out = Path(os.environ["RUNNER_TEMP"]) / ("docsync-" + uuid.uuid4().hex)
    cmd = [
        sys.executable,
        "-m",
        "docsync",
        "scan",
        "--repo",
        os.environ["DOCSYNC_REPO"],
        "--head",
        os.environ["DOCSYNC_HEAD"],
        "--mode",
        os.environ["DOCSYNC_MODE"],
        "--fail-on",
        os.environ["DOCSYNC_FAIL_ON"],
        "--out",
        str(out),
    ]
    for key, flag in [("DOCSYNC_BASE", "--base"), ("DOCSYNC_CONFIG", "--config")]:
        if os.environ.get(key):
            cmd.extend([flag, os.environ[key]])
    if os.environ.get("DOCSYNC_REQUIRE_COMPLETE", "false").lower() == "true":
        cmd.append("--require-complete")
    result = subprocess.run(cmd, check=False)
    summary_path = out / "summary.json"
    summary = (
        json.loads(summary_path.read_text())
        if summary_path.exists()
        else {"status": "FAILED", "confirmed_count": 0, "uncertain_count": 0}
    )
    patch_path = ""
    report_path = out / "report.json"
    if report_path.exists() and summary["status"] != "FAILED":
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if any(p["validation"] == "VALIDATED" for p in report["patches"]):
            patch = out / "fixes.patch"
            exported = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "docsync",
                    "patch",
                    "--report",
                    str(report_path),
                    "--out",
                    str(patch),
                ],
                check=False,
            )
            if exported.returncode == 0:
                patch_path = str(patch)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        for key, value in {
            "report-path": str(report_path),
            "confirmed-count": summary["confirmed_count"],
            "uncertain-count": summary["uncertain_count"],
            "scan-status": summary["status"],
            "patch-path": patch_path,
        }.items():
            stream.write(f"{key}={value}\n")
    # Use fixed, short summary fields; do not render untrusted repository Markdown as job instructions.
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
        stream.write(f"## DocSync\n\nStatus: {summary['status']}\n\n")
        stream.write(
            f"Confirmed: {summary['confirmed_count']}; uncertain: {summary['uncertain_count']}\n\n"
        )
        stream.write(
            "Coverage: supported default, signature and configuration claims. See manifest for actual model usage.\n"
        )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
