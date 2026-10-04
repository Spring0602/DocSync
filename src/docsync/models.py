"""Schema 2.0 contracts; 1.0 reports remain readable for review and patch export."""

from datetime import date
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

type LiteralType = Literal[
    "NoneType", "bool", "int", "float", "str", "list", "tuple", "dict", "set"
]
type ParameterKind = Literal[
    "POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY", "VAR_POSITIONAL", "VAR_KEYWORD"
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Decision(StrEnum):
    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    UNCERTAIN = "UNCERTAIN"
    SKIPPED = "SKIPPED"


class RunStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Diagnostic(Model):
    code: str
    message: str
    stage: str
    path: str | None = None
    retryable: bool = False
    affects_completeness: bool = True


class SourceSpan(Model):
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    blob_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if not value or path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
            raise ValueError("Expected a repository-relative POSIX path")
        return value

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end_byte < self.start_byte or self.end_line < self.start_line:
            raise ValueError("Invalid source interval")
        return self


class LiteralValue(Model):
    type: LiteralType
    canonical: str


class Parameter(Model):
    name: str
    kind: ParameterKind
    required: bool
    value_state: Literal["KNOWN", "UNKNOWN", "ABSENT"]
    typed_value: LiteralValue | None = None
    expression: str | None = None


class CodeEntity(Model):
    entity_id: str
    kind: Literal["function", "async_function", "method", "config"]
    qualified_name: str
    module: str
    signature: list[Parameter]
    decorators: list[str]
    span: SourceSpan


class CodeFact(Model):
    fact_id: str
    entity_id: str
    subject: str
    property: str
    value_state: Literal["KNOWN", "UNKNOWN"]
    typed_value: LiteralValue | None
    expression: str
    span: SourceSpan
    fact_kind: Literal["DEFAULT_VALUE", "SIGNATURE", "CONFIG"] = "DEFAULT_VALUE"
    parameters: list[Parameter] = Field(default_factory=list)
    receiver: Literal["none", "instance", "class"] = "none"
    extractor_version: str = "python-static/2"


class DocumentClaim(Model):
    claim_id: str
    subject: str
    predicate: str
    kind: Literal["DEFAULT_ASSERTION", "CALL_EXAMPLE", "VERSION_NOTE", "CONFIG_ASSERTION"]
    value: LiteralValue | None
    qualifiers: list[str] = Field(default_factory=list)
    version_scope: Literal["current", "unresolved"] = "current"
    span: SourceSpan
    value_span: SourceSpan | None = None
    quote: str
    extraction_method: str = "markdown-rules/1"
    source_hint: str | None = None
    positional_count: int | None = Field(default=None, ge=0)
    keyword_names: list[str] = Field(default_factory=list)
    unpacking: bool = False
    bound_receiver: bool = False


class Candidate(Model):
    fact_id: str
    rank: int = Field(ge=1)
    score: float
    features: list[str]


class CandidateSet(Model):
    claim_id: str
    candidates: list[Candidate]
    ambiguity: bool
    reason: str


class JudgeResult(Model):
    claim_id: str
    decision: Decision
    fact_ids: list[str]
    reason_code: str
    reason_text: str
    claim_type_check: bool = False
    version_compatible: bool = False
    score: float | None = Field(default=None, ge=0, le=1)
    uncertainty_reason: str | None = None
    model_run_id: str | None = None


class Evidence(Model):
    head_sha: str
    snapshot_hash: str
    entity_id: str
    document: SourceSpan
    code: SourceSpan
    rule_id: str = "DEFAULT_VALUE/1"
    verifier_version: str = "verifier/2"


class Finding(Model):
    finding_id: str
    drift_type: Literal["DEFAULT_VALUE", "SIGNATURE", "CONFIG"] = "DEFAULT_VALUE"
    claim_id: str
    fact_ids: list[str]
    evidence: Evidence
    severity: Literal["warning"] = "warning"
    status: Literal["INCONSISTENT"] = "INCONSISTENT"
    verification_status: Literal["VERIFIED"] = "VERIFIED"
    ignored: bool = False
    ignore_reason: str | None = None
    ignore_expires: date | None = None


class RejectedDecision(Model):
    claim_id: str
    reason: str
    decision: Literal["UNCERTAIN"] = "UNCERTAIN"


class FileRecord(Model):
    path: str
    blob_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(ge=0)
    encoding: str = "utf-8"

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if not value or path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
            raise ValueError("Expected a repository-relative POSIX path")
        return value


class RepositorySnapshot(Model):
    repo_id: str
    head_sha: str
    base_sha: str | None
    mode: Literal["commit", "working-tree"]
    files_hash: str
    dirty: bool
    files: list[FileRecord]
    changed_paths: list[str]


class RunManifest(Model):
    schema_version: Literal["1.0", "2.0"] = "2.0"
    run_id: str
    versions: dict[str, str]
    config_hash: str
    mode: Literal["rules", "hybrid"]
    status: RunStatus
    enabled_types: list[str] = Field(
        default_factory=lambda: ["DEFAULT_VALUE", "SIGNATURE", "CONFIG"]
    )
    semantic_coverage: str = "supported-static-claims-only"
    budget: dict[str, int]
    usage: dict[str, int]
    diagnostics: list[Diagnostic]
    stage_seconds: dict[str, float] = Field(default_factory=dict)
    model: dict[str, str | float | None] = Field(default_factory=dict)
    events: list[str] = Field(default_factory=list)
    model_calls: list[dict[str, str | int | float | bool | None]] = Field(default_factory=list)


class PatchEdit(Model):
    span: SourceSpan
    old_text: str
    new_text: str


class PatchProposal(Model):
    patch_id: str
    finding_ids: list[str]
    base_hashes: dict[str, str]
    edits: list[PatchEdit]
    diff: str
    validation: Literal["VALIDATED", "CONFLICT", "NOT_ELIGIBLE"]
    requires_review: bool = True
    validation_details: list[str]


class ScanReport(Model):
    schema_version: Literal["1.0", "2.0"] = "2.0"
    manifest: RunManifest
    snapshot: RepositorySnapshot
    entities: list[CodeEntity]
    facts: list[CodeFact]
    claims: list[DocumentClaim]
    candidates: list[CandidateSet]
    judgments: list[JudgeResult]
    findings: list[Finding]
    rejected: list[RejectedDecision]
    patches: list[PatchProposal] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_exist(self) -> Self:
        entities = {e.entity_id for e in self.entities}
        facts = {f.fact_id: f for f in self.facts}
        claims = {c.claim_id: c for c in self.claims}
        findings = {f.finding_id: f for f in self.findings}
        blobs = {f.path: f.blob_hash for f in self.snapshot.files}
        if len(blobs) != len(self.snapshot.files):
            raise ValueError("Duplicate snapshot paths")
        if (
            len(entities) != len(self.entities)
            or len(facts) != len(self.facts)
            or len(claims) != len(self.claims)
            or len(findings) != len(self.findings)
        ):
            raise ValueError("Duplicate report IDs")
        for fact in self.facts:
            if fact.entity_id not in entities or blobs.get(fact.span.path) != fact.span.blob_hash:
                raise ValueError("Fact has an invalid entity or snapshot reference")
        for claim in self.claims:
            if blobs.get(claim.span.path) != claim.span.blob_hash:
                raise ValueError("Claim has an invalid snapshot reference")
        for candidate in self.candidates:
            if candidate.claim_id not in claims or any(
                c.fact_id not in facts for c in candidate.candidates
            ):
                raise ValueError("Invalid candidate reference")
        for judgment in self.judgments:
            if judgment.claim_id not in claims or any(f not in facts for f in judgment.fact_ids):
                raise ValueError("Invalid judgment reference")
        for finding in self.findings:
            if (
                finding.claim_id not in claims
                or not finding.fact_ids
                or any(f not in facts for f in finding.fact_ids)
            ):
                raise ValueError("Invalid finding reference")
            if (
                finding.evidence.document != claims[finding.claim_id].span
                or finding.evidence.code != facts[finding.fact_ids[0]].span
                or finding.evidence.head_sha != self.snapshot.head_sha
                or finding.evidence.snapshot_hash != self.snapshot.files_hash
            ):
                raise ValueError("Finding evidence does not match its snapshot")
        for patch in self.patches:
            if any(f not in findings for f in patch.finding_ids):
                raise ValueError("Patch references a missing finding")
        return self

    @property
    def uncertain_count(self) -> int:
        return len(
            {j.claim_id for j in self.judgments if j.decision == Decision.UNCERTAIN}
            | {r.claim_id for r in self.rejected}
        )

    @property
    def confirmed_count(self) -> int:
        return sum(not finding.ignored for finding in self.findings)

    @property
    def ignored_count(self) -> int:
        return sum(finding.ignored for finding in self.findings)
