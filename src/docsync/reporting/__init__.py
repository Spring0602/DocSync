import html
import json
from pathlib import Path

from docsync.models import ScanReport


def markdown_report(report: ScanReport) -> str:
    manifest, snapshot = report.manifest, report.snapshot
    lines = [
        "# DocSync 扫描报告",
        "",
        f"- 状态：{manifest.status}",
        f"- 提交：`{snapshot.head_sha}`",
        f"- 快照：{snapshot.mode}；工作树 dirty={snapshot.dirty}",
        f"- 模式：{manifest.mode}；实际能力：默认值、支持的调用绑定、简单配置",
        f"- 纳入文件：{len(snapshot.files)}；提取事实：{len(report.facts)}；声明/示例：{len(report.claims)}",
        f"- 已确认（未忽略）：{report.confirmed_count}；已忽略：{report.ignored_count}；不确定：{report.uncertain_count}",
        "- 范围说明：未提取的文本不代表一致；实际模型调用量、降级原因见 manifest。",
        "",
    ]
    claims = {c.claim_id: c for c in report.claims}
    facts = {f.fact_id: f for f in report.facts}
    for finding in report.findings:
        claim = claims[finding.claim_id]
        fact = facts[finding.fact_ids[0]]
        lines.extend(
            [
                f"## {finding.finding_id}",
                "",
                f"类型：{finding.drift_type}；证据：VERIFIED；忽略：{finding.ignored}",
                "",
                f"文档：{html.escape(claim.span.path)}:{claim.span.start_line}",
                "",
                "    " + claim.quote.replace("\n", "\n    "),
                "",
                f"代码：{html.escape(fact.span.path)}:{fact.span.start_line}",
                "",
                "    "
                + fact.subject
                + "."
                + fact.property
                + " = "
                + fact.expression.replace("\n", "\n    "),
                "",
                f"规则：{finding.evidence.rule_id}；两侧 SHA-256 见 JSON。",
                "",
            ]
        )
    if report.uncertain_count:
        lines.extend(["## 待核查", ""])
        for judgment in report.judgments:
            if judgment.decision == "UNCERTAIN":
                lines.append(f"- {judgment.claim_id}：{judgment.reason_code}")
        for rejected in report.rejected:
            lines.append(f"- {rejected.claim_id}：证据拒绝 {rejected.reason}")
        lines.append("")
    lines.extend(["## 诊断", ""])
    lines.extend(
        f"- {d.code}：{d.message}" + (f"（{html.escape(d.path)}）" if d.path else "")
        for d in manifest.diagnostics
    )
    if not manifest.diagnostics:
        lines.append("支持范围内未出现扫描故障。")
    lines.extend(
        [
            "",
            "## 补丁",
            "",
            "补丁仅为文档修改建议，需要人工审阅后显式 apply。",
            "内存复扫通过只代表支持范围内的目标告警消失，不代表文档整体正确。",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: ScanReport, out: Path, formats: set[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if "json" in formats:
        (out / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    if "md" in formats:
        (out / "report.md").write_text(markdown_report(report), encoding="utf-8")
    (out / "manifest.json").write_text(report.manifest.model_dump_json(indent=2), encoding="utf-8")
    for name in ("entities", "facts", "claims", "candidates", "judgments", "findings", "rejected"):
        (out / f"{name}.jsonl").write_text(
            "".join(item.model_dump_json() + "\n" for item in getattr(report, name)),
            encoding="utf-8",
        )
    (out / "snapshot.json").write_text(report.snapshot.model_dump_json(indent=2), encoding="utf-8")
    (out / "summary.json").write_text(
        json.dumps(
            {
                "status": report.manifest.status,
                "confirmed_count": report.confirmed_count,
                "ignored_count": report.ignored_count,
                "uncertain_count": report.uncertain_count,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
