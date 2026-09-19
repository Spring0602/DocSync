"""Build hash locks from previously downloaded wheels, with no network access."""

import argparse
import hashlib
from collections import defaultdict
from pathlib import Path

from packaging.utils import canonicalize_name, parse_wheel_filename

RUNTIME_AND_BUILD = {
    "annotated-types",
    "markdown-it-py",
    "mdurl",
    "pydantic",
    "pydantic-core",
    "typing-extensions",
    "typing-inspection",
    "hatchling",
    "packaging",
    "pathspec",
    "pluggy",
    "trove-classifiers",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheels", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    hashes = defaultdict(set)
    for wheel in args.wheels.glob("*.whl"):
        name, version, _, _ = parse_wheel_filename(wheel.name)
        hashes[(canonicalize_name(name), str(version))].add(
            hashlib.sha256(wheel.read_bytes()).hexdigest()
        )
    entries = {}
    for line in (root / "requirements-dev.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==")
        name = canonicalize_name(name)
        available = hashes[(name, version)]
        if not available:
            raise ValueError("Missing downloaded artifact: " + line)
        entries[name] = (
            name
            + "=="
            + version
            + " \\\n"
            + " \\\n".join("    --hash=sha256:" + value for value in sorted(available))
            + "\n"
        )
    header = "# Python 3.12; Windows x64 and manylinux x86_64 wheels.\n# Generated from downloaded artifacts; review and regenerate on dependency upgrades.\n"
    (root / "requirements-dev.lock").write_text(
        header + "".join(entries.values()), encoding="utf-8"
    )
    (root / "requirements-runtime.lock").write_text(
        header
        + "# Includes pinned build backend for offline installation.\n"
        + "".join(value for name, value in entries.items() if name in RUNTIME_AND_BUILD),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
