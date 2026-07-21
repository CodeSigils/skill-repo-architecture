#!/usr/bin/env python3
"""Validate the canonical skill payload and behavioral contract."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "skill-repo-architecture"
SKILL = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"
README = ROOT / "README.md"
EVAL = ROOT / "evals" / "cases" / "architecture-audit.json"
EVIDENCE = ROOT / "docs" / "evidence-urls.json"
PORTABILITY_CONTRACT = ROOT / "docs" / "portability-contract.md"

ALLOWED_FIELDS = {"name", "description"}
REQUIRED_SECTIONS = {
    "## Procedure",
    "## Repository Archetypes",
    "## Four Boundaries",
    "## Reference Routing",
    "## Completion Checklist",
}
ARCHETYPES = {
    "markdown-only-skill",
    "multi-skill-pack",
    "tool-backed-skill",
    "operational-skill",
    "distribution-monorepo",
    "non-skill-control",
}
BOUNDARIES = {
    "authoring_source",
    "runtime_payload",
    "install_artifact",
    "maintainer_infrastructure",
}
LINK_RE = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message: str) -> None:
    raise ValueError(message)


def parse_skill(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing opening YAML frontmatter delimiter")
    try:
        _, raw, body = text.split("---\n", 2)
    except ValueError as exc:
        raise ValueError(f"{path}: unclosed YAML frontmatter") from exc
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        fail(f"{path}: frontmatter must be a YAML mapping")
    return data, body


def validate_frontmatter(data: dict[str, object], path: Path) -> None:
    extra = set(data) - ALLOWED_FIELDS
    if extra:
        fail(f"{path}: unsupported frontmatter fields: {sorted(extra)}")
    if set(data) != ALLOWED_FIELDS:
        fail(f"{path}: frontmatter must contain exactly name and description")
    name = data["name"]
    description = data["description"]
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        fail(f"{path}: invalid skill name")
    if name != path.parent.name:
        fail(f"{path}: skill name must match directory {path.parent.name!r}")
    if not isinstance(description, str) or not description.strip():
        fail(f"{path}: description must be a non-empty string")
    if len(description) > 1024:
        fail(f"{path}: description exceeds 1024 characters")
    if len(description.split()) < 12:
        fail(f"{path}: description is too short to trigger reliably")


def local_link_errors(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
        target = target.strip().strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative = target.split("#", 1)[0]
        if relative and not (path.parent / relative).resolve().is_relative_to(root.resolve()):
            errors.append(f"{path}: local link escapes repository: {target}")
        elif relative and not (path.parent / relative).exists():
            errors.append(f"{path}: missing local link target: {target}")
    return errors


def validate_skill() -> None:
    if not SKILL.exists():
        fail(f"missing canonical runtime entrypoint: {SKILL}")
    data, body = parse_skill(SKILL)
    validate_frontmatter(data, SKILL)
    for section in sorted(REQUIRED_SECTIONS):
        if section not in body:
            fail(f"{SKILL}: missing section {section!r}")
    if len(SKILL.read_text(encoding="utf-8").splitlines()) > 500:
        fail(f"{SKILL}: exceeds the 500-line runtime budget")

    references = sorted(REF_DIR.glob("*.md"))
    if not references:
        fail(f"{REF_DIR}: no runtime references found")
    for reference in references:
        route = f"references/{reference.name}"
        if route not in body:
            fail(f"{SKILL}: does not route {route}")

    for path in [SKILL, *references]:
        errors = local_link_errors(path, SKILL_DIR)
        if errors:
            fail("\n".join(errors))


def validate_readme() -> None:
    if not README.exists():
        fail("README.md is missing")
    text = README.read_text(encoding="utf-8")
    required = (
        "## Install",
        "## Support status",
        "## Architecture",
        "## Verify",
        "## Maintainer ownership",
        "skills/skill-repo-architecture/",
        "evals/cases/architecture-audit.json",
        "docs/portability-contract.md",
    )
    for phrase in required:
        if phrase not in text:
            fail(f"README.md is missing {phrase!r}")
    errors = local_link_errors(README, ROOT)
    if errors:
        fail("\n".join(errors))


def validate_eval() -> None:
    try:
        data = json.loads(EVAL.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{EVAL}: unreadable behavioral contract: {exc}") from exc
    if data.get("schema_version") != 1:
        fail(f"{EVAL}: schema_version must be 1")
    if data.get("skill_name") != "skill-repo-architecture":
        fail(f"{EVAL}: skill_name mismatch")
    trigger = data.get("trigger")
    if not isinstance(trigger, dict):
        fail(f"{EVAL}: trigger must be an object")
    for polarity in ("positive", "negative"):
        values = trigger.get(polarity)
        if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
            fail(f"{EVAL}: trigger.{polarity} must be a non-empty string list")

    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) < 5:
        fail(f"{EVAL}: at least five representative fixtures are required")
    seen: set[str] = set()
    covered: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("name"), str):
            fail(f"{EVAL}: every fixture needs a string name")
        name = fixture["name"]
        if name in seen:
            fail(f"{EVAL}: duplicate fixture name {name!r}")
        seen.add(name)
        expected = fixture.get("expected")
        if not isinstance(expected, dict):
            fail(f"{EVAL}: fixture {name!r} needs expected behavior")
        archetype = expected.get("archetype")
        if archetype not in ARCHETYPES:
            fail(f"{EVAL}: fixture {name!r} has invalid archetype {archetype!r}")
        covered.add(archetype)
        boundaries = expected.get("boundaries")
        if not isinstance(boundaries, dict) or set(boundaries) != BOUNDARIES:
            fail(f"{EVAL}: fixture {name!r} must declare all four boundaries")
        for field in ("required_recommendations", "prohibited_recommendations"):
            values = expected.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
                fail(f"{EVAL}: fixture {name!r} needs a non-empty {field} list")
    if covered != ARCHETYPES:
        fail(f"{EVAL}: archetype coverage mismatch: {sorted(ARCHETYPES - covered)} missing")
    required_fixtures = {
        "portable-payload-without-runtime-certification",
        "audit-with-secret-like-evidence",
    }
    if not required_fixtures <= seen:
        fail(f"{EVAL}: required evidence fixtures missing: {sorted(required_fixtures - seen)}")


def validate_portability_contract() -> None:
    try:
        text = PORTABILITY_CONTRACT.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"{PORTABILITY_CONTRACT}: unreadable: {exc}") from exc
    required = (
        "## Evidence levels",
        "## Runtime states",
        "## Current status",
        "Payload portable",
        "Install verified",
        "Workflow verified",
        "`candidate`",
    )
    for phrase in required:
        if phrase not in text:
            fail(f"{PORTABILITY_CONTRACT}: missing {phrase!r}")


def validate_evidence_sources() -> None:
    try:
        entries = json.loads(EVIDENCE.read_text(encoding="utf-8"))["urls"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{EVIDENCE}: invalid evidence manifest: {exc}") from exc
    if not isinstance(entries, list) or not entries:
        fail(f"{EVIDENCE}: urls must be a non-empty list")
    for entry in entries:
        if not isinstance(entry, dict):
            fail(f"{EVIDENCE}: every URL entry must be an object")
        source_name = entry.get("source_section")
        url = entry.get("url")
        if not isinstance(source_name, str) or not isinstance(url, str):
            fail(f"{EVIDENCE}: every entry needs string url and source_section fields")
        source = (ROOT / source_name).resolve()
        if not source.is_relative_to(ROOT.resolve()) or not source.is_file():
            fail(f"{EVIDENCE}: source file does not exist: {source_name}")
        if url not in source.read_text(encoding="utf-8"):
            fail(f"{EVIDENCE}: {url} is not present in {source_name}")


def self_test() -> None:
    folded = "---\nname: example-skill\ndescription: >\n  Folded descriptions parse as one complete and useful YAML string for reliable skill triggering.\n---\n# Body\n"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        skill = root / "example-skill" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text(folded, encoding="utf-8")
        data, _ = parse_skill(skill)
        validate_frontmatter(data, skill)
        source = root / "README.md"
        source.write_text("[missing](nope.md)", encoding="utf-8")
        assert local_link_errors(source, root)
    try:
        validate_frontmatter({"name": "Bad_Name", "description": "word " * 12}, SKILL)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid skill names must fail")
    print("PASS: validator self-tests")


def main() -> int:
    try:
        if "--self-test" in sys.argv:
            self_test()
        else:
            validate_skill()
            validate_readme()
            validate_eval()
            validate_portability_contract()
            validate_evidence_sources()
            print("PASS: canonical payload, docs, links, and behavioral contract")
    except (AssertionError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
