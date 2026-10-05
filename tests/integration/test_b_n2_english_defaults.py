import hashlib

import pytest

from docsync.config import RepoSpec
from docsync.pipeline import scan

CODE = "def connect(timeout=60):\n    return timeout\n"


def english_default(value: str, heading: str = "`connect`") -> str:
    return (
        f"## {heading}\r\n\r\n"
        "中文前缀用于验证 UTF-8 字节位置。\r\n"
        f"The default value of `timeout` is `{value}`.\r\n"
    )


def default_claim_and_judgment(report):
    claim = next(item for item in report.claims if item.kind == "DEFAULT_ASSERTION")
    judgment = next(item for item in report.judgments if item.claim_id == claim.claim_id)
    return claim, judgment


@pytest.mark.parametrize(
    ("documented", "decision", "finding_count"),
    [("60", "CONSISTENT", 0), ("30", "INCONSISTENT", 1)],
)
def test_english_default_value_of_is_extracted_with_exact_evidence(
    commit_files, documented, decision, finding_count
):
    document = english_default(documented)
    repo = commit_files({"client.py": CODE, "README.md": document})

    report = scan(RepoSpec(repo=repo))
    claim, judgment = default_claim_and_judgment(report)
    raw = document.encode("utf-8")

    assert claim.subject == "connect"
    assert claim.predicate == "timeout"
    assert claim.value.type == "int"
    assert claim.value.canonical == f'["int",{documented}]'
    assert claim.span.path == "README.md"
    assert claim.span.start_line == claim.span.end_line == 4
    assert claim.value_span.start_line == claim.value_span.end_line == 4
    assert raw[claim.value_span.start_byte : claim.value_span.end_byte] == documented.encode()
    assert claim.span.blob_hash == hashlib.sha256(raw).hexdigest()
    assert claim.value_span.blob_hash == claim.span.blob_hash
    assert judgment.decision == decision
    assert len(report.findings) == finding_count


def test_english_default_value_of_preserves_historical_refusal(commit_files):
    document = english_default("30", "Old version `connect`")
    repo = commit_files({"client.py": CODE, "README.md": document})

    report = scan(RepoSpec(repo=repo))
    claim, judgment = default_claim_and_judgment(report)

    assert claim.version_scope == "unresolved"
    assert judgment.decision == "UNCERTAIN"
    assert judgment.reason_code == "VERSION_UNRESOLVED"
    assert not report.findings


def test_english_default_value_of_preserves_same_name_ambiguity(commit_files):
    document = english_default("60")
    repo = commit_files({"one.py": CODE, "two.py": CODE, "README.md": document})

    report = scan(RepoSpec(repo=repo))
    claim, judgment = default_claim_and_judgment(report)
    candidates = next(item for item in report.candidates if item.claim_id == claim.claim_id)

    assert candidates.ambiguity
    assert judgment.decision == "UNCERTAIN"
    assert judgment.reason_code == "AMBIGUOUS"
    assert not report.findings


def test_english_default_value_of_uses_explicit_source_link(commit_files):
    document = english_default("30", "[connect](client.py)")
    repo = commit_files(
        {
            "client.py": CODE,
            "other.py": "def connect(timeout=30): pass\n",
            "README.md": document,
        }
    )

    report = scan(RepoSpec(repo=repo))
    claim, judgment = default_claim_and_judgment(report)

    assert claim.source_hint == "client.py"
    assert judgment.decision == "INCONSISTENT"
    assert len(report.findings) == 1
    assert report.findings[0].evidence.code.path == "client.py"


def test_english_default_does_not_turn_legal_explicit_call_into_drift(commit_files):
    document = english_default("60") + ("\r\n```python\r\nconnect(timeout=30)\r\n```\r\n")
    repo = commit_files({"client.py": CODE, "README.md": document})

    report = scan(RepoSpec(repo=repo))
    decisions = {item.reason_code: item.decision for item in report.judgments}

    assert decisions["LITERAL_EQUAL"] == "CONSISTENT"
    assert decisions["CALL_ACCEPTED"] == "CONSISTENT"
    assert not report.findings
