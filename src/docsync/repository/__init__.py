"""Read-only repository snapshots backed by commit objects or explicit working trees."""

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from docsync.config import RepoSpec, ScanConfig
from docsync.models import Diagnostic, FileRecord, RepositorySnapshot
from docsync.utils import DocSyncError, digest, stable_id

EXCLUDED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".tox"}


@dataclass(frozen=True)
class SnapshotData:
    manifest: RepositorySnapshot
    blobs: dict[str, bytes]
    diagnostics: list[Diagnostic]


def git(repo: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DocSyncError("GIT_UNAVAILABLE", "Git failed or timed out") from exc
    if result.returncode:
        raise DocSyncError("GIT_ERROR", "Git operation failed: " + args[0])
    return result.stdout


def resolve_ref(repo: Path, ref: str) -> str:
    if not ref or ref.startswith("-") or "\x00" in ref:
        raise DocSyncError("INVALID_REF", "Invalid Git reference")
    try:
        return (
            git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
            .decode()
            .strip()
        )
    except DocSyncError as exc:
        raise DocSyncError(
            "MISSING_REF", "Cannot resolve reference; fetch the required commit first"
        ) from exc


def matches(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, p) or (p.startswith("**/") and fnmatch.fnmatchcase(path, p[3:]))
        for p in patterns
    )


def analyze(spec: RepoSpec, cfg: ScanConfig) -> SnapshotData:
    repo = spec.repo.resolve()
    root = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if root != repo:
        raise DocSyncError("REPO_ROOT_REQUIRED", "--repo must point to the Git repository root")
    head = resolve_ref(repo, spec.head)
    base = resolve_ref(repo, spec.base) if spec.base else None
    if spec.working_tree and spec.head != "HEAD":
        raise DocSyncError("INCOMPATIBLE_INPUT", "Working-tree mode only accepts --head HEAD")
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=normal"))
    changes = (
        []
        if base is None
        else [
            p.decode("utf-8")
            for p in git(repo, "diff", "--name-only", "-z", base, head, "--").split(b"\0")
            if p
        ]
    )
    diagnostics: list[Diagnostic] = []
    entries: list[tuple[str, str, str, int | None]] = []
    if spec.working_tree:
        paths = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        entries = [(p.decode("utf-8"), "working", "", None) for p in set(paths.split(b"\0")) if p]
    else:
        for record in git(repo, "ls-tree", "-r", "-z", "-l", head).split(b"\0"):
            if record:
                meta, raw_path = record.split(b"\t", 1)
                raw_mode, raw_kind, raw_oid, raw_size = meta.split()
                entries.append(
                    (
                        raw_path.decode("utf-8"),
                        raw_mode.decode(),
                        raw_oid.decode(),
                        int(raw_size) if raw_kind == b"blob" else None,
                    )
                )
    blobs: dict[str, bytes] = {}
    records: list[FileRecord] = []
    total = 0
    for path, mode, oid, size in sorted(entries):
        parts = PurePosixPath(path).parts
        if PurePosixPath(path).suffix not in {".py", ".md"}:
            continue
        if (
            EXCLUDED_PARTS.intersection(parts)
            or not matches(path, cfg.scan.include)
            or matches(path, cfg.scan.exclude)
        ):
            diagnostics.append(
                Diagnostic(
                    code="EXCLUDED",
                    message="Path excluded by scan policy",
                    stage="repository",
                    path=path,
                    affects_completeness=False,
                )
            )
            continue
        if ".." in parts or PurePosixPath(path).is_absolute() or "\\" in path or ":" in path:
            diagnostics.append(
                Diagnostic(
                    code="UNSAFE_PATH",
                    message="Unsafe repository path",
                    stage="repository",
                    path=path,
                )
            )
            continue
        target = repo / path
        if mode == "120000" or (
            spec.working_tree and (target.is_symlink() or not target.resolve().is_relative_to(repo))
        ):
            diagnostics.append(
                Diagnostic(
                    code="SYMLINK_SKIPPED",
                    message="Symlinks are not scanned",
                    stage="repository",
                    path=path,
                )
            )
            continue
        try:
            if spec.working_tree:
                if not target.is_file():
                    diagnostics.append(
                        Diagnostic(
                            code="MISSING_FILE",
                            message="Working file unavailable",
                            stage="repository",
                            path=path,
                        )
                    )
                    continue
                size = target.stat().st_size
            if (
                size is None
                or size > cfg.scan.max_file_bytes
                or total + size > cfg.scan.max_total_bytes
            ):
                diagnostics.append(
                    Diagnostic(
                        code="LIMIT_EXCEEDED",
                        message="Text size limit exceeded",
                        stage="repository",
                        path=path,
                    )
                )
                continue
            if spec.working_tree:
                with target.open("rb") as stream:
                    data = stream.read(cfg.scan.max_file_bytes + 1)
            else:
                data = git(repo, "cat-file", "blob", oid)
            if len(data) > cfg.scan.max_file_bytes or total + len(data) > cfg.scan.max_total_bytes:
                diagnostics.append(
                    Diagnostic(
                        code="LIMIT_EXCEEDED",
                        message="Text size limit exceeded",
                        stage="repository",
                        path=path,
                    )
                )
                continue
            data.decode("utf-8")
            if b"\x00" in data:
                raise UnicodeError("Binary content")
        except (OSError, UnicodeError):
            diagnostics.append(
                Diagnostic(
                    code="UNREADABLE_TEXT",
                    message="Expected readable UTF-8 text",
                    stage="repository",
                    path=path,
                )
            )
            continue
        total += len(data)
        blobs[path] = data
        records.append(FileRecord(path=path, blob_hash=digest(data), size=len(data)))
    if base:
        diagnostics.append(
            Diagnostic(
                code="FULL_SCAN_FALLBACK",
                message="Base recorded; impact analysis uses full scan",
                stage="repository",
                affects_completeness=False,
            )
        )
    manifest = RepositorySnapshot(
        repo_id=stable_id(repo.name, head),
        head_sha=head,
        base_sha=base,
        mode="working-tree" if spec.working_tree else "commit",
        dirty=dirty,
        files_hash=stable_id(*(f.path + ":" + f.blob_hash for f in records)),
        files=records,
        changed_paths=changes,
    )
    return SnapshotData(manifest, blobs, diagnostics)
