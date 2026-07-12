# Cross-Project Pattern Analysis: Skill Repo Architecture  # portability: allow-platform-ref

> Session-derived detail from 2026-07-08 cold-read of four CodeSigils shipping projects.
> Not project authority. For project truth, read each repository directly.

## Source Projects

| Project | Scope | Core insight |
|---------|-------|-------------|
| **skill-discovery** | 1 methodology SKILL.md teaching agents how to find skills across 2,460 indexed entries | Reframed from "ship a collection" to "teach agents to find skills" |
| **py-review-skill** | 1 routing SKILL.md + 5 focused sub-skills (type safety, error handling, anti-patterns, async, style) | Route by what changed, not a fixed checklist |
| **repo-health-and-sync-skill** | 22-phase procedure (B1-B11, C1-C4) with runtime heuristic discovery | Discover at runtime; no hardcoded project metadata |
| **emerging-pattern-proposals** (Evidentia/RAMDA) | Cross-project pattern atlas, ADRs, lesson records, methodology proposal | Research once, reuse with evidence; pattern preservation across projects |

## Evidence per Principle

### Principle 1: Methodology over Collection

- skill-discovery explicitly reframed from "ship 3-9 skills" to "ship 1 methodology that teaches agents to search 2,460." README states: "This is a **methodology**, not a skill collection."
- py-review-skill ships a routing skill whose only job is to orient on context and dispatch. The routing IS the methodology; the sub-skills are reference knowledge.
- repo-health-and-sync-skill discovers everything at runtime — scripts, manifests, version sources, sync targets — via heuristics. No pre-packaged project metadata.
- Evidentia/RAMDA is a meta-methodology: a methodology about how to research, reuse claims, and refresh stale knowledge across projects.

### Principle 2: Declared Shipping Boundaries

- skill-discovery: "What This Repo Does NOT Include" in both README and plan files. Deliberately excludes static collections, install scripts, platform adapter files, index manifests. Only `skills/*/SKILL.md` ships.
- py-review-skill: "The runtime surface is intentionally small: `skills/*/SKILL.md` files use only `name` and `description` frontmatter." No one-file-per-rule pattern.
- repo-health-and-sync-skill: "The git repository is the authoritative copy of every file it tracks. Deployed runtime targets are derived copies." Explicitly prohibits shipping maintainer tooling to user machines.
- Evidentia: Extensive non-goals section — not a scaffolding generator, not a vector database, not a dumping ground, not a static-site generator.

### Principle 3: Proportionate Anti-Drift from Observed Failure

- skill-discovery CI validates exactly what no runtime catches: cross-agent portability drift and docs frontmatter integrity. Everything else left to runtime.
- py-review-skill ships 4 validation scripts, each with a clear single purpose (rule schema, inline examples, timestamp drift, URL status).
- repo-health-and-sync-skill B0: "Proportionate anti-drift. Every check should trace to a specific observed failure mode. Speculative checks accumulate maintenance debt before they create value."
- Evidentia Pattern A: "Automate invariants, not nuanced narrative prose." Three-layer defense: prevent through contracts, detect through checks, recover through documented process.

### Principle 4: Heuristic Discovery over Hardcoded Configuration

- skill-discovery: "Verify source reachability at runtime." The agentskills.io Showcase 404->200->404 loop within hours proved this principle non-academic.
- py-review-skill: Routes review by inspecting what changed (scanning for type annotations, async patterns, error handling patterns).
- repo-health-and-sync-skill: "Detect, don't enforce. No convention is universal across ecosystems." Discovers shell scripts, version sources, formatter configs at runtime. `.repo-health.json` is optional.
- Evidentia Pattern S (Source-of-Truth & Volatile Claim Registry): agents verify the lowest authoritative source before trusting prose.

### Principle 5: Self-Verifying Agent Instructions

- skill-discovery: "The methodology is self-verifying — it teaches agents to check source reachability at runtime rather than relying on hardcoded URLs that drift."
- py-review-skill: "Read the exact changed files before flagging issues. A rule match is a signal, not a verdict." First step is context orientation, not review.
- repo-health-and-sync-skill: Every B-phase sub-step includes "How" instructions telling the agent which commands to run. Co-author guard (B11) ships as a Python checker used identically by hooks and CI.
- Evidentia RAMDA loop: "search KB -> reuse current claims -> refresh stale sources -> apply -> capture lessons -> promote." The agent executes the freshness check.

### Principle 6: Cross-Project Pattern Preservation

- skill-discovery's durable findings note (2026-07-01) extracted 13 cross-project findings, each with source provenance and transfer test.
- py-review-skill's methodology-alignment doc and extraction-log trace provenance from an external source commit.
- repo-health-and-sync-skill's design principles cite cross-project patterns: "Zero tags is valid (ohmyzsh, 188k stars)," "Commit log vs CHANGELOG" from multiple project observations.
- Evidentia's entire purpose IS cross-project pattern preservation. Cross-Project Pattern Atlas maps 14 failure modes across 5 source repos to their cures.

## File-Swamp Cascade (from skill-discovery research)

The cascade mechanism behind Principle 2's warning:

```
No distribution boundary
  -> per-guide refs/ directories
  -> hq-review pipeline to maintain it all
  -> ADRs to document architecture decisions (10 files)
  -> index/ because frontmatter wasn't trusted as catalog
  -> shell+Python pairs in scripts/
  = 161 files for 9 skills (hermes-skill-hq)
```

Each step was locally reasonable. No step included the question: "Can a runtime consume the skill without this file?"

## Cross-Platform Convergence (2026-07-01 snapshot)

Major agent platforms and their skill discovery paths:

| Platform | Discovery path | Mechanism |
|----------|---------------|-----------|
| Claude Code | `.claude/skills/` + `.claude-plugin/plugin.json` | Native SKILL.md discovery |
| Codex CLI | `.codex/skills/` or `AGENTS.md` | Two-layer: persistent + on-demand |
| Gemini CLI | `.agents/skills/` or `.gemini/skills/` | Cross-tool interoperable |
| OpenCode | `.opencode/skills/` -> symlink | Platform adapter |
| Cursor | `.cursor/rules/` | Rule-based |
| Copilot | `awesome-copilot` plugin marketplace | Community-driven |
| Hermes Agent | 6 paths (external_dirs, hub install, /learn, direct drop-in, hub tap, direct URL) | Directory-based progressive disclosure |
| Any agentskills.io client | `skills/*/SKILL.md` | Native format |

The emerging cross-tool path is `.agents/`. Platform adapter files should not ship in the repo — they are user-side configuration.

## Open Questions (from the agent-concepts-study note)

- Whether 6 patterns is exhaustive or selective — observed across 4 projects by same maintainer (CodeSigils). Transferability to projects with different authorship is unknown.
- Methodology-over-collection requires a skill ecosystem dense enough to navigate. Below what density does a collection become the right answer? (2,460 made the reframe obvious; threshold for other domains unknown.)
- Self-verifying instructions consume more tokens per invocation. Breakpoint where runtime cost of verification exceeds maintenance cost of keeping static instructions fresh is unknown.
