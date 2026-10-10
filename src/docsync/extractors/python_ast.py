import ast
from dataclasses import dataclass
from typing import Any

from docsync.models import CodeEntity, CodeFact, Diagnostic, Parameter, ParameterKind
from docsync.repository import SnapshotData
from docsync.utils import literal_value, span_for, stable_id


@dataclass(frozen=True)
class CodeExtractionResult:
    entities: list[CodeEntity]
    facts: list[CodeFact]
    diagnostics: list[Diagnostic]


_UNKNOWN = object()


def _static_value(
    node: ast.expr,
    bindings: dict[str, Any],
    functions: dict[str, Any],
    *,
    dict_available: bool,
) -> Any:
    """Evaluate only side-effect-free literal syntax with proven local bindings."""

    if isinstance(node, ast.Constant):
        return node.value if literal_value(node.value) is not None else _UNKNOWN
    if isinstance(node, ast.Name):
        return bindings.get(node.id, _UNKNOWN)
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        values = [
            _static_value(item, bindings, functions, dict_available=dict_available)
            for item in node.elts
        ]
        if any(item is _UNKNOWN for item in values):
            return _UNKNOWN
        if isinstance(node, ast.List):
            return values
        if isinstance(node, ast.Tuple):
            return tuple(values)
        try:
            return set(values)
        except TypeError:
            return _UNKNOWN
    if isinstance(node, ast.Dict):
        result: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            value = _static_value(value_node, bindings, functions, dict_available=dict_available)
            if value is _UNKNOWN:
                return _UNKNOWN
            if key_node is None:
                if type(value) is not dict:
                    return _UNKNOWN
                result.update(value)
                continue
            key = _static_value(key_node, bindings, functions, dict_available=dict_available)
            if key is _UNKNOWN:
                return _UNKNOWN
            try:
                result[key] = value
            except TypeError:
                return _UNKNOWN
        return result if literal_value(result) is not None else _UNKNOWN
    if isinstance(node, ast.UnaryOp):
        operand = _static_value(node.operand, bindings, functions, dict_available=dict_available)
        if operand is _UNKNOWN or type(operand) not in {int, float}:
            return _UNKNOWN
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        return _UNKNOWN
    if isinstance(node, ast.BinOp):
        left = _static_value(node.left, bindings, functions, dict_available=dict_available)
        right = _static_value(node.right, bindings, functions, dict_available=dict_available)
        if left is _UNKNOWN or right is _UNKNOWN:
            return _UNKNOWN
        try:
            if isinstance(node.op, ast.Add) and (
                (type(left) in {int, float} and type(right) in {int, float})
                or (type(left) is type(right) and type(left) in {str, tuple, list})
            ):
                value = left + right
            elif (
                isinstance(node.op, ast.Sub)
                and type(left) in {int, float}
                and type(right) in {int, float}
            ):
                value = left - right
            else:
                return _UNKNOWN
        except (TypeError, ValueError, OverflowError):
            return _UNKNOWN
        return value if literal_value(value) is not None else _UNKNOWN
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if not node.args and not node.keywords and node.func.id in functions:
            return functions[node.func.id]
        if node.func.id == "dict" and dict_available and not node.args:
            call_result: dict[str, Any] = {}
            for keyword in node.keywords:
                if keyword.arg is None:
                    return _UNKNOWN
                value = _static_value(
                    keyword.value, bindings, functions, dict_available=dict_available
                )
                if value is _UNKNOWN:
                    return _UNKNOWN
                call_result[keyword.arg] = value
            return call_result
    return _UNKNOWN


def _pure_literal_return(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    bindings: dict[str, Any],
    functions: dict[str, Any],
    *,
    dict_available: bool,
) -> Any:
    if (
        isinstance(node, ast.AsyncFunctionDef)
        or node.decorator_list
        or node.args.posonlyargs
        or node.args.args
        or node.args.kwonlyargs
        or node.args.vararg
        or node.args.kwarg
        or len(node.body) != 1
        or not isinstance(node.body[0], ast.Return)
        or node.body[0].value is None
    ):
        return _UNKNOWN
    return _static_value(node.body[0].value, bindings, functions, dict_available=dict_available)


