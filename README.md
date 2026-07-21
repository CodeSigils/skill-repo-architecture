# Skill Repo Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/CodeSigils/skill-repo-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeSigils/skill-repo-architecture/actions/workflows/ci.yml)
[![Skill format](https://img.shields.io/badge/skill%20format-agentskills.io-blue)](https://agentskills.io/specification)

**Architecture follows the artifact.** This methodology helps an agent design,
review, and tighten skill repositories without forcing the same structure onto a
static Markdown skill, routed skill pack, CLI-backed skill, and published plugin.

It classifies what the repository ships, separates authoring source, runtime
payload, install artifact, and maintainer infrastructure, then recommends only
the validation and release controls justified by those boundaries.

## What it covers

- Five repository archetypes: Markdown-only, multi-skill, tool-backed,
  operational, and distribution monorepo.
- Four explicit boundaries: authoring source, runtime payload, install/publish
  artifact, and maintainer infrastructure.
- Progressive disclosure and portable runtime instructions.
- Canonical-source, generated-payload, and installed-copy drift decisions.
- Deterministic validation, behavioral fixtures, volatile monitoring, and
  release-only controls.
- File-swamp diagnosis based on ownership and consumers rather than universal
  script or reference ratios.

Use `repo-health-and-sync-skill` for general repository health and
`skill-discovery` for finding third-party skills. This skill focuses specifically
on the architecture of repositories that create or distribute skills.

## What it does in practice

Suppose you ask an agent:

> Review this repository. It contains a CLI, an npm package, and a `SKILL.md`.
> Tell me what should ship, whether it needs a payload manifest, and which checks
> belong in pull requests.

The methodology guides the agent to:

1. classify the repository as a tool-backed skill rather than a Markdown-only
   skill;
2. identify the CLI source as authoring source, the activated instructions and
   invoked code as runtime payload, the npm tarball and skill directory as
   separate install artifacts, and tests or release scripts as maintainer
   infrastructure;
3. inspect each artifact inventory independently instead of applying a raw
   script-to-skill ratio;
4. keep deterministic package, link, unit, and staged-install checks in pull
   requests while moving registry monitoring outside that lane; and
5. report the smallest changes needed, with evidence and skipped checks.

For a Markdown-only skill, the result is deliberately smaller: keep one
canonical skill directory, avoid a generated mirror, validate its structure and
references, and add behavioral fixtures only when the procedure makes meaningful
decisions.

## Scope

| Use this skill for                                             | Use another workflow for                       |
| -------------------------------------------------------------- | ---------------------------------------------- |
| Designing or auditing a skill repository                       | General repository-health audits               |
| Declaring source, runtime, artifact, and maintainer boundaries | Domain-specific skill content authoring        |
| Choosing payload, adapter, validation, and release patterns    | Finding or installing third-party skills       |
| Reducing unowned files or unnecessary generated copies         | Ordinary feature implementation or code review |

## Install

The canonical payload is
[`skills/skill-repo-architecture/`](skills/skill-repo-architecture/). There is no
build or generated mirror.

The generic installation shape is to copy that directory into a client-supported
skill location:

```bash
cp -R skills/skill-repo-architecture <your-skills-directory>/
```

For development, point clients that support external skill directories at this
repository's `skills/` directory so edits are immediately visible.

Client discovery locations change independently of the payload format. Verify
the named client's current documentation and record its version and installation
result before claiming support.

## Support status

Deterministic checks establish that the canonical payload has valid baseline
frontmatter, resolvable references, and no known platform-only runtime markers.
That supports a **payload-portable candidate** claim only.

No named runtime and version has yet received recorded installation plus positive
and negative workflow certification for this payload revision. The current
runtime status is therefore `candidate`, not “compatible” or “workflow verified.”
See [the portability contract](docs/portability-contract.md) for evidence levels
and certification requirements.

## Use

1. Make `skill-repo-architecture` discoverable to the agent.
2. Ask it to design or audit a skill repository, naming any active distribution
   targets or portability requirements.
3. Expect an archetype classification, four-boundary map, artifact-specific
   controls, prioritized recommendations, and an exact record of checks run or
   skipped.

Typical requests include:

- “Design a repository for a portable Markdown-only skill.”
- “Audit this skill pack's router and standalone loading behavior.”
- “Does this CLI-backed skill need a generated payload manifest?”
- “Extract a portable core from these platform-specific instructions.”

The reviewable behavior contract lives in
[`evals/cases/architecture-audit.json`](evals/cases/architecture-audit.json).

## Runtime payload

Only [`skills/skill-repo-architecture/`](skills/skill-repo-architecture/) ships.
It contains one `SKILL.md`, eight conditionally loaded references, and no runtime
scripts or configuration:

| Reference                            | Load when                                                   |
| ------------------------------------ | ----------------------------------------------------------- |
| `skill-repo-audit-procedure.md`      | Running a complete architecture audit                       |
| `file-swamp-patterns.md`             | File ownership, consumers, or growth is unclear             |
| `portability-patterns.md`            | Selecting portability tier or bounding compatibility claims |
| `payload-manifest-pattern.md`        | A real install or publication artifact must be assembled    |
| `dev-workflow-patterns.md`           | Choosing canonical source, adapters, or drift handling      |
| `operational-patterns.md`            | Designing CI lanes and behavioral evaluation                |
| `npm-publishing-for-agent-skills.md` | The skill wraps a publishable Node.js tool                  |
| `portability-migration.md`           | Extracting a portable core from platform coupling           |

The payload is authored in place. There is no root reference mirror, generated
payload, runtime dependency, or synchronization step.

## Architecture

```text
skill-repo-architecture/
├── AGENTS.md                    # maintainer routing; not shipped
├── CITATION.cff
├── LICENSE
├── README.md
├── SECURITY.md
├── requirements-dev.txt        # exact validation dependencies
├── docs/
│   ├── evidence-urls.json       # external monitoring contract
│   └── portability-contract.md  # compatibility evidence levels and status
├── evals/
│   └── cases/
│       └── architecture-audit.json
├── scripts/
│   ├── validate.py              # deterministic schema/link/fixture checks
│   └── verify-urls.py           # scheduled external monitoring
└── skills/
    └── skill-repo-architecture/ # canonical runtime payload
        ├── SKILL.md
        └── references/
```

The tracked payload is both authoring source and install artifact. CI, fixtures,
evidence contracts, and repository documentation are maintainer infrastructure.

## Design examples behind the methodology

| Repository shape               | Architectural lesson                                                            |
| ------------------------------ | ------------------------------------------------------------------------------- |
| Small discovery methodology    | Keep runtime guidance compact and monitor external contracts separately.        |
| Routed Python review pack      | Test routing and preserve standalone safety for every focused skill.            |
| Markdown formatter CLI         | Let the package manifest own executable payload and test staged installation.   |
| Operational health methodology | Pair structural validation with explicit behavioral fixtures.                   |
| Reproducible build repository  | Import provenance and release controls only when a real artifact warrants them. |

These are transfer patterns, not templates. The skill asks whether the same
artifact and failure mode exist before recommending the corresponding control.

## Verify

Create an isolated environment and install the exact development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

Run the deterministic suite:

```bash
.venv/bin/python scripts/validate.py
.venv/bin/python scripts/validate.py --self-test
.venv/bin/python .github/scripts/check-portability.py
.venv/bin/python -m ruff check scripts .github/scripts
```

External URL checks are intentionally separate because they depend on network
and provider state:

```bash
.venv/bin/python scripts/verify-urls.py
```

CI runs deterministic checks on pull requests and external monitoring only on
schedule or manual dispatch. Runtime-specific behavior remains a separate,
non-blocking certification activity.

## Maintainer ownership

- `skills/skill-repo-architecture/SKILL.md` owns runtime procedure and triggers.
- Runtime references own conditional detail and examples.
- `evals/` owns intended classification and recommendation behavior.
- `README.md` owns installation, repository layout, and verification commands.
- `docs/` and any research notes are evidence, not runtime authority.
- `AGENTS.md` routes maintainers to these sources without repeating them.

## See also

- [`skill-discovery`](https://github.com/CodeSigils/skill-discovery) — find and
  assess reusable skills.
- [`repo-health-and-sync-skill`](https://github.com/CodeSigils/repo-health-and-sync-skill)
  — audit general repository health and release readiness.
- [`py-review-skill`](https://github.com/CodeSigils/py-review-skill) — review
  Python code with focused routing and rules.

## License

MIT — see [LICENSE](LICENSE).
