"""Position-preserving Markdown assertions, tables and Python call examples."""

import ast
import posixpath
import re
from dataclasses import dataclass

from markdown_it import MarkdownIt

from docsync.models import Diagnostic, DocumentClaim
from docsync.repository import SnapshotData
from docsync.utils import span_for, stable_id, typed_literal

IDENT = r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
VALUE = r"(?:`(?P<tick>[^`\r\n]+)`|(?P<plain>None|True|False|[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|'[^'\r\n]*'|\"[^\"\r\n]*\"))"
DEFAULT = re.compile(
    rf"`?(?P<param>[A-Za-z_]\w*)`?\s*(?:的\s*)?(?:(?:通常|可能|usually|sometimes)\s*)?"
    rf"(?:默认值?(?:为|是)?|defaults?\s+to|default(?:\s+value)?\s*(?:is|:|=))\s*{VALUE}",
    re.I,
)
HISTORICAL = re.compile(
    r"旧版|历史|迁移|反例|错误示例|legacy|historical|migration|invalid example|old(?:er)? version|\bv\d+(?:\.\d+)*\b",
    re.I,
)
QUALIFIED = re.compile(r"通常|可能|如果|当.+时|usually|sometimes|\bif\b|depending", re.I)


@dataclass(frozen=True)
class ClaimExtractionResult:
    claims: list[DocumentClaim]
    diagnostics: list[Diagnostic]


def subject_from(text: str) -> str:
    names = re.findall(rf"`({IDENT})(?:\([^`]*\))?`", text)
    if names:
        return names[-1]
    links = re.findall(rf"\[({IDENT})\]\(", text)
    if links:
        return links[-1]
    calls = re.findall(rf"\b({IDENT})\s*\(", text)
    if calls:
        return calls[-1]
    plain = text.strip().strip("# ")
    return plain if re.fullmatch(IDENT, plain) else ""


def source_hint(text: str, document_path: str) -> str | None:
    links = re.findall(r"\]\(([^\s()]+\.py)(?:#[^()]*)?\)", text)
    if len(set(links)) != 1 or ":" in links[0]:
        return None
    path = posixpath.normpath(posixpath.join(posixpath.dirname(document_path), links[0]))
    return path if not path.startswith(("../", "/")) else None


