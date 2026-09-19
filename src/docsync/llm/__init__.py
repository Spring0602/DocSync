"""Provider extension contract; no fabricated model responses in production."""

import inspect
from typing import Protocol

from docsync.models import CandidateSet, CodeFact, Decision, DocumentClaim, JudgeResult


class Provider(Protocol):
    model_id: str

    def judge(self, claim: DocumentClaim, facts: list[CodeFact]) -> JudgeResult:
        """Return a validated response; implementations must enforce budgets and timeouts."""
        ...


def validate_response(
    payload: str, claim: DocumentClaim, allowed_fact_ids: set[str]
) -> JudgeResult:
    response = JudgeResult.model_validate_json(payload, strict=True)
    if response.claim_id != claim.claim_id or not set(response.fact_ids) <= allowed_fact_ids:
        raise ValueError("Provider cited IDs outside its input")
    if response.decision == Decision.SKIPPED:
        raise ValueError("Provider must use CONSISTENT, INCONSISTENT or UNCERTAIN")
    return response


def judge(
    claim: DocumentClaim, candidates: CandidateSet, facts: dict[str, CodeFact]
) -> JudgeResult:
    reason = ""
    if claim.kind not in {"DEFAULT_ASSERTION", "CONFIG_ASSERTION", "CALL_EXAMPLE"}:
        return JudgeResult(
            claim_id=claim.claim_id,
            decision=Decision.SKIPPED,
            fact_ids=[],
            reason_code="UNSUPPORTED_CLAIM",
            reason_text="Unsupported claim kind",
        )
    if claim.version_scope != "current":
        reason = "VERSION_UNRESOLVED"
    elif claim.qualifiers:
        reason = "QUALIFIED_ASSERTION"
    elif candidates.ambiguity:
        reason = "AMBIGUOUS"
    elif not candidates.candidates:
        reason = "NO_CANDIDATE"
    else:
        fact = facts[candidates.candidates[0].fact_id]
        if claim.kind == "CALL_EXAMPLE" and fact.fact_kind == "SIGNATURE":
            return judge_call(claim, fact)
        if fact.value_state != "KNOWN" or fact.typed_value is None or claim.value is None:
            reason = "UNKNOWN_VALUE"
        else:
            equal = fact.typed_value == claim.value
            return JudgeResult(
                claim_id=claim.claim_id,
                decision=Decision.CONSISTENT if equal else Decision.INCONSISTENT,
                fact_ids=[fact.fact_id],
                reason_code="LITERAL_EQUAL" if equal else "LITERAL_MISMATCH",
                reason_text="Compare explicit typed default values for the same parameter",
                claim_type_check=True,
                version_compatible=True,
            )
    return JudgeResult(
        claim_id=claim.claim_id,
        decision=Decision.UNCERTAIN,
        fact_ids=[],
        reason_code=reason,
        reason_text="Insufficient evidence for a deterministic decision",
        uncertainty_reason=reason,
    )


def judge_call(claim: DocumentClaim, fact: CodeFact) -> JudgeResult:
    if fact.value_state != "KNOWN" or claim.unpacking or claim.positional_count is None:
        return JudgeResult(
            claim_id=claim.claim_id,
            decision=Decision.UNCERTAIN,
            fact_ids=[fact.fact_id],
            reason_code="DYNAMIC_CALL",
            reason_text="Cannot bind a dynamic or unsupported call",
            uncertainty_reason="DYNAMIC_CALL",
        )
    parameters = list(fact.parameters)
    if fact.receiver == "class" or (fact.receiver == "instance" and claim.bound_receiver):
        if not parameters or parameters[0].kind not in {"POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD"}:
            return JudgeResult(
                claim_id=claim.claim_id,
                decision=Decision.UNCERTAIN,
                fact_ids=[fact.fact_id],
                reason_code="RECEIVER_UNKNOWN",
                reason_text="Unsupported receiver binding",
            )
        parameters = parameters[1:]
    kinds = {
        "POSITIONAL_ONLY": inspect.Parameter.POSITIONAL_ONLY,
        "POSITIONAL_OR_KEYWORD": inspect.Parameter.POSITIONAL_OR_KEYWORD,
        "VAR_POSITIONAL": inspect.Parameter.VAR_POSITIONAL,
        "KEYWORD_ONLY": inspect.Parameter.KEYWORD_ONLY,
        "VAR_KEYWORD": inspect.Parameter.VAR_KEYWORD,
    }
    # Extractors store named parameters before *args; Signature requires semantic order.
    ordered = sorted(parameters, key=lambda p: kinds[p.kind])
    try:
        signature = inspect.Signature(
            [
                inspect.Parameter(
                    p.name,
                    kinds[p.kind],
                    default=inspect.Parameter.empty
                    if p.required or p.kind in {"VAR_POSITIONAL", "VAR_KEYWORD"}
                    else None,
                )
                for p in ordered
            ]
        )
    except ValueError:
        return JudgeResult(
            claim_id=claim.claim_id,
            decision=Decision.UNCERTAIN,
            fact_ids=[fact.fact_id],
            reason_code="INVALID_SIGNATURE",
            reason_text="Unsupported or invalid signature",
        )
    try:
        if len(set(claim.keyword_names)) != len(claim.keyword_names):
            raise TypeError("Duplicate keyword argument")
        signature.bind(*([None] * claim.positional_count), **dict.fromkeys(claim.keyword_names))
        decision = Decision.CONSISTENT
        reason = "CALL_ACCEPTED"
    except TypeError:
        decision = Decision.INCONSISTENT
        reason = "CALL_BINDING_ERROR"
    return JudgeResult(
        claim_id=claim.claim_id,
        decision=decision,
        fact_ids=[fact.fact_id],
        reason_code=reason,
        reason_text="Statically bind supplied arguments to the supported signature",
        claim_type_check=True,
        version_compatible=True,
    )
