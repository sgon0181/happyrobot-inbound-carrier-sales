"""The coverage gate counts branches only, so high statement coverage cannot hide untested ones."""

import json
from pathlib import Path

import pytest

from tools.check_branch_coverage import branch_counts, main


def summary(covered: int, total: int, percent: float = 100.0) -> dict[str, object]:
    return {
        "summary": {"covered_branches": covered, "num_branches": total, "percent_covered": percent}
    }


def test_only_the_business_rule_files_count() -> None:
    files = {
        "service/core/pricing.py": summary(9, 10),
        "service/calls.py": summary(1, 2),
        "service/adapters/tms/client.py": summary(0, 50),  # adapters are not gated
    }
    assert branch_counts(files) == (10, 12)


def test_a_report_without_any_gated_file_is_refused() -> None:
    with pytest.raises(ValueError):
        branch_counts({"service/adapters/tms/client.py": summary(1, 1)})


def test_half_the_branches_fails_even_when_combined_coverage_is_high(tmp_path: Path) -> None:
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"files": {"service/core/x.py": summary(1, 2, percent=92.31)}}))
    assert main(report) == 1


def test_full_branch_coverage_passes(tmp_path: Path) -> None:
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"files": {"service/core/x.py": summary(2, 2)}}))
    assert main(report) == 0
