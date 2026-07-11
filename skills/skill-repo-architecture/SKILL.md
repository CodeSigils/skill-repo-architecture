---
name: skill-repo-architecture
description: Design and structure agent skill repositories — shipping boundaries, methodology-over-collection decisions, proportionate anti-drift, heuristic discovery patterns, self-verifying instructions, cross-project pattern preservation, file-swamp diagnosis, portability gradations, information density analysis, and evaluation rubric/CI triage. Use when creating a new skill repo, refactoring an existing one, or deciding what to ship vs keep repo-local.  # portability: allow-platform-ref
---

# Skill Repo Architecture  # portability: allow-platform-ref

Design principles for structuring, shipping, and maintaining agent skill repositories at the repo level. This skill covers the **why** before the **how** — the design philosophy that drives decisions in packaging (skill-packaging), authoring (hermes-agent-skill-authoring), and research (cross-ecosystem-skill-research).

## When to Use

- Creating a new skill repository from scratch
- Refactoring an existing skill repo that has accumulated file-swamp
- Deciding whether to ship a skill collection vs a discovery methodology
- Evaluating whether a new directory, script, or reference file belongs in the shipping surface
- Deciding which drift checks to add (and which to skip)
- Teaching an agent how to architect skills at the repo level

Do NOT use for: writing a single SKILL.md (see hermes-agent-skill-authoring), packaging for hub distribution (see skill-packaging), or running health checks inside a repo (see repo-health-and-sync-skill).

## The Ten Design Principles

These ten principles emerged from cold-read analysis of four shipping projects (CodeSigils: `skill-discovery`, `py-review-skill`, `repo-health-and-sync-skill`, and `emerging-pattern-proposals`) plus operational patterns extracted from their CI workflows, scripts, and research docs. Each project independently converged on the same philosophy despite different scopes and timelines.

### 1. Methodology over Collection

**Principle:** When the ecosystem already has abundance of something (skills, tools, libraries, datasets), don't ship more instances. Ship a methodology that teaches agents how to navigate what already exists.

**When this applies:** The ecosystem has a dense, discoverable set of resources. Adding N more instances would be invisible and compete with scale. The marginal utility of teaching navigation exceeds the marginal utility of adding inventory.

**Transfer question:** "Is the marginal utility of adding another instance higher than the utility of teaching agents to navigate what already exists?"

| Signals to ship methodology | Signals to ship collection |
|---|---|
| Ecosystem has 2,000+ discoverable items | Ecosystem has <50 items, poorly indexed |
| Search/filter tooling exists (APIs, catalogs) | No search mechanism exists |
| Items vary in quality and need evaluation | Items are uniform and well-understood |
| Agent can verify source reachability at runtime | Agent has constrained runtime (no network, limited tools) |

**Relationship to other skills:** A methodology skill can reference skills found via `skill-discovery`. It does not replace `skill-packaging` — it changes what gets packaged.

---

### 2. Declared Shipping Boundaries

**Principle:** Explicitly declare what is NOT part of the runtime shipping surface. The exclusions encode design principles as rigorously as the inclusions.

A shipping boundary answers: "Can a runtime consume this file without the repo's development tooling? If yes, it ships. If no, it stays repo-local."

**Artifacts that typically stay repo-local:**
- CI workflows (.github/, CI configs)
- Development instructions (AGENTS.md, plan.md, todos.md)
- Research notes, evidence snapshots, investigation reports
- Architecture decisions, ADRs
- Eval/infrastructure scripts not invoked by the skill at runtime
- Platform adapter files (.claude/, .cursor/, .codex/, .gemini/)  # portability: allow-platform-ref
- CHANGELOG.md, SECURITY.md (repo metadata, not runtime)
- Dev scaffolding (install scripts, test suites, lint configs)

**Artifacts that ship:**
- `skills/*/SKILL.md` (required)
- Runtime scripts the skill invokes
- Reference files the skill's instructions rely on
- Runtime config files used by the skill

**Without an explicit boundary, ANY repo accumulates file-swamp.** The mechanism is structural: each new file is locally reasonable; collectively they produce a cascade:
- No shipping boundary
- -> Per-feature reference directories
- -> Maintenance pipeline (scripts to keep refs in sync)
- -> Index files because frontmatter wasn't trusted as catalog
- -> Architecture docs to explain the growing structure
- -> = file-swamp

