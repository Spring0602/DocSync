"""Offline, read-only readiness checks that can run without runtime dependencies."""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlsplit

from docsync import __version__

if TYPE_CHECKING:
    from docsync.config import ScanConfig

CheckStatus = Literal["OK", "WARN", "ERROR", "SKIP"]


@dataclass(frozen=True)
class DoctorCheck:
    code: str
    status: CheckStatus
    message: str
    action: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def status(self) -> str:
        if any(check.status == "ERROR" for check in self.checks):
            return "ERROR"
        if any(check.status == "WARN" for check in self.checks):
            return "WARN"
        return "OK"

    @property
    def exit_code(self) -> int:
        return 2 if self.status == "ERROR" else 0

    def to_dict(self) -> dict[str, object]:
        return {
            "doctor_schema_version": "1.0",
            "docsync_version": __version__,
            "status": self.status,
            "read_only": True,
            "network_checked": False,
            "checks": [asdict(check) for check in self.checks],
        }


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    # status normally refreshes the index; optional locks and fsmonitor are disabled
    # so this preflight neither writes the index nor invokes a configured helper.
    return subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
        capture_output=True,
        check=False,
        timeout=10,
    )


def _repository_checks(repo: Path) -> list[DoctorCheck]:
    try:
        if not repo.is_dir():
            return [
                DoctorCheck(
                    "REPO_PATH",
                    "ERROR",
                    "Repository directory does not exist or is not readable.",
                    "Pass --repo with the path to an existing Git repository root.",
                )
            ]
        root = _git("-C", str(repo), "rev-parse", "--show-toplevel")
        if root.returncode:
            return [
                DoctorCheck(
                    "REPO_ROOT",
                    "ERROR",
                    "Cannot read a Git working tree at this location.",
                    "Use a local Git clone; a downloaded ZIP has no commit history. "
                    "Check repository ownership if this is already a clone.",
                )
            ]
        if Path(os.fsdecode(root.stdout).strip()).resolve() != repo.resolve():
            return [
                DoctorCheck(
                    "REPO_ROOT",
                    "ERROR",
                    "The selected path is inside a repository, not its root.",
                    "Pass the Git repository root to --repo.",
                )
            ]
        checks = [DoctorCheck("REPO_ROOT", "OK", "Repository root is readable.")]
        head = _git("-C", str(repo), "rev-parse", "--verify", "HEAD^{commit}")
        if head.returncode:
            checks.append(
                DoctorCheck(
                    "REPO_HEAD",
                    "ERROR",
                    "HEAD does not resolve to a commit.",
                    "Select a repository with an existing commit before scanning.",
                )
            )
        else:
            checks.append(DoctorCheck("REPO_HEAD", "OK", "HEAD resolves to a committed snapshot."))
        status = _git("-C", str(repo), "status", "--porcelain", "--untracked-files=normal")
        if status.returncode:
            checks.append(
                DoctorCheck("REPO_WORKTREE", "ERROR", "Cannot inspect working-tree state.")
            )
        elif status.stdout:
            checks.append(
                DoctorCheck(
                    "REPO_WORKTREE",
                    "WARN",
                    "Uncommitted or untracked files are present.",
                    "Default scans read committed files only; use --working-tree when "
                    "you intend to include local changes.",
                )
            )
        else:
            checks.append(DoctorCheck("REPO_WORKTREE", "OK", "Working tree is clean."))
        return checks
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return [
            DoctorCheck(
                "REPO_READ",
                "ERROR",
                "Repository check failed or timed out.",
                "Check local access permissions and retry with a readable Git root.",
            )
        ]


