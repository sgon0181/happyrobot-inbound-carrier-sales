"""Keep the top-level documents consistent: each result is stated once, and no long dashes.

Test counts, coverage and evaluation scores change with every release. They live only in
docs/results.md, so the top-level documents cannot drift out of date. Reference and history
documents describe a named release or experiment and are exempt from the number rule.
"""

import re
import sys
from pathlib import Path

TOP_LEVEL = (
    "README.md",
    "ARCHITECTURE.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/build-description.md",
    "docs/decisions.md",
    "docs/recording-script.md",
    "docs/submission.md",
    "docs/reference/README.md",
    "docs/history/README.md",
    "service/README.md",
    "ops-app/README.md",
    "happyrobot/README.md",
)
COUNT = re.compile(
    r"\b\d[\d,]* (?:service |App |automated |platform )?(?:tests?|checks|checkpoints)\b",
    re.IGNORECASE,
)
COVERAGE = re.compile(r"\b\d+(?:\.\d+)?% (?:of )?(?:business|branch|coverage|statement)", re.I)
# A ratio counts as a score only near result words, and never inside a date such as 11/07/2026.
RATIO = re.compile(r"(?<![\d/])\d+ ?(?:/|of|out of) ?\d+(?![\d/])", re.IGNORECASE)
RESULT_WORDS = re.compile(
    r"\b(?:pass(?:ed|es)?|fail(?:ed|s)?|scor(?:e|ed|es)|grades?|graded|sweeps?|checks|"
    r"checkpoints?|evaluations?|tests?)\b",
    re.IGNORECASE,
)
LONG_DASHES = re.compile("[\u2013\u2014]")
DASH_EXEMPT = ("docs/history/archive/",)  # verbatim third-party research exports


def markdown_files(root: Path) -> list[str]:
    """Walk the tree rather than ask git, so the pre-commit copy of the index works too."""
    skip = {".git", ".venv", "node_modules", ".next", ".mypy_cache", ".ruff_cache"}
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if not skip.intersection(path.relative_to(root).parts)
    )


def results_in(text: str) -> list[str]:
    """Result-like phrases, ignoring markdown emphasis so **608** tests is still found."""
    plain = re.sub(r"[*_`]", "", text)
    found = [m.group(0) for pattern in (COUNT, COVERAGE) for m in pattern.finditer(plain)]
    for match in RATIO.finditer(plain):
        window = plain[max(0, match.start() - 60) : match.end() + 60]
        if RESULT_WORDS.search(window):
            found.append(match.group(0))
    return found


def problems(root: Path) -> list[str]:
    found = []
    for name in TOP_LEVEL:
        for phrase in results_in((root / name).read_text(encoding="utf-8")):
            found.append(f"{name}: '{phrase}' belongs in docs/results.md")
    for name in markdown_files(root):
        if name.startswith(DASH_EXEMPT):
            continue
        if LONG_DASHES.search((root / name).read_text(encoding="utf-8")):
            found.append(f"{name}: long dash character; use a comma, colon or parentheses")
    return found


def main(root: Path) -> int:
    found = problems(root)
    for line in found:
        print(line)
    if not found:
        print("Docs check: results are stated once and no long dashes were found.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parents[1]))
