import ast
import hashlib
import json
import math
from typing import Any, cast

from docsync.models import LiteralType, LiteralValue, SourceSpan


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(*parts: str) -> str:
    return digest(json.dumps(parts, ensure_ascii=False).encode())[:24]


def typed_literal(expression: str) -> LiteralValue | None:
    if len(expression) > 4096:
        return None
    try:
        node = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(node)) > 128:
            return None
        value = ast.literal_eval(node)

        def encode(item: Any, depth: int = 0) -> Any:
            if depth > 8:
                raise ValueError("Literal too deep")
            kind = type(item).__name__
            if item is None or type(item) in (bool, int, str):
                return [kind, item]
            if type(item) is float and math.isfinite(item):
                return [kind, item]
            if type(item) in (list, tuple, set):
                values = [encode(v, depth + 1) for v in item]
                if isinstance(item, set):
                    values.sort(key=lambda v: json.dumps(v, ensure_ascii=False))
                return [kind, values]
            if type(item) is dict:
                values = [[encode(k, depth + 1), encode(v, depth + 1)] for k, v in item.items()]
                values.sort(key=lambda v: json.dumps(v[0], ensure_ascii=False))
                return [kind, values]
            raise ValueError("Unsupported literal")

        canonical = json.dumps(encode(value), ensure_ascii=False, separators=(",", ":"))
        return LiteralValue(type=cast(LiteralType, type(value).__name__), canonical=canonical)
    except (ValueError, SyntaxError, TypeError, RecursionError, MemoryError):
        return None


def span_for(path: str, data: bytes, start: int, end: int) -> SourceSpan:
    return SourceSpan(
        path=path,
        start_line=data[:start].count(b"\n") + 1,
        end_line=data[: max(start, end - 1)].count(b"\n") + 1,
        start_byte=start,
        end_byte=end,
        blob_hash=digest(data),
    )


class DocSyncError(Exception):
    def __init__(self, code: str, message: str, stage: str = "repository") -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
