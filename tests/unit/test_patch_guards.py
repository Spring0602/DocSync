import pytest

from docsync.models import PatchEdit
from docsync.patches import edited_blobs, safe_target
from docsync.utils import DocSyncError, span_for


@pytest.mark.parametrize("path", ["../outside.md", "a.py", ".git/README.md", "C:/README.md"])
def test_only_safe_markdown_paths(tmp_path, path):
    with pytest.raises(DocSyncError):
        safe_target(tmp_path.resolve(), path)


def test_overlap_is_rejected():
    data = b"default = 30"
    edit = PatchEdit(span=span_for("README.md", data, 10, 12), old_text="30", new_text="60")
    with pytest.raises(DocSyncError):
        edited_blobs([edit, edit], {"README.md": data})


def test_external_symlink_is_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside")
    link = root / "README.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("OS does not grant symlink creation to this process")
    with pytest.raises(DocSyncError):
        safe_target(root, "README.md")
