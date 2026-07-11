# Skill Repo Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/CodeSigils/skill-repo-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeSigils/skill-repo-architecture/actions)
[![agentskills.io](https://img.shields.io/badge/agentskills.io-v1-blue)](https://agentskills.io/specification)

**Design principles for structuring, shipping, and maintaining agent skill
repositories.** Covers the *why* before the *how* — methodology over collection,
shipping boundaries, proportionate anti-drift, portability gradations, and
cross-project pattern preservation.

This is not a collection of skills. It is a methodology that teaches any
agent how to architect skill repos.

---

## Quick Start

Make the skill discoverable by your agent.

<details>
<summary><b>Hermes Agent</b></summary>

**Recommended for development — clone the repo and add to `external_dirs`:**
```yaml
skills:
  external_dirs:
    - /path/to/skill-repo-architecture/skills
```
Every commit is immediately reflected without reinstalling.

**For end users — install from hub:**
```bash
hermes skills install CodeSigils/skill-repo-architecture
```

*Other agents: see sections below for their native setup commands.*
</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
cp -r skills/skill-repo-architecture ~/.claude/skills/
```

Claude Code discovers skills by scanning `.claude/skills/` for SKILL.md files.
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
cp -r skills/skill-repo-architecture ~/.codex/skills/
```

Codex CLI discovers skills in `.codex/skills/` via filesystem walk.
</details>

<details>
<summary><b>OpenCode</b></summary>

```bash
cp -r skills/skill-repo-architecture .opencode/skills/
```
</details>

<details>
<summary><b>Gemini CLI / .agents/ path</b></summary>

```bash
cp -r skills/skill-repo-architecture .agents/skills/
```

Gemini CLI explicitly supports `.agents/skills/` as a cross-tool path.
</details>

<details>
<summary><b>Generic agentskills.io client</b></summary>

```bash
cp -r skills/skill-repo-architecture <your-skills-dir>/
```

Most clients that support the agentskills.io standard scan a `skills/`
or `.agents/skills/` directory.
</details>

For agents that support external skill directories, point the config at
`skills/skill-repo-architecture/` for live-updating access.

---

## How to Use

1. **Load `skill-repo-architecture`** when designing or reviewing a skill repo.
2. **The skill teaches 10 design principles** with decision frameworks for each.
3. **Use the companion methodology skills** for related tasks:
   - [`skill-discovery`](https://github.com/CodeSigils/skill-discovery) — how to *find* skills in catalogs and marketplaces
   - [`repo-health-and-sync-skill`](https://github.com/CodeSigils/repo-health-and-sync-skill) — how to *audit* any repo's health
   - [`py-review-skill`](https://github.com/CodeSigils/py-review-skill) — Python code review rules

All three share the same design philosophy. This architecture skill is the
layer above them: it teaches how to *design* repos that those skills can
then audit.

---

## Portability

Each shipped file in `skills/` is checked by CI for agent-specific references
(`skill_view`, `hermes skills`, platform adapter paths, etc.). If a commit
adds a platform-specific command, CI fails before it reaches the runtime.

The current surface is fully cross-agent compatible — zero platform
references in any shipped skill file or reference.

---

## Is This The Same As `skill-discovery`?

No. They are complementary methodologies at different abstraction levels:

| Skill | Question it answers |
|-------|-------------------|
| **skill-discovery** | "Find me the right skill for this task" |
| **repo-health-and-sync-skill** | "Check this repo for health issues" |
| **skill-repo-architecture** | "Design and ship a skill repo correctly" |

---

## What This Repo Contains

```text
skill-repo-architecture/
├── README.md                   # you are here
├── SECURITY.md                 # vulnerability reporting
├── LICENSE                     # MIT
├── .gitignore
├── .github/
│   ├── workflows/ci.yml        # 4-step CI pipeline
│   └── scripts/check-portability.py  # cross-agent portability gate
├── scripts/
│   ├── payload-manifest.json   # declares shipped files
│   ├── sync-payload.sh         # builds payload from manifest
│   └── validate.py             # skill source integrity checks
├── references/                 # per-principle reference detail
│   ├── agent-concepts-study-cross-project-patterns.md
│   ├── dev-workflow-patterns.md
│   ├── file-swamp-patterns.md
│   ├── npm-publishing-for-agent-skills.md
│   ├── operational-patterns.md
│   ├── payload-manifest-pattern.md
│   ├── portability-patterns.md
│   └── skill-repo-audit-procedure.md
└── skills/
    └── skill-repo-architecture/
        ├── SKILL.md            # the methodology (~450 lines)
        └── references/         # synced from root references/
```

Shipping boundary: `skills/skill-repo-architecture/` is the runtime payload.
Everything else is development infrastructure.

---

## Verify

```bash
python3 .github/scripts/check-portability.py   # cross-agent gate
python3 scripts/validate.py                     # source integrity
bash scripts/sync-payload.sh --ci               # payload in sync
bash -n scripts/sync-payload.sh                 # shell syntax
```

---

## References

| Reference | Purpose |
| :--- | :--- |
| `agent-concepts-study-cross-project-patterns.md` | Full 6-principle research note with evidence from 4 projects |
| `dev-workflow-patterns.md` | Development workflows, no-copy principle, README patterns, session findings |
| `file-swamp-patterns.md` | Diagnostic checklist, causal chain, ecosystem benchmarks |
| `npm-publishing-for-agent-skills.md` | Evaluating and publishing an agent-first tool on npm |
| `operational-patterns.md` | CI triage, fallback chains, evidence-base as architecture |
| `payload-manifest-pattern.md` | JSON manifest + bash sync implementation details |
| `portability-patterns.md` | Three-tier gradation, decision tree, portability CI gate |
| `skill-repo-audit-procedure.md` | 9-phase audit for skill repositories |

---

## Licenses

MIT — see [LICENSE](LICENSE).
