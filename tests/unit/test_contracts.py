import pytest
from pydantic import ValidationError

from docsync.config import ScanConfig
from docsync.models import SourceSpan
from docsync.utils import typed_literal


@pytest.mark.parametrize("path", ["../README.md", "/tmp/README.md", "C:/README.md", "a\\README.md"])
def test_span_rejects_unsafe_paths(path):
    with pytest.raises(ValidationError):
        SourceSpan(
            path=path, start_line=1, end_line=1, start_byte=0, end_byte=1, blob_hash="0" * 64
        )


def test_config_forbids_executable_extras():
    with pytest.raises(ValidationError):
        ScanConfig.model_validate({"plugin": "execute_me.py"})


@pytest.mark.parametrize(
    "expression", ["factory()", "os.getenv('X')", "x if ready else 1", "float('nan')"]
)
def test_dynamic_literals_are_unknown(expression):
    assert typed_literal(expression) is None


def test_literals_retain_nested_types():
    assert typed_literal("True") != typed_literal("1")
    assert typed_literal("[True]") != typed_literal("[1]")
    assert typed_literal("None") is not None
    assert typed_literal("{'b': 2, 'a': 1}") == typed_literal("{'a': 1, 'b': 2}")
    assert typed_literal("[1, 2]") != typed_literal("(1, 2)")
