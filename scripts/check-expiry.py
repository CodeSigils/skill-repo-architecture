"""Reject expired documentation and external-evidence freshness markers."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from pathlib import Path

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
    if reviewed is not None and (today - reviewed).days > SECURITY_REVIEW_MAX_AGE_DAYS:
        problems.append(f"SECURITY.md: review is {(today - reviewed).days} days old")


def check_external_evidence(today: date, problems: list[str]) -> None:
    path = ROOT / "docs" / "evidence-urls.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"{path.relative_to(ROOT)}: unreadable evidence index ({exc})")
        return
    for index, entry in enumerate(data.get("urls", [])):
        if entry.get("status") != "active" or entry.get("monitor", True) is False:
            continue
        context = f"{path.relative_to(ROOT)}: urls[{index}]"
        value = entry.get("last_verified")
        if not isinstance(value, str):
            problems.append(f"{context}: missing last_verified")
            continue
        verified = parse_date(value, context, problems)
        if verified is not None and (today - verified).days > EXTERNAL_EVIDENCE_MAX_AGE_DAYS:
            problems.append(f"{context}: last verified {(today - verified).days} days ago")


def main() -> int:
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
