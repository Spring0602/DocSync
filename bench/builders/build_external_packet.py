"""Build the external-v1 unlabelled packet from fixed, already fetched Git objects.

No target import, scan, model request or label inference is performed.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from bench.annotation_packet import FIELDS, prepare

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bench/sources/external-v1"
CACHE = ROOT / "runs/external-v1-repos"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def safe_name(value):
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or "\\" in value or ":" in value:
        raise ValueError("Unsafe path")
    return value


def blob(source, name):
    safe_name(name)
    repo = CACHE / source["source_id"]
    spec = source["head_sha"] + ":" + name
    data = subprocess.check_output(["git", "-C", str(repo), "cat-file", "blob", spec])
    oid = subprocess.check_output(["git", "-C", str(repo), "rev-parse", spec], text=True).strip()
    if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != oid:
        raise ValueError("Git blob integrity mismatch")
    return data, oid


def line_range(value, data):
    match = re.fullmatch(r"([1-9][0-9]*)(?:-([1-9][0-9]*))?", value)
    if not match or not (
        int(match[1]) <= int(match[2] or match[1]) <= len(data.decode("utf-8").splitlines())
    ):
        raise ValueError("Invalid source coordinates")


def verify(out):
    expected = read_json(out / "checksums.json")
    actual = {
        p.relative_to(out).as_posix(): sha(p.read_bytes())
        for p in out.rglob("*")
        if p.is_file() and p != out / "checksums.json"
    }
    if actual != expected:
        raise ValueError("Packet file inventory or SHA-256 mismatch")
    packet = read_json(out / "packet.json")
    selection = read_json(out / "selection.json")
    selected = {s["sample_id"]: s for s in selection["samples"]}
    ids = [s["sample_id"] for s in packet["samples"]]
    if len(ids) != len(set(ids)) or set(ids) != set(selected) or packet["formal_test_ready"]:
        raise ValueError("Invalid sample inventory or readiness flag")
    for sample in packet["samples"]:
        sid = safe_name(sample["sample_id"])
        for kind, coords in (("code", "code_entry"), ("document", "document_focus")):
            data = (out / sid / (kind + "_path.txt")).read_bytes()
            if sha(data) != sample["files"][kind + "_path"]["sha256"]:
                raise ValueError("Original payload mismatch")
            line_range(selected[sid][coords], data)
    for member in ("B", "C"):
        with (out / f"individual-{member}.csv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS:
                raise ValueError("CSV header mismatch")
            rows = list(reader)
        if [r["sample_id"] for r in rows] != ids:
            raise ValueError("CSV sample mismatch")
        for row, sample in zip(rows, packet["samples"]):
            for key in FIELDS:
                want = (
                    sample[key]
                    if key in ("sample_id", "head_sha", "code_path", "document_path")
                    else ""
                )
                if row.get(key) != want:
                    raise ValueError("Original packet must contain blank reviews")
    return {
        "status": "VERIFIED_UNLABELLED_PACKET",
        "samples": len(ids),
        "files": len(actual),
        "formal_test_ready": False,
        "packet_sha256": sha((out / "packet.json").read_bytes()),
        "checksums_sha256": sha((out / "checksums.json").read_bytes()),
    }


def build(out):
    if out.exists():
        raise ValueError("Output already exists; do not overwrite original packets")
    sources = {
        s["source_id"]: s
        for s in map(
            json.loads, (SOURCE / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        )
    }
    selection = read_json(SOURCE / "selection.json")
    for sample in selection["samples"]:
        if {"gold", "label", "prediction"} & sample.keys():
            raise ValueError("Selection must not contain answers")
    for source_id in sources:
        if sum(s["source_id"] == source_id for s in selection["samples"]) > 4:
            raise ValueError("Per-source screening cap exceeded")
    development = []
    dev_hashes = set()
    dev_evidence = []
    # Rebuild trusted local development fixtures, then hash their committed blobs.
    # Frozen folders contain manifests, not source payloads; hashing only them is insufficient.
    with tempfile.TemporaryDirectory(prefix="docsync-dev-overlap-") as scratch:
        for family, command in (
            ("seed-dev-v1", [sys.executable, str(ROOT / "bench/builders/build_reviewed_seed.py")]),
            (
                "candidate-dev-v1",
                [sys.executable, "-m", "bench.builders.build_reviewed_candidates"],
            ),
        ):
            rebuilt = Path(scratch) / family
            subprocess.run(
                command + ["--out", str(rebuilt)], cwd=ROOT, check=True, capture_output=True
            )
            manifest = ROOT / "bench/frozen" / family / "manifest.jsonl"
            if (rebuilt / "manifest.jsonl").read_bytes() != manifest.read_bytes():
                raise ValueError("Rebuilt development manifest mismatch")
            for r in map(json.loads, manifest.read_bytes().splitlines()):
                development.append({k: r[k] for k in ("sample_id", "repo_id", "group_id")})
                for key in ("code_path", "document_path"):
                    data = subprocess.check_output(
                        [
                            "git",
                            "-C",
                            str(rebuilt / r["repo_path"]),
                            "cat-file",
                            "blob",
                            r["head_sha"] + ":" + r[key],
                        ]
                    )
                    dev_hashes.add(sha(data))
            dev_evidence.append(
                {
                    "path": manifest.relative_to(ROOT).as_posix(),
                    "sha256": sha(manifest.read_bytes()),
                    "verification": "reviewed builder validates frozen artifacts and fixed commits; primary code/document blobs hashed",
                }
            )
    rows, payloads, context_index, rights = [], {}, [], []
    for source_id, source in sources.items():
        names = set(selection["context_files"][source_id])
        names.update(
            s[k]
            for s in selection["samples"]
            if s["source_id"] == source_id
            for k in ("code_path", "document_path")
        )
        notices = []
        for name in sorted(names):
            data, oid = blob(source, name)
            if sha(data) in dev_hashes:
                raise ValueError("Exact development payload overlap")
            for f in source["candidate_files"]:
                if f["path"] == name and f["git_blob_sha"] != oid:
                    raise ValueError("Shortlist blob mismatch")
            dest = f"context/{source_id}/{name}.txt"
            payloads[dest] = data
            context_index.append(
                {
                    "source_id": source_id,
                    "path": name,
                    "packet_path": dest,
                    "head_sha": source["head_sha"],
                    "git_blob_sha": oid,
                    "sha256": sha(data),
                    "lines": len(data.decode("utf-8").splitlines()),
                    "url": source["source_url"] + "/blob/" + source["head_sha"] + "/" + name,
                }
            )
            hits = [
                {"line": i, "text": line}
                for i, line in enumerate(data.decode("utf-8").splitlines(), 1)
                if re.search(r"(?i)SPDX|copyright|all rights reserved|licensed under", line)
            ]
            if hits:
                notices.append({"path": name, "visible_notice_matches": hits})
        for evidence in source["license_evidence"]:
            data, oid = blob(source, evidence["original_path"])
            if oid != evidence["git_blob_sha"] or sha(data) != evidence["sha256"]:
                raise ValueError("License does not match fixed evidence")
            name = PurePosixPath(evidence["archived_path"]).name
            payloads[f"licenses/{source_id}/{name}"] = data
        rights.append(
            {
                "source_id": source_id,
                "repo_id": source["repo_id"],
                "license": source["license_spdx_reported"],
                "scope": sorted(names),
                "license_evidence": source["license_evidence"],
                "notices": notices,
                "review_status": "FIXED_LICENSE_AND_VISIBLE_NOTICES_RECORDED_PENDING_A_FINAL_REVIEW",
                "limits": "Original text only; linked images, logos and websites not downloaded. Upstream licence retained; no Apache-2.0 relicensing.",
            }
        )
    for s in selection["samples"]:
        source = sources[s["source_id"]]
        for kind, coords in (("code", "code_entry"), ("document", "document_focus")):
            line_range(s[coords], payloads[f"context/{s['source_id']}/{s[kind + '_path']}.txt"])
        rows.append(
            {
                "sample_id": s["sample_id"],
                "repo_id": source["repo_id"],
                "group_id": source["provisional_group_id"],
                "repo_path": f"../../../runs/external-v1-repos/{s['source_id']}",
                "head_sha": source["head_sha"],
                "code_path": s["code_path"],
                "document_path": s["document_path"],
                "origin": "real",
                "source": source["source_url"],
                "license": source["license_spdx_reported"],
                "rights_evidence": "rights-review.json and licenses/" + s["source_id"],
                "prior_exposure": "A reports not previously used; B/C declarations pending; collector AI knows DocSync development history and has screened originals; model training exposure unknown",
                "collected_at": "2026-10-11",
            }
        )
    # Intake paths remain relative to SOURCE; absolute cache paths are used only in temporary prepare input.
    intake = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="docsync-external-") as scratch:
        folder = Path(scratch)
        (folder / "development.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in development), encoding="utf-8"
        )
        temporary_rows = [
            dict(r, repo_path=str(CACHE / s["source_id"]))
            for r, s in zip(rows, selection["samples"])
        ]
        (folder / "intake.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in temporary_rows), encoding="utf-8"
        )
        meta = prepare(folder / "intake.jsonl", out, folder / "development.jsonl")
    # prepare uses csv CRLF plus text-mode translation on Windows. Preserve
    # CSV records with one CRLF, not CRCRLF (which spreadsheet readers treat as empty rows).
    for member in ("B", "C"):
        csv_path = out / f"individual-{member}.csv"
        csv_path.write_bytes(csv_path.read_bytes().replace(b"\r\r\n", b"\r\n"))
    meta["intake_sha256"] = sha(intake)
    meta["selection_sha256"] = sha((SOURCE / "selection.json").read_bytes())
    meta["screening_policy_sha256"] = sha((SOURCE / "screening-policy.md").read_bytes())
    meta["generator_sha256"] = sha(Path(__file__).read_bytes())
    meta["context_index"] = "context-index.json"
    meta["model_requests"] = 0
    meta["target_scans"] = 0
    meta["limits"] = (
        "Purposive source-order sample; shared repository groups are correlated. Human labels, source-family review, B/C exposure declarations and formal evaluation freeze pending. Not a benchmark manifest."
    )
    write_json(out / "packet.json", meta)
    (out / "intake.jsonl").write_bytes(intake)
    for name, data in payloads.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for name in (
        "selection.json",
        "screening-policy.md",
        "sources.jsonl",
        "source-acceptance.json",
    ):
        (out / name).write_bytes((SOURCE / name).read_bytes())
    (out / "README.md").write_bytes((SOURCE / "handoff.md").read_bytes())
    (out / ".gitattributes").write_bytes(b"** -text\n")
    write_json(out / "context-index.json", context_index)
    write_json(out / "rights-review.json", rights)
    write_json(
        out / "overlap-review.json",
        {
            "development_manifests": dev_evidence,
            "development_rows_checked": len(development),
            "development_unique_file_hashes_checked": len(dev_hashes),
            "declared_id_repo_group_overlap": [],
            "exact_payload_hash_overlap": [],
            "provisional_groups": [s["provisional_group_id"] for s in sources.values()],
            "family_review": "PENDING_A_REVIEW; distinct IDs and hashes do not establish independence",
            "annotator_exposure": "PENDING_SEPARATE_B_C_DECLARATIONS",
            "formal_test_ready": False,
        },
    )
    guide = [
        "# 样本导航",
        "",
        "坐标均为完整原文件行号。代码入口只是查阅提示，最终标签/类型/实体/证据坐标由标注者独立填写。",
        "",
    ]
    for s in selection["samples"]:
        source = sources[s["source_id"]]
        guide.extend(
            [
                f"## {s['sample_id']}：{s['title']}",
                "",
                s["question"],
                "",
                f"来源：{source['repo_id']}，固定提交 `{source['head_sha']}`。",
                "",
                f"文档：[{s['document_path']}]({s['sample_id']}/document_path.txt)，焦点 {s['document_focus']} 行。",
                "",
                f"代码：[{s['code_path']}]({s['sample_id']}/code_path.txt)，查阅入口 {s['code_entry']} 行。",
                "",
                f"补充上下文：`context/{s['source_id']}/`，索引见 context-index.json。",
                "",
            ]
        )
    (out / "SAMPLES.md").write_text("\n".join(guide), encoding="utf-8", newline="\n")
    for member in ("B", "C"):
        exposure = [
            f"# 成员 {member} 接触与独立标注声明（待本人填写）",
            "",
            "审核人：",
            "实际开始/完成日期：",
            "收到的 packet.json SHA-256：",
            "收到的 checksums.json SHA-256：",
            "个人表 SHA-256（完成后填写）：",
            "",
            "每项说明此前是否读过、开发、调参或看过具体缺陷/答案；未知写未知，不能把本次查阅当作事先未见证明。",
            "",
            "| 来源 | 既往代码/文档/缺陷接触 | 涉及样本 | 说明 |",
            "| --- | --- | --- | --- |",
        ]
        exposure.extend(f"| {s['repo_id']} | | | |" for s in sources.values())
        exposure.extend(
            [
                "",
                "是否查看对方答案或 DocSync/模型预测（时间及范围）：",
                "是否使用 AI 辅助标注（工具、任务、实际人工复核范围）：",
                "是否接触过旧开发种子/扩展候选及本包家族关系：",
                "原文证据不足或需要补充的同版本文件：",
                "本人确认及日期：",
                "",
            ]
        )
        (out / f"exposure-{member}.md").write_text(
            "\n".join(exposure), encoding="utf-8", newline="\n"
        )
    checksums = {
        p.relative_to(out).as_posix(): sha(p.read_bytes())
        for p in sorted(out.rglob("*"))
        if p.is_file()
    }
    write_json(out / "checksums.json", checksums)
    return verify(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    result = verify(args.verify) if args.verify else build(args.out)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
