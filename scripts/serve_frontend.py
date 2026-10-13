"""Serve only DocSync's bundled UI on loopback; no uploads or backend execution."""

from __future__ import annotations

import argparse
import mimetypes
import socket
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import unquote, urlsplit

FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "DOCsync-demo-video-package" / "demo-ui"
PUBLIC_FILES = frozenset(
    {
        "index.html",
        "reports.html",
        "data.html",
        "code.html",
        "history.html",
        "styles.css",
        "portal.css",
        "app.js",
        "portal.js",
        "report-store.js",
        "demo-data.js",
    }
)
ASSET_SUFFIXES = frozenset(
    {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2", ".ttf"}
)
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}
MAX_ASSET_BYTES = 16 * 1024 * 1024
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; font-src 'self'; connect-src 'none'; "
    "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)


def resolve_static(root: Path, request_path: str) -> Path | None:
    """Resolve an explicitly public UI path without falling back to parent directories."""
    try:
        parsed = urlsplit(request_path)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            return None
        decoded = unquote(parsed.path, errors="strict")
        if any(character in decoded for character in ("\\", "\x00", ":", "%")):
            return None
        if decoded == "/":
            relative = "index.html"
        else:
            relative = decoded[1:]
            if any(part in {"", ".", ".."} for part in relative.split("/")):
                return None
        path = PurePosixPath(relative)
        if relative not in PUBLIC_FILES and not (
            len(path.parts) >= 2
            and path.parts[0] == "assets"
            and all(not part.startswith(".") for part in path.parts)
            and path.suffix.lower() in ASSET_SUFFIXES
        ):
            return None
        candidate = root
        for part in path.parts:
            candidate = candidate / part
            if candidate.is_symlink() or candidate.is_junction():
                return None
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            return None
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None


class FrontendServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, root: Path, port: int = 0) -> None:
        if root.is_symlink() or root.is_junction():
            raise ValueError("The frontend directory must not be a symlink or junction.")
        self.root = root.resolve(strict=True)
        if not self.root.is_dir() or resolve_static(self.root, "/index.html") is None:
            raise ValueError("Cannot find the bundled frontend index.html.")
        super().__init__(("127.0.0.1", port), FrontendHandler)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"

    def get_request(self) -> tuple[socket.socket, tuple[str, int]]:
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address


class FrontendHandler(BaseHTTPRequestHandler):
    server_version = "DocSyncLocalPreview"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        # Avoid recording request paths, report contents, or imported filenames.
        pass

    def _send(
        self, status: int, body: bytes, content_type: str = "text/plain; charset=utf-8"
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        if status == 405:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def _serve(self) -> None:
        server = cast(FrontendServer, self.server)
        hosts = {f"127.0.0.1:{server.server_port}", f"localhost:{server.server_port}"}
        origins = {f"http://{host}" for host in hosts}
        if self.headers.get("Host") not in hosts or (
            self.headers.get("Origin") is not None and self.headers["Origin"] not in origins
        ):
            self._send(403, b"This preview is available only through its local browser address.\n")
            return
        target = resolve_static(server.root, self.path)
        if target is None:
            self._send(404, b"Not found in the bundled frontend.\n")
            return
        try:
            with target.open("rb") as stream:
                data = stream.read(MAX_ASSET_BYTES + 1)
            if len(data) > MAX_ASSET_BYTES:
                self._send(413, b"Static asset is too large.\n")
                return
        except OSError:
            self._send(404, b"Static asset is unavailable.\n")
            return
        content_type = CONTENT_TYPES.get(target.suffix.lower())
        if content_type is None:
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._send(200, data, content_type)

    def do_GET(self) -> None:
        self._serve()

    def do_HEAD(self) -> None:
        self._serve()

    def _read_only(self) -> None:
        self._send(
            405,
            b"Read-only preview. Files are read locally by your browser; uploads are disabled.\n",
        )

    do_POST = _read_only
    do_PUT = _read_only
    do_PATCH = _read_only
    do_DELETE = _read_only
    do_OPTIONS = _read_only


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open the bundled DocSync frontend locally.")
    parser.add_argument(
        "--port", type=int, default=0, help="Local port; default 0 chooses an available port"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Print the address without opening a browser"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    try:
        with FrontendServer(FRONTEND_ROOT, args.port) as server:
            address = server.url + "/index.html"
            print(f"DocSync frontend: {address}", flush=True)
            print("Local read-only preview. Only bundled UI files are served.", flush=True)
            print("Keep this window open. Press Ctrl+C to stop.", flush=True)
            if not args.no_browser:
                try:
                    if not webbrowser.open(address):
                        print(
                            "Browser did not open automatically. Copy the address above.",
                            flush=True,
                        )
                except (webbrowser.Error, OSError):
                    print("Copy the address above into your browser.", flush=True)
            try:
                server.serve_forever(poll_interval=0.2)
            except KeyboardInterrupt:
                print("\nPreview stopped.")
    except (OSError, ValueError):
        print(
            "Cannot start the local preview. Check the bundled demo-ui files and choose another "
            "--port (or omit it for an available port).",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
