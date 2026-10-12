"""Opt-in claim-level scoring. Evaluation metadata never enters detection."""

from typing import Self

from pydantic import Field, model_validator

from docsync.models import Model, ScanReport, SourceSpan


class LineRange(Model):
    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end < self.start:
            raise ValueError("Reversed line range")
        return self


class ClaimScope(Model):
    document_ranges: list[LineRange] = Field(min_length=1)
    code_path: str = Field(min_length=1)
    entity_names: list[str] = Field(min_length=1)
    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    required_provenance: list[SourceSpan] = Field(default_factory=list)

    @model_validator(mode="after")
    def names(self) -> Self:
        if any(not name.strip() for name in self.entity_names):
            raise ValueError("Empty entity alias")
        return self


def scoped_predict(
    report: ScanReport,
    document_path: str,
    drift_type: str,
    head_sha: str,
    scope: ClaimScope,
    method: str,
) -> str:
    """Require full claim containment and exact fact ownership; ambiguity abstains."""
    if report.snapshot.head_sha != head_sha or report.manifest.status == "FAILED":
        return "UNCERTAIN"
    claims = {
        c.claim_id
        for c in report.claims
        if c.span.path == document_path
        and c.subject == scope.subject
        and c.predicate == scope.predicate
        and any(
            r.start <= c.span.start_line <= c.span.end_line <= r.end for r in scope.document_ranges
        )
    }
    if not claims:
        return "SKIPPED"
    entities = {
        e.entity_id
        for e in report.entities
        if e.qualified_name in scope.entity_names and e.span.path == scope.code_path
    }
    facts = {
        f.fact_id
        for f in report.facts
        if f.entity_id in entities
        and f.span.path == scope.code_path
        and f.property == scope.predicate
        and f.fact_kind == drift_type
        and all(span in [f.span, *f.provenance] for span in scope.required_provenance)
    }
    outcomes: set[str] = set()
    for claim in claims:
        decisions: set[str] = set()
        for j in report.judgments:
            if j.claim_id != claim:
                continue
            if not j.fact_ids or not set(j.fact_ids) <= facts:
                decisions.add("UNCERTAIN")
            elif j.decision == "INCONSISTENT" and method not in {"llm", "no_verifier"}:
                verified = any(
                    f.claim_id == claim
                    and not f.ignored
                    and f.drift_type == drift_type
                    and f.fact_ids
                    and set(f.fact_ids) <= facts
                    for f in report.findings
                )
                decisions.add("INCONSISTENT" if verified else "UNCERTAIN")
            else:
                decisions.add(str(j.decision))
        if any(r.claim_id == claim for r in report.rejected):
            decisions.add("UNCERTAIN")
        outcomes.update(decisions or {"UNCERTAIN"})
    if outcomes == {"CONSISTENT"}:
        return "CONSISTENT"
    if outcomes == {"INCONSISTENT"}:
        return "INCONSISTENT"
    return "UNCERTAIN"
