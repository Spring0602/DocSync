"""Bounded Chat Completions adapter; all repository content is untrusted data."""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from docsync.config import LLMOptions
from docsync.llm import validate_response
from docsync.llm.prompts import PROMPT_VERSION, SYSTEM_PROMPT
from docsync.models import CodeFact, Diagnostic, DocumentClaim, JudgeResult
from docsync.utils import digest, stable_id


class ProviderError(Exception):
    def __init__(self, code: str, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def http_transport(endpoint: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            result = response.read(2 * 1024 * 1024 + 1)
            if len(result) > 2 * 1024 * 1024:
                raise ProviderError("RESPONSE_TOO_LARGE")
            return result
    except urllib.error.HTTPError as exc:
        raise ProviderError(
            "RATE_LIMIT" if exc.code == 429 else f"HTTP_{exc.code}",
            exc.code in {429, 500, 502, 503, 504},
        ) from None
    except (TimeoutError, urllib.error.URLError, OSError):
        raise ProviderError("MODEL_TIMEOUT_OR_NETWORK_ERROR", True) from None


def strict_schema() -> dict[str, Any]:
    schema = JudgeResult.model_json_schema()

    def tighten(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            if value.get("type") == "object":
                value["required"] = list(value.get("properties", {}))
                value["additionalProperties"] = False
            if "enum" in value:
                value["enum"] = [item for item in value["enum"] if item != "SKIPPED"]
            for child in value.values():
                tighten(child)
        elif isinstance(value, list):
            for child in value:
                tighten(child)

    tighten(schema)
    return schema


class ChatCompletionsProvider:
    def __init__(
        self,
        cfg: LLMOptions,
        transport: Callable[[str, dict[str, str], bytes, float], bytes] = http_transport,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if cfg.provider != "chat-completions" or not cfg.endpoint or not cfg.model:
            raise ProviderError("AI_UNAVAILABLE")
        endpoint = urllib.parse.urlsplit(cfg.endpoint)
        if (
            not endpoint.hostname
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
            or (
                endpoint.scheme != "https"
                and not (
                    endpoint.scheme == "http"
                    and endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
                )
            )
        ):
            raise ProviderError("UNSAFE_MODEL_ENDPOINT")
        self._key = os.environ.get(cfg.api_key_env, "")
        if not self._key:
            raise ProviderError("AI_UNAVAILABLE")
        self.cfg = cfg
        self.model_id = cfg.model
        self.endpoint = cfg.endpoint
        self.transport = transport
        self.sleep = sleep
        self.usage = {
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hits": 0,
            "reserved_tokens": 0,
            "unknown_usage_requests": 0,
        }
        self.calls: list[dict[str, str | int | float | bool | None]] = []
        self.diagnostics: list[Diagnostic] = []

    def judge(self, claim: DocumentClaim, facts: list[CodeFact]) -> JudgeResult:
        content = json.dumps(
            {
                "claim": claim.model_dump(mode="json"),
                "facts": [fact.model_dump(mode="json") for fact in facts],
            },
            ensure_ascii=False,
        )
        return self._request(claim, facts, content)

    def judge_raw(
        self, claim: DocumentClaim, facts: list[CodeFact], code: dict[str, str]
    ) -> JudgeResult:
        """Pure-LLM baseline: no structured values/parameters, only fixed raw evidence."""
        content = json.dumps(
            {
                "claim_id": claim.claim_id,
                "document": claim.quote,
                "allowed_facts": [{"fact_id": f.fact_id, "path": f.span.path} for f in facts],
                "code": code,
            },
            ensure_ascii=False,
        )
        return self._request(claim, facts, content)

    def _request(self, claim: DocumentClaim, facts: list[CodeFact], content: str) -> JudgeResult:
        schema = strict_schema()
        response_format: dict[str, Any] = {"type": self.cfg.response_format}
        if self.cfg.response_format == "json_schema":
            response_format["json_schema"] = {
                "name": "docsync_judgment",
                "strict": True,
                "schema": schema,
            }
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT + "\nRequired JSON schema: " + json.dumps(schema),
                },
                {"role": "user", "content": content},
            ],
            "response_format": response_format,
            self.cfg.token_parameter: self.cfg.max_output_tokens,
            "stream": False,
        }
        if self.cfg.send_temperature and self.cfg.temperature is not None:
            payload["temperature"] = self.cfg.temperature
        if self.cfg.thinking is not None:
            payload["thinking"] = {"type": self.cfg.thinking}
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        if len(body) > self.cfg.max_input_bytes:
            raise ProviderError("CONTEXT_BUDGET_EXCEEDED")
        allowed_ids = {fact.fact_id for fact in facts}
        key = digest(self.endpoint.encode() + PROMPT_VERSION.encode() + body)
        cache = self.cfg.cache_dir / (key + ".json") if self.cfg.cache_dir else None
        if cache and cache.is_file():
            try:
                result = validate_response(cache.read_text(encoding="utf-8"), claim, allowed_ids)
            except (ValueError, OSError):
                self.diagnostics.append(
                    Diagnostic(
                        code="CACHE_INVALID",
                        message="Invalid cached response ignored",
                        stage="judge",
                        affects_completeness=False,
                    )
                )
            else:
                self.usage["cache_hits"] += 1
                self.calls.append(
                    {
                        "request_hash": key,
                        "cache_hit": True,
                        "status": "CACHED",
                        "prompt_version": PROMPT_VERSION,
                        "model": self.model_id,
                    }
                )
                return result
        for attempt in range(self.cfg.max_retries + 1):
            # Byte-length + output allowance is a conservative local reservation, not measured usage.
            reserve = len(body) + self.cfg.max_output_tokens + 1024
            if (
                self.usage["requests"] >= self.cfg.max_requests
                or self.usage["reserved_tokens"] + reserve > self.cfg.max_total_tokens
            ):
                raise ProviderError("MODEL_BUDGET_EXHAUSTED")
            self.usage["requests"] += 1
            self.usage["reserved_tokens"] += reserve
            started = time.perf_counter()
            entry: dict[str, str | int | float | bool | None] = {
                "request_hash": key,
                "attempt": attempt + 1,
                "cache_hit": False,
                "model": self.model_id,
                "prompt_version": PROMPT_VERSION,
            }
            usage_known = False
            try:
                raw = self.transport(
                    self.endpoint,
                    {"Authorization": "Bearer " + self._key, "Content-Type": "application/json"},
                    body,
                    self.cfg.timeout_seconds,
                )
                # Never persist an echoed credential, even if a faulty upstream returns one.
                safe_raw = raw.decode("utf-8").replace(self._key, "[REDACTED]")
                entry["response_hash"] = digest(safe_raw.encode())
                parsed = json.loads(safe_raw)
                entry["returned_model"] = (
                    parsed.get("model") if isinstance(parsed.get("model"), str) else None
                )
                usage = parsed.get("usage", {})
                input_tokens, output_tokens = (
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                )
                if (
                    type(input_tokens) is not int
                    or type(output_tokens) is not int
                    or min(input_tokens, output_tokens) < 0
                ):
                    raise ProviderError("USAGE_MISSING")
                usage_known = True
                self.usage["input_tokens"] += input_tokens
                self.usage["output_tokens"] += output_tokens
                self.usage["reserved_tokens"] += max(0, input_tokens + output_tokens - reserve)
                entry.update({"input_tokens": input_tokens, "output_tokens": output_tokens})
                choice = parsed["choices"][0]
                if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
                    raise ProviderError("MODEL_REFUSED_OR_TRUNCATED")
                if choice["message"].get("tool_calls"):
                    raise ProviderError("UNEXPECTED_TOOL_CALL")
                result = validate_response(choice["message"]["content"], claim, allowed_ids)
                result = result.model_copy(
                    update={"model_run_id": stable_id(key, str(self.usage["requests"]))}
                )
                entry["status"] = "SUCCEEDED"
                if cache:
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    temporary = cache.with_suffix(".tmp")
                    temporary.write_text(result.model_dump_json(), encoding="utf-8")
                    temporary.replace(cache)
                return result
            except (ValueError, KeyError, IndexError, TypeError, AttributeError, OSError):
                entry["status"] = "INVALID_MODEL_RESPONSE"
                raise ProviderError("INVALID_MODEL_RESPONSE") from None
            except ProviderError as exc:
                entry["status"] = exc.code
                if not exc.retryable or attempt == self.cfg.max_retries:
                    raise
                self.sleep(min(2**attempt, 4))
            finally:
                if not usage_known:
                    self.usage["unknown_usage_requests"] += 1
                entry["elapsed_seconds"] = round(time.perf_counter() - started, 6)
                self.calls.append(entry)
        raise ProviderError("MODEL_RETRIES_EXHAUSTED")
