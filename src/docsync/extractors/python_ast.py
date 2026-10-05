import ast
from dataclasses import dataclass

from docsync.models import CodeEntity, CodeFact, Diagnostic, Parameter, ParameterKind
from docsync.repository import SnapshotData
from docsync.utils import span_for, stable_id, typed_literal


@dataclass(frozen=True)
class CodeExtractionResult:
    entities: list[CodeEntity]
    facts: list[CodeFact]
    diagnostics: list[Diagnostic]


def extract_code(snapshot: SnapshotData) -> CodeExtractionResult:
    entities: list[CodeEntity] = []
    facts: list[CodeFact] = []
    diagnostics: list[Diagnostic] = []
    module_trees: dict[str, tuple[str, ast.Module]] = {}
    for path, data in snapshot.blobs.items():
        if not path.endswith(".py"):
            continue
        text = data.decode("utf-8")
        try:
            tree = ast.parse(text, filename=path)
        except (SyntaxError, ValueError, RecursionError):
            diagnostics.append(
                Diagnostic(
                    code="PYTHON_PARSE_ERROR",
                    message="Cannot parse Python file",
                    stage="extraction",
                    path=path,
                )
            )
            continue
        offsets = [0]
        for line in data.splitlines(keepends=True):
            offsets.append(offsets[-1] + len(line))
        module = path[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module.removesuffix(".__init__")
        module_trees[module] = (path, tree)

        def visit(
            body: list[ast.stmt], parents: tuple[str, ...] = (), inherited_safe: bool = True
        ) -> None:
            definition_names = [
                statement.name
                for statement in body
                if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            ]
            rebound = {name for name in definition_names if definition_names.count(name) > 1}
            for statement in body:
                if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    continue
                if isinstance(statement, ast.Import | ast.ImportFrom):
                    rebound.update(
                        alias.asname or alias.name.split(".")[0] for alias in statement.names
                    )
                if any(
                    isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
                    for child in ast.walk(statement)
                ):
                    diagnostics.append(
                        Diagnostic(
                            code="CONDITIONAL_DEFINITION",
                            message="Conditional public definitions are not statically resolved",
                            stage="extraction",
                            path=path,
                        )
                    )
                for child in ast.walk(statement):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store | ast.Del):
                        rebound.add(child.id)
                    if isinstance(child, ast.Attribute) and isinstance(
                        child.ctx, ast.Store | ast.Del
                    ):
                        root = child.value
                        while isinstance(root, ast.Attribute | ast.Subscript):
                            root = root.value
                        if isinstance(root, ast.Name):
                            rebound.add(root.id)
            for node in body:
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    visit(
                        node.body,
                        (*parents, node.name),
                        inherited_safe
                        and not node.decorator_list
                        and not node.bases
                        and not node.keywords
                        and node.name not in rebound,
                    )
                if not isinstance(
                    node, ast.FunctionDef | ast.AsyncFunctionDef
                ) or node.name.startswith("_"):
                    continue
                name = ".".join((module, *parents, node.name))
                span = span_for(
                    path,
                    data,
                    offsets[node.lineno - 1] + node.col_offset,
                    offsets[(node.end_lineno or node.lineno) - 1] + (node.end_col_offset or 0),
                )
                entity_id = stable_id("entity", path, name, str(node.lineno))
                decorators = [ast.unparse(d) for d in node.decorator_list]
                safe = (
                    inherited_safe
                    and node.name not in rebound
                    and all(d in {"staticmethod", "classmethod"} for d in decorators)
                    and not any(d in rebound for d in decorators)
                )
                if not safe:
                    diagnostics.append(
                        Diagnostic(
                            code="DYNAMIC_FUNCTION",
                            message="Decorator or rebinding may change this public interface",
                            stage="extraction",
                            path=path,
                        )
                    )
                positional = [*node.args.posonlyargs, *node.args.args]
                defaults: list[ast.expr | None] = [None] * (
                    len(positional) - len(node.args.defaults)
                ) + list(node.args.defaults)
                parameters: list[Parameter] = []
                all_args = list(zip(positional, defaults, strict=True)) + list(
                    zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
                )
                for arg, default in all_args:
                    expression = (
                        ast.get_source_segment(text, default) if default is not None else None
                    )
                    value = typed_literal(expression) if expression is not None and safe else None
                    kind: ParameterKind = (
                        "POSITIONAL_ONLY"
                        if arg in node.args.posonlyargs
                        else (
                            "KEYWORD_ONLY"
                            if arg in node.args.kwonlyargs
                            else "POSITIONAL_OR_KEYWORD"
                        )
                    )
                    parameters.append(
                        Parameter(
                            name=arg.arg,
                            kind=kind,
                            required=default is None,
                            value_state="ABSENT"
                            if default is None
                            else ("KNOWN" if value is not None else "UNKNOWN"),
                            typed_value=value,
                            expression=expression,
                        )
                    )
                    if default is not None and expression is not None:
                        default_span = span_for(
                            path,
                            data,
                            offsets[default.lineno - 1] + default.col_offset,
                            offsets[(default.end_lineno or default.lineno) - 1]
                            + (default.end_col_offset or 0),
                        )
                        facts.append(
                            CodeFact(
                                fact_id=stable_id("fact", entity_id, arg.arg, span.blob_hash),
                                entity_id=entity_id,
                                subject=name,
                                property=arg.arg,
                                value_state="KNOWN" if value is not None else "UNKNOWN",
                                typed_value=value,
                                expression=expression,
                                span=default_span,
                            )
                        )
                variadics: list[tuple[ast.arg | None, ParameterKind]] = [
                    (node.args.vararg, "VAR_POSITIONAL"),
                    (node.args.kwarg, "VAR_KEYWORD"),
                ]
                for variadic, variadic_kind in variadics:
                    if variadic is not None:
                        parameters.append(
                            Parameter(
                                name=variadic.arg,
                                kind=variadic_kind,
                                required=False,
                                value_state="ABSENT",
                            )
                        )
                entities.append(
                    CodeEntity(
                        entity_id=entity_id,
                        kind="method"
                        if parents
                        else (
                            "async_function"
                            if isinstance(node, ast.AsyncFunctionDef)
                            else "function"
                        ),
                        qualified_name=name,
                        module=module,
                        signature=parameters,
                        decorators=decorators,
                        span=span,
                    )
                )
                facts.append(
                    CodeFact(
                        fact_id=stable_id("signature", entity_id, span.blob_hash),
                        entity_id=entity_id,
                        subject=name,
                        property="__signature__",
                        value_state="KNOWN" if safe else "UNKNOWN",
                        typed_value=None,
                        expression=data[span.start_byte : span.end_byte].decode("utf-8"),
                        span=span,
                        fact_kind="SIGNATURE",
                        parameters=parameters,
                        receiver="class"
                        if "classmethod" in decorators
                        else (
                            "instance" if parents and "staticmethod" not in decorators else "none"
                        ),
                    )
                )

        visit(tree.body)
        # Only explicit top-level uppercase constants and dict literals are config interfaces.
        assignments: dict[str, list[ast.Assign | ast.AnnAssign]] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign | ast.AnnAssign):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id.isupper()
                        and node.value is not None
                    ):
                        assignments.setdefault(target.id, []).append(node)
        for key, nodes in assignments.items():
            node = nodes[0]
            assert node.value is not None
            value_node = node.value
            entity_span = span_for(
                path,
                data,
                offsets[node.lineno - 1] + node.col_offset,
                offsets[(node.end_lineno or node.lineno) - 1] + (node.end_col_offset or 0),
            )
            config_id = stable_id("config", path, key)
            entities.append(
                CodeEntity(
                    entity_id=config_id,
                    kind="config",
                    qualified_name=module + "." + key,
                    module=module,
                    signature=[],
                    decorators=[],
                    span=entity_span,
                )
            )
            fields: list[tuple[str, str, ast.expr]] = [(module, key, value_node)]
            dict_unknown: set[str] = set()
            if isinstance(value_node, ast.Dict):
                fields = []
                for dict_key, dict_value in zip(value_node.keys, value_node.values, strict=True):
                    if dict_key is None:
                        # An unpack can override any explicit string key seen before it.
                        dict_unknown.update(prop for _, prop, _ in fields)
                    elif isinstance(dict_key, ast.Constant) and isinstance(dict_key.value, str):
                        prop = dict_key.value
                        if any(existing == prop for _, existing, _ in fields):
                            # Duplicate explicit keys remain conservative even though Python
                            # currently selects the last value.
                            dict_unknown.add(prop)
                        fields.append((module + "." + key, prop, dict_value))
                    elif not isinstance(dict_key, ast.Constant):
                        # A later runtime-computed key may equal any earlier string key.
                        dict_unknown.update(prop for _, prop, _ in fields)
                fields = list(
                    {
                        prop: (subject, prop, expression) for subject, prop, expression in fields
                    }.values()
                )
            for subject, prop, expression_node in fields:
                expression = ast.get_source_segment(text, expression_node) or ""
                value = (
                    typed_literal(expression)
                    if len(nodes) == 1 and prop not in dict_unknown
                    else None
                )
                # Any later mutation/update of the constant makes static defaults unknown.
                for statement in tree.body:
                    if statement is node or isinstance(
                        statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
                    ):
                        continue
                    if any(
                        isinstance(child, ast.Name) and child.id == key
                        for child in ast.walk(statement)
                    ):
                        value = None
                fact_span = span_for(
                    path,
                    data,
                    offsets[expression_node.lineno - 1] + expression_node.col_offset,
                    offsets[(expression_node.end_lineno or expression_node.lineno) - 1]
                    + (expression_node.end_col_offset or 0),
                )
                facts.append(
                    CodeFact(
                        fact_id=stable_id("config", config_id, prop, fact_span.blob_hash),
                        entity_id=config_id,
                        subject=subject,
                        property=prop,
                        value_state="KNOWN" if value is not None else "UNKNOWN",
                        typed_value=value,
                        expression=expression,
                        span=fact_span,
                        fact_kind="CONFIG",
                    )
                )

    # A direct module-level ``from module import name`` is a statically provable namespace
    # alias only when that local binding is unique. Clone facts with the exported subject while
    # retaining the original entity and source span. Star imports, conditional imports, missing
    # modules and any rebinding deliberately produce no alias facts.
    exports: list[tuple[str, str, str, str, str]] = []
    for module, (path, tree) in module_trees.items():
        binding_counts: dict[str, int] = {}
        candidates: list[tuple[ast.ImportFrom, ast.alias, str]] = []
        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    if alias.name == "*":
                        continue
                    binding = alias.asname or alias.name
                    binding_counts[binding] = binding_counts.get(binding, 0) + 1
                    candidates.append((statement, alias, binding))
                continue
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    binding = alias.asname or alias.name.split(".")[0]
                    binding_counts[binding] = binding_counts.get(binding, 0) + 1
                continue
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                binding_counts[statement.name] = binding_counts.get(statement.name, 0) + 1
                continue
            rebound = {
                child.id
                for child in ast.walk(statement)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store | ast.Del)
            }
            rebound.update(
                child.name
                for child in ast.walk(statement)
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            )
            for binding in rebound:
                binding_counts[binding] = binding_counts.get(binding, 0) + 1
        for statement, alias, binding in candidates:
            if binding_counts[binding] != 1 or statement.module is None:
                continue
            if statement.level:
                package = (
                    module.split(".") if path.endswith("/__init__.py") else module.split(".")[:-1]
                )
                parents = statement.level - 1
                if parents > len(package):
                    continue
                prefix = package[: len(package) - parents]
                source_module = ".".join([*prefix, statement.module])
            else:
                source_module = statement.module
            exports.append((module, path, source_module, alias.name, binding))

    seen = {
        (
            fact.subject,
            fact.property,
            fact.fact_kind,
            fact.entity_id,
            fact.span.path,
            fact.span.start_byte,
            fact.span.end_byte,
        )
        for fact in facts
    }
    for _ in range(len(exports) + 1):
        changed = False
        for target_module, target_path, source_module, imported_name, binding in exports:
            source = source_module + "." + imported_name
            exported_subject = target_module + "." + binding
            for fact in list(facts):
                if fact.subject != source and not fact.subject.startswith(source + "."):
                    continue
                subject = exported_subject + fact.subject[len(source) :]
                identity = (
                    subject,
                    fact.property,
                    fact.fact_kind,
                    fact.entity_id,
                    fact.span.path,
                    fact.span.start_byte,
                    fact.span.end_byte,
                )
                if identity in seen:
                    continue
                facts.append(
                    fact.model_copy(
                        update={
                            "fact_id": stable_id("export", target_path, subject, fact.fact_id),
                            "subject": subject,
                        }
                    )
                )
                seen.add(identity)
                changed = True
        if not changed:
            break
    return CodeExtractionResult(entities, facts, diagnostics)
