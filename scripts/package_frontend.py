"""Build an allowlisted frontend handoff ZIP without traversing the workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from serve_frontend import PUBLIC_FILES

PACKAGE_ROOT = "DocSync-frontend"
UI_PREFIX = "DOCsync-demo-video-package/demo-ui"
REQUIRED_FILES = (
    "scripts/serve_frontend.py",
    "DOCsync-demo-video-package/启动前端.cmd",
    "DOCsync-demo-video-package/README.md",
    "DOCsync-demo-video-package/给队友-打开与修改.md",
    "LICENSE",
)
OPTIONAL_ARTIFACTS = (
    "before-report.json",
    "before-report.md",
    "after-report.json",
    "after-report.md",
    "fixes.patch",
    "fixes.patch.json",
    "README.md",
    "SHA256SUMS",
)
MAX_FILE_BYTES = 16 * 1024 * 1024


def _read_source(root: Path, relative: str, required: bool = True) -> bytes | None:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise ValueError("Package sources must be explicit relative paths.")
    candidate = root
    for part in path.parts:
        candidate = candidate / part
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError("Symlinks and junctions are not allowed in package sources.")
    if not candidate.exists():
        if required:
            raise ValueError("A required frontend package file is missing.")
        return None
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("Package source is not a regular file within the project.")
    with resolved.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("A package source exceeds the 16 MiB per-file limit.")
    return data


def build_package(root: Path, out: Path) -> dict[str, object]:
    """Read the exact public manifest, then exclusively create a new ZIP."""
    if out.exists() or out.is_symlink():
        raise FileExistsError("Output already exists; choose a new ZIP filename.")
    if root.is_symlink() or root.is_junction():
        raise ValueError("Project root must not be a symlink or junction.")
    root = root.resolve(strict=True)
    files: list[tuple[str, bytes]] = []
    for relative in (*REQUIRED_FILES, *(f"{UI_PREFIX}/{name}" for name in sorted(PUBLIC_FILES))):
        data = _read_source(root, relative)
        assert data is not None
        files.append((relative, data))
    skipped = []
    for name in OPTIONAL_ARTIFACTS:
        relative = f"DOCsync-demo-video-package/artifacts/{name}"
        data = _read_source(root, relative, required=False)
        if data is None:
            skipped.append(name)
        else:
            files.append((relative, data))
    out.parent.mkdir(parents=True, exist_ok=True)
    # Use an exclusive file handle: a target appearing after preflight is never overwritten.
    with out.open("xb") as stream, ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
        for relative, data in files:
            archive.writestr(f"{PACKAGE_ROOT}/{relative}", data)
    with out.open("rb") as digest_stream:
        digest = hashlib.file_digest(digest_stream, "sha256").hexdigest()
    return {"archive": str(out), "files": len(files), "sha256": digest, "skipped_optional": skipped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package only public DocSync frontend handoff files."
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="New ZIP filename; existing outputs are preserved"
    )
    args = parser.parse_args(argv)
    try:
        summary = build_package(Path(__file__).resolve().parents[1], args.out)
    except (OSError, ValueError):
        print(
            "Cannot package the frontend. Use a new output filename, check required files and "
            "permissions, and keep symlinks/junctions out of the package sources.",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
