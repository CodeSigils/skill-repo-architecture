#!/usr/bin/env python3
"""Validate skill-repo-architecture source integrity."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "skill-repo-architecture"
SKILL = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"
IGNORE_EXPIRY = {"PASS", None}

ALLOWED_FIELDS = {
    "name", "description", "version", "author", "license",
    "tier", "ref", "compatibility", "metadata",
}
REQUIRED_SECTIONS = {"## When to Use", "## Verification Checklist"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md does not start with YAML frontmatter")
    try:
        _, raw, _ = text.split("---\n", 2)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")
    data = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip().strip('"')
    extra = set(data) - ALLOWED_FIELDS
    if extra:
        fail(f"unsupported frontmatter fields: {sorted(extra)}")
    if data.get("name") != "skill-repo-architecture":
        fail("frontmatter name must be skill-repo-architecture")
    if len(data.get("description", "").split()) < 12:
        fail("description too short to trigger reliably")
    return data


def check_skill() -> None:
    text = (SKILL).read_text(encoding="utf-8")
    body = text.split("---\n", 2)[2] if text.startswith("---\n") else text
    parse_frontmatter(text)
    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            fail(f"missing section: {sec}")
    # Portability check on body
    for needle in [".hermes", "hermes-verify"]:
        if needle in body:
            fail(f"body contains non-portable runtime marker: {needle}")


def check_references() -> None:
    ref_dir = ROOT / "references"
    if not ref_dir.exists():
        fail("references directory missing")
    skill_ref_dir = SKILL_DIR / "references"
    if not skill_ref_dir.exists():
        fail("payload references directory missing")
    # Root and payload must match
    root_files = sorted(ref_dir.glob("*.md"))
    payload_files = sorted(skill_ref_dir.glob("*.md"))
    root_set = {p.name for p in root_files}
    payload_set = {p.name for p in payload_files}
    if root_set != payload_set:
        extra = payload_set - root_set
        missing = root_set - payload_set
        if extra:
            fail(f"payload has extra references: {sorted(extra)}")
        if missing:
            fail(f"payload missing references: {sorted(missing)}")


def check_readme() -> None:
    readme = ROOT / "README.md"
    if not readme.exists():
        fail("README.md missing")
    text = readme.read_text()
    normalized = " ".join(text.split())
    for phrase in ["skills/skill-repo-architecture/", "agent skill repositor"]:
        if phrase not in normalized:
            fail(f"README.md missing: {phrase}")


def main() -> int:
    check_skill()
    check_references()
    check_readme()
    print("OK: skill source checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