**Mechanism for declaring a boundary:**
1. List what ships vs what doesn't in the repo's README
2. For every new file at creation time, ask the boundary question
3. Remove maintainer-only files from the deployable package before hub submission (see skill-packaging for the specific scanner behavior)
4. **Add a payload manifest** (see "Payload Manifest Pattern" below) to mechanically enforce the boundary in CI

#### Payload Manifest Pattern

To enforce the shipping boundary mechanically, maintain a **payload manifest** — a single file that declares which source files belong in the deployable skill package, paired with a **sync script** that copies those files into the payload directory and removes orphans.

**File:**

`scripts/payload-manifest.json`:
```json
{
  "files": ["SKILL.md", ".repo-health.json"],
  "scripts": ["check-pattern.py"],
  "references": "*"
}
```

Use three categories:
- `"files"` — root-level files listed explicitly by relative path
- `"scripts"` — files under `scripts/` listed by basename
- `"references"` — `"*"` to mirror the entire directory; or an explicit array for selective inclusion

**Sync script:**

`scripts/sync-payload.sh` reads the manifest, copies each source file to `skills/<skill-name>/` at the same relative path, and removes any file in the payload that is no longer in the manifest (orphan cleanup). The script should have:

- **Normal mode:** `bash scripts/sync-payload.sh` — rebuilds payload in-place
- **CI mode:** `bash scripts/sync-payload.sh --ci` — exits 1 on drift for CI enforcement
- **Execute permission handling:** preserve `chmod +x` from source to target
- **Reference mirroring:** copy all `references/*.md` when `"*"` is declared, and clean removed references from the payload
- **Empty directory cleanup:** remove now-empty directories after orphan deletion

**CI integration:**

```yaml
- name: Payload sync check
  run: bash scripts/sync-payload.sh --ci
- name: Staged-install smoke test
  run: |
    python3 skills/<skill-name>/scripts/check-pattern.py --self-test
```

The `--ci` mode enforces that:
1. Every file in the manifest exists at its source path
2. Every file in the payload is declared in the manifest (no orphans)
3. The payload is byte-identical to the source for all declared files

