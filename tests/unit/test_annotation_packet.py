import csv
import json
import subprocess

import pytest

from bench.annotation_packet import check_annotations, prepare


@pytest.fixture
def intake(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    git("init", "--quiet")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("config", "core.autocrlf", "false")
    (repo / "x.py").write_text("def run(): pass\n", encoding="utf-8")
    (repo / "README.md").write_text("Example\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "fixture")
    row = dict(
        sample_id="new-01",
        repo_id="new-repo",
        group_id="new-family",
        repo_path="repo",
        head_sha=git("rev-parse", "HEAD"),
        code_path="x.py",
        document_path="README.md",
        origin="controlled",
        source="unit fixture",
        license="Apache-2.0",
        rights_evidence="fixture only",
        prior_exposure="unit test",
        collected_at="2026-10-07",
    )
    path = tmp_path / "intake.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    dev = tmp_path / "dev.jsonl"
    dev.write_text("", encoding="utf-8")
    return path, dev, row


def test_packet_uses_committed_blob_and_blank_reviews(intake, tmp_path):
    path, dev, row = intake
    (tmp_path / "repo/x.py").write_text("DIRTY WORKTREE", encoding="utf-8")
    out = tmp_path / "packet"
    result = prepare(path, out, dev)
    assert not result["formal_test_ready"]
    assert (out / "new-01/code_path.txt").read_text() == "def run(): pass\n"
    checked = check_annotations(
        out / "packet.json", out / "individual-B.csv", out / "individual-C.csv"
    )
    assert not checked["structurally_complete"]
    assert any("missing reviewer" in x for x in checked["errors"])
    with pytest.raises(ValueError):
        prepare(path, out, dev)


@pytest.mark.parametrize(
    "change", [{"gold": "CONSISTENT"}, {"code_path": "../x.py"}, {"sample_id": "../../escape"}]
)
def test_reject_answers_and_unsafe_paths(intake, tmp_path, change):
    path, dev, row = intake
    row.update(change)
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError):
        prepare(path, tmp_path / "bad", dev)
    assert not (tmp_path / "bad").exists()


def test_overlap_and_annotation_differences(intake, tmp_path):
    path, dev, row = intake
    dev.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError):
        prepare(path, tmp_path / "overlap", dev)
    dev.write_text("", encoding="utf-8")
    out = tmp_path / "packet"
    prepare(path, out, dev)
    for member, label in [("B", "CONSISTENT"), ("C", "INSUFFICIENT")]:
        file = out / f"individual-{member}.csv"
        with file.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        rows[0].update(
            reviewer=member,
            reviewed_at="2026-10-07",
            label=label,
            drift_type="SIGNATURE",
            code_lines="1",
            document_lines="1",
            target_entity="run",
            evidence="fixture",
            reason="fixture",
        )
        with file.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    report = check_annotations(
        out / "packet.json", out / "individual-B.csv", out / "individual-C.csv"
    )
    assert report["structurally_complete"]
    assert report["requires_adjudication"] == ["new-01"]
    assert not report["formal_test_ready"]
    text = (out / "individual-C.csv").read_text(encoding="utf-8")
    (out / "individual-C.csv").write_text(text.replace(",1,", ",999,"), encoding="utf-8")
    assert not check_annotations(
        out / "packet.json", out / "individual-B.csv", out / "individual-C.csv"
    )["structurally_complete"]
