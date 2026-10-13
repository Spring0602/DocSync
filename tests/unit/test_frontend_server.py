"""Exercise the real loopback preview and verify its private-file boundary."""

import http.client
import importlib.util
import threading
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "serve_frontend.py"
SPEC = importlib.util.spec_from_file_location("docsync_frontend_server", SCRIPT)
assert SPEC and SPEC.loader
server_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server_module)


@pytest.fixture
def preview(tmp_path):
    root = tmp_path / "demo-ui"
    root.mkdir()
    (root / "index.html").write_text("<h1>Local UI</h1>", encoding="utf-8")
    (root / "app.js").write_text("const preview = true;", encoding="utf-8")
    (root / "styles.css").write_text("body { color: blue; }", encoding="utf-8")
    (root / "private.json").write_text('{"secret":"private"}', encoding="utf-8")
    (root / "nested").mkdir()
    (root / "nested" / "index.html").write_text("private nested page", encoding="utf-8")
    (tmp_path / "private.json").write_text('{"secret":"outside-root"}', encoding="utf-8")
    with server_module.FrontendServer(root) as server:
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


def request(server, path="/", method="GET", body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_preview_serves_index_assets_and_head_on_loopback(preview):
    assert preview.server_address[0] == "127.0.0.1"
    assert preview.server_port != 0
    status, headers, body = request(preview)
    assert status == 200
    assert body == b"<h1>Local UI</h1>"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"
    assert "connect-src 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert request(preview, "/app.js?version=1")[0] == 200
    assert request(preview, "/styles.css")[0] == 200
    head_status, head_headers, head_body = request(preview, "/", method="HEAD")
    assert head_status == 200
    assert head_headers["Content-Length"] == str(len(body))
    assert head_body == b""


@pytest.mark.parametrize(
    "path",
    [
        "/../private.json",
        "/%2e%2e/private.json",
        "/%252e%252e/private.json",
        "/%2e%2e%5cprivate.json",
        "/%2F..%2Fprivate.json",
        "/C:/private.json",
        "/app.js:secret",
        "/%00index.html",
        "/private.json",
        "/nested/",
        "/nested/index.html",
        "/artifacts/report.json",
        "/tests/report-store.test.cjs",
        "/.git/config",
        "/assets/../../private.json",
        "/assets/.hidden.svg",
    ],
)
def test_private_paths_and_directory_listing_are_unavailable(preview, path):
    status, _headers, body = request(preview, path)
    assert status == 404
    assert b"secret" not in body
    assert b"outside-root" not in body
    assert b"private nested page" not in body


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_upload_and_write_endpoints_are_disabled(preview, method):
    status, headers, _body = request(
        preview,
        "/report.json",
        method,
        '{"private":"uploaded"}',
        {"Content-Type": "application/json"},
    )
    assert status == 405
    assert headers["Allow"] == "GET, HEAD"
    assert not (preview.root / "report.json").exists()


def test_foreign_host_and_origin_are_rejected(preview):
    assert request(preview, headers={"Host": "attacker.invalid"})[0] == 403
    assert request(preview, headers={"Origin": "https://attacker.invalid"})[0] == 403
    assert request(preview, headers={"Origin": preview.url})[0] == 200


def test_only_public_asset_extensions_are_served(preview):
    assets = preview.root / "assets"
    assets.mkdir()
    (assets / "mark.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    (assets / "report.json").write_text('{"secret":true}', encoding="utf-8")
    assert request(preview, "/assets/mark.svg")[0] == 200
    assert request(preview, "/assets/report.json")[0] == 404
    assert request(preview, "/assets/")[0] == 404


def test_symlink_to_parent_is_rejected(preview):
    outside = preview.root.parent / "outside.js"
    outside.write_text("private outside source", encoding="utf-8")
    link = preview.root / "portal.js"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("OS does not grant symlink creation to this process")
    assert request(preview, "/portal.js")[0] == 404


def test_symlink_guard_without_platform_privileges(preview, monkeypatch):
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path.name == "app.js" or original(path))
    assert request(preview, "/app.js")[0] == 404


def test_server_rejects_directory_without_index(tmp_path):
    with pytest.raises(ValueError, match="index.html"):
        server_module.FrontendServer(tmp_path)


def test_port_validation_does_not_start_server():
    with pytest.raises(SystemExit) as exc:
        server_module.main(["--port", "65536", "--no-browser"])
    assert exc.value.code == 2
