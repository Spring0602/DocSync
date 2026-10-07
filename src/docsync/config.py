"""Explicit configuration; target repositories cannot load executable plugins."""

import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field

from docsync.models import Model


class ScanOptions(Model):
    mode: Literal["rules", "hybrid"] = "rules"
    fail_on: Literal["none", "warning"] = "none"
    require_complete: bool = False
    analysis_method: Literal["full", "rules", "llm", "no_alignment", "no_verifier", "no_static"] = (
        "full"
    )
    include: list[str] = Field(default_factory=lambda: ["**/*.py", "**/*.md"])
    exclude: list[str] = Field(default_factory=list)
    max_file_bytes: int = Field(default=1048576, ge=1, le=10485760)
    max_total_bytes: int = Field(default=52428800, ge=1, le=524288000)


class AlignmentOptions(Model):
    top_k: int = Field(default=5, ge=1, le=100)


class LLMOptions(Model):
    provider: Literal["none", "chat-completions"] = "none"
    endpoint: str | None = None
    model: str | None = None
    api_key_env: str = "DOCSYNC_API_KEY"
    temperature: float | None = Field(default=0, ge=0, le=2)
    send_temperature: bool = True
    thinking: Literal["enabled", "disabled"] | None = None
    response_format: Literal["json_schema", "json_object"] = "json_schema"
    token_parameter: Literal["max_completion_tokens", "max_tokens"] = "max_completion_tokens"
    max_output_tokens: int = Field(default=1024, ge=64, le=16384)
    max_input_bytes: int = Field(default=32000, ge=256, le=262144)
    max_total_tokens: int = Field(default=100000, ge=1)
    cache_dir: Path | None = None
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_requests: int = Field(default=20, ge=0, le=1000)


class IgnoreRule(Model):
    finding_id: str | None = None
    rule_id: str | None = None
    path: str = "**/*.md"
    reason: str = Field(min_length=1)
    expires: date | None = None


class ScanConfig(Model):
    scan: ScanOptions = Field(default_factory=ScanOptions)
    alignment: AlignmentOptions = Field(default_factory=AlignmentOptions)
    llm: LLMOptions = Field(default_factory=LLMOptions)
    ignores: list[IgnoreRule] = Field(default_factory=list)


class RepoSpec(Model):
    repo: Path
    head: str = "HEAD"
    base: str | None = None
    working_tree: bool = False


def load_config(path: Path | None) -> ScanConfig:
    if path is None:
        return ScanConfig()
    with path.open("rb") as stream:
        return ScanConfig.model_validate(tomllib.load(stream))
