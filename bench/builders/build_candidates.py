"""Rebuild unlabelled controlled candidates; never run target code or inference."""

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def build(out: Path) -> Path:
    project = Path(__file__).resolve().parents[2]
    source = project / "bench/candidates/controlled-v1/spec.json"
    spec_bytes = source.read_bytes()
    spec = json.loads(spec_bytes)
    freeze = source.parent / "freeze.json"
    if freeze.exists():
        expected = json.loads(freeze.read_bytes())
        if hashlib.sha256(spec_bytes).hexdigest() != expected["spec_sha256"]:
            raise ValueError("Candidate specification changed; create a new version")
    if (
        freeze.exists()
        and hashlib.sha256((project / "LICENSE").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        != expected["license_sha256"]
    ):
        raise ValueError("License content changed; review candidate version")
    samples = spec["samples"]
    ids = set()
    groups = {}
    for item in samples:
        sid, group = item["sample_id"], item["group_id"]
        if not re.fullmatch(r"candidate-[0-9]{2}", sid) or sid in ids:
            raise ValueError("Invalid or duplicate sample ID")
        if not re.fullmatch(r"candidate-family-[0-9]{2}", group):
            raise ValueError("Invalid group")
        if set(item) != {"sample_id", "group_id", "code", "document"}:
            raise ValueError("Unexpected candidate metadata; answers are not allowed")
        ast.parse(item["code"])
        ids.add(sid)
        groups.setdefault(group, []).append(item)
    if out.exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True)
    rows = []
    # Fixed synthetic commit timestamp is for reproducibility, not reviewer sign-off.
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-10-07T00:00:00+08:00",
        "GIT_COMMITTER_DATE": "2026-10-07T00:00:00+08:00",
        "GIT_AUTHOR_NAME": "DocSync Controlled Candidates",
        "GIT_COMMITTER_NAME": "DocSync Controlled Candidates",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }
    for group, members in sorted(groups.items()):
        repo = out / "repos" / group
        repo.mkdir(parents=True)
        hooks = repo / ".empty-hooks"
        hooks.mkdir()

        def git(*args: str) -> str:
            return subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "commit.gpgsign=false",
                    "-c",
                    "core.hooksPath=" + str(hooks.resolve()),
                    *args,
                ],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        git("init", "--quiet", "--initial-branch=main", "--object-format=sha1", "--template=")
        (repo / "LICENSE").write_bytes((project / "LICENSE").read_bytes().replace(b"\r\n", b"\n"))
        (repo / ".gitattributes").write_bytes(b"* text eol=lf\n")
        for item in members:
            num = item["sample_id"].rsplit("-", 1)[1]
            (repo / f"case{num}.py").write_bytes(item["code"].encode("utf-8"))
            (repo / f"case{num}.md").write_bytes(item["document"].encode("utf-8"))
        git("add", ".")
        git("commit", "--quiet", "-m", "Unlabelled controlled candidates v1")
        sha = git("rev-parse", "HEAD")
        for item in members:
            num = item["sample_id"].rsplit("-", 1)[1]
            rows.append(
                {
                    "sample_id": item["sample_id"],
                    "repo_id": group,
                    "group_id": group,
                    "repo_path": "repos/" + group,
                    "head_sha": sha,
                    "code_path": f"case{num}.py",
                    "document_path": f"case{num}.md",
                    "origin": "controlled",
                    "source": "AI-assisted original fixture; bench/candidates/controlled-v1/spec.json",
                    "license": "Apache-2.0",
                    "rights_evidence": "Team original-material approval in docs/license-scope.md; repository LICENSE",
                    "prior_exposure": "Authoring assistant has seen seed-dev-v1 and its seven-method results; no scan of these candidates. B/C must disclose prior exposure. Template independence pending human review.",
                    "collected_at": spec["collected_at"],
                }
            )
    intake = out / "intake.jsonl"
    intake.write_bytes(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    )
    (out / "build.json").write_text(
        json.dumps(
            {
                "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
                "intake_sha256": hashlib.sha256(intake.read_bytes()).hexdigest(),
                "sample_count": len(rows),
                "group_count": len(groups),
                "formal_test_ready": False,
                "models_called": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if (
        freeze.exists()
        and hashlib.sha256(intake.read_bytes()).hexdigest() != expected["intake_sha256"]
    ):
        raise ValueError("Rebuilt Git snapshots differ from frozen candidates")
    return intake


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(build(args.out))


if __name__ == "__main__":
    main()
