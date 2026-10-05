"""B3: alignment, deterministic rules and guarded patch application."""

import hashlib

import pytest

from docsync.alignment import align
from docsync.config import AlignmentOptions, RepoSpec, ScanConfig
from docsync.patches import apply_patch
from docsync.pipeline import scan
from docsync.reporting import markdown_report
from docsync.utils import DocSyncError, stable_id

DEFAULT_CODE = "def connect(timeout=60):\n    return timeout\n"
DEFAULT_DOC = "## `connect`\n\n`timeout` defaults to `30`.\n"


def test_exact_symbol_and_parameter_owner_win_over_suffix_matches(commit_files):
    repo = commit_files(
        {
            "one.py": "def connect(timeout=60, retries=3): pass\n",
            "two.py": "def connect(timeout=30, retries=9): pass\n",
            "README.md": "## `one.connect`\n\n`timeout` defaults to `30`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    candidate = report.candidates[0]
    assert not candidate.ambiguity
    assert len(candidate.candidates) == 1
    fact = next(item for item in report.facts if item.fact_id == candidate.candidates[0].fact_id)
    assert fact.subject == "one.connect"
    assert fact.property == "timeout"
    assert candidate.candidates[0].features[:2] == ["exact_symbol", "parameter_owner"]
    assert report.findings[0].evidence.code.path == "one.py"


def test_source_link_resolves_name_collision_and_top_k_never_hides_ambiguity(commit_files):
    repo = commit_files(
        {
            "one.py": "def connect(timeout=60): pass\n",
            "two.py": "def connect(timeout=90): pass\n",
            "README.md": (
                "## [connect](two.py)\n\n| parameter | default |\n|---|---|\n|timeout|30|\n"
            ),
        }
    )
    report = scan(RepoSpec(repo=repo), ScanConfig(alignment=AlignmentOptions(top_k=1)))
    candidate = report.candidates[0]
    assert not candidate.ambiguity
    assert len(candidate.candidates) == 1
    assert "link_match" in candidate.candidates[0].features
    assert report.findings[0].evidence.code.path == "two.py"

    unlinked = report.claims[0].model_copy(update={"source_hint": None})
    ambiguous = align([unlinked], report.facts, top_k=1)[0]
    assert ambiguous.ambiguity
    assert len(ambiguous.candidates) == 1


def test_import_alias_keeps_signature_parameter_ownership(commit_files):
    repo = commit_files(
        {
            "pkg/client.py": "def connect(required): pass\n",
            "other.py": "def connect(optional=1): pass\n",
            "README.md": (
                "```python\nfrom pkg.client import connect as open_connection\n"
                "open_connection()\n```\n"
            ),
        }
    )
    report = scan(RepoSpec(repo=repo))
    claim = next(item for item in report.claims if item.subject == "pkg.client.connect")
    judgment = next(item for item in report.judgments if item.claim_id == claim.claim_id)
    assert judgment.decision == "INCONSISTENT"
    assert report.findings[0].drift_type == "SIGNATURE"
    assert report.findings[0].evidence.code.path == "pkg/client.py"


def test_repeated_calls_have_distinct_but_repeatable_claim_and_finding_ids(commit_files):
    repo = commit_files(
        {
            "api.py": "def connect(required): pass\n",
            "README.md": "```python\nconnect()\nconnect()\n```\n",
        }
    )
    first = scan(RepoSpec(repo=repo))
    second = scan(RepoSpec(repo=repo))
    assert len(first.findings) == 2
    assert len({item.claim_id for item in first.claims}) == 2
    assert len({item.finding_id for item in first.findings}) == 2
    assert [item.claim_id for item in first.claims] == [item.claim_id for item in second.claims]
    assert [item.finding_id for item in first.findings] == [
        item.finding_id for item in second.findings
    ]


@pytest.mark.parametrize(
    "code,document,drift_type",
    [
        (DEFAULT_CODE, DEFAULT_DOC, "DEFAULT_VALUE"),
        (
            "CONFIG = {'timeout': 60}\n",
            "## config `settings.CONFIG`\n\n`timeout` defaults to `30`.\n",
            "CONFIG",
        ),
    ],
)
def test_default_and_config_patches_are_minimal_and_proven_by_rescan(
    commit_files, code, document, drift_type
):
    source_path = "settings.py" if drift_type == "CONFIG" else "api.py"
    repo = commit_files({source_path: code, "README.md": document})
    before_doc = (repo / "README.md").read_bytes()
    before_code = (repo / source_path).read_bytes()
    report = scan(RepoSpec(repo=repo))

    assert report.findings[0].drift_type == drift_type
    assert len(report.patches) == 1
    proposal = report.patches[0]
    assert proposal.validation == "VALIDATED"
    assert len(proposal.edits) == 1
    edit = proposal.edits[0]
    assert edit.span.path == "README.md"
    assert edit.old_text == "30" and edit.new_text == "60"
    assert proposal.base_hashes == {"README.md": hashlib.sha256(before_doc).hexdigest()}
    assert "All byte preimages match" in proposal.validation_details
    assert "In-memory rescan" in " ".join(proposal.validation_details)
    assert "-`timeout` defaults to `30`." in proposal.diff
    assert "+`timeout` defaults to `60`." in proposal.diff

    assert apply_patch(repo, proposal, proposal.diff) == ["README.md"]
    assert (repo / "README.md").read_bytes() == before_doc.replace(b"30", b"60", 1)
    assert (repo / source_path).read_bytes() == before_code
    rescanned = scan(RepoSpec(repo=repo, working_tree=True))
    assert not rescanned.findings


@pytest.mark.parametrize(
    "case",
    [
        "patch_id",
        "duplicate_finding_ids",
        "empty_finding_ids",
        "line_numbers",
        "diff",
        "base_hash",
        "old_text",
    ],
)
def test_apply_rejects_tampered_patch_metadata_without_writing(commit_files, case):
    repo = commit_files({"api.py": DEFAULT_CODE, "README.md": DEFAULT_DOC})
    proposal = scan(RepoSpec(repo=repo)).patches[0]
    supplied_diff = proposal.diff
    if case == "patch_id":
        proposal = proposal.model_copy(update={"patch_id": "0" * 24})
    elif case == "duplicate_finding_ids":
        finding_ids = proposal.finding_ids * 2
        proposal = proposal.model_copy(
            update={
                "finding_ids": finding_ids,
                "patch_id": stable_id("patch", *finding_ids),
            }
        )
    elif case == "empty_finding_ids":
        proposal = proposal.model_copy(update={"finding_ids": [], "patch_id": stable_id("patch")})
    elif case == "line_numbers":
        edit = proposal.edits[0]
        span = edit.span.model_copy(update={"start_line": 999, "end_line": 999})
        proposal = proposal.model_copy(update={"edits": [edit.model_copy(update={"span": span})]})
    elif case == "diff":
        supplied_diff += "forged"
    elif case == "base_hash":
        proposal = proposal.model_copy(update={"base_hashes": {"README.md": "0" * 64}})
    elif case == "old_text":
        edit = proposal.edits[0].model_copy(update={"old_text": "99"})
        proposal = proposal.model_copy(update={"edits": [edit]})

    before = (repo / "README.md").read_bytes()
    with pytest.raises(DocSyncError):
        apply_patch(repo, proposal, supplied_diff)
    assert (repo / "README.md").read_bytes() == before


def test_patch_cannot_be_applied_twice(commit_files):
    repo = commit_files({"api.py": DEFAULT_CODE, "README.md": DEFAULT_DOC})
    proposal = scan(RepoSpec(repo=repo)).patches[0]
    apply_patch(repo, proposal, proposal.diff)
    once = (repo / "README.md").read_bytes()
    with pytest.raises(DocSyncError) as error:
        apply_patch(repo, proposal, proposal.diff)
    assert error.value.code == "STALE_PATCH"
    assert (repo / "README.md").read_bytes() == once


def test_signature_rule_emits_evidence_and_manual_guidance_without_patch(commit_files):
    repo = commit_files(
        {
            "api.py": "def connect(required): pass\n",
            "README.md": "```python\nconnect()\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 1
    finding = report.findings[0]
    assert finding.drift_type == "SIGNATURE"
    assert finding.verification_status == "VERIFIED"
    assert finding.evidence.document.path == "README.md"
    assert finding.evidence.code.path == "api.py"
    assert not report.patches
    rendered = markdown_report(report)
    assert "签名问题不自动生成参数值" in rendered
    assert "人工" in rendered
