"""Small Markdown edits with preimage checks, preview validation and rollback."""

import difflib
import os
import tempfile
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from markdown_it import MarkdownIt

from docsync.models import FileRecord, PatchEdit, PatchProposal, ScanReport
from docsync.repository import SnapshotData
from docsync.utils import DocSyncError, digest, span_for, stable_id


def edited_blobs(edits: list[PatchEdit], blobs: dict[str, bytes]) -> dict[str, bytes]:
    grouped: dict[str, list[PatchEdit]] = defaultdict(list)
    for edit in edits:
        if not edit.span.path.endswith(".md"):
            raise DocSyncError("UNSAFE_PATCH", "Only Markdown patches are allowed", "patch")
        grouped[edit.span.path].append(edit)
    updated = dict(blobs)
    for path, group in grouped.items():
        data = blobs[path]
        boundary = len(data)
        for edit in sorted(group, key=lambda e: e.span.start_byte, reverse=True):
            span = edit.span
            if (
                digest(blobs[path]) != span.blob_hash
                or span.end_byte > boundary
                or span_for(path, blobs[path], span.start_byte, span.end_byte) != span
                or data[span.start_byte : span.end_byte] != edit.old_text.encode("utf-8")
            ):
                raise DocSyncError("PATCH_CONFLICT", "Overlapping, stale or invalid edit", "patch")
            data = data[: span.start_byte] + edit.new_text.encode("utf-8") + data[span.end_byte :]
            boundary = span.start_byte
        updated[path] = data
    return updated


def unified_diff(before: dict[str, bytes], after: dict[str, bytes]) -> str:
    chunks = []
    for path in sorted(before):
        if before[path] != after[path]:
            lines = difflib.unified_diff(
                before[path].decode("utf-8").splitlines(keepends=True),
                after[path].decode("utf-8").splitlines(keepends=True),
                fromfile="a/" + path,
                tofile="b/" + path,
            )
            for line in lines:
                chunks.append(
                    line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                )
    return "".join(chunks)


def propose_patch(
    report: ScanReport, snapshot: SnapshotData, rescan: Callable[[SnapshotData], ScanReport]
) -> PatchProposal | None:
    claims = {c.claim_id: c for c in report.claims}
    facts = {f.fact_id: f for f in report.facts}
    edits: list[PatchEdit] = []
    finding_ids = []
    for finding in report.findings:
        if finding.ignored or finding.drift_type == "SIGNATURE":
            continue
        claim = claims[finding.claim_id]
        fact = facts[finding.fact_ids[0]]
        if claim.value_span is None or any(c in fact.expression for c in ("`", "\n", "\r")):
            continue
        data = snapshot.blobs[claim.span.path]
        old = data[claim.value_span.start_byte : claim.value_span.end_byte].decode("utf-8")
        edits.append(PatchEdit(span=claim.value_span, old_text=old, new_text=fact.expression))
        finding_ids.append(finding.finding_id)
    if not edits:
        return None
    patch_id = stable_id("patch", *finding_ids)
    hashes = {e.span.path: e.span.blob_hash for e in edits}
    try:
        after = edited_blobs(edits, snapshot.blobs)
    except DocSyncError:
        return PatchProposal(
            patch_id=patch_id,
            finding_ids=finding_ids,
            base_hashes=hashes,
            edits=edits,
            diff="",
            validation="CONFLICT",
            validation_details=["Overlapping edits"],
            requires_review=True,
        )
    parser = MarkdownIt("commonmark")
    for path in hashes:
        before_fences = [
            (t.type, t.content)
            for t in parser.parse(snapshot.blobs[path].decode())
            if t.type in {"fence", "code_block"}
        ]
        after_fences = [
            (t.type, t.content)
            for t in parser.parse(after[path].decode())
            if t.type in {"fence", "code_block"}
        ]
        if before_fences != after_fences:
            return None
    records = [
        FileRecord(path=p, blob_hash=digest(data), size=len(data))
        for p, data in sorted(after.items())
    ]
    manifest = snapshot.manifest.model_copy(
        update={
            "files": records,
            "files_hash": stable_id(*(f.path + ":" + f.blob_hash for f in records)),
        }
    )
    fresh = rescan(SnapshotData(manifest, after, snapshot.diagnostics))
    fresh_decisions = {j.claim_id: j.decision for j in fresh.judgments}
    findings_by_id = {f.finding_id: f for f in report.findings}
    # A disappeared claim is not a repaired claim. Re-identify each edited value
    # at its shifted byte position and require an explicit CONSISTENT decision.
    for edit, finding_id in zip(edits, finding_ids, strict=True):
        original_claim = claims[findings_by_id[finding_id].claim_id]
        shift = sum(
            len(e.new_text.encode("utf-8")) - len(e.old_text.encode("utf-8"))
            for e in edits
            if e.span.path == edit.span.path and e.span.start_byte < edit.span.start_byte
        )
        expected_start = edit.span.start_byte + shift
        if not any(
            c.value_span is not None
            and c.span.path == edit.span.path
            and c.value_span.start_byte == expected_start
            and c.subject == original_claim.subject
            and c.predicate == original_claim.predicate
            and fresh_decisions[c.claim_id] == "CONSISTENT"
            for c in fresh.claims
        ):
            return None
    targets = {
        (claims[f.claim_id].span.path, claims[f.claim_id].subject, claims[f.claim_id].predicate)
        for f in report.findings
        if f.finding_id in finding_ids
    }
    remaining = {
        (c.span.path, c.subject, c.predicate)
        for c in fresh.claims
        if any(f.claim_id == c.claim_id for f in fresh.findings)
    }
    original = {
        (claims[f.claim_id].span.path, claims[f.claim_id].subject, claims[f.claim_id].predicate)
        for f in report.findings
    }
    if targets & remaining or remaining - original:
        return None
    return PatchProposal(
        patch_id=patch_id,
        finding_ids=finding_ids,
        base_hashes=hashes,
        edits=edits,
        diff=unified_diff(snapshot.blobs, after),
        validation="VALIDATED",
        validation_details=[
            "All byte preimages match",
            "Code fences unchanged",
            "In-memory rescan: target conflicts removed; no new confirmed conflicts",
            "Human semantic review still required",
        ],
    )


