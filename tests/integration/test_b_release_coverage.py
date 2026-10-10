"""Member B closeout: conservative coverage for the candidate-v1 gaps."""

from docsync.config import RepoSpec
from docsync.pipeline import scan


def decisions(report):
    claims = {claim.claim_id: claim for claim in report.claims}
    return {
        (claims[item.claim_id].subject, claims[item.claim_id].predicate): item
        for item in report.judgments
    }


def test_constructor_defaults_are_public_static_facts(commit_files):
    repo = commit_files(
        {
            "api.py": (
                "class PageReader:\n"
                "    def __init__(self, encoding: str = 'utf-8'):\n"
                "        self.encoding = encoding\n\n"
                "class MemoryBuffer:\n"
                "    def __init__(self, capacity=None):\n"
                "        self.capacity = 32 if capacity is None else capacity\n"
            ),
            "README.md": (
                "## `PageReader.__init__`\n\n`encoding` defaults to `utf-16`.\n\n"
                "## `MemoryBuffer.__init__`\n\n`capacity` defaults to `None`.\n"
            ),
        }
    )

    report = scan(RepoSpec(repo=repo))
    result = decisions(report)

    assert result[("PageReader.__init__", "encoding")].decision == "INCONSISTENT"
    assert result[("MemoryBuffer.__init__", "capacity")].decision == "CONSISTENT"
    constructors = {
        fact.subject for fact in report.facts if fact.property in {"encoding", "capacity"}
    }
    assert constructors == {"api.PageReader.__init__", "api.MemoryBuffer.__init__"}


def test_definition_time_literals_expand_only_when_statically_provable(commit_files):
    repo = commit_files(
        {
            "api.py": (
                "BATCH_LIMIT = 12\n"
                "def read_batch(limit=BATCH_LIMIT): return limit\n"
                "BATCH_LIMIT = 24\n\n"
                "def choose_format(): return 'json'\n"
                "def export_records(format_name=choose_format()): return format_name\n\n"
                "def environment_format(): return env()\n"
                "def dynamic_export(format_name=environment_format()): return format_name\n\n"
                "def encode_packet(payload, codec='latin-1'): return payload, codec\n"
                "encode_packet.__defaults__ = ('utf-8',)\n"
            ),
            "README.md": (
                "## `read_batch`\n\n`limit` defaults to `24`.\n\n"
                "## `export_records`\n\n`format_name` defaults to `json`.\n\n"
                "## `dynamic_export`\n\n`format_name` defaults to `json`.\n\n"
                "## `encode_packet`\n\n`codec` defaults to `utf-8`.\n"
            ),
        }
    )

    report = scan(RepoSpec(repo=repo))
    result = decisions(report)

    assert result[("read_batch", "limit")].decision == "INCONSISTENT"
    assert result[("export_records", "format_name")].decision == "CONSISTENT"
    assert result[("dynamic_export", "format_name")].decision == "UNCERTAIN"
    assert result[("encode_packet", "codec")].decision == "UNCERTAIN"
    assert {item.code for item in report.manifest.diagnostics} == {"DYNAMIC_FUNCTION"}


