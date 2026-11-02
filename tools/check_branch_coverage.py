"""Fail unless branch coverage on the business rules is at least 90% (architecture section 14).

coverage's own fail_under mixes statements and branches, so high statement coverage can
hide untested branches. This reads only the branch counts from `coverage json`.
"""

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

GATED = ("service/core/", "service/calls.py", "service/bookings.py")
MINIMUM = 90.0


def branch_counts(files: Mapping[str, Any]) -> tuple[int, int]:
    """Covered and total branches across the gated files of a coverage JSON report."""
    summaries = [data["summary"] for path, data in files.items() if path.startswith(GATED)]
    if not summaries:
        raise ValueError("The coverage report has none of the gated files.")
    covered = sum(summary["covered_branches"] for summary in summaries)
    total = sum(summary["num_branches"] for summary in summaries)
    return covered, total


def main(report: Path) -> int:
    covered, total = branch_counts(json.loads(report.read_text())["files"])
    percent = 100.0 if total == 0 else 100 * covered / total
    print(f"Business-rule branch coverage: {covered}/{total} = {percent:.1f}% (minimum 90%)")
    return 0 if percent >= MINIMUM else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "coverage.json")))