def safe_target(root: Path, relative: str) -> Path:
    target = root / relative
    if (
        not relative.endswith(".md")
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or "\\" in relative
        or ":" in relative
        or ".git" in Path(relative).parts
        or not target.resolve().is_relative_to(root)
        or target.is_symlink()
    ):
        raise DocSyncError("UNSAFE_PATCH", "Patch path is not an allowed Markdown file", "apply")
    for parent in target.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise DocSyncError("UNSAFE_PATCH", "Symlinked parent directory", "apply")
    return target


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temp = tempfile.mkstemp(prefix=".docsync-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def apply_patch(repo: Path, proposal: PatchProposal, diff: str) -> list[str]:
    if (
        proposal.validation != "VALIDATED"
        or diff != proposal.diff
        or not proposal.edits
        or not proposal.finding_ids
        or len(set(proposal.finding_ids)) != len(proposal.finding_ids)
        or proposal.patch_id != stable_id("patch", *proposal.finding_ids)
    ):
        raise DocSyncError(
            "INVALID_PATCH", "Expected the matching validated patch and manifest", "apply"
        )
    root = repo.resolve()
    paths = {edit.span.path for edit in proposal.edits}
    if paths != set(proposal.base_hashes):
        raise DocSyncError("INVALID_PATCH", "Manifest paths do not match edits", "apply")
    targets = {path: safe_target(root, path) for path in paths}
    originals = {path: target.read_bytes() for path, target in targets.items()}
    for path, data in originals.items():
        if digest(data) != proposal.base_hashes[path]:
            raise DocSyncError(
                "STALE_PATCH", "Preimage changed or patch already applied: " + path, "apply"
            )
    after = edited_blobs(proposal.edits, originals)
    if unified_diff(originals, after) != proposal.diff:
        raise DocSyncError("INVALID_PATCH", "Diff does not match manifest edits", "apply")
    written: list[str] = []
    try:
        for path, target in sorted(targets.items()):
            if safe_target(root, path).read_bytes() != originals[path]:
                raise DocSyncError("STALE_PATCH", "File changed during apply: " + path, "apply")
            atomic_write(target, after[path])
            written.append(path)
    except (OSError, DocSyncError):
        for path in reversed(written):
            atomic_write(targets[path], originals[path])
        raise
    return written
