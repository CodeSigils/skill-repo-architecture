# Operational Patterns — Session Detail

> Session-derived detail from 2026-07-08 CI triage analysis.
> See the main skill SKILL.md §10 for the actionable principles.

## CI Triage: Full Rationale Per Check

From skill-discovery's CI (3 checks):

| Check | What it catches | Why CI is right | Why NOT runtime |
|-------|----------------|-----------------|-----------------|
| Portability gate | Hermes-specific refs in skills/ | Non-Hermes agents silently fail — no runtime validates cross-agent portability | A Hermes agent never sees the problem; a Codex agent silently misreads |
| Docs frontmatter | Missing fields, expired dates, unlabelled fences in docs/ | Docs are repo-only artifacts that no runtime touches | No runtime ever reads repo-local docs |
| URL drift | Live URL status differs from expected state | Drift is invisible without periodic checking | Methodology self-verifies at execution time, but the evidence base doesn't self-correct |

## Path-Restricted CI Triggers

From skill-discovery's CI workflow:

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'README.md'
      - 'SECURITY.md'
      - '.agents/skills/skill-discovery'
      - 'skills/**/*.md'
      - 'docs/**'
      - '.github/workflows/ci.yml'
      - '.github/scripts/**'
```

This does two things: (1) documentation-only changes don't waste CI minutes, (2) any newly added file either affects the shipping surface (goes in the trigger list) or is dev tooling (doesn't). A file not in this list is implicitly declared non-shipping.

## Two-Question Test Decisions

From skill-discovery's planning:

| Decision | Evidence | Verdict |
|----------|----------|---------|
| Frontmatter validation CI | Runtimes validate shipped SKILL.md on load, but repo-only docs benefit | Keep scoped — validate docs/frontmatter |
| Ceiling checks (40 files, 24 skills) | At 4 skills, ls skills/ is half a screen | Skip — manual review catches violations |
| index.json generation | No runtime reads it for discovery | Skip entirely |
| Hermes-reference drift detection | Non-Hermes agents silently fail — no runtime validates this | Keep in CI |

## Four-Tier Evaluation Rubric Detail

```text
Direct hit:  Name, description, body match task. Source trusted. Install path clear.
             -> Recommend first.
Good partial: Covers domain but misses a feature or workflow.
             -> Recommend with the gap stated.
Weak partial: Shares keywords but needs substantial adaptation.
             -> Mention only if no better option exists.
Off-domain:   Does not solve the task.
             -> Exclude.
```

Nine independent checks applied per candidate: task fit, trigger quality, trust, freshness, compatibility, installability, resource quality, safety, coverage. A candidate must pass all to be a "direct hit."

## Fallback Chain Architecture

From skill-discovery's methodology (7-stage progressive widening):

1. Installed/local skills (tools: filesystem)
2. Local or hosted catalog index (tools: filesystem, json)
3. Featured or curated sources (tools: filesystem or HTTP)
4. Marketplace APIs (tools: HTTP, json parser)
5. Browser-rendered marketplace (tools: browser, conditional)
6. GitHub and web research (tools: HTTP, GitHub API)
7. Build or draft a new skill (tools: any)

Each stage documents tool requirements. If the agent lacks a tool, the stage is skipped and reported. Exit condition per stage: "did we find a direct-hit candidate?" not "did we find any candidate?"

## Evidence-Base-as-Architecture

From skill-discovery: research evidence lives in docs/ and is explicitly NOT shipped:

```text
docs/                      # repo-only — provenance and audit trail
  hub-marketplace-research.md
  evidence-urls.json

skills/                    # shipping surface
  skill-discovery/
    SKILL.md               # self-contained, agent-agnostic
```

The research doc records methodology, limitations, verification timestamps, and a drift register. The shipped SKILL.md references nothing in docs/. This prevents two failure modes: (1) evidence rot — if docs were shipped, every URL status change would produce false positives for users; (2) blind shipping — if the skill referenced docs/, it would break on reorganization.
