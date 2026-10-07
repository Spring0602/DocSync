"""Prepare unlabelled annotation packets from fixed Git blobs; never scan samples."""

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

FIELDS = "sample_id,head_sha,reviewer,reviewed_at,label,drift_type,document_path,document_lines,code_path,code_lines,target_entity,evidence,reason,questions".split(
    ","
)
REQUIRED = "sample_id,repo_id,group_id,repo_path,head_sha,code_path,document_path,origin,source,license,rights_evidence,prior_exposure,collected_at".split(
    ","
)


def prepare(intake: Path, out: Path, development: Path) -> dict:
    if out.exists():
        raise ValueError("Output already exists")
    raw = intake.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not rows:
        raise ValueError("Intake is empty; no samples collected")
    dev = [json.loads(line) for line in development.read_bytes().splitlines() if line.strip()]
    seen = set()
    payloads = {}
    records = []
    for row in rows:
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in REQUIRED):
            raise ValueError("Missing intake metadata")
        if any(k in row for k in ("gold", "label", "prediction")):
            raise ValueError("Annotation intake must not include answers")
        sid = row["sample_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", sid) or sid in seen:
            raise ValueError("Unsafe or duplicate sample ID")
        seen.add(sid)
        if any(row[k] == old[k] for old in dev for k in ("sample_id", "repo_id", "group_id")):
            raise ValueError("Known development sample/repository/group overlap")
        if not re.fullmatch(r"[0-9a-f]{40}", row["head_sha"]):
            raise ValueError("Use a complete lowercase Git SHA")
        repo = (intake.parent / row["repo_path"]).resolve()
        record = {k: row[k] for k in REQUIRED if k != "repo_path"}
        record["files"] = {}
        for key in ("code_path", "document_path"):
            name = row[key]
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError("Unsafe repository file path")
            data = subprocess.run(
                ["git", "-C", str(repo), "cat-file", "blob", row["head_sha"] + ":" + name],
                capture_output=True,
                check=True,
            ).stdout
            text = data.decode("utf-8")
            record["files"][key] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "lines": len(text.splitlines()),
            }
            # Flat storage: code/document paths cannot overwrite packet metadata.
            payloads[f"{sid}/{key}.txt"] = data
        records.append(record)
    out.mkdir(parents=True)
    for name, data in payloads.items():
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    metadata = {
        "status": "AWAITING_INDEPENDENT_ANNOTATION",
        "formal_test_ready": False,
        "intake_sha256": hashlib.sha256(raw).hexdigest(),
        "samples": records,
        "limits": "Overlap check only detects declared IDs; A must review provenance and template families.",
    }
    (out / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    for member in ("B", "C"):
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in records:
            writer.writerow(
                {k: row[k] for k in ("sample_id", "head_sha", "code_path", "document_path")}
            )
        (out / f"individual-{member}.csv").write_text(stream.getvalue(), encoding="utf-8")
    return metadata


def check_annotations(packet: Path, b: Path, c: Path) -> dict:
    meta = json.loads(packet.read_bytes())
    samples = {r["sample_id"]: r for r in meta["samples"]}
    errors, reviews = [], []
    for member, path in (("B", b), ("C", c)):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        indexed = {r.get("sample_id"): r for r in rows}
        if len(indexed) != len(rows) or set(indexed) != set(samples):
            errors.append(f"{member}: duplicate/missing/unexpected sample IDs")
        for sid, sample in samples.items():
            row = indexed.get(sid, {})
            for key in FIELDS:
                if key != "questions" and not (row.get(key) or "").strip():
                    errors.append(f"{member}/{sid}: missing {key}")
            for key in ("head_sha", "code_path", "document_path"):
                if row.get(key) != sample[key]:
                    errors.append(f"{member}/{sid}: changed {key}")
            if row.get("label") not in {"CONSISTENT", "INCONSISTENT", "INSUFFICIENT"}:
                errors.append(f"{member}/{sid}: invalid label")
            if row.get("drift_type") not in {"DEFAULT_VALUE", "SIGNATURE", "CONFIG"}:
                errors.append(f"{member}/{sid}: invalid drift type")
            for kind in ("code", "document"):
                coords = re.fullmatch(
                    r"([1-9][0-9]*)(?:-([1-9][0-9]*))?", row.get(kind + "_lines") or ""
                )
                if not coords or not (
                    int(coords[1])
                    <= int(coords[2] or coords[1])
                    <= sample["files"][kind + "_path"]["lines"]
                ):
                    errors.append(f"{member}/{sid}: invalid {kind} lines")
        reviews.append(indexed)
    differences = []
    for sid in samples:
        left, right = (r.get(sid, {}) for r in reviews)
        if left.get("reviewer") and left.get("reviewer") == right.get("reviewer"):
            errors.append(f"{sid}: same reviewer in both files")
        if any(
            left.get(k) != right.get(k)
            for k in ("label", "drift_type", "target_entity", "code_lines", "document_lines")
        ):
            differences.append(sid)
    return {
        "structurally_complete": not errors,
        "errors": errors,
        "requires_adjudication": differences,
        "formal_test_ready": False,
        "note": "A must review every row, rights, independence and evidence; this does not certify human authorship.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--intake", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument(
        "--development", type=Path, default=Path("bench/frozen/seed-dev-v1/manifest.jsonl")
    )
    check = sub.add_parser("check")
    for flag in ("packet", "b", "c"):
        check.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.intake, args.out, args.development)
            print(json.dumps({"status": result["status"], "samples": len(result["samples"])}))
        else:
            result = check_annotations(args.packet, args.b, args.c)
            print(json.dumps(result, indent=2))
            if not result["structurally_complete"]:
                raise SystemExit(2)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError):
        parser.exit(2, "Invalid intake/packet or unavailable Git snapshot; no scan performed.\n")


if __name__ == "__main__":
    main()