def _definition_contexts(
    tree: ast.Module,
) -> dict[int, tuple[dict[str, Any], dict[str, Any], bool]]:
    """Capture literal bindings as they exist when each definition executes."""

    contexts: dict[int, tuple[dict[str, Any], dict[str, Any], bool]] = {}
    bindings: dict[str, Any] = {}
    functions: dict[str, Any] = {}
    dict_available = True
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            contexts[id(statement)] = (dict(bindings), dict(functions), dict_available)
            value = _pure_literal_return(
                statement, bindings, functions, dict_available=dict_available
            )
            if value is _UNKNOWN:
                functions.pop(statement.name, None)
            else:
                functions[statement.name] = value
            bindings.pop(statement.name, None)
            if statement.name == "dict":
                dict_available = False
            continue
        if isinstance(statement, ast.ClassDef):
            contexts[id(statement)] = (dict(bindings), dict(functions), dict_available)
            bindings.pop(statement.name, None)
            functions.pop(statement.name, None)
            if statement.name == "dict":
                dict_available = False
            continue
        if isinstance(statement, ast.Assign | ast.AnnAssign):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            value_node = statement.value
            value = (
                _static_value(value_node, bindings, functions, dict_available=dict_available)
                if value_node is not None
                else _UNKNOWN
            )
            for target in targets:
                if isinstance(target, ast.Name):
                    if value is _UNKNOWN:
                        bindings.pop(target.id, None)
                    else:
                        bindings[target.id] = value
                    functions.pop(target.id, None)
                    if target.id == "dict":
                        dict_available = False
            continue
        if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
            synthetic = ast.BinOp(
                left=ast.Name(id=statement.target.id, ctx=ast.Load()),
                op=statement.op,
                right=statement.value,
            )
            value = _static_value(synthetic, bindings, functions, dict_available=dict_available)
            if value is _UNKNOWN:
                bindings.pop(statement.target.id, None)
            else:
                bindings[statement.target.id] = value
            continue
        for child in ast.walk(statement):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store | ast.Del):
                bindings.pop(child.id, None)
                functions.pop(child.id, None)
                if child.id == "dict":
                    dict_available = False
    return contexts


@dataclass
class _ConfigLeaf:
    path: tuple[str, ...]
    node: ast.expr | ast.stmt
    value: Any


def _config_leaves(
    node: ast.expr,
    bindings: dict[str, Any],
    functions: dict[str, Any],
    *,
    dict_available: bool,
    prefix: tuple[str, ...] = (),
) -> dict[tuple[str, ...], _ConfigLeaf]:
    """Flatten explicit string-key mappings while retaining unknown leaf evidence."""

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        if not dict_available or node.args or any(item.arg is None for item in node.keywords):
            return {}
        return {
            (*prefix, item.arg): _ConfigLeaf(
                (*prefix, item.arg),
                item.value,
                _static_value(item.value, bindings, functions, dict_available=dict_available),
            )
            for item in node.keywords
            if item.arg is not None
        }
    if not isinstance(node, ast.Dict):
        return {
            prefix: _ConfigLeaf(
                prefix,
                node,
                _static_value(node, bindings, functions, dict_available=dict_available),
            )
        }

    leaves: dict[tuple[str, ...], _ConfigLeaf] = {}
    seen: set[str] = set()
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        if key_node is None or not (
            isinstance(key_node, ast.Constant) and isinstance(key_node.value, str)
        ):
            for leaf in leaves.values():
                leaf.value = _UNKNOWN
            continue
        key = key_node.value
        child_prefix = (*prefix, key)
        child = _config_leaves(
            value_node,
            bindings,
            functions,
            dict_available=dict_available,
            prefix=child_prefix,
        )
        if key in seen:
            for path, leaf in leaves.items():
                if path[: len(child_prefix)] == child_prefix:
                    leaf.value = _UNKNOWN
            for leaf in child.values():
                leaf.value = _UNKNOWN
        else:
            for path in [path for path in leaves if path[: len(child_prefix)] == child_prefix]:
                del leaves[path]
        leaves.update(child)
        seen.add(key)
    return leaves


