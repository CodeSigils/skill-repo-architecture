#!/usr/bin/env python3
"""Validate skill-repo-architecture source integrity."""

from __future__ import annotations

import sys
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "skill-repo-architecture"
SKILL = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"

ALLOWED_FIELDS = {
    "name",
    "description",
    "version",
    "author",
    "license",
    "tier",
    "ref",
    "compatibility",
    "metadata",
}
REQUIRED_SECTIONS = {
    "## When to Use",
    "## Default Procedure",
    "## Reference Routing",
    "## Verification Checklist",
}
REQUIRED_REFERENCES = {
    "agent-concepts-study-cross-project-patterns.md",
    "dev-workflow-patterns.md",
    "file-swamp-patterns.md",
    "npm-publishing-for-agent-skills.md",
    "operational-patterns.md",
    "payload-manifest-pattern.md",
    "portability-migration.md",
    "portability-patterns.md",
    "skill-repo-audit-procedure.md",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(text: str, *, strict: bool = True) -> dict[str, str]:
    """Parse YAML frontmatter from text.

    Args:
        text: Input text starting with '---'
        strict: If True, raise SystemExit on failure. If False, return empty dict on failure.
    """
    if not text.startswith("---\n"):
        if strict:
            fail("SKILL.md does not start with YAML frontmatter")
        return {}
    try:
        _, raw, _ = text.split("---\n", 2)
    except ValueError:
        if strict:
            fail("SKILL.md frontmatter is not closed")
        return {}

    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def validate_frontmatter(data: dict[str, str]) -> None:
    extra = set(data) - ALLOWED_FIELDS
    if extra:
        fail(f"unsupported frontmatter fields: {sorted(extra)}")
    if data.get("name") != "skill-repo-architecture":
        fail("frontmatter name must be skill-repo-architecture")
    if len(data.get("description", "").split()) < 12:
        fail("description too short to trigger reliably")


def check_skill() -> None:
    if not SKILL.exists():
        fail("skills/skill-repo-architecture/SKILL.md missing")
    text = SKILL.read_text(encoding="utf-8")
    body = text.split("---\n", 2)[2] if text.startswith("---\n") else text
    data = parse_frontmatter(text)
    validate_frontmatter(data)
    for sec in sorted(REQUIRED_SECTIONS):
        if sec not in body:
            fail(f"missing section: {sec}")
    # Portability check on body
    for needle in (".hermes", "hermes-verify"):
        if needle in body:
            fail(f"body contains non-portable runtime marker: {needle}")


def check_references() -> None:
    if not REF_DIR.exists():
        fail("payload references directory missing")
    root_ref_dir = ROOT / "references"
    if not root_ref_dir.exists():
        fail("root references directory missing")
    root_set = {p.name for p in root_ref_dir.glob("*.md")}
    payload_set = {p.name for p in REF_DIR.glob("*.md")}
    if root_set != payload_set:
        extra = payload_set - root_set
        missing = root_set - payload_set
        if extra:
            fail(f"payload has extra references: {sorted(extra)}")
        if missing:
            fail(f"payload missing references: {sorted(missing)}")
    actual = payload_set
    missing = REQUIRED_REFERENCES - actual
    if missing:
        fail(f"missing references: {sorted(missing)}")

    text = SKILL.read_text(encoding="utf-8")
    for name in sorted(REQUIRED_REFERENCES):
        if f"references/{name}" not in text:
            fail(f"SKILL.md does not route reference: {name}")


def check_readme() -> None:
    readme = ROOT / "README.md"
    if not readme.exists():
        fail("README.md missing")
    text = readme.read_text()
    normalized = " ".join(text.split())
    for phrase in ("skills/skill-repo-architecture/", "agent skill repositor"):
        if phrase not in normalized:
            fail(f"README.md missing: {phrase}")


def check_self_test() -> None:
    """Run internal self-tests for the validation logic."""
    # Test parse_frontmatter with valid input
    valid_fm = "---\nname: skill-repo-architecture\nversion: 1.0\n---\n"
    data = parse_frontmatter(valid_fm)
    assert data["name"] == "skill-repo-architecture"
    assert data["version"] == "1.0"

    # Test parse_frontmatter rejects invalid (non-strict mode)
    assert parse_frontmatter("no frontmatter", strict=False) == {}
    # With strict=False, short description still parses but validate_frontmatter would fail
    parsed = parse_frontmatter("---\nname: test\n---\n", strict=False)
    assert "name" in parsed

    # Test validate_frontmatter
    try:
        validate_frontmatter({"name": "skill-repo-architecture", "description": "a " * 12})
        print("  PASS  validate_frontmatter valid")
    except SystemExit:
        assert False, "should not fail"

    try:
        with redirect_stderr(StringIO()):
            validate_frontmatter({"name": "skill-repo-architecture", "description": "short"})
        assert False, "should have failed"
    except SystemExit:
        pass

    print("  PASS  validate.py self-tests")


def main() -> int:
    if "--self-test" in sys.argv:
        check_self_test()
        return 0

    check_skill()
    check_references()
    check_readme()
    print("OK: skill source checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