def extract_claims(snapshot: SnapshotData) -> ClaimExtractionResult:
    claims: list[DocumentClaim] = []
    diagnostics: list[Diagnostic] = []
    parser = MarkdownIt("commonmark").enable("table")
    for path, data in snapshot.blobs.items():
        if not path.endswith(".md"):
            continue
        text = data.decode("utf-8")
        lines = text.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line.encode("utf-8")))
        tokens = parser.parse(text)
        headings: list[tuple[int, str]] = []
        contexts: dict[int, str] = {}
        subjects: dict[int, str] = {}
        excluded: set[int] = set()
        heading_at: dict[int, tuple[int, str]] = {}
        tables: list[tuple[int, int]] = []
        for index, token in enumerate(tokens):
            if token.type == "heading_open" and token.map:
                heading_at[token.map[0]] = (int(token.tag[1:]), tokens[index + 1].content)
            if token.type == "table_open" and token.map:
                tables.append((token.map[0], token.map[1]))
                excluded.update(range(*token.map))
            if token.type in {"fence", "code_block", "html_block"} and token.map:
                start, end = token.map
                excluded.update(range(start, end))
                if token.type == "fence":
                    closing = lines[end - 1].strip() if end > start + 1 else ""
                    if not re.fullmatch(
                        re.escape(token.markup[0]) + "{" + str(len(token.markup)) + ",}", closing
                    ):
                        diagnostics.append(
                            Diagnostic(
                                code="UNCLOSED_FENCE",
                                message="Unclosed Markdown code fence",
                                stage="extraction",
                                path=path,
                            )
                        )

        def add_value(
            number: int,
            subject: str,
            prop: str,
            start: int,
            end: int,
            method: str = "markdown-rules/2",
        ) -> None:
            line, context = lines[number], contexts[number]
            raw_value = line[start:end]
            span = span_for(
                path, data, offsets[number], offsets[number] + len(line.rstrip("\r\n").encode())
            )
            value_span = span_for(
                path,
                data,
                offsets[number] + len(line[:start].encode()),
                offsets[number] + len(line[:end].encode()),
            )
            claims.append(
                DocumentClaim(
                    claim_id=stable_id(
                        "claim",
                        path,
                        str(span.start_byte),
                        str(value_span.start_byte),
                        span.blob_hash,
                    ),
                    subject=subject,
                    predicate=prop,
                    kind="CONFIG_ASSERTION"
                    if re.search(r"配置|\bconfig(?:uration)?\b", context, re.I)
                    else "DEFAULT_ASSERTION",
                    value=typed_literal(raw_value),
                    qualifiers=["conditional"] if QUALIFIED.search(context + line) else [],
                    version_scope="unresolved"
                    if HISTORICAL.search(context + " " + line)
                    else "current",
                    span=span,
                    value_span=value_span,
                    quote=line.rstrip("\r\n"),
                    extraction_method=method,
                    source_hint=source_hint(line + " " + context, path),
                )
            )

        for number, line in enumerate(lines):
            if number in heading_at:
                level, heading = heading_at[number]
                headings = [(depth, h) for depth, h in headings if depth < level] + [
                    (level, heading)
                ]
            contexts[number] = " ".join(h for _, h in headings)
            subjects[number] = next(
                (s for _, h in reversed(headings) if (s := subject_from(h))), ""
            )
            if number in excluded or number in heading_at:
                continue
            for match in DEFAULT.finditer(line):
                group = "tick" if match.group("tick") is not None else "plain"
                if group == "plain" and re.match(r"(?:\w|\.(?=\w))", line[match.end() :]):
                    continue
                subject = subject_from(line[: match.start()]) or subjects[number]
                add_value(
                    number, subject, match.group("param"), match.start(group), match.end(group)
                )
        for start, end in tables:

            def cells(line: str) -> list[tuple[str, int, int]]:
                if "\\|" in line:
                    return []
                return [
                    (m.group().strip(), m.start(), m.end())
                    for m in re.finditer(r"[^|\r\n]+", line)
                    if m.group().strip()
                ]

            header = cells(lines[start])
            labels = [cell[0].strip("`* ").lower() for cell in header]
            parameter = next(
                (
                    i
                    for i, label in enumerate(labels)
                    if label in {"parameter", "param", "name", "key", "参数", "配置项"}
                ),
                None,
            )
            default = next(
                (
                    i
                    for i, label in enumerate(labels)
                    if label in {"default", "default value", "默认", "默认值"}
                ),
                None,
            )
            if parameter is None or default is None:
                continue
            for number in range(start + 2, end):
                row = cells(lines[number])
                if len(row) != len(header):
                    continue
                prop = row[parameter][0].strip("` ")
                value, begin, _ = row[default]
                if not re.fullmatch(r"[A-Za-z_]\w*", prop):
                    continue
                expression = value[1:-1] if value.startswith("`") and value.endswith("`") else value
                begin = lines[number].find(value, begin) + (1 if value != expression else 0)
                add_value(
                    number,
                    subjects[number],
                    prop,
                    begin,
                    begin + len(expression),
                    "markdown-table/1",
                )
        for token in tokens:
            if token.type != "fence" or not token.map or token.info.strip() not in {"python", "py"}:
                continue
            try:
                tree = ast.parse(token.content)
            except (SyntaxError, ValueError, RecursionError):
                diagnostics.append(
                    Diagnostic(
                        code="PARTIAL_SNIPPET",
                        message="Python example is not parseable",
                        stage="extraction",
                        path=path,
                        affects_completeness=False,
                    )
                )
                continue
            aliases: dict[str, str] = {}
            instances: dict[str, str] = {}
            blocked: set[str] = set()
            bindings: list[tuple[ast.Call, str, bool, bool]] = []
            star_import = False

            def resolve(name: str) -> str:
                first, _, rest = name.partition(".")
                return aliases.get(first, first) + ("." + rest if rest else "")

            for statement in tree.body:
                dynamic = not isinstance(statement, ast.Expr | ast.Assign | ast.AnnAssign)
                for call in (n for n in ast.walk(statement) if isinstance(n, ast.Call)):
                    name = ast.unparse(call.func)
                    first, _, rest = name.partition(".")
                    bound = first in instances and bool(rest)
                    subject = instances[first] + "." + rest if bound else resolve(name)
                    if first in blocked:
                        subject = ""
                    bindings.append((call, subject, bound, dynamic or star_import))
                if (
                    isinstance(statement, ast.ImportFrom)
                    and statement.module
                    and not statement.level
                ):
                    for alias in statement.names:
                        if alias.name != "*":
                            binding = alias.asname or alias.name
                            blocked.discard(binding)
                            instances.pop(binding, None)
                            aliases[binding] = statement.module + "." + alias.name
                        else:
                            star_import = True
                elif isinstance(statement, ast.Import):
                    for alias in statement.names:
                        binding = alias.asname or alias.name.split(".")[0]
                        blocked.discard(binding)
                        instances.pop(binding, None)
                        aliases[binding] = alias.name if alias.asname else alias.name.split(".")[0]
                elif isinstance(statement, ast.Assign | ast.AnnAssign):
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    constructor = (
                        ast.unparse(statement.value.func)
                        if isinstance(statement.value, ast.Call)
                        else ""
                    )
                    resolved = resolve(constructor) if re.fullmatch(IDENT, constructor) else ""
                    for target in targets:
                        if isinstance(target, ast.Name):
                            aliases.pop(target.id, None)
                            instances.pop(target.id, None)
                            blocked.add(target.id)
                            if resolved:
                                blocked.discard(target.id)
                                instances[target.id] = resolved
                elif not isinstance(statement, ast.Expr):
                    # Any unsupported scope/flow can rebind imports or receiver variables.
                    blocked.update(
                        n.id
                        for n in ast.walk(statement)
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store | ast.Del)
                    )
            start, end = token.map
            span = span_for(path, data, offsets[start], offsets[end])
            for call_index, (node, subject, bound, dynamic) in enumerate(bindings):
                context = contexts[start]
                claims.append(
                    DocumentClaim(
                        claim_id=stable_id(
                            "example", path, str(start), str(call_index), span.blob_hash
                        ),
                        subject=subject,
                        predicate="__signature__",
                        kind="CALL_EXAMPLE",
                        value=None,
                        span=span,
                        quote=data[span.start_byte : span.end_byte].decode(),
                        positional_count=len(node.args),
                        keyword_names=[k.arg for k in node.keywords if k.arg is not None],
                        unpacking=any(isinstance(a, ast.Starred) for a in node.args)
                        or any(k.arg is None for k in node.keywords),
                        bound_receiver=bound,
                        version_scope="unresolved" if HISTORICAL.search(context) else "current",
                        qualifiers=(["conditional"] if QUALIFIED.search(context) else [])
                        + (["dynamic_scope"] if dynamic else []),
                        source_hint=source_hint(context, path),
                        extraction_method="markdown-call/2",
                    )
                )
    return ClaimExtractionResult(claims, diagnostics)