def _mark_unknown(leaves: dict[tuple[str, ...], _ConfigLeaf]) -> None:
    for leaf in leaves.values():
        leaf.value = _UNKNOWN


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
        definition_contexts = _definition_contexts(tree)

        def visit(
            body: list[ast.stmt],
            parents: tuple[str, ...] = (),
            inherited_safe: bool = True,
            literal_bindings: dict[str, Any] | None = None,
            literal_functions: dict[str, Any] | None = None,
            dict_available: bool = True,
        ) -> None:
            literal_bindings = literal_bindings or {}
            literal_functions = literal_functions or {}
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
                    context = definition_contexts.get(
                        id(node), (literal_bindings, literal_functions, dict_available)
                    )
                    visit(
                        node.body,
                        (*parents, node.name),
                        inherited_safe
                        and not node.decorator_list
                        and not node.bases
                        and not node.keywords
                        and node.name not in rebound,
                        *context,
                    )
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or (
                    node.name.startswith("_") and node.name != "__init__"
                ):
                    continue
                context = definition_contexts.get(
                    id(node), (literal_bindings, literal_functions, dict_available)
                )
                definition_bindings, definition_functions, definition_dict_available = context
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
                    static_value = (
                        _static_value(
                            default,
                            definition_bindings,
                            definition_functions,
                            dict_available=definition_dict_available,
                        )
                        if default is not None and safe
                        else _UNKNOWN
                    )
                    value = literal_value(static_value) if static_value is not _UNKNOWN else None
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
        # Evaluate explicit module initialization in source order. Supported operations are
        # deliberately narrow: literal assignment, literal +=/-=, and dict.update with an
        # explicit mapping. Every other mutation keeps the affected facts UNKNOWN.
        config_states: dict[str, dict[tuple[str, ...], _ConfigLeaf]] = {}
        config_nodes: dict[str, ast.Assign | ast.AnnAssign] = {}
        runtime_bindings: dict[str, Any] = {}
        runtime_functions: dict[str, Any] = {}
        runtime_dict_available = True
        for statement in tree.body:
            handled_names: set[str] = set()
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                value = _pure_literal_return(
                    statement,
                    runtime_bindings,
                    runtime_functions,
                    dict_available=runtime_dict_available,
                )
                if value is _UNKNOWN:
                    runtime_functions.pop(statement.name, None)
                else:
                    runtime_functions[statement.name] = value
                runtime_bindings.pop(statement.name, None)
                if statement.name == "dict":
                    runtime_dict_available = False
                continue
            if isinstance(statement, ast.ClassDef):
                runtime_bindings.pop(statement.name, None)
                runtime_functions.pop(statement.name, None)
                if statement.name == "dict":
                    runtime_dict_available = False
                continue
            if isinstance(statement, ast.Assign | ast.AnnAssign):
                targets = (
                    statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                )
                value_node = statement.value
                value = (
                    _static_value(
                        value_node,
                        runtime_bindings,
                        runtime_functions,
                        dict_available=runtime_dict_available,
                    )
                    if value_node is not None
                    else _UNKNOWN
                )
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    handled_names.add(target.id)
                    runtime_functions.pop(target.id, None)
                    if value is _UNKNOWN:
                        runtime_bindings.pop(target.id, None)
                    else:
                        runtime_bindings[target.id] = value
                    if target.id == "dict":
                        runtime_dict_available = False
                    if not target.id.isupper() or value_node is None:
                        continue
                    config_nodes.setdefault(target.id, statement)
                    config_states[target.id] = _config_leaves(
                        value_node,
                        runtime_bindings,
                        runtime_functions,
                        dict_available=runtime_dict_available,
                    )
            elif isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
                key = statement.target.id
                handled_names.add(key)
                synthetic = ast.BinOp(
                    left=ast.Name(id=key, ctx=ast.Load()),
                    op=statement.op,
                    right=statement.value,
                )
                value = _static_value(
                    synthetic,
                    runtime_bindings,
                    runtime_functions,
                    dict_available=runtime_dict_available,
                )
                if value is _UNKNOWN:
                    runtime_bindings.pop(key, None)
                else:
                    runtime_bindings[key] = value
                if key in config_states:
                    config_states[key] = {(): _ConfigLeaf((), statement, value)}
            elif (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Attribute)
                and statement.value.func.attr == "update"
                and isinstance(statement.value.func.value, ast.Name)
            ):
                key = statement.value.func.value.id
                handled_names.add(key)
                call = statement.value
                update_node: ast.expr | None = None
                if len(call.args) == 1 and not call.keywords:
                    update_node = call.args[0]
                elif not call.args and all(item.arg is not None for item in call.keywords):
                    update_node = ast.Dict(
                        keys=[ast.Constant(item.arg) for item in call.keywords],
                        values=[item.value for item in call.keywords],
                    )
                    ast.copy_location(update_node, call)
                    ast.fix_missing_locations(update_node)
                if key in config_states and update_node is not None:
                    updates = _config_leaves(
                        update_node,
                        runtime_bindings,
                        runtime_functions,
                        dict_available=runtime_dict_available,
                    )
                    update_value = _static_value(
                        update_node,
                        runtime_bindings,
                        runtime_functions,
                        dict_available=runtime_dict_available,
                    )
                    current = runtime_bindings.get(key, _UNKNOWN)
                    if type(current) is dict and type(update_value) is dict:
                        merged = dict(current)
                        merged.update(update_value)
                        runtime_bindings[key] = merged
                        for update_path, leaf in updates.items():
                            if not update_path:
                                _mark_unknown(config_states[key])
                                break
                            update_prefix = update_path[:1]
                            for old_path in [
                                path for path in config_states[key] if path[:1] == update_prefix
                            ]:
                                del config_states[key][old_path]
                            config_states[key][update_path] = leaf
                    else:
                        runtime_bindings.pop(key, None)
                        _mark_unknown(config_states[key])
                elif key in config_states:
                    runtime_bindings.pop(key, None)
                    _mark_unknown(config_states[key])

            for child in ast.walk(statement):
                if not isinstance(child, ast.Name) or child.id in handled_names:
                    continue
                if isinstance(child.ctx, ast.Store | ast.Del):
                    runtime_bindings.pop(child.id, None)
                    runtime_functions.pop(child.id, None)
                if child.id in config_states:
                    _mark_unknown(config_states[child.id])

        for key, leaves in config_states.items():
            node = config_nodes[key]
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
            for leaf_path, leaf in leaves.items():
                if leaf_path:
                    subject = ".".join((module, key, *leaf_path[:-1]))
                    prop = leaf_path[-1]
                else:
                    subject = module
                    prop = key
                expression = ast.get_source_segment(text, leaf.node) or ""
                value = literal_value(leaf.value) if leaf.value is not _UNKNOWN else None
                fact_span = span_for(
                    path,
                    data,
                    offsets[leaf.node.lineno - 1] + leaf.node.col_offset,
                    offsets[(leaf.node.end_lineno or leaf.node.lineno) - 1]
                    + (leaf.node.end_col_offset or 0),
                )
                facts.append(
                    CodeFact(
                        fact_id=stable_id("config", config_id, subject, prop, fact_span.blob_hash),
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
