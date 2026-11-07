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
COVERAGE = re.compile(
    r"\b\d+(?:\.\d+)?% (?:of )?(?:business|branch|coverage|statement)"
    r"|\bcoverage\b\W{1,3}\d+(?:\.\d+)?%",
    re.IGNORECASE,
)
# A ratio is a score only near result words. Full dates (11/07/2026) never match, and a short
# slash date (on 11/07, 03/15) is recognized by its leading zero, a larger first number or a
# date word before it. Real scores such as 70/74 or 10/10 are still reported.
RATIO = re.compile(r"(?<![\d/])(\d+) ?(/|of|out of) ?(\d+)(?![\d/])", re.IGNORECASE)
DATE_WORDS = ("on", "since", "until", "from", "by", "dated")
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
        if RESULT_WORDS.search(window) and not _short_date(match, plain):
            found.append(match.group(0))
    return found


def _short_date(match: re.Match[str], text: str) -> bool:
    first, separator, second = match.groups()
    if separator != "/":
        return False
    before = text[: match.start()].split()
    return (
        first.startswith("0")
        or second.startswith("0")
        or int(first) > int(second)
        or bool(before and before[-1].lower() in DATE_WORDS)
    )


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