def _model_checks(cfg: ScanConfig) -> list[DoctorCheck]:
    # Match evaluate_snapshot: explicit model-only ablations override mode="rules".
    method = cfg.scan.analysis_method
    wants_model = (cfg.scan.mode == "hybrid" and method != "rules") or method in {
        "llm",
        "no_static",
    }
    if not wants_model:
        return [DoctorCheck("MODEL", "OK", "Rules mode needs no model service or API key.")]
    if cfg.llm.provider != "chat-completions" or not cfg.llm.endpoint or not cfg.llm.model:
        return [
            DoctorCheck(
                "MODEL_CONFIG",
                "WARN",
                "The selected analysis requires a model, but its configuration is incomplete.",
                "Configure provider, endpoint and model, or set scan.mode and "
                "scan.analysis_method to rules for offline analysis. "
                "Unavailable model judgments remain uncertain.",
            )
        ]
    try:
        endpoint = urlsplit(cfg.llm.endpoint)
        valid_endpoint = (
            bool(endpoint.hostname)
            and not any((endpoint.username, endpoint.password, endpoint.query, endpoint.fragment))
            and (
                endpoint.scheme == "https"
                or (
                    endpoint.scheme == "http"
                    and endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
                )
            )
        )
    except ValueError:
        valid_endpoint = False
    if not valid_endpoint:
        return [
            DoctorCheck(
                "MODEL_ENDPOINT",
                "ERROR",
                "Model endpoint does not satisfy the provider policy.",
                "Use HTTPS (or HTTP on localhost), without credentials, query or fragment.",
            )
        ]
    if not os.environ.get(cfg.llm.api_key_env):
        return [
            DoctorCheck(
                "MODEL_KEY",
                "WARN",
                "The configured API key environment variable is not set.",
                "Set the variable named by llm.api_key_env, or set scan.mode and "
                "scan.analysis_method to rules for offline analysis. "
                "Do not put secrets in the report or TOML file.",
            )
        ]
    return [
        DoctorCheck(
            "MODEL", "OK", "Model settings and an API key are present; service not contacted."
        )
    ]


def check_environment(repo: Path | None = None, config: Path | None = None) -> DoctorReport:
    checks: list[DoctorCheck] = []
    supported_python = sys.version_info[:2] == (3, 12)
    checks.append(
        DoctorCheck(
            "PYTHON",
            "OK" if supported_python else "ERROR",
            f"Python {sys.version_info.major}.{sys.version_info.minor}; supported version is 3.12.",
            None
            if supported_python
            else "Create an environment with Python 3.12 and install DocSync.",
        )
    )
    dependencies_ok = True
    for distribution, module, expected in (
        ("pydantic", "pydantic", "2.11.7"),
        ("markdown-it-py", "markdown_it", "3.0.0"),
    ):
        try:
            installed = metadata.version(distribution)
            importlib.import_module(module)
        except (ImportError, metadata.PackageNotFoundError):
            dependencies_ok = False
            checks.append(
                DoctorCheck(
                    "DEPENDENCY_" + module.upper(),
                    "ERROR",
                    f"Required dependency {distribution} is missing or cannot be imported.",
                    "Install DocSync with its declared dependencies in this Python environment.",
                )
            )
            continue
        checks.append(
            DoctorCheck(
                "DEPENDENCY_" + module.upper(),
                "OK" if installed == expected else "WARN",
                f"{distribution} {installed}; project pins {expected}.",
                None
                if installed == expected
                else "Use the pinned dependencies for release checks.",
            )
        )
    git_ready = False
    if shutil.which("git"):
        try:
            git_ready = _git("--version").returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass
    checks.append(
        DoctorCheck(
            "GIT",
            "OK" if git_ready else "ERROR",
            "Git is available." if git_ready else "Git is missing, cannot start, or timed out.",
            None if git_ready else "Install Git, add it to PATH, and open a new terminal.",
        )
    )
    if repo is None:
        checks.append(
            DoctorCheck("REPO", "SKIP", "No --repo supplied; repository was not checked.")
        )
    elif git_ready:
        checks.extend(_repository_checks(repo))
    else:
        checks.append(DoctorCheck("REPO", "SKIP", "Repository check requires working Git."))
    if dependencies_ok:
        try:
            from docsync.config import load_config

            cfg = load_config(config)
        except (ImportError, OSError, ValueError):
            checks.append(
                DoctorCheck(
                    "CONFIG",
                    "ERROR",
                    "Cannot read or validate the explicit TOML configuration.",
                    "Check file access, TOML syntax and supported field names. "
                    "Configuration contents are not printed.",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    "CONFIG",
                    "OK",
                    "Explicit TOML configuration is valid."
                    if config is not None
                    else "Built-in rules configuration selected; local TOML files are not auto-loaded.",
                )
            )
            checks.extend(_model_checks(cfg))
    else:
        checks.append(
            DoctorCheck("CONFIG", "SKIP", "Install runtime dependencies to validate config.")
        )
    return DoctorReport(checks)


def render_text(report: DoctorReport) -> str:
    lines = [f"DocSync {__version__} - local readiness checks", ""]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.code}: {check.message}")
        if check.action:
            lines.append(f"       Next: {check.action}")
    errors = sum(check.status == "ERROR" for check in report.checks)
    warnings = sum(check.status == "WARN" for check in report.checks)
    lines.extend(
        [
            "",
            f"Result: {report.status} ({errors} errors, {warnings} warnings).",
            "Read-only checks; no scan, model request, repository change, or network test was performed.",
        ]
    )
    return "\n".join(lines)
