"""Ensure frontend handoffs include public files and preserve private workspaces."""

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

SCRIPTS = Path(__file__).parents[2] / "scripts"


@pytest.fixture
def packager(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "docsync_frontend_packager", SCRIPTS / "package_frontend.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def package_source(tmp_path, packager):
    root = tmp_path / "source"
    for relative in (
        *packager.REQUIRED_FILES,
        *(f"{packager.UI_PREFIX}/{name}" for name in packager.PUBLIC_FILES),
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        content = b"public fixture"
        if relative == "scripts/serve_frontend.py":
            content = (SCRIPTS / "serve_frontend.py").read_bytes()
        target.write_bytes(content)
    for relative in (
        ".env",
        "individual-B.csv",
        "B-external-v1-private/exposure-B.md",
        "DOCsync-demo-video-package/demo-ui/private.json",
        "DOCsync-demo-video-package/artifacts/unlisted-private.json",
        "DOCsync-demo-video-package/demo-ui/tests/private.test.cjs",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"never include this private content")
    optional = root / "DOCsync-demo-video-package/artifacts/before-report.json"
    optional.write_text('{"public":"before report"}', encoding="utf-8")
    return root


def test_package_is_exactly_allowlisted_and_extracts_with_working_launcher(
    packager, package_source, tmp_path
):
    out = tmp_path / "handoff.zip"
    summary = packager.build_package(package_source, out)
    assert summary["sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert "after-report.json" in summary["skipped_optional"]
    expected = {
        *(f"DocSync-frontend/{relative}" for relative in packager.REQUIRED_FILES),
        *(f"DocSync-frontend/{packager.UI_PREFIX}/{name}" for name in packager.PUBLIC_FILES),
        "DocSync-frontend/DOCsync-demo-video-package/artifacts/before-report.json",
    }
    with ZipFile(out) as archive:
        assert set(archive.namelist()) == expected
        assert summary["files"] == len(expected)
        assert all(b"never include" not in archive.read(name) for name in archive.namelist())
        archive.extractall(tmp_path / "extracted")
    extracted = tmp_path / "extracted/DocSync-frontend"
    assert (extracted / "DOCsync-demo-video-package/启动前端.cmd").is_file()
    assert (extracted / "DOCsync-demo-video-package/demo-ui/index.html").is_file()
    result = subprocess.run(
        [sys.executable, str(extracted / "scripts/serve_frontend.py"), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
    assert "--no-browser" in result.stdout


def test_package_never_overwrites_existing_output(packager, package_source, tmp_path):
    out = tmp_path / "keep.zip"
    out.write_bytes(b"existing archive")
    with pytest.raises(FileExistsError):
        packager.build_package(package_source, out)
    assert out.read_bytes() == b"existing archive"


def test_missing_required_file_fails_before_creating_archive(packager, package_source, tmp_path):
    (package_source / "LICENSE").unlink()
    out = tmp_path / "incomplete.zip"
    with pytest.raises(ValueError, match="required"):
        packager.build_package(package_source, out)
    assert not out.exists()


def test_package_rejects_symlink_source_without_privileged_setup(
    packager, package_source, tmp_path, monkeypatch
):
    original = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path.name == "index.html" or original(path)
    )
    out = tmp_path / "symlink.zip"
    with pytest.raises(ValueError, match="Symlinks"):
        packager.build_package(package_source, out)
    assert not out.exists()


def test_output_created_after_preflight_is_preserved(
    packager, package_source, tmp_path, monkeypatch
):
    out = tmp_path / "race.zip"
    original_open = Path.open

    def racing_open(path, mode="r", *args, **kwargs):
        if path == out and mode == "xb":
            with original_open(path, "wb") as stream:
                stream.write(b"archive from another process")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", racing_open)
    with pytest.raises(FileExistsError):
        packager.build_package(package_source, out)
    assert out.read_bytes() == b"archive from another process"
