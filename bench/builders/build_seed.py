"""Create 20 self-authored, provisional development cases; no model or network calls."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


def cases() -> list[dict]:
    def default(value: str, heading: str = "connect") -> str:
        return f"## `{heading}`\n\n`timeout` 默认值为 `{value}`。\n"

    def call(value: str) -> str:
        return f"```python\n{value}\n```\n"

    code = "def connect(timeout=60):\n    return timeout\n"
    table = "## `connect`\n\n| parameter | default |\n|---|---|\n|timeout|30|\n"
    definitions = [
        ("default_drift", "DEFAULT_VALUE", "INCONSISTENT", {"client.py": code}, default("30")),
        ("default_equal", "DEFAULT_VALUE", "CONSISTENT", {"client.py": code}, default("60")),
        (
            "typed_bool",
            "DEFAULT_VALUE",
            "INCONSISTENT",
            {"client.py": code.replace("60", "True")},
            default("1"),
        ),
        (
            "factory_unknown",
            "DEFAULT_VALUE",
            "INSUFFICIENT",
            {"client.py": code.replace("60", "factory()")},
            default("30"),
        ),
        (
            "historical",
            "DEFAULT_VALUE",
            "INSUFFICIENT",
            {"client.py": code},
            default("30").replace("##", "## 旧版"),
        ),
        (
            "ambiguous",
            "DEFAULT_VALUE",
            "INSUFFICIENT",
            {"client.py": code, "other.py": code},
            default("30"),
        ),
        ("table_drift", "DEFAULT_VALUE", "INCONSISTENT", {"client.py": code}, table),
        (
            "table_equal",
            "DEFAULT_VALUE",
            "CONSISTENT",
            {"client.py": code},
            table.replace("|30|", "|60|"),
        ),
        (
            "linked_owner",
            "DEFAULT_VALUE",
            "INCONSISTENT",
            {"client.py": code, "other.py": code.replace("60", "30")},
            default("30").replace("`connect`", "[connect](client.py)"),
        ),
        (
            "constant_drift",
            "CONFIG",
            "INCONSISTENT",
            {"settings.py": "TIMEOUT = 60\n"},
            "## 配置 `settings`\n\n`TIMEOUT` 默认值为 `30`。\n",
        ),
        (
            "constant_equal",
            "CONFIG",
            "CONSISTENT",
            {"settings.py": "TIMEOUT = 60\n"},
            "## 配置 `settings`\n\n`TIMEOUT` 默认值为 `60`。\n",
        ),
        (
            "dict_drift",
            "CONFIG",
            "INCONSISTENT",
            {"settings.py": "CONFIG = {'timeout': 60}\n"},
            default("30", "settings.CONFIG"),
        ),
        (
            "dict_dynamic",
            "CONFIG",
            "INSUFFICIENT",
            {"settings.py": "CONFIG = {'timeout': env()}\n"},
            default("30", "settings.CONFIG"),
        ),
        (
            "missing_required",
            "SIGNATURE",
            "INCONSISTENT",
            {"client.py": "def connect(host): pass\n"},
            call("connect()"),
        ),
        (
            "unexpected_keyword",
            "SIGNATURE",
            "INCONSISTENT",
            {"client.py": code},
            call("connect(host='local')"),
        ),
        (
            "kwargs_legal",
            "SIGNATURE",
            "CONSISTENT",
            {"client.py": "def connect(**kwargs): pass\n"},
            call("connect(host='local')"),
        ),
        (
            "positional_only",
            "SIGNATURE",
            "INCONSISTENT",
            {"client.py": "def connect(host, /): pass\n"},
            call("connect(host='local')"),
        ),
        (
            "keyword_only",
            "SIGNATURE",
            "INCONSISTENT",
            {"client.py": "def connect(*, host): pass\n"},
            call("connect()"),
        ),
        (
            "optional_added",
            "SIGNATURE",
            "CONSISTENT",
            {"client.py": "def connect(timeout=60, retries=3): pass\n"},
            call("connect(timeout=30)"),
        ),
        (
            "import_alias",
            "SIGNATURE",
            "INCONSISTENT",
            {"client.py": "def connect(host): pass\n"},
            call("from client import connect as open_connection\nopen_connection()"),
        ),
    ]
    return [
        {
            "sample_id": f"seed-{i:02d}-{name}",
            "drift_type": kind,
            "gold": label,
            "files": {**files, "README.md": doc},
            "code_path": next(iter(files)),
        }
        for i, (name, kind, label, files, doc) in enumerate(definitions, 1)
    ]


def build(out: Path) -> Path:
    if out.exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True)
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-09-18T00:00:00+08:00",
        "GIT_COMMITTER_DATE": "2026-09-18T00:00:00+08:00",
    }
    rows = []
    for sample in cases():
        root = out / "repos" / sample["sample_id"]
        root.mkdir(parents=True)

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(root), *args], env=env, capture_output=True, text=True, check=True
            ).stdout.strip()

        git("init", "--quiet", "--initial-branch=main")
        git("config", "core.autocrlf", "false")
        git("config", "commit.gpgsign", "false")
        git("config", "user.name", "DocSync Controlled Fixture")
        git("config", "user.email", "fixture@example.invalid")
        hooks = root / ".git" / "disabled-hooks"
        hooks.mkdir()
        git("config", "core.hooksPath", str(hooks.resolve()))
        for path, text in sample["files"].items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        git("add", ".")
        git("commit", "--quiet", "-m", "Self-authored provisional seed")
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "repo_id": "controlled-" + sample["sample_id"],
                "repo_path": "repos/" + sample["sample_id"],
                "head_sha": git("rev-parse", "HEAD"),
                "code_path": sample["code_path"],
                "document_path": "README.md",
                "group_id": "controlled-" + sample["drift_type"],
                "split": "dev",
                "origin": "controlled",
                "gold": sample["gold"],
                "drift_type": sample["drift_type"],
                "rights_status": "pending",
                "annotation_status": "provisional",
                "claim_line": None,
            }
        )
    manifest = out / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    (out / "manifest.sha256").write_text(hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n")
    (out / "README.md").write_text(
        "# Controlled development seed\n\n20 self-authored cases. All labels provisional; two-person annotation pending.\nNot historical open-source cases or a frozen test set.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.out))


if __name__ == "__main__":
    main()
