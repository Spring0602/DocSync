"""Rebuild the reviewed development seed, verifying source annotations and frozen hashes."""

import argparse
import hashlib
import json
from pathlib import Path

from build_seed import build


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    frozen = project / "bench/frozen/seed-dev-v1"
    meta = json.loads((frozen / "freeze.json").read_bytes())
    for name, expected in meta["source_files"].items():
        raw = (project / name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Source annotations changed; create a new reviewed version")
    for name, expected in meta["artifacts"].items():
        if hashlib.sha256((frozen / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen artifact hash mismatch")
    manifest = build(args.out)
    actual = [json.loads(line) for line in manifest.read_bytes().splitlines()]
    expected_rows = [
        json.loads(line) for line in (frozen / "manifest.jsonl").read_bytes().splitlines()
    ]
    for row in actual:
        row["annotation_status"] = "adjudicated"
        row["rights_status"] = "cleared"
    if actual != expected_rows:
        raise ValueError("Rebuilt samples differ from reviewed development version")
    manifest.write_bytes((frozen / "manifest.jsonl").read_bytes())
    (args.out / "manifest.sha256").write_text(meta["artifacts"]["manifest.jsonl"] + "\n")
    (args.out / "README.md").write_text(
        "# Reviewed development seed\n\nseed-dev-v1; 20 reviewed cases; all dev. "
        "Not an independent test set. See bench/frozen/seed-dev-v1.\n",
        encoding="utf-8",
    )
    print(manifest)


if __name__ == "__main__":
    main()
