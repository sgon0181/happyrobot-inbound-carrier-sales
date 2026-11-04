"""The architecture gate must inspect nested helpers, not only public functions."""

from pathlib import Path

import pytest

from tools.check_service_shape import violations


@pytest.mark.parametrize("wrapped", ["function", "method", "nested_class"])
def test_complex_closures_are_rejected(tmp_path: Path, wrapped: str) -> None:
    branch = "if value:\n    value = False\n"
    body = "def nested(value):\n" + "".join(
        "    " + line for line in (branch * 11).splitlines(True)
    )
    if wrapped == "method":
        source = "class Thing:\n    def method(self):\n" + "".join(
            "        " + line for line in body.splitlines(True)
        )
    elif wrapped == "nested_class":
        source = "def outer():\n    class Thing:\n" + "".join(
            "        " + line for line in body.splitlines(True)
        )
    else:
        source = "def outer():\n" + "".join("    " + line for line in body.splitlines(True))
    path = tmp_path / "complex.py"
    path.write_text(source)
    assert any("nested complexity 12" in issue for issue in violations(path))


def test_small_simple_service_passes(tmp_path: Path) -> None:
    path = tmp_path / "simple.py"
    path.write_text("def okay():\n    return 1\n")
    assert violations(path) == []
