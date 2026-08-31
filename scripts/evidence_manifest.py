"""Shared validated loader for the external-evidence URL manifest.

docs/evidence-urls.json is the machine-readable source of truth for monitored
and snapshot external URLs. verify-urls.py, check-expiry.py, and validate.py
each used to hand-roll partial, divergent views of the same file; this module
is the single validated parser they all consume.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from evaluation_contract import object_mapping

EVIDENCE_SCHEMA_VERSION = 3
EVIDENCE_STATUSES = frozenset({"active", "retired"})


@dataclass(frozen=True)
class EvidenceEntry:
    """Validated entry from the evidence manifest."""

    name: str
    url: str
    expected_statuses: tuple[int, ...]
    monitor: bool
    content_type: str | None
    required_text: tuple[str, ...]
    source_section: str
    status: str
    last_verified: str | None
    notes: str | None


@dataclass(frozen=True)
class EvidenceManifest:
    """Validated evidence manifest."""

    entries: tuple[EvidenceEntry, ...]


def _absolute_http_url(value: object) -> bool:
    """Return whether value is an absolute http(s) URL string."""
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_evidence_manifest(path: Path) -> EvidenceManifest:
    """Load the evidence manifest and validate every consumed field.

    Collects all problems and raises one ValueError describing them so
    callers can report the full manifest state instead of the first failure.
    """
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read manifest: {exc}") from exc

    problems: list[str] = []
    try:
        data = object_mapping(raw, f"{path}: top level")
    except TypeError as exc:
        raise ValueError(str(exc)) from exc

    version = data.get("version")
    if type(version) is not int or version != EVIDENCE_SCHEMA_VERSION:
        problems.append(f"{path}: version must be {EVIDENCE_SCHEMA_VERSION}")
    description = data.get("description")
    if description is not None and not isinstance(description, str):
        problems.append(f"{path}: description must be a string")

    raw_urls = data.get("urls")
    if not isinstance(raw_urls, list) or not raw_urls:
        problems.append(f"{path}: urls must be a non-empty list")
        raise ValueError("\n".join(problems))

    entries: list[EvidenceEntry] = []
    seen_names: set[str] = set()
    seen_urls: set[str] = set()
    for index, raw_entry in enumerate(raw_urls):
        context = f"{path}: urls[{index}]"
        if not isinstance(raw_entry, dict):
            problems.append(f"{context}: expected an object")
            continue
        missing = [
            key
            for key in ("name", "url", "expected_statuses", "source_section", "status")
            if key not in raw_entry
        ]
        if missing:
            problems.append(f"{context}: missing required field(s): {', '.join(missing)}")
            continue

        name = raw_entry["name"]
        if not isinstance(name, str) or not name:
            problems.append(f"{context}: name must be a non-empty string")
        elif name.casefold() in seen_names:
            problems.append(f"{context}: duplicate name {name!r}")
        else:
            seen_names.add(name.casefold())
        url = raw_entry["url"]
        if not _absolute_http_url(url):
            problems.append(f"{context}: url must be an absolute HTTP(S) URL")
        elif url in seen_urls:
            problems.append(f"{context}: duplicate url {url!r}")
        else:
            seen_urls.add(url)

        statuses: tuple[int, ...] = ()
        expected_statuses: object = raw_entry["expected_statuses"]
        if not isinstance(expected_statuses, list) or not expected_statuses:
            problems.append(f"{context}: expected_statuses must be a non-empty list")
        elif not all(
            type(status) is int and 100 <= status <= 599 for status in expected_statuses
        ):
            problems.append(f"{context}: expected_statuses must contain HTTP status integers")
        else:
            statuses = tuple(expected_statuses)

        monitor: bool = True
        if "monitor" in raw_entry:
            raw_monitor = raw_entry["monitor"]
            if type(raw_monitor) is not bool:
                problems.append(f"{context}: monitor must be a boolean")
            else:
                monitor = raw_monitor

        content_type: str | None = None
        if "content_type" in raw_entry:
            raw_content_type = raw_entry["content_type"]
            if raw_content_type != "json":
                problems.append(f"{context}: content_type must be 'json' when present")
            else:
                content_type = raw_content_type

        required_text: tuple[str, ...] = ()
        if "required_text" in raw_entry:
            raw_required_text = raw_entry["required_text"]
            if not isinstance(raw_required_text, list) or not all(
                isinstance(anchor, str) and anchor for anchor in raw_required_text
            ):
                problems.append(f"{context}: required_text must be a list of non-empty strings")
            else:
                required_text = tuple(raw_required_text)

        source_section = raw_entry["source_section"]
        if not isinstance(source_section, str) or not source_section:
            problems.append(f"{context}: source_section must be a non-empty string")

        status = raw_entry["status"]
        if not isinstance(status, str) or status not in EVIDENCE_STATUSES:
            problems.append(f"{context}: status must be one of {sorted(EVIDENCE_STATUSES)}")
        if status == "retired" and monitor:
            problems.append(f"{context}: retired entries must set monitor to false")

        last_verified: str | None = None
        if "last_verified" in raw_entry:
            raw_last_verified = raw_entry["last_verified"]
            if not isinstance(raw_last_verified, str) or not raw_last_verified:
                problems.append(f"{context}: last_verified must be a non-empty string")
            else:
                last_verified = raw_last_verified

        notes: str | None = None
        if "notes" in raw_entry:
            raw_notes = raw_entry["notes"]
            if not isinstance(raw_notes, str) or not raw_notes:
                problems.append(f"{context}: notes must be a non-empty string")
            else:
                notes = raw_notes

        entries.append(
            EvidenceEntry(
                name=name,
                url=url,
                expected_statuses=statuses,
                monitor=monitor,
                content_type=content_type,
                required_text=required_text,
                source_section=source_section,
                status=status,
                last_verified=last_verified,
                notes=notes,
            )
        )

    if problems:
        raise ValueError("\n".join(problems))
    return EvidenceManifest(entries=tuple(entries))
