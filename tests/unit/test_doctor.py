"""User-facing setup diagnostics and non-destructive patch export regressions."""

import json
import os
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pytest

from docsync import doctor
from docsync.cli import main

ARCHIVE = Path(__file__).parents[1] / "fixtures/reports/v1-default.json"
SOURCE = Path(__file__).parents[2] / "src"


@pytest.fixture
def healthy_environment(monkeypatch):
    version_info = namedtuple("VersionInfo", "major minor micro releaselevel serial")
    monkeypatch.setattr(sys, "version_info", version_info(3, 12, 14, "final", 0))
    monkeypatch.setattr(doctor.shutil, "which", lambda _: "git")
    monkeypatch.setattr(
        doctor.metadata,
        "version",
        lambda name: {"pydantic": "2.11.7", "markdown-it-py": "3.0.0"}[name],
    )
    monkeypatch.setattr(
        doctor, "_git", lambda *args: subprocess.CompletedProcess(args, 0, b"", b"")
    )


def check_by_code(report, code):
    return next(check for check in report.checks if check.code == code)


def test_default_doctor_text_and_json(healthy_environment, capsys):
    assert main(["doctor"]) == 0
    text = capsys.readouterr().out
    assert "[OK] PYTHON" in text
    assert "[SKIP] REPO" in text
    assert "no scan, model request" in text
    assert main(["doctor", "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["doctor_schema_version"] == "1.0"
    assert report["status"] == "OK"
    assert report["read_only"] is True
    assert report["network_checked"] is False


def test_unsupported_python_is_error(healthy_environment, monkeypatch):
    monkeypatch.setattr(sys, "version_info", sys.version_info._replace(minor=14))
    report = doctor.check_environment()
    assert check_by_code(report, "PYTHON").status == "ERROR"
    assert report.exit_code == 2


def test_missing_dependency_keeps_doctor_available(healthy_environment, monkeypatch):
    def missing(_name):
        raise doctor.metadata.PackageNotFoundError

    monkeypatch.setattr(doctor.metadata, "version", missing)
    report = doctor.check_environment()
    assert report.exit_code == 2
    assert check_by_code(report, "DEPENDENCY_PYDANTIC").status == "ERROR"
    assert check_by_code(report, "CONFIG").status == "SKIP"


def test_module_doctor_runs_without_site_packages():
    result = subprocess.run(
        [sys.executable, "-S", "-m", "docsync", "doctor", "--format", "json"],
        env={**os.environ, "PYTHONPATH": str(SOURCE)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["status"] == "ERROR"
    assert "Traceback" not in result.stderr
    assert any(check["code"] == "DEPENDENCY_PYDANTIC" for check in report["checks"])


def test_missing_git_skips_repo(healthy_environment, monkeypatch, tmp_path):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)
    report = doctor.check_environment(tmp_path)
    assert check_by_code(report, "GIT").status == "ERROR"
    assert check_by_code(report, "REPO").status == "SKIP"
    assert report.exit_code == 2


def test_git_timeout_is_structured(healthy_environment, monkeypatch):
    def timeout(*_args):
        raise subprocess.TimeoutExpired("git", 10)

    monkeypatch.setattr(doctor, "_git", timeout)
    report = doctor.check_environment()
    assert check_by_code(report, "GIT").status == "ERROR"


@pytest.mark.parametrize("content", ["not valid TOML = [", '[llm]\nsecret="do-not-print"'])
def test_invalid_config_does_not_echo_contents(healthy_environment, tmp_path, capsys, content):
    config = tmp_path / "private.toml"
    config.write_text(content, encoding="utf-8")
    assert main(["doctor", "--config", str(config), "--format", "json"]) == 2
    output = capsys.readouterr().out
    assert content not in output
    assert "do-not-print" not in output
    report = json.loads(output)
    assert (
        next(check for check in report["checks"] if check["code"] == "CONFIG")["status"] == "ERROR"
    )


def test_default_config_does_not_autoload_local_file(healthy_environment, monkeypatch, tmp_path):
    (tmp_path / "docsync.toml").write_text("bad input", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    report = doctor.check_environment()
    assert check_by_code(report, "CONFIG").status == "OK"
    assert check_by_code(report, "MODEL").status == "OK"


@pytest.mark.parametrize(
    "mode,method,expected",
    [
        ("rules", "llm", "WARN"),
        ("rules", "no_static", "WARN"),
        ("hybrid", "rules", "OK"),
        ("rules", "full", "OK"),
    ],
)
def test_doctor_model_requirement_matches_selected_analysis(
    healthy_environment, tmp_path, mode, method, expected
):
    config = tmp_path / "analysis.toml"
    config.write_text(f'[scan]\nmode="{mode}"\nanalysis_method="{method}"\n', encoding="utf-8")
    report = doctor.check_environment(config=config)
    check = check_by_code(report, "MODEL_CONFIG" if expected == "WARN" else "MODEL")
    assert check.status == expected
    if expected == "WARN":
        assert "requires a model" in check.message
        assert "scan.analysis_method" in check.action
    assert report.exit_code == 0


@pytest.mark.parametrize("has_key,expected", [(False, "WARN"), (True, "OK")])
def test_model_check_never_calls_service_or_prints_secrets(
    healthy_environment, monkeypatch, tmp_path, has_key, expected
):
    config = tmp_path / "hybrid.toml"
    config.write_text(
        '[scan]\nmode="hybrid"\n[llm]\nprovider="chat-completions"\n'
        'endpoint="https://example.invalid/v1/chat/completions"\nmodel="test"\n'
        'api_key_env="DOCSYNC_TEST_KEY"\n',
        encoding="utf-8",
    )
    if has_key:
        monkeypatch.setenv("DOCSYNC_TEST_KEY", "never-print-this-secret")
    else:
        monkeypatch.delenv("DOCSYNC_TEST_KEY", raising=False)

    def forbidden(*_args, **_kwargs):
        pytest.fail("doctor must not contact a model service")

    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    report = doctor.check_environment(config=config)
    assert report.status == expected
    assert report.exit_code == 0
    assert "never-print-this-secret" not in json.dumps(report.to_dict())
    assert "example.invalid" not in doctor.render_text(report)


def test_unsafe_model_endpoint_reported_without_echo(healthy_environment, tmp_path):
    config = tmp_path / "unsafe.toml"
    config.write_text(
        '[scan]\nmode="hybrid"\n[llm]\nprovider="chat-completions"\n'
        'endpoint="https://user:do-not-print@example.invalid/v1"\nmodel="test"\n',
        encoding="utf-8",
    )
    report = doctor.check_environment(config=config)
    assert check_by_code(report, "MODEL_ENDPOINT").status == "ERROR"
    assert "do-not-print" not in json.dumps(report.to_dict())


def test_clean_and_dirty_repo_checks_do_not_modify_index(commit_files):
    repo = commit_files({"README.md": "# A project\n", "sample.py": "DEFAULT = 1\n"})
    index = repo / ".git" / "index"
    before = index.read_bytes()
    report = doctor.check_environment(repo)
    assert check_by_code(report, "REPO_ROOT").status == "OK"
    assert check_by_code(report, "REPO_HEAD").status == "OK"
    assert check_by_code(report, "REPO_WORKTREE").status == "OK"
    (repo / "sample.py").write_text("DEFAULT = 2\n", encoding="utf-8")
    report = doctor.check_environment(repo)
    check = check_by_code(report, "REPO_WORKTREE")
    assert check.status == "WARN"
    assert "--working-tree" in check.action
    assert index.read_bytes() == before
    assert (repo / "sample.py").read_text() == "DEFAULT = 2\n"


def test_repo_requires_root_and_commit(commit_files, repo, tmp_path, monkeypatch):
    # Keep an unrelated repository above the temporary directory out of this fixture.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    empty = doctor.check_environment(repo)
    assert check_by_code(empty, "REPO_HEAD").status == "ERROR"
    repo = commit_files({"subdir/file.py": "A = 1\n"})
    nested = doctor.check_environment(repo / "subdir")
    assert check_by_code(nested, "REPO_ROOT").status == "ERROR"
    missing = doctor.check_environment(tmp_path / "absent")
    assert check_by_code(missing, "REPO_PATH").status == "ERROR"
    archive = tmp_path / "archive"
    archive.mkdir()
    downloaded = doctor.check_environment(archive)
    assert "ZIP" in check_by_code(downloaded, "REPO_ROOT").action


@pytest.mark.parametrize("existing", ["patch", "manifest", "report"])
def test_patch_export_preserves_existing_files(tmp_path, capsys, existing):
    report = tmp_path / "report.json"
    report.write_bytes(ARCHIVE.read_bytes())
    out = report if existing == "report" else tmp_path / "fix.patch"
    manifest = tmp_path / "fix.patch.json"
    if existing != "report":
        (out if existing == "patch" else manifest).write_bytes(b"keep existing bytes")
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    assert main(["patch", "--report", str(report), "--out", str(out)]) == 2
    assert json.loads(capsys.readouterr().err)["code"] == "OUTPUT_EXISTS"
    assert {path: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_patch_manifest_cannot_be_same_file(tmp_path, capsys):
    out = tmp_path / "fix.patch"
    assert main(["patch", "--report", str(ARCHIVE), "--out", str(out), "--manifest", str(out)]) == 2
    assert json.loads(capsys.readouterr().err)["code"] == "OUTPUT_COLLISION"
    assert not out.exists()


def test_patch_export_does_not_overwrite_file_created_after_preflight(
    tmp_path, monkeypatch, capsys
):
    out = tmp_path / "fix.patch"
    original_open = Path.open

    def racing_open(path, mode="r", *args, **kwargs):
        if path == out and mode == "xb":
            with original_open(path, "wb") as stream:
                stream.write(b"created by another process")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", racing_open)
    assert main(["patch", "--report", str(ARCHIVE), "--out", str(out)]) == 2
    assert json.loads(capsys.readouterr().err)["status"] == "FAILED"
    assert out.read_bytes() == b"created by another process"
    assert not out.with_suffix(".patch.json").exists()