**Benefits over the flat-array approach (e.g., zero-md-formatter's RUNTIME_PAYLOAD_FILES):**

| Criterion | Flat array (JS export) | JSON manifest (bash sync) |
|---|---|---|
| Reference dir support | Must list each file | `"*"` mirrors entire directory |
| Orphan detection | Manual cleanup on rename | Automatic — removes files not in manifest |
| CI integration | Separate test for expected count | Single `--ci` mode exits 1 on drift |
| Test-file coupling | Must update unit test array | No test file to update |
| Cross-project portable | JS-specific (requires Node) | JSON + bash — works anywhere |
| Different file types | All treated the same | Categorized (files, scripts, references) |

This is described in detail in `references/dev-workflow-patterns.md` §4 and `references/payload-manifest-pattern.md`.

---

### 3. Proportionate Anti-Drift from Observed Failure

**Principle:** Every drift check must trace to a specific, observed failure mode. Speculative checks accumulate maintenance debt before they create value.

**Anti-pattern guard:** "If a check fires and you haven't seen this failure before, consider disabling it rather than patching around it."

| Characteristic | Proportionate | Disproportionate |
|---|---|---|
| Origin | Added after a specific failure | Added speculatively |
| Scope | One clear failure mode | Overlapping or unclear scope |
| Complexity | Simpler than what it verifies | More complex than what it verifies |
| Maintenance | Low relative to the drift it prevents | Accumulates without a pruning mechanism |
| Evidence | Traceable to an incident | "This could break someday" |

**Three-layer defense (recurring pattern across all four reviewed projects):**
1. **Prevent** through contracts and design principles (shipping boundary, methodology choice)
2. **Detect** through checks tied to observed failures (URL status checks, file existence checks, version alignment)
3. **Recover** through documented process (how to fix when a check fires)

**Good checker targets:** Required files exist, generated artifacts match source, JSON/TOML/YAML parse, local links resolve, installed mirrors match canonical payloads, test sets are balanced, forbidden stale sentinel terms are absent, shipped payload boundaries are explicit.

**Poor checker targets:** Full README prose interpretation, historical handoff commit hashes, nuanced current-status paragraphs, volatile markdown layout trees (unless generated from a source manifest).

**Two drift classes:** Payload drift (derived copy out of sync with source) and mirror staleness (installed copy predates a restructuring) need different fixes. See `references/dev-workflow-patterns.md` §5.

---

### 4. Heuristic Discovery over Hardcoded Configuration

**Principle:** Prefer runtime detection to static declarations. A heuristic that detects at runtime stays current with the project's actual state. A hardcoded table or config file is wrong the moment the project changes.

**When to use heuristics:**
- The thing being detected changes frequently (URL statuses, version numbers, file presence)
- The detection command is simple and reliable (find, grep, command -v, stat, git diff)
- Different projects have different conventions (formatters, linters, version sources)
- The project's state at runtime is the authoritative truth

**When hardcoded config is appropriate:**
- The value changes rarely (project name, author, license)
- The config defines an invariant that should never change without explicit review (shipping boundary, allowed tools)
- Runtime detection would require dangerous or unreliable operations

**Common heuristic targets in skill repos:**
- Shell scripts to check: `find . -name '*.sh'`
- Version sources: probe package.json, Cargo.toml, pyproject.toml, SKILL.md frontmatter
- Formatter config: probe .prettierrc*, pyproject.toml [tool.ruff], Makefile targets
- Consistency checks: probe .repo-health.json, check-consistency.js, verify.py, Makefile targets
- Sync targets: probe .repo-health.json, heuristic clues (Hermes skill dirs, config mirrors)  # portability: allow-platform-ref
- CI structures: walk .github/workflows/*.yml

**Ecosystem precedent:** repo-health-and-sync-skill ("Detect, don't enforce. No convention is universal across ecosystems") and skill-discovery ("verify source reachability at runtime") both demonstrate this principle in action.

---

### 5. Self-Verifying Agent Instructions

**Principle:** Build verification INTO the agent instructions themselves. The skill teaches the agent to check before acting, not just to act.

A self-verifying instruction decouples the skill's correctness from the author's maintenance cycles. The skill stays correct between edits because the agent re-verifies at execution time.

**Three components of a self-verifying instruction:**
1. **Canonical source list** — what to try (URLs, directories, commands)
2. **Runtime verification step** — how to check reachability/validity before using
3. **Fallback chain** — what to do when the primary source is unreachable

**Examples:**
- Instead of "the agentskills.io Showcase page is at X" with a hardcoded status, teach: "check if the source is reachable before using it; if 404, fall back to direct GitHub search"
- Instead of "run checklist A for every file", teach: "scan the changed files to detect what patterns changed; route to the relevant sub-skill based on what you find"
- Instead of "the version is 1.2.3", teach: "inspect pyproject.toml for version; if absent, try package.json or SKILL.md frontmatter"

**Principle underlying this:** "Trust the runtime, not the document." This is the same concept as a unit test vs documentation: one proves correctness at runtime, the other asserts it at write time.

---

### 6. Cross-Project Pattern Preservation

**Principle:** Capture and index patterns learned from other projects rather than treating each project as an isolated design. The preservation can range from inline citations to dedicated knowledge bases, depending on how many projects the maintainer runs.

**Spectrum of preservation:**

| Level | Mechanism | When appropriate |
|---|---|---|
| Inline citation | Reference another project's pattern in-line (e.g., "ohmyzsh proves zero tags is valid") | 1-3 projects, occasional cross-references |
| Extraction note | Durable findings note in the study repo (e.g., agent-concepts-study), tagged with source provenance and transfer tests | 3-8 projects, recurring pattern discovery |
| Dedicated knowledge base | Structured topic folders with claims, sources, freshness metadata (like Evidentia) | 8+ projects, high pattern recurrence rate |

**Transfer test per finding:** Frame each preserved pattern as a question a future project can ask itself. "When approaching any crowded ecosystem, ask: 'Is the marginal utility of adding another instance higher than the utility of teaching agents to navigate what already exists?'"

**Evidence hierarchy (from most to least reliable):**
1. Official standards and platform docs
2. Top ecosystem repositories (read via GitHub API)
3. Community resources, blogs, discussions
4. Your own prior project artifacts (with timestamp and context caveats)

See `durable-findings-extraction` for the methodology of extracting portable findings from a completed body of work.

---

### 7. File-Swamp Diagnosis and Prevention

**Principle:** Every skill repo needs a declared shipping boundary and a mechanism to detect when it's being eroded. File-swamp — development artifacts accumulating alongside the shipping surface — is structural, not accidental.

**Diagnostic checklist (6 metrics):**

| Metric | Swamp signal | Healthy range |
|--------|--------------|---------------|
| Per-skill reference ratio | > 3:1 ref files per SKILL.md | 0 per-skill refs to < 1:1 |
| Hand-maintained indexes | INDEX.md, DESCRIPTIONS.md prose | `ls skills/` or generated JSON |
| Dev artifacts shipped | ADRs, review infra in product dir | Dev in labelled non-shipping area |
| Script-to-skill ratio | > 2:1 scripts per skill | 0.1-0.3:1 (2-4 scripts for small repos) |
| Root items | > 12 | 6-8 |
| Agent instruction length | > 100 lines | ~20 lines |

**Causal chain:** No distribution boundary -> per-feature reference directories -> maintenance pipeline -> index files because frontmatter wasn't trusted -> architecture docs for the growing structure -> file-swamp. Each step was locally reasonable; no step asked the boundary question.

**The one-question gate:** Before adding any file, ask: "Can a runtime consume the skill without this file?" If no, it belongs in development tooling, not the shipping surface.

**Ecosystem benchmarks:**

| Repo | Skills | Files | Per-skill ref ratio | Scripts |
|------|--------|-------|--------------------|---------|
| addyosmani/agent-skills | 24 | 137 | 0:1 | 2 |
| cybersecurity-skills | 817 | ~3,700 | 1.8:1 | 22 |
| wondelai/skills | 50 | ~55 | 0:1 | 0 |
| skill-discovery | 1 | 12 | 0:1 | 3 |
| py-review-skill | 6 | ~25 | 0:1 | 4 |

**Remediation sequence:** (1) Declare the shipping boundary, (2) identify what runtimes actually load, (3) move dev artifacts out, (4) inline what can be inlined, (5) verify with `ls skills/` as catalog, (6) add CI gate for most likely drift surface.

**Meta-review trap:** File-swamp's most dangerous property is that it consumes its own maintainers. The review pipeline that exists to maintain the refs becomes the largest directory. If your repo has a meta-review directory, check whether it exists to maintain files that are themselves unnecessary.

See `references/file-swamp-patterns.md` for full diagnostic detail and benchmark data.

---

### 8. Portability Gradations and Decision Tree

**Principle:** Portability is not binary. Every skill falls into one of three tiers based on content and tool references. Choose the right tier consciously.

| Tier | What it means | Agent coverage |
|------|---------------|----------------|
| **Fully portable** | `name` + `description` frontmatter only. No agent-specific commands. | Any agentskills.io-compatible agent (42+ clients) |
| **Tools-portable** | References general CLI tools (`git`, `python3`, `curl`). No agent-specific tool names. | Any agent with shell access |
| **Platform-specific** | References agent-specific tools or config paths (`skill_view`, `hermes skills`). | One agent runtime |

**Decision tree:** Does the skill need agent-specific tooling?
- No -> Fully portable. Frontmatter: name + description only.
- Yes, but generic CLI suffice -> Tools-portable. May include scripts/.
- Yes, requires agent API -> Platform-specific. Add `compatibility` field.

**Body-content portability boundary:** Tool references in skill bodies are the primary portability boundary. A CI gate scans for agent-specific patterns:

| Pattern | Example | Breaks on |
|---------|---------|-----------|
| Hermes tool name | `skill_view(name)` | Claude Code, Codex, OpenCode, Cursor |
| Hermes CLI | `hermes skills install` | All non-Hermes agents |
| Agent config path | Hermes skills directory | All non-Hermes agents |
| Claude Code tool | `Claude()` | Hermes, Codex, OpenCode |
| Codex CLI command | `codex run` | Hermes, Claude Code |

**Portability testing (three layers):** (1) Frontmatter: validate against agentskills.io spec, (2) Body references: portability gate scan, (3) Shell commands: CI matrix on Linux + macOS for tools-portable skills.

**Schema gate vs portability gate:** Keep them separate. The schema gate (validate.py) defines what frontmatter fields are accepted. The portability gate (check-portability.py) scans for agent-specific references. They serve different purposes and evolve independently. See `references/dev-workflow-patterns.md` §3.

**Platform adapter anti-pattern:** Shipping `.claude/`, `.cursor/`, `.codex/` in the repo ties it to specific platforms. Exception: `.agents/skills/` symlink (no-maintenance cross-tool pointer).

See `references/portability-patterns.md` for full gradation framework, frontmatter portability table, and decision tree.

---

### 9. Information Density Analysis

**Principle:** The value of a SKILL.md is not measured by line count alone. Evaluate the information-to-line ratio to distinguish efficient density from wasteful expansion.

**When to use this:** When evaluating whether a skill is well-structured, comparing two similar skills, or deciding whether to inline vs reference content.

**Metrics to evaluate:**

| Aspect | High density signal | Low density signal |
|--------|-------------------|-------------------|
| Description scope | 8+ triggers in one sentence | Separate sentence per trigger |
| Procedural steps | Compact list, one decision per line | Expanded with examples per step |
| Code blocks | Show algorithm, serve as executable spec | Over-written, duplicate prose |
| Tables | 2-10 rows, non-obvious mappings | 10+ rows of common knowledge |
| Principle statements | Stated once, context-referenced | Repeated in each section |

**Layered signal strategy:** A skill serves multiple agent runtimes with varying capabilities. Low-density zones (code blocks, template commentary) serve as an **executable floor** for weak models, while high-density zones (trigger scope, fallback chain, evaluation rubric) serve as the **high ceiling** for strong models. The condensed quality lives in the structure, not a minimized line count.

**Transfer question:** "If I shipped this skill without the code blocks and template commentary, would a weak model execute it correctly? If no, the expansion is justified."

---

### 10. Evaluation Rubric and CI Triage

**Principle:** Skills that evaluate candidates (skills, patterns, tools) should use tiered classification, not binary pass/fail. CI for skill repos should automate only what no runtime catches.

**Four-tier evaluation rubric:**

| Tier | Criteria | Action |
|------|----------|--------|
| Direct hit | Name, description, body match. Source trusted. Install path clear. | Recommend first |
| Good partial | Covers domain but misses a feature or workflow detail | Recommend with gap stated |
| Weak partial | Shares keywords but needs substantial adaptation | Mention only if no better option |
| Off-domain | Does not solve the task | Exclude |

Apply 9 independent checks per candidate: task fit, trigger quality, trust, freshness, compatibility, installability, resource quality, safety, coverage.

**CI triage for skill repos:** Before adding any CI check, ask:
1. "What evidence says this is necessary at our scale?"
2. "Will a human or runtime catch this faster than our CI?"

| Check type | Verdict | Rationale |
|------------|---------|-----------|
| Frontmatter validity in shipped SKILL.md | Skip — runtime validates on load | Runtime catches it cheaper |
| Frontmatter validity in repo-local docs | Keep scoped | No runtime reads repo-local docs |
| Cross-agent portability | Keep in CI | No runtime validates this |
| URL status | Keep with evidence-urls.json manifest | Methodology self-verifies at runtime |
| Ceiling/ceiling monitors | Skip | `ls skills/` visible in one screen |
| index.json generation | Skip entirely | No runtime reads index.json for discovery |

**Path-restricted CI triggers** mechanically enforce the shipping boundary:
```yaml
on:
  push:
    paths:
      - 'README.md'
      - 'skills/**/*.md'
      - '.github/workflows/ci.yml'
      - '.github/scripts/**'
```
A file not in the trigger list is invisible to CI — and implicitly declared non-shipping.

See `references/operational-patterns.md` for full CI triage detail, fallback chain architecture, and evidence-base-as-architecture pattern.

---

The ten principles are not independent — they reinforce each other:

- **Methodology over collection** (1) reduces the need for anti-drift (3) because the methodology re-verifies at runtime instead of trusting static content
- **Declared shipping boundaries** (2) prevent the cascade that **file-swamp diagnosis** (7) would otherwise need to remediate
- **Heuristic discovery** (4) is the operational mechanism behind **self-verifying instructions** (5)
- **Portability gradations** (8) determine what goes in the shipping surface (2) and what needs the **CI portability gate** (10)
- **Information density analysis** (9) prevents the meta-review trap where reference files expand beyond the content they support
- **Cross-project pattern preservation** (6) makes the other nine principles cumulative instead of rediscovered

**Root philosophy (common across all ten):**

> **Trust the runtime, not the document.**
> Teach agents to verify at execution time. Ship methodologies, not snapshots. Add drift checks only after failure proves the need. Declare boundaries to prevent cascade. Preserve patterns so they need not be rediscovered.

This is not a design preference — it's a response to a measured property of the ecosystem: sources drift within hours, catalogs stale within weeks, and hardcoded assertions decay faster than any maintenance cycle can keep up with.

## Common Pitfalls

1. **Skipping the boundary declaration.** Without an explicit "what does NOT ship" list, every new directory seems reasonable. The file-swamp cascade starts with the first unexamined directory. Always declare the boundary at repo creation time.

2. **Adding drift checks before failure proves the need.** "Could break someday" is not a reason to add a check. Wait until an actual failure demonstrates the cost of not having the check. Then the ROI calculation is grounded.

3. **Assuming you need a knowledge base when 3 inline citations would do.** Pattern preservation has a spectrum. Start with inline citations. Add extraction notes when you find yourself re-citing the same project in multiple places. Only build a dedicated KB when you have 8+ active projects with recurring cross-project patterns.

4. **Designing the shipping boundary after building the repo.** By the time a repo has 160 files across 9 skills, declaring a boundary means deleting or relocating 80% of them. Declare the boundary first — it constrains every subsequent addition.

5. **Treating the methodology decision as permanent.** The right choice changes with ecosystem density. A methodology skill that was right at 2,460 skills may need to become a collection if the ecosystem fragments or the search experience degrades. Re-evaluate the methodology-vs-collection decision when ecosystem conditions change.

6. **Confusing self-verifying instructions with self-testing code.** A self-verifying instruction tells the agent HOW to verify. It does not automatically execute the verification. The agent must be capable of running the checks (which depends on available tools: terminal, network, browser). Document which agent capabilities each verification step requires.

## Verification Checklist

- [ ] Shipping boundary declared — what ships vs what stays repo-local is explicit in README
- [ ] No speculative drift checks — every check traces to an observed failure
- [ ] Runtime heuristics preferred over hardcoded tables for volatile values
- [ ] Agent instructions include verification steps, not just actions
- [ ] Cross-project patterns preserved at the appropriate level for the project count
- [ ] Methodology-vs-collection decision is documented with the reasoning
- [ ] File count and structure match the shipping boundary (no leaked dev artifacts)
- [ ] File-swamp metrics measured — per-skill ref ratio, script-to-skill ratio, root items all in healthy range
- [ ] Portability tier chosen consciously — gradation documented and CI gate matches
- [ ] Information density evaluated — code blocks and examples justified by weak-model need
- [ ] CI checks pass the two-question test — every check has a verified failure mode
- [ ] CI triggers path-restricted — only files affecting shipping surface run the pipeline
- [ ] If the ecosystem has changed since the repo was designed, the methodology decision has been re-evaluated
- [ ] Related skills referenced: skill-packaging (distribution), hermes-agent-skill-authoring (file format), cross-ecosystem-skill-research (research methodology), durable-findings-extraction (knowledge extraction), skill-portability-gate (CI enforcement)

## References

- `references/dev-workflow-patterns.md` — 6 operational patterns from cross-repo refactoring: no-copy development (external_dirs), README install section structure, schema gate vs portability gate separation, payload manifest pattern, two drift classes, and frontmatter evolution bridge.
- `references/agent-concepts-study-cross-project-patterns.md` — the 6 design principles in full detail with observed evidence from four shipping projects (CodeSigils: skill-discovery, py-review-skill, repo-health-and-sync-skill, emerging-pattern-proposals). Includes the full research note from 2026-07-08 with source analysis per principle.
- `references/file-swamp-patterns.md` — diagnostic checklist, causal chain analysis, ecosystem benchmarks (6 repos with file-to-skill ratios), remediation sequence, and prevention guidance for avoiding file-swamp in skill repositories.
- `references/portability-patterns.md` — three-tier portability gradation framework (fully portable, tools-portable, platform-specific), frontmatter vs body-content portability rules, decision tree, and portability CI gate implementation.
- `references/operational-patterns.md` — scoped CI triage logic (automate only what no runtime catches), path-restricted CI triggers, four-tier evaluation rubric, and the two-question test for infrastructure decisions.
- `references/skill-repo-audit-procedure.md` — structured 9-phase audit for skill repositories: git hygiene, CI workflow review, portability verification, structure metrics, provenance checks, .gitignore audit, local validation execution, GitHub metadata review, and findings documentation.
- `references/npm-publishing-for-agent-skills.md` — methodology for evaluating and publishing an agent-first tool on npm: landscape survey, competitive analysis, naming strategy, dual-use repo design, and per-competitor evaluation checklist.
- `references/payload-manifest-pattern.md` — JSON manifest + bash sync-script implementation for mechanically enforcing the shipping boundary in CI. Covers manifest format, orphan cleanup algorithm, reference mirroring, hub scanner pitfalls, and CI integration.
