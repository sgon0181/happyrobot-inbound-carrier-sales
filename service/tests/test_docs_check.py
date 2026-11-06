"""The docs check keeps results in one place and rejects long dashes."""

from pathlib import Path

from tools.check_docs import TOP_LEVEL, problems


def _tree(tmp_path: Path) -> Path:
    for name in TOP_LEVEL:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Title\n\nPlain text.\n", encoding="utf-8")
    return tmp_path


def test_clean_tree_passes(tmp_path: Path) -> None:
    assert problems(_tree(tmp_path)) == []


def test_results_outside_results_page_are_reported(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "README.md").write_text("It passed 604 tests and scored 70/74.\n", encoding="utf-8")
    found = problems(root)
    assert any("'604 tests'" in line for line in found)
    assert any("'70/74'" in line for line in found)


def test_results_page_and_reference_may_state_numbers(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    for name in ("docs/results.md", "docs/reference/release.md"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("604 tests; 98.1% business branches.\n", encoding="utf-8")
    assert problems(root) == []


def test_long_dashes_are_reported_except_verbatim_archive(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "docs/note.md").write_text("A \u2014 B\n", encoding="utf-8")
    (root / "docs/history/archive").mkdir(parents=True)
    (root / "docs/history/archive/export.md").write_text("A \u2013 B\n", encoding="utf-8")
    expected = "docs/note.md: long dash character; use a comma, colon or parentheses"
    assert problems(root) == [expected]
