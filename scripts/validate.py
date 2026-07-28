#!/usr/bin/env python3
"""Validate the canonical skill payload and behavioral contract."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "repo-architecture-skill"
SKILL = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"
README = ROOT / "README.md"
EVAL = ROOT / "evals" / "cases" / "architecture-audit.json"
CODEX_SCHEMA = ROOT / "evals" / "codex" / "result.schema.json"
CODEX_POSITIVE = ROOT / "evals" / "codex" / "positive-prompt.md"
CODEX_NEGATIVE = ROOT / "evals" / "codex" / "negative-prompt.md"
EVIDENCE = ROOT / "docs" / "evidence-urls.json"
PORTABILITY_CONTRACT = ROOT / "docs" / "portability-contract.md"
SECURITY = ROOT / "SECURITY.md"
GITIGNORE = ROOT / ".gitignore"
CI = ROOT / ".github" / "workflows" / "ci.yml"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
PYPROJECT = ROOT / "pyproject.toml"
UV_LOCK = ROOT / "uv.lock"
PAYLOAD_LICENSE = SKILL_DIR / "LICENSE.txt"
ROOT_LICENSE = ROOT / "LICENSE"

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
EXPECTED_REFERENCES = {
    "dev-workflow-patterns.md",
    "file-swamp-patterns.md",
    "npm-publishing-for-agent-skills.md",
    "operational-patterns.md",
    "payload-manifest-pattern.md",
    "portability-migration.md",
    "portability-patterns.md",
    "skill-repo-audit-procedure.md",
}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("credential-bearing URL", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")),
)
DANGEROUS_RUNTIME_PATTERNS = (
    ("destructive Git reset", re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE)),
    ("forced Git push", re.compile(r"\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?|-f\b)", re.IGNORECASE)),
    ("privilege escalation", re.compile(r"(?:^|[`\s])sudo\s+", re.IGNORECASE | re.MULTILINE)),
    (
        "verification bypass",
        re.compile(r"--no-verify\b|\bbypass(?:ing)?\s+(?:approval|review|checks?)\b", re.IGNORECASE),
    ),
    (
        "raw secret-file output",
        re.compile(r"\b(?:cat|type|get-content)\s+[^\n]*(?:\.env\b|credentials\b|id_rsa\b)", re.IGNORECASE),
    ),
    (
        "raw commit-body output",
        re.compile(r"\bgit\s+(?:log|show)\b[^\n]*(?:--format=.?%B|--pretty=.?%B)", re.IGNORECASE),
    ),
)


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


def validate_payload_inventory() -> list[Path]:
    allowed_files = {SKILL, PAYLOAD_LICENSE, *(REF_DIR / name for name in EXPECTED_REFERENCES)}
    allowed_directories = {SKILL_DIR, REF_DIR}
    observed_files: set[Path] = set()
    for path in sorted(SKILL_DIR.rglob("*")):
        if path.is_symlink():
            fail(f"{path}: symlinks are not allowed in the runtime payload")
        if path.is_dir():
            if path not in allowed_directories:
                fail(f"{path}: unexpected runtime payload directory")
            continue
        if path not in allowed_files:
            fail(f"{path}: unexpected runtime payload file")
        if path.stat().st_mode & 0o111:
            fail(f"{path}: executable files are not allowed in the runtime payload")
        observed_files.add(path)
    missing = allowed_files - observed_files
    if missing:
        fail(f"runtime payload inventory is missing: {[str(path.relative_to(SKILL_DIR)) for path in sorted(missing)]}")
    if PAYLOAD_LICENSE.read_text(encoding="utf-8") != ROOT_LICENSE.read_text(encoding="utf-8"):
        fail(f"{PAYLOAD_LICENSE}: must match the repository LICENSE exactly")
    return sorted(observed_files)


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

    payload_files = validate_payload_inventory()
    references = [path for path in payload_files if path.parent == REF_DIR]
    for reference in references:
        route = f"references/{reference.name}"
        if route not in body:
            fail(f"{SKILL}: does not route {route}")

    for path in [SKILL, *references]:
        errors = local_link_errors(path, SKILL_DIR)
        if errors:
            fail("\n".join(errors))


def repository_text_files() -> list[Path]:
    try:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, stderr=subprocess.DEVNULL)
        paths = [ROOT / item.decode() for item in output.split(b"\0") if item]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        paths = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and not {".git", ".venv"}.intersection(path.relative_to(ROOT).parts)
        ]
    required = (SECURITY, GITIGNORE, CI, DEPENDABOT, PYPROJECT, UV_LOCK)
    return sorted({path for path in [*paths, *required] if path.is_file()})


def secret_types(text: str) -> list[str]:
    return [label for label, pattern in SECRET_PATTERNS if pattern.search(text)]


def validate_repository_secrets() -> None:
    findings: list[str] = []
    for path in repository_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label in secret_types(text):
            findings.append(f"{path.relative_to(ROOT)}: {label}")
    if findings:
        fail("secret-like material detected (values suppressed):\n" + "\n".join(findings))


def validate_runtime_trust() -> None:
    findings: list[str] = []
    for path in [SKILL, *(REF_DIR / name for name in sorted(EXPECTED_REFERENCES))]:
        text = path.read_text(encoding="utf-8")
        for label, pattern in DANGEROUS_RUNTIME_PATTERNS:
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {label}")
    if findings:
        fail("unsafe runtime instruction detected:\n" + "\n".join(findings))


def validate_security_contract() -> None:
    text = SECURITY.read_text(encoding="utf-8")
    required = (
        "## Supported Versions",
        "## Reporting a Vulnerability",
        "/security/advisories/new",
        "## Repository Security Scope",
        "## Shipped Payload Inventory",
        "## Runtime Trust Guarantees",
        "## Sensitive Evidence",
        "## Maintainer Security Checklist",
        "Last reviewed:",
    )
    for phrase in required:
        if phrase not in text:
            fail(f"{SECURITY}: missing {phrase!r}")

    ignored = set(GITIGNORE.read_text(encoding="utf-8").splitlines())
    for rule in (".env", ".env.*", "!.env.example", "!.env.*.example"):
        if rule not in ignored:
            fail(f"{GITIGNORE}: missing local-secret rule {rule!r}")

    workflow = CI.read_text(encoding="utf-8")
    if workflow.count("persist-credentials: false") < 2:
        fail(f"{CI}: every checkout must disable persisted credentials")
    if workflow.count("timeout-minutes:") < 2 or "permissions:\n  contents: read" not in workflow:
        fail(f"{CI}: jobs need timeouts and read-only repository permissions")
    if (
        'env:\n  PYTHON_VERSION: "3.13"' not in workflow
        or workflow.count("python-version: ${{ env.PYTHON_VERSION }}") != 2
    ):
        fail(f"{CI}: both jobs must use the shared Python version")

    dependabot = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
    if not isinstance(dependabot, dict) or not isinstance(dependabot.get("updates"), list):
        fail(f"{DEPENDABOT}: updates must be a list")
    if not all(isinstance(entry, dict) for entry in dependabot["updates"]):
        fail(f"{DEPENDABOT}: every update must be a mapping")
    ecosystems = {entry.get("package-ecosystem") for entry in dependabot["updates"]}
    if ecosystems != {"github-actions", "uv"}:
        fail(f"{DEPENDABOT}: must monitor github-actions and uv")


def validate_maintainer_environment() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = project.get("dependency-groups", {}).get("dev", [])
    pins: dict[str, str] = {}
    for dependency in dependencies:
        match = re.fullmatch(
            r"(pyyaml|ruff)==([0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9.+-]*))",
            dependency,
        )
        if match is None or match.group(1) in pins:
            fail(f"{PYPROJECT}: dev dependencies must be unique exact pins")
        pins[match.group(1)] = match.group(2)
    if set(pins) != {"pyyaml", "ruff"}:
        fail(f"{PYPROJECT}: dev dependencies must be exactly pyyaml and ruff")

    lock = tomllib.loads(UV_LOCK.read_text(encoding="utf-8"))
    locked_versions = {
        package["name"]: package["version"]
        for package in lock.get("package", [])
        if package.get("name") in pins and "version" in package
    }
    if locked_versions != pins:
        fail(f"{UV_LOCK}: locked dev dependency versions must match {PYPROJECT}")
    if project.get("tool", {}).get("uv", {}).get("package") is not False:
        fail(f"{PYPROJECT}: maintainer environment must be a non-package uv project")
    if not UV_LOCK.is_file():
        fail(f"{UV_LOCK}: committed uv lockfile is required")


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
        "skills/repo-architecture-skill/",
        "evals/cases/architecture-audit.json",
        "docs/portability-contract.md",
        "uv sync --locked",
        "SECURITY.md",
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
    if data.get("skill_name") != "repo-architecture-skill":
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
        "shared-core-with-client-discovery-adapters",
        "writable-external-skill-directory",
        "client-extension-isolated-in-adapter",
    }
    if not required_fixtures <= seen:
        fail(f"{EVAL}: required evidence fixtures missing: {sorted(required_fixtures - seen)}")


def validate_codex_eval() -> None:
    try:
        schema = json.loads(CODEX_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{CODEX_SCHEMA}: unreadable result schema: {exc}") from exc
    required = set(schema.get("required", []))
    common = {
        "case_id",
        "skills_used",
        "actions",
        "changed_paths",
        "outcome",
        "summary",
        "environment_limitations",
    }
    if not common <= required:
        fail(f"{CODEX_SCHEMA}: missing common result fields {sorted(common - required)}")
    for path in (CODEX_POSITIVE, CODEX_NEGATIVE):
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            fail(f"{path}: evaluation prompt must be non-empty")


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
    synthetic_token = "ghp_" + ("a" * 36)
    assert secret_types(synthetic_token) == ["GitHub token"]
    assert not secret_types("tokens should be redacted")
    assert DANGEROUS_RUNTIME_PATTERNS[0][1].search("git reset --hard")
    assert DANGEROUS_RUNTIME_PATTERNS[4][1].search("cat .env")
    print("PASS: validator self-tests")


def main() -> int:
    try:
        if "--self-test" in sys.argv:
            self_test()
        else:
            validate_skill()
            validate_runtime_trust()
            validate_readme()
            validate_eval()
            validate_codex_eval()
            validate_portability_contract()
            validate_evidence_sources()
            validate_security_contract()
            validate_maintainer_environment()
            validate_repository_secrets()
            print("PASS: payload, docs, behavior, security, and maintainer environment")
    except (AssertionError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
