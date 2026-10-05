"""B2: conservative static facts, provenance and stable identity."""

import hashlib

import pytest

from docsync.config import RepoSpec, ScanConfig
from docsync.extractors.python_ast import extract_code
from docsync.pipeline import scan
from docsync.repository import analyze


@pytest.mark.parametrize(
    "class_header",
    ["class Client(Base):", "class Client(metaclass=Meta):"],
)
def test_inheritance_and_metaclasses_make_method_facts_unknown(commit_files, class_header):
    repo = commit_files(
        {
            "api.py": f"class Base: pass\nclass Meta(type): pass\n{class_header}\n    def connect(self, timeout=60): pass\n",
            "README.md": "## `api.Client.connect`\n\n`timeout` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    fact = next(item for item in report.facts if item.property == "timeout")
    assert fact.value_state == "UNKNOWN"
    assert report.judgments[0].decision == "UNCERTAIN"
    assert not report.findings


def test_dynamic_dict_key_after_explicit_key_is_unknown(commit_files):
    repo = commit_files(
        {
            "settings.py": "CONFIG = {'timeout': 60, dynamic_key(): 30}\n",
            "README.md": "## config `settings.CONFIG`\n\n`timeout` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    fact = next(item for item in report.facts if item.property == "timeout")
    assert fact.value_state == "UNKNOWN"
    assert report.judgments[0].decision == "UNCERTAIN"
    assert not report.findings


@pytest.mark.parametrize(
    "code,subject,property_name",
    [
        ("@runtime_wrap\ndef connect(timeout=60): pass", "api.connect", "timeout"),
        (
            "def connect(timeout=60): pass\nconnect = replacement",
            "api.connect",
            "timeout",
        ),
        (
            "def connect(timeout=factory()): pass",
            "api.connect",
            "timeout",
        ),
        (
            "CONFIG = {'timeout': 60, **other}",
            "api.CONFIG",
            "timeout",
        ),
        (
            "CONFIG = {'timeout': 60}\nCONFIG.update(other)",
            "api.CONFIG",
            "timeout",
        ),
    ],
)
def test_dynamic_or_rebound_values_never_become_consistent(
    commit_files, code, subject, property_name
):
    repo = commit_files(
        {
            "api.py": code + "\n",
            "README.md": f"## config `{subject}`\n\n`{property_name}` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    relevant = [item for item in report.facts if item.property == property_name]
    assert relevant and all(item.value_state == "UNKNOWN" for item in relevant)
    assert report.judgments[0].decision == "UNCERTAIN"
    assert not report.findings


def test_duplicate_function_definition_is_a_rebinding_boundary(commit_files):
    repo = commit_files(
        {
            "api.py": "def connect(timeout=60): pass\ndef connect(timeout=30): pass\n",
            "README.md": "## `api.connect`\n\n`timeout` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    facts = [item for item in report.facts if item.property == "timeout"]
    assert len(facts) == 2
    assert all(item.value_state == "UNKNOWN" for item in facts)
    assert report.judgments[0].decision == "UNCERTAIN"


@pytest.mark.parametrize(
    "exporter",
    ["from impl import *", "from impl import connect\nconnect = runtime_wrapper"],
)
def test_unsafe_cross_file_exports_are_not_resolved(commit_files, exporter):
    repo = commit_files(
        {
            "impl.py": "def connect(timeout=60): pass\n",
            "api.py": exporter + "\n",
            "README.md": "## `api.connect`\n\n`timeout` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.judgments[0].decision == "UNCERTAIN"
    assert not [item for item in report.facts if item.subject == "api.connect"]
    assert not report.findings


def test_dynamic_call_unpacking_is_never_simplified_to_a_valid_call(commit_files):
    repo = commit_files(
        {
            "api.py": "def connect(required): pass\n",
            "README.md": "```python\nfrom api import connect\nconnect(*args, **kwargs)\n```\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    call = next(item for item in report.claims if item.subject == "api.connect")
    judgment = next(item for item in report.judgments if item.claim_id == call.claim_id)
    assert judgment.decision == "UNCERTAIN"
    assert judgment.reason_code == "DYNAMIC_CALL"
    assert not report.findings


def test_fact_provenance_points_back_to_the_exact_blob(commit_files):
    source = "def connect(\n    timeout: int = 60,\n    label: str | None = None,\n):\n    pass\n"
    repo = commit_files({"api.py": source, "README.md": "# API\n"})
    snapshot = analyze(RepoSpec(repo=repo), ScanConfig())
    extracted = extract_code(snapshot)
    entities = {item.entity_id: item for item in extracted.entities}
    raw = source.encode()

    for fact in extracted.facts:
        assert fact.entity_id in entities
        assert fact.span.path == "api.py"
        assert fact.span.blob_hash == hashlib.sha256(raw).hexdigest()
        assert raw[fact.span.start_byte : fact.span.end_byte].decode() == fact.expression
        assert fact.span.start_line <= fact.span.end_line
        assert fact.subject == entities[fact.entity_id].qualified_name


def test_defaults_distinguish_types_none_absent_and_unknown(commit_files):
    repo = commit_files(
        {
            "api.py": (
                "def configure(required, none=None, flag=False, count=0, ratio=0.0, "
                "text='', items=[], dynamic=factory()):\n    pass\n"
            )
        }
    )
    extracted = extract_code(analyze(RepoSpec(repo=repo), ScanConfig()))
    entity = next(item for item in extracted.entities if item.qualified_name == "api.configure")
    parameters = {item.name: item for item in entity.signature}
    facts = {item.property: item for item in extracted.facts if item.fact_kind == "DEFAULT_VALUE"}

    assert parameters["required"].required
    assert parameters["required"].value_state == "ABSENT"
    assert "required" not in facts
    assert parameters["none"].value_state == "KNOWN"
    assert parameters["none"].typed_value.type == "NoneType"
    assert parameters["dynamic"].value_state == "UNKNOWN"
    assert parameters["dynamic"].typed_value is None
    assert facts["dynamic"].value_state == "UNKNOWN"
    assert facts["dynamic"].expression == "factory()"
    assert {
        name: parameters[name].typed_value.type
        for name in ("flag", "count", "ratio", "text", "items")
    } == {
        "flag": "bool",
        "count": "int",
        "ratio": "float",
        "text": "str",
        "items": "list",
    }
    assert parameters["flag"].typed_value != parameters["count"].typed_value


def test_safe_direct_and_chained_exports_keep_original_evidence(commit_files):
    repo = commit_files(
        {
            "impl.py": "def connect(timeout=60): pass\n",
            "api.py": "from impl import connect as open_connection\n",
            "facade.py": "from api import open_connection as connect\n",
            "README.md": (
                "## `facade.connect`\n\n`timeout` defaults to `30`.\n\n"
                "```python\nfrom facade import connect\nconnect()\n```\n"
            ),
        }
    )
    report = scan(RepoSpec(repo=repo))
    exported = [item for item in report.facts if item.subject == "facade.connect"]
    assert {item.fact_kind for item in exported} == {"DEFAULT_VALUE", "SIGNATURE"}
    assert all(item.span.path == "impl.py" for item in exported)
    assert all(item.entity_id == exported[0].entity_id for item in exported)
    owner = next(item for item in report.entities if item.entity_id == exported[0].entity_id)
    assert owner.qualified_name == "impl.connect"
    assert report.confirmed_count == 1
    call = next(item for item in report.claims if item.kind == "CALL_EXAMPLE")
    judgment = next(item for item in report.judgments if item.claim_id == call.claim_id)
    assert judgment.decision == "CONSISTENT"
    assert report.findings[0].evidence.code.path == "impl.py"


def test_safe_relative_export_is_supported(commit_files):
    repo = commit_files(
        {
            "pkg/impl.py": "def connect(timeout=60): pass\n",
            "pkg/api.py": "from .impl import connect\n",
            "README.md": "## `pkg.api.connect`\n\n`timeout` defaults to `30`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 1
    assert report.findings[0].evidence.code.path == "pkg/impl.py"
    assert any(item.subject == "pkg.api.connect" for item in report.facts)


def test_package_init_export_uses_public_package_name(commit_files):
    repo = commit_files(
        {
            "pkg/impl.py": "def connect(timeout=60): pass\n",
            "pkg/__init__.py": "from .impl import connect\n",
            "README.md": "## `pkg.connect`\n\n`timeout` defaults to `30`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.confirmed_count == 1
    assert report.findings[0].evidence.code.path == "pkg/impl.py"
    assert any(item.subject == "pkg.connect" for item in report.facts)
    assert not any(item.subject.startswith("pkg.__init__") for item in report.facts)


@pytest.mark.parametrize(
    "expression",
    ["{**other, 'timeout': 60}", "{dynamic_key(): 30, 'timeout': 60}"],
)
def test_explicit_dict_key_after_dynamic_entries_is_known(commit_files, expression):
    repo = commit_files(
        {
            "settings.py": "CONFIG = " + expression + "\n",
            "README.md": "## config `settings.CONFIG`\n\n`timeout` defaults to `30`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    fact = next(item for item in report.facts if item.property == "timeout")
    assert fact.value_state == "KNOWN"
    assert report.judgments[0].decision == "INCONSISTENT"
    assert report.confirmed_count == 1


def test_receivers_and_parameter_kinds_are_preserved(commit_files):
    repo = commit_files(
        {
            "api.py": (
                "class Client:\n"
                "    def instance(self, value, /, option=None): pass\n"
                "    @classmethod\n"
                "    def build(cls, *, required): pass\n"
                "    @staticmethod\n"
                "    def utility(*args, **kwargs): pass\n"
            )
        }
    )
    extracted = extract_code(analyze(RepoSpec(repo=repo), ScanConfig()))
    signatures = {item.subject: item for item in extracted.facts if item.fact_kind == "SIGNATURE"}
    assert signatures["api.Client.instance"].receiver == "instance"
    assert signatures["api.Client.build"].receiver == "class"
    assert signatures["api.Client.utility"].receiver == "none"
    assert [item.kind for item in signatures["api.Client.instance"].parameters] == [
        "POSITIONAL_ONLY",
        "POSITIONAL_ONLY",
        "POSITIONAL_OR_KEYWORD",
    ]
    assert [item.kind for item in signatures["api.Client.build"].parameters] == [
        "POSITIONAL_OR_KEYWORD",
        "KEYWORD_ONLY",
    ]
    assert [item.kind for item in signatures["api.Client.utility"].parameters] == [
        "VAR_POSITIONAL",
        "VAR_KEYWORD",
    ]


def test_same_named_symbols_remain_ambiguous(commit_files):
    repo = commit_files(
        {
            "one.py": "def connect(timeout=60): pass\n",
            "two.py": "def connect(timeout=60): pass\n",
            "README.md": "## `connect`\n\n`timeout` defaults to `60`.\n",
        }
    )
    report = scan(RepoSpec(repo=repo))
    assert report.candidates[0].ambiguity
    assert report.judgments[0].decision == "UNCERTAIN"
    assert not report.findings


def test_fact_ids_are_stable_across_repeated_scans_and_unrelated_commits(commit_files):
    repo = commit_files(
        {
            "api.py": "def connect(timeout=60): pass\n",
            "README.md": "# First\n",
        }
    )
    first = scan(RepoSpec(repo=repo))
    repeated = scan(RepoSpec(repo=repo))
    commit_files({"README.md": "# Second\n"})
    new_head = scan(RepoSpec(repo=repo))

    def identities(report):
        return sorted(
            (
                item.fact_id,
                item.entity_id,
                item.subject,
                item.property,
                item.span.path,
                item.span.start_byte,
                item.span.end_byte,
                item.span.blob_hash,
            )
            for item in report.facts
        )

    assert identities(first) == identities(repeated) == identities(new_head)
    assert first.snapshot.head_sha != new_head.snapshot.head_sha
