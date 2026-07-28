#!/usr/bin/env python3
"""Grade repo-architecture Codex evaluation artifacts deterministically."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BOUNDARIES = {
    "authoring_source",
    "runtime_payload",
    "install_artifact",
    "maintainer_infrastructure",
}
COMMON_FIELDS = {
    "case_id",
    "skills_used",
    "actions",
    "changed_paths",
    "outcome",
    "summary",
    "environment_limitations",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def normalized_path(value: str) -> str:
    return value.removeprefix("./").rstrip("/")


def grade_positive(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = COMMON_FIELDS - result.keys()
    if missing:
        errors.append(f"result lacks common fields: {sorted(missing)}")
        return errors
    if result["case_id"] != "architecture-duplicate-mirror":
        errors.append("positive result has the wrong case_id")
    skills = result.get("skills_used")
    if not isinstance(skills, list) or not any(
        "repo-architecture-skill" in str(item) for item in skills
    ):
        errors.append("repo-architecture-skill was not selected")
    if result.get("changed_paths") != []:
        errors.append("read-only audit must not report changed paths")
    if result.get("outcome") not in {"passed", "limited"}:
        errors.append("positive audit did not complete")

    classification = result.get("classification")
    if not isinstance(classification, dict):
        errors.append("classification is missing")
        return errors
    if classification.get("archetype") != "markdown-only-skill":
        errors.append("fixture was not classified as markdown-only-skill")
    boundaries = classification.get("boundaries")
    if not isinstance(boundaries, dict) or set(boundaries) != BOUNDARIES:
        errors.append("classification does not map all four boundaries")
    evidence = classification.get("evidence_paths")
    if not isinstance(evidence, list) or not evidence:
        errors.append("classification lacks repository-relative evidence")

    recommendations = result.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        errors.append("audit lacks recommendations")
        return errors
    combined = " ".join(
        str(item.get("recommendation", ""))
        for item in recommendations
        if isinstance(item, dict)
    ).lower()
    if not (
        ("duplicate" in combined or "mirror" in combined)
        and ("remove" in combined or "canonical" in combined)
    ):
        errors.append("audit does not address the unowned duplicate mirror")
    for index, item in enumerate(recommendations):
        paths = item.get("evidence_paths") if isinstance(item, dict) else None
        if not isinstance(paths, list) or not paths:
            errors.append(f"recommendation {index} lacks evidence paths")
    return errors


def grade_negative(text: str) -> list[str]:
    if not text.strip():
        return ["negative run produced no response"]
    lowered = text.lower()
    markers = (
        "repo-architecture-skill",
        "four boundaries",
        "runtime payload",
        "install artifact",
    )
    found = [marker for marker in markers if marker in lowered]
    return [f"negative run appears to activate architecture audit: {found}"] if found else []


def run_self_tests() -> int:
    passing = {
        "case_id": "architecture-duplicate-mirror",
        "skills_used": ["repo-architecture-skill"],
        "actions": ["inspected tracked files"],
        "changed_paths": [],
        "outcome": "passed",
        "summary": "Found an unowned duplicate.",
        "environment_limitations": [],
        "classification": {
            "archetype": "markdown-only-skill",
            "boundaries": {
                "authoring_source": "skills/example",
                "runtime_payload": "skills/example",
                "install_artifact": "copied skill directory",
                "maintainer_infrastructure": "tests and CI",
            },
            "evidence_paths": ["skills/example/SKILL.md"],
        },
        "recommendations": [
            {
                "recommendation": "Remove the duplicate mirror; keep the skill canonical.",
                "evidence_paths": ["SKILL.md", "skills/example/SKILL.md"],
            }
        ],
    }
    assert grade_positive(passing) == []
    failing = json.loads(json.dumps(passing))
    failing["classification"]["boundaries"].pop("runtime_payload")
    assert any("four boundaries" in error for error in grade_positive(failing))
    assert grade_negative("Use split('=', 1) in parser.py.") == []
    assert grade_negative("Run repo-architecture-skill and map the runtime payload.")
    assert normalized_path("./skills/example/") == "skills/example"
    print("PASS: grade-codex-regression.py self-tests")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive-result", type=Path)
    parser.add_argument("--negative-result", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_tests()
    if args.positive_result is None or args.negative_result is None:
        parser.error("--positive-result and --negative-result are required")
    try:
        errors = grade_positive(read_json(args.positive_result))
        errors.extend(grade_negative(args.negative_result.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [f"cannot read evaluation artifacts: {exc}"]
    report = {"passed": not errors, "errors": errors}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("PASS: Codex architecture regression")
    return 0


if __name__ == "__main__":
    sys.exit(main())
