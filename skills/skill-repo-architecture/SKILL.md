---
name: skill-repo-architecture
description: Design, review, and tighten agent skill repositories. Use when creating or auditing a skill repo, deciding what belongs in the shipped skill versus repo-local tooling, reducing file-swamp, choosing portability boundaries, adding proportionate validation, or converting research into compact runtime instructions with reference files.
---

# Skill Repo Architecture

Use this skill to design or audit an agent skill repository. Prefer a compact
runtime skill with explicit reference routing over a large self-contained essay.

## When to Use

- Creating a new skill repo.
- Reviewing or refactoring an existing skill repo.
- Deciding whether content belongs in `SKILL.md`, `references/`, `scripts/`, or repo-local docs.
- Tightening an oversized or unclear skill.
- Adding validation without creating speculative maintenance burden.
- Choosing whether a skill should be portable, tool-portable, or platform-specific.

Do not use this as a substitute for domain-specific skill authoring guidance,
distribution documentation, or a general repo health audit. Use this skill for
the architecture of the skill repo itself.

## Default Procedure

1. Locate the runtime skill entrypoint, usually `skills/<name>/SKILL.md` for a cross-agent package or root `SKILL.md` only when the whole repo root is intentionally the skill package.
2. Identify the shipping boundary: runtime skill files, runtime references, runtime scripts, and non-shipping development files.
3. Measure structure: root file count, skill count, reference count per skill, script count, generated files, ignored files, and hand-maintained indexes.
4. Read `SKILL.md` for trigger quality, procedure clarity, reference routing, portability, and verification instructions.
5. Read only the references needed for the audit question. Do not load every reference by default.
6. Inspect validation scripts and CI to see whether checks match observed failure modes.
7. Run local checks when available and report exact pass/fail results.
8. Recommend changes in priority order: correctness, installability, portability, clarity, then polish.

## Design Principles

### 1. Methodology Over Collection

Ship a methodology when the ecosystem already has abundant resources and the
agent benefits more from navigation and evaluation criteria than from another
static list. Ship a collection when resources are scarce, uniform, and hard to
discover.

Decision question: is another item more valuable than a way to find, evaluate,
and verify the existing items?

### 2. Declared Shipping Boundary

Every skill repo needs an explicit answer to: "Can the runtime use this file
without development tooling?" If yes, it may ship. If no, keep it repo-local.

Usually ships:
- `skills/<name>/SKILL.md`
- Reference files that `SKILL.md` routes to
- Scripts invoked by the skill at runtime
- Runtime config required by those scripts

Usually repo-local:
- CI workflows and validation-only scripts
- Security, citation, changelog, and release metadata
- Research notes not routed from `SKILL.md`
- Editor, agent, or platform adapter folders
- Plans, todos, local instructions, and generated caches

### 3. Proportionate Anti-Drift

Add a check only when it maps to a concrete failure mode or a high-cost invariant.
Good checks are simpler than what they verify and have a clear recovery path.

Good targets: required file presence, parseable frontmatter, local reference
existence, generated payload drift, forbidden platform references, executable
script syntax, and URL evidence when the skill depends on live sources.

Poor targets: prose interpretation, volatile markdown layout, speculative
future risks, or checks whose failures require judgment every time.

### 4. Runtime Verification

For volatile facts, teach the agent how to verify at execution time instead of
embedding claims that decay. Prefer current filesystem state, command output,
source reachability, and parsed manifests over hardcoded assertions.

### 5. Progressive Disclosure

Keep `SKILL.md` as the operating procedure. Put detail in `references/` and tell
the agent when to load each file. Avoid duplicating the same explanation in both
places.

Use references when detail is large, conditional, historical, or only needed for
some audits. Keep details inline only when the agent needs them on every run.

### 6. Portability as a Tier

Choose the tier intentionally:

| Tier | Content | Expected reach |
| --- | --- | --- |
| Fully portable | Frontmatter, Markdown, no platform-specific commands | Any compatible skill runtime |
| Tool-portable | Uses general shell tools like `git`, `python3`, `curl` | Agents with shell access |
| Platform-specific | Requires one agent's APIs, commands, or config paths | That runtime only |

Do not claim broad portability if the body requires a specific agent runtime.
If platform-specific examples are educational, isolate them in references and
mark them intentionally in the portability gate.

### 7. File-Swamp Prevention

File-swamp starts when locally reasonable additions accumulate without a
boundary. Warning signs include too many root files, references that outnumber
skills without routing, indexes duplicating filesystem discovery, and scripts
that maintain files the runtime does not need.

Remediate in this order: declare the boundary, identify runtime-loaded files,
remove or relocate development artifacts, inline small fragments, route larger
details to references, and add only the checks needed to prevent recurrence.

### 8. Cross-Project Pattern Preservation

Preserve reusable findings at the smallest durable level:

| Scope | Mechanism |
| --- | --- |
| Occasional pattern | Inline note |
| Repeated across several repos | Reference file |
| Repeated across many active projects | Dedicated knowledge base |

Record transfer questions, not just anecdotes. A future agent should be able to
ask whether the pattern applies in a new repo.

## Reference Routing

- Read `references/skill-repo-audit-procedure.md` for a full phased audit.
- Read `references/file-swamp-patterns.md` when the repo has too many files, references, scripts, or indexes.
- Read `references/portability-patterns.md` when choosing or checking portability tier.
- Read `references/payload-manifest-pattern.md` only when a repo intentionally has a generated payload.
- Read `references/dev-workflow-patterns.md` for development workflow and drift-class decisions.
- Read `references/operational-patterns.md` for CI scope and evaluation rubric decisions.
- Read `references/agent-concepts-study-cross-project-patterns.md` for evidence behind the principles.
- Read `references/npm-publishing-for-agent-skills.md` only for npm-oriented skill tooling.
- Read `references/portability-migration.md` when migrating from platform-specific to portable instructions.

## Verification Checklist

- [ ] Runtime entrypoint is present and tracked.
- [ ] Shipping boundary is documented in the README.
- [ ] `SKILL.md` is concise enough to act as procedure, with detail routed to references.
- [ ] References are directly reachable from `SKILL.md` and are not duplicated inline.
- [ ] Platform-specific references match the declared portability tier.
- [ ] Validation checks map to concrete failure modes.
- [ ] CI runs only checks that runtime or review would not catch cheaply.
- [ ] Install or discovery instructions match the actual repo layout.
- [ ] Local checks have been run or skipped with a clear reason.
