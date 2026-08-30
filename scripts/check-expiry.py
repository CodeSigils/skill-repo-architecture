"""Reject expired documentation and external-evidence freshness markers."""

from __future__ import annotations

import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from evidence_manifest import load_evidence_manifest

ROOT = Path(__file__).resolve().parents[1]
EXPIRES_RE = re.compile(r"^\*\*Expires:\*\* (?P<date>\d{4}-\d{2}-\d{2})$", re.MULTILINE)
LAST_REVIEWED_RE = re.compile(r"^Last reviewed: (?P<date>\d{4}-\d{2}-\d{2})\.$", re.MULTILINE)
SECURITY_REVIEW_MAX_AGE_DAYS = 365
EXTERNAL_EVIDENCE_MAX_AGE_DAYS = 90


def parse_date(value: str, context: str, problems: list[str]) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        problems.append(f"{context}: invalid date {value!r}")
        return None


def age_in_days(value: date, today: date, context: str, problems: list[str]) -> int | None:
    """Return a non-negative age, reporting future-dated evidence as invalid."""
    age = (today - value).days
    if age < 0:
        problems.append(f"{context}: date {value.isoformat()} is in the future")
        return None
    return age


def check_explicit_expiries(today: date, problems: list[str]) -> None:
    paths = [*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md"), *(ROOT / "skills").rglob("*.md")]
    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8")
        for match in EXPIRES_RE.finditer(text):
            expiry = parse_date(match.group("date"), str(path.relative_to(ROOT)), problems)
            if expiry is not None and expiry < today:
                problems.append(f"{path.relative_to(ROOT)}: expired {expiry.isoformat()}")


def check_security_review(today: date, problems: list[str]) -> None:
    path = ROOT / "SECURITY.md"
    text = path.read_text(encoding="utf-8")
    match = LAST_REVIEWED_RE.search(text)
    if match is None:
        problems.append("SECURITY.md: missing 'Last reviewed: YYYY-MM-DD.' marker")
        return
    reviewed = parse_date(match.group("date"), "SECURITY.md", problems)
    if reviewed is not None:
        age = age_in_days(reviewed, today, "SECURITY.md", problems)
        if age is not None and age > SECURITY_REVIEW_MAX_AGE_DAYS:
            problems.append(f"SECURITY.md: review is {age} days old")


def check_external_evidence(today: date, problems: list[str]) -> None:
    path = ROOT / "docs" / "evidence-urls.json"
    try:
        entries = load_evidence_manifest(path).entries
    except (OSError, ValueError) as exc:
        problems.append(f"{path.relative_to(ROOT)}: {exc}")
        return
    for index, entry in enumerate(entries):
        context = f"{path.relative_to(ROOT)}: urls[{index}]"
        if entry.status != "active" or not entry.monitor:
            continue
        value = entry.last_verified
        if value is None:
            problems.append(f"{context}: missing last_verified")
            continue
        verified = parse_date(value, context, problems)
        if verified is not None:
            age = age_in_days(verified, today, context, problems)
            if age is not None and age > EXTERNAL_EVIDENCE_MAX_AGE_DAYS:
                problems.append(f"{context}: last verified {age} days ago")


def run_self_tests() -> int:
    problems: list[str] = []
    today = date(2026, 8, 30)
    assert age_in_days(date(2026, 8, 29), today, "test", problems) == 1
    assert problems == []
    assert age_in_days(date(2026, 8, 31), today, "test", problems) is None
    assert problems == ["test: date 2026-08-31 is in the future"]
    print("PASS: check-expiry.py self-tests")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return run_self_tests()
    today = datetime.now(tz=UTC).date()
    problems: list[str] = []
    check_explicit_expiries(today, problems)
    check_security_review(today, problems)
    check_external_evidence(today, problems)

    if problems:
        print("Freshness check failures:")
        for item in problems:
            print(f"- {item}")
        return 1
    print("no expired freshness markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
