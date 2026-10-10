import shutil
from pathlib import Path

import pytest

from bench.builders.build_reviewed_candidates import verify_freeze


def test_reviewed_candidate_freeze_and_evidence_tampering(tmp_path):
    import json

    project = Path(__file__).resolve().parents[2]
    frozen, rows = verify_freeze(project)
    assert len(rows) == 24
    assert {r["split"] for r in rows} == {"dev"}
    assert sum(r["gold"] == "INSUFFICIENT" for r in rows) == 5
    meta = json.loads((frozen / "freeze.json").read_bytes())
    shutil.copytree(frozen, tmp_path / "bench/frozen/candidate-dev-v1")
    for name in meta["source_hashes_lf"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((project / name).read_bytes())
    verify_freeze(tmp_path)
    name = next(iter(meta["source_hashes_lf"]))
    (tmp_path / name).write_bytes(b"changed source")
    with pytest.raises(ValueError, match="source changed"):
        verify_freeze(tmp_path)
    (tmp_path / name).write_bytes((project / name).read_bytes())
    target = tmp_path / "bench/frozen/candidate-dev-v1/manifest.jsonl"
    target.write_bytes(target.read_bytes().replace(b'"dev"', b'"test"'))
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_freeze(tmp_path)
