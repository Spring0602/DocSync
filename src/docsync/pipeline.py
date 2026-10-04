"""One explicit, auditable pipeline shared by CLI, Action and benchmark runners."""

import time
import uuid
from datetime import date
from importlib.metadata import version

from docsync import __version__
from docsync.alignment import align
from docsync.config import IgnoreRule, RepoSpec, ScanConfig
from docsync.extractors.markdown import extract_claims
from docsync.extractors.python_ast import extract_code
from docsync.llm import judge
from docsync.llm.provider import ChatCompletionsProvider, ProviderError
from docsync.models import (
    Candidate,
    CandidateSet,
    Decision,
    Diagnostic,
    Finding,
    JudgeResult,
    RejectedDecision,
    RunManifest,
    RunStatus,
    ScanReport,
)
from docsync.patches import propose_patch
from docsync.repository import SnapshotData, analyze, matches
from docsync.utils import digest
from docsync.verification import VerificationIndex, verify


def evaluate_snapshot(
    snapshot: SnapshotData,
    cfg: ScanConfig,
    provider: ChatCompletionsProvider | None = None,
    scan_date: date | None = None,
) -> ScanReport:
    started = time.perf_counter()
    code = extract_code(snapshot)
    docs = extract_claims(snapshot)
    stages = {"extraction": time.perf_counter() - started}
    candidates = align(docs.claims, code.facts, cfg.alignment.top_k)
    method = cfg.scan.analysis_method
    if method == "no_alignment":
        candidates = [
            CandidateSet(
                claim_id=c.claim_id,
                ambiguity=False,
                reason="EXPERIMENT_NO_ALIGNMENT",
                candidates=[
                    Candidate(fact_id=f.fact_id, rank=i + 1, score=0, features=["property_only"])
                    for i, f in enumerate(
                        [f for f in code.facts if f.property == c.predicate][: cfg.alignment.top_k]
                    )
                ],
            )
            for c in docs.claims
        ]
    stages["alignment"] = time.perf_counter() - started - stages["extraction"]
    facts = {fact.fact_id: fact for fact in code.facts}
    diagnostics = [*snapshot.diagnostics, *code.diagnostics, *docs.diagnostics]
    wants_model = (cfg.scan.mode == "hybrid" and method != "rules") or method in {
        "llm",
        "no_static",
    }
    if wants_model and provider is None:
        try:
            provider = ChatCompletionsProvider(cfg.llm)
        except ProviderError as exc:
            diagnostics.append(
                Diagnostic(
                    code=exc.code,
                    stage="judge",
                    message="Model adapter unavailable; any retained rules do not provide AI coverage",
                )
            )
    judgments: list[JudgeResult] = []
    findings: list[Finding] = []
    rejected: list[RejectedDecision] = []
    verification_index = VerificationIndex.from_snapshot(snapshot)
    judge_seconds, verify_seconds = 0.0, 0.0
    scan_date = scan_date or date.today()
    for claim, candidate in zip(docs.claims, candidates, strict=True):
        step = time.perf_counter()
        judgment = judge(claim, candidate, facts)
        if wants_model and (
            method in {"llm", "no_static"} or judgment.decision != Decision.CONSISTENT
        ):
            if provider is not None:
                try:
                    selected = [facts[c.fact_id] for c in candidate.candidates]
                    if method in {"llm", "no_static"}:
                        judgment = provider.judge_raw(
                            claim,
                            selected,
                            {
                                f.span.path: snapshot.blobs[f.span.path].decode("utf-8")
                                for f in selected
                            },
                        )
                    else:
                        judgment = provider.judge(claim, selected)
                except ProviderError as exc:
                    diagnostics.append(
                        Diagnostic(
                            code=exc.code,
                            message="Model decision unavailable",
                            stage="judge",
                            path=claim.span.path,
                            retryable=exc.retryable,
                        )
                    )
                    judgment = JudgeResult(
                        claim_id=claim.claim_id,
                        decision=Decision.UNCERTAIN,
                        fact_ids=[],
                        reason_code=exc.code,
                        reason_text="Model request did not yield a valid decision",
                        uncertainty_reason=exc.code,
                    )
            elif method in {"llm", "no_static"}:
                judgment = JudgeResult(
                    claim_id=claim.claim_id,
                    decision=Decision.UNCERTAIN,
                    fact_ids=[],
                    reason_code="AI_UNAVAILABLE",
                    reason_text="This method requires a real model",
                )
        judge_seconds += time.perf_counter() - step
        judgments.append(judgment)
        step = time.perf_counter()
        result = verify(judgment, claim, facts, snapshot, verification_index)
        if isinstance(result, Finding):
            expired_match: IgnoreRule | None = None
            for rule in cfg.ignores:
                if (
                    (rule.finding_id is None or rule.finding_id == result.finding_id)
                    and (rule.rule_id is None or rule.rule_id == result.evidence.rule_id)
                    and matches(claim.span.path, [rule.path])
                ):
                    if rule.expires is not None and rule.expires < scan_date:
                        if expired_match is None:
                            expired_match = rule
                        continue
                    result = result.model_copy(
                        update={
                            "ignored": True,
                            "ignore_reason": rule.reason,
                            "ignore_expires": rule.expires,
                        }
                    )
                    break
            else:
                if expired_match is not None:
                    result = result.model_copy(
                        update={
                            "ignore_reason": expired_match.reason,
                            "ignore_expires": expired_match.expires,
                        }
                    )
            findings.append(result)
        elif isinstance(result, RejectedDecision):
            rejected.append(result)
        verify_seconds += time.perf_counter() - step
    stages.update(
        judging=judge_seconds,
        verification=verify_seconds,
        analysis_total=time.perf_counter() - started,
    )
    if provider:
        diagnostics.extend(provider.diagnostics)
    status = (
        RunStatus.PARTIAL
        if any(d.affects_completeness for d in diagnostics)
        else RunStatus.COMPLETED
    )
    return ScanReport(
        manifest=RunManifest(
            run_id=uuid.uuid4().hex,
            versions={
                "docsync": __version__,
                "schema": "2.0",
                "extractor": "python-static/2",
                "claims": "markdown/2",
                "verifier": "verifier/2",
                "method": method,
                "pydantic": version("pydantic"),
                "markdown-it-py": version("markdown-it-py"),
            },
            config_hash=digest(cfg.model_dump_json().encode()),
            mode=cfg.scan.mode,
            status=status,
            budget={
                "max_requests": cfg.llm.max_requests,
                "max_total_tokens": cfg.llm.max_total_tokens,
            },
            usage=dict(provider.usage)
            if provider
            else {"requests": 0, "input_tokens": 0, "output_tokens": 0},
            model={
                "provider": cfg.llm.provider,
                "model": cfg.llm.model,
                "temperature": cfg.llm.temperature,
            },
            stage_seconds=stages,
            events=[
                "CREATED",
                "ANALYZING",
                "EXTRACTING",
                "ALIGNING",
                "JUDGING",
                "VERIFYING",
                "REPORTING",
                status.value,
            ],
            model_calls=list(provider.calls) if provider else [],
            diagnostics=diagnostics,
        ),
        snapshot=snapshot.manifest,
        entities=code.entities,
        facts=code.facts,
        claims=docs.claims,
        candidates=candidates,
        judgments=judgments,
        findings=findings,
        rejected=rejected,
    )


def scan(
    spec: RepoSpec, cfg: ScanConfig | None = None, provider: ChatCompletionsProvider | None = None
) -> ScanReport:
    cfg = cfg or ScanConfig()
    started = time.perf_counter()
    scan_date = date.today()
    snapshot = analyze(spec, cfg)
    repository_seconds = time.perf_counter() - started
    report = evaluate_snapshot(snapshot, cfg, provider, scan_date)
    patch_started = time.perf_counter()
    # Patch verification is deterministic, does not spend extra model budget or rerun experiments.
    validation_cfg = cfg.model_copy(
        update={
            "scan": cfg.scan.model_copy(update={"mode": "rules", "analysis_method": "rules"}),
            "ignores": [],
        }
    )
    proposal = propose_patch(
        report, snapshot, lambda data: evaluate_snapshot(data, validation_cfg, scan_date=scan_date)
    )
    manifest = report.manifest.model_copy(
        update={
            "stage_seconds": {
                **report.manifest.stage_seconds,
                "repository": repository_seconds,
                "patch_validation": time.perf_counter() - patch_started,
                "total": time.perf_counter() - started,
            }
        }
    )
    return report.model_copy(
        update={"manifest": manifest, "patches": [proposal] if proposal else []}
    )
