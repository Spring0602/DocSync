"""Re-extract both sides from immutable blobs before publishing a conflict."""

from dataclasses import dataclass

from docsync.alignment import align
from docsync.extractors.markdown import extract_claims
from docsync.extractors.python_ast import extract_code
from docsync.llm import judge
from docsync.models import (
    CodeFact,
    Decision,
    DocumentClaim,
    Evidence,
    Finding,
    JudgeResult,
    RejectedDecision,
    SourceSpan,
)
from docsync.repository import SnapshotData
from docsync.utils import digest, span_for, stable_id


@dataclass(frozen=True)
class VerificationIndex:
    claims: dict[str, DocumentClaim]
    facts: dict[str, CodeFact]

    @classmethod
    def from_snapshot(cls, snapshot: SnapshotData) -> "VerificationIndex":
        return cls(
            {c.claim_id: c for c in extract_claims(snapshot).claims},
            {f.fact_id: f for f in extract_code(snapshot).facts},
        )


def valid_span(span: SourceSpan, snapshot: SnapshotData, quote: str) -> bool:
    data = snapshot.blobs.get(span.path)
    if data is None or digest(data) != span.blob_hash or span.end_byte > len(data):
        return False
    return span_for(span.path, data, span.start_byte, span.end_byte) == span and data[
        span.start_byte : span.end_byte
    ] == quote.encode("utf-8")


def verify(
    judgment: JudgeResult,
    claim: DocumentClaim,
    facts: dict[str, CodeFact],
    snapshot: SnapshotData,
    index: VerificationIndex | None = None,
) -> Finding | RejectedDecision | None:
    if judgment.decision != Decision.INCONSISTENT:
        return None

    def reject(reason: str) -> RejectedDecision:
        return RejectedDecision(claim_id=claim.claim_id, reason=reason)

    if judgment.claim_id != claim.claim_id or len(judgment.fact_ids) != 1:
        return reject("INVALID_REFERENCE")
    fact = facts.get(judgment.fact_ids[0])
    if fact is None:
        return reject("INVALID_REFERENCE")
    if not valid_span(claim.span, snapshot, claim.quote) or not valid_span(
        fact.span, snapshot, fact.expression
    ):
        return reject("EVIDENCE_MISMATCH")
    index = index or VerificationIndex.from_snapshot(snapshot)
    fresh_claims, fresh_facts = index.claims, index.facts
    if fresh_claims.get(claim.claim_id) != claim or fresh_facts.get(fact.fact_id) != fact:
        return reject("REEXTRACTION_MISMATCH")
    candidates = align([claim], list(fresh_facts.values()))[0]
    checked = judge(claim, candidates, fresh_facts)
    if checked.decision != Decision.INCONSISTENT or checked.fact_ids != judgment.fact_ids:
        return reject("CONFLICT_NOT_PROVEN")
    rule_id = fact.fact_kind + "/1"
    return Finding(
        finding_id=stable_id(
            rule_id,
            claim.span.path,
            claim.subject,
            claim.predicate,
            claim.quote,
            claim.claim_id,
            snapshot.manifest.head_sha,
        ),
        drift_type=fact.fact_kind,
        claim_id=claim.claim_id,
        fact_ids=[fact.fact_id],
        evidence=Evidence(
            head_sha=snapshot.manifest.head_sha,
            snapshot_hash=snapshot.manifest.files_hash,
            entity_id=fact.entity_id,
            document=claim.span,
            code=fact.span,
            rule_id=rule_id,
        ),
    )
