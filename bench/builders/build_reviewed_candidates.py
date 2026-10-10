"""Rebuild technically adjudicated extension data; all samples remain development data."""

import argparse
import hashlib
import json
from pathlib import Path

from bench.builders.build_candidates import build


def verify_freeze(project: Path) -> tuple[Path, list[dict]]:
    frozen = project / "bench/frozen/candidate-dev-v1"
    meta = json.loads((frozen / "freeze.json").read_bytes())
    for name, expected in meta["source_hashes_lf"].items():
        raw = (project / name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Received annotation/source changed; create a new reviewed version")
    for name, expected in meta["artifacts"].items():
        if hashlib.sha256((frozen / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Adjudicated artifact hash mismatch")
    rows = [json.loads(line) for line in (frozen / "manifest.jsonl").read_bytes().splitlines()]
    if len(rows) != 24 or len({r["sample_id"] for r in rows}) != 24:
        raise ValueError("Unexpected candidate set")
    if any(r["split"] != "dev" or r["annotation_status"] != "adjudicated" for r in rows):
        raise ValueError("Reviewed candidates must remain adjudicated development data")
    return frozen, rows


def rebuild(out: Path) -> Path:
    frozen, rows = verify_freeze(Path(__file__).resolve().parents[2])
    intake = build(out)
    actual = {r["sample_id"]: r for r in map(json.loads, intake.read_bytes().splitlines())}
    if set(actual) != {r["sample_id"] for r in rows}:
        raise ValueError("Rebuilt sample set differs")
    for row in rows:
        for key in ("head_sha", "repo_id", "repo_path", "group_id", "code_path", "document_path"):
            if row[key] != actual[row["sample_id"]][key]:
                raise ValueError("Rebuilt candidate differs from frozen adjudication")
    manifest = out / "manifest.jsonl"
    manifest.write_bytes((frozen / "manifest.jsonl").read_bytes())
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(rebuild(args.out))


if __name__ == "__main__":
    main()
