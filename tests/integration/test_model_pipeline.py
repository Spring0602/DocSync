import json

from docsync.config import LLMOptions, RepoSpec, ScanConfig, ScanOptions
from docsync.llm.provider import ChatCompletionsProvider, ProviderError
from docsync.models import JudgeResult
from docsync.pipeline import scan


def test_hybrid_real_adapter_with_controlled_transport(commit_files, monkeypatch):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    monkeypatch.setenv("DOCSYNC_TEST_KEY", "controlled")
    cfg = ScanConfig(
        scan=ScanOptions(mode="hybrid"),
        llm=LLMOptions(
            provider="chat-completions",
            endpoint="https://example.invalid/v1/chat/completions",
            model="test-only",
            api_key_env="DOCSYNC_TEST_KEY",
        ),
    )

    def transport(endpoint, headers, body, timeout):
        content = json.loads(json.loads(body)["messages"][1]["content"])
        judgment = JudgeResult(
            claim_id=content["claim"]["claim_id"],
            decision="INCONSISTENT",
            fact_ids=[content["facts"][0]["fact_id"]],
            reason_code="TEST",
            reason_text="Controlled fixture",
        )
        return json.dumps(
            {
                "choices": [
                    {"finish_reason": "stop", "message": {"content": judgment.model_dump_json()}}
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 30},
            }
        ).encode()

    provider = ChatCompletionsProvider(cfg.llm, transport)
    report = scan(RepoSpec(repo=repo), cfg, provider)
    assert report.confirmed_count == 1 and report.manifest.status == "COMPLETED"
    assert report.manifest.usage["requests"] == 1  # Patch rescan does not call the model.
    assert report.manifest.model_calls[0]["status"] == "SUCCEEDED"


def test_model_timeout_is_partial_uncertain(commit_files, monkeypatch):
    repo = commit_files(
        {"api.py": "def f(x=60): pass\n", "README.md": "## `f`\n`x` defaults to `30`.\n"}
    )
    monkeypatch.setenv("DOCSYNC_TEST_KEY", "controlled")
    cfg = ScanConfig(
        scan=ScanOptions(mode="hybrid"),
        llm=LLMOptions(
            provider="chat-completions",
            endpoint="https://example.invalid/v1/chat/completions",
            model="test-only",
            api_key_env="DOCSYNC_TEST_KEY",
            max_retries=0,
        ),
    )

    def timeout(*args):
        raise ProviderError("MODEL_TIMEOUT_OR_NETWORK_ERROR", True)

    report = scan(RepoSpec(repo=repo), cfg, ChatCompletionsProvider(cfg.llm, timeout))
    assert report.manifest.status == "PARTIAL" and report.uncertain_count == 1
    assert report.confirmed_count == 0 and not report.patches