def test_literal_call_unpacking_is_bound_but_runtime_unpacking_abstains(commit_files):
    repo = commit_files(
        {
            "api.py": (
                "def attach_volume(name, *, readonly): return name, readonly\n"
                "def send_notice(address, *, channel): return address, channel\n"
                "def place_marker(x, y, /, *, color='red'): return x, y, color\n"
                "def queue_notice(topic, *, priority): return topic, priority\n"
                "def read_options(): return runtime_options()\n"
            ),
            "README.md": (
                "```python\n"
                "from api import attach_volume\n"
                "options = {'readonly': True}\n"
                "attach_volume('logs', **options)\n"
                "```\n\n"
                "```python\n"
                "from api import send_notice\n"
                "arguments = ('ops@example.invalid', 'email')\n"
                "send_notice(*arguments)\n"
                "```\n\n"
                "```python\n"
                "from api import place_marker\n"
                "position = (3, 7)\n"
                "style = {'color': 'blue'}\n"
                "place_marker(*position, **style)\n"
                "```\n\n"
                "```python\n"
                "from api import queue_notice, read_options\n"
                "queue_notice('maintenance', **read_options())\n"
                "```\n"
            ),
        }
    )

    report = scan(RepoSpec(repo=repo))
    call_results = {
        claim.subject: next(item for item in report.judgments if item.claim_id == claim.claim_id)
        for claim in report.claims
        if claim.kind == "CALL_EXAMPLE"
        and claim.subject
        in {
            "api.attach_volume",
            "api.send_notice",
            "api.place_marker",
            "api.queue_notice",
        }
    }

    assert call_results["api.attach_volume"].reason_code == "CALL_ACCEPTED"
    assert call_results["api.send_notice"].reason_code == "CALL_BINDING_ERROR"
    assert call_results["api.place_marker"].reason_code == "CALL_ACCEPTED"
    assert call_results["api.queue_notice"].reason_code == "DYNAMIC_CALL"


def test_sequential_and_nested_config_updates_keep_final_static_values(commit_files):
    repo = commit_files(
        {
            "settings.py": (
                "RETRY_WINDOW: int = 6\n"
                "RETRY_WINDOW = 14\n"
                "PORT: int = 8020\n"
                "PORT += 3\n"
                "SERVICE_OPTIONS = {'workers': 2}\n"
                "SERVICE_OPTIONS.update({'workers': 6})\n"
                "PIPELINE = {'export': {'compression': 'gzip', 'level': 3}}\n"
                "STORAGE = {'local': {'root': env()}}\n"
                "CACHE = dict(enabled=True, capacity=128)\n"
            ),
            "README.md": (
                "## `settings`\n\n`RETRY_WINDOW` defaults to `6`.\n\n"
                "## `settings`\n\n`PORT` defaults to `8023`.\n\n"
                "## `settings.SERVICE_OPTIONS`\n\n`workers` defaults to `6`.\n\n"
                "## `settings.PIPELINE.export`\n\n`compression` defaults to `zstd`.\n\n"
                "## `settings.STORAGE.local`\n\n`root` defaults to `./cache`.\n\n"
                "## `settings.CACHE`\n\n`enabled` defaults to `True`.\n"
            ),
        }
    )

    report = scan(RepoSpec(repo=repo))
    result = decisions(report)

    assert result[("settings", "RETRY_WINDOW")].decision == "INCONSISTENT"
    assert result[("settings", "PORT")].decision == "CONSISTENT"
    assert result[("settings.SERVICE_OPTIONS", "workers")].decision == "CONSISTENT"
    assert result[("settings.PIPELINE.export", "compression")].decision == "INCONSISTENT"
    assert result[("settings.STORAGE.local", "root")].decision == "UNCERTAIN"
    assert result[("settings.CACHE", "enabled")].decision == "CONSISTENT"


def test_dynamic_config_mutations_and_shadowed_dict_stay_unknown(commit_files):
    repo = commit_files(
        {
            "settings.py": (
                "OPTIONS = {'workers': 2}\n"
                "OPTIONS.update(runtime_options())\n"
                "PORT = 8000\n"
                "PORT += runtime_offset()\n"
                "dict = factory()\n"
                "CACHE = dict(enabled=True)\n"
            ),
            "README.md": (
                "## `settings.OPTIONS`\n\n`workers` defaults to `2`.\n\n"
                "## `settings`\n\n`PORT` defaults to `8000`.\n\n"
                "## `settings.CACHE`\n\n`enabled` defaults to `True`.\n"
            ),
        }
    )

    report = scan(RepoSpec(repo=repo))
    result = decisions(report)

    assert result[("settings.OPTIONS", "workers")].decision == "UNCERTAIN"
    assert result[("settings", "PORT")].decision == "UNCERTAIN"
    assert result[("settings.CACHE", "enabled")].decision == "UNCERTAIN"
