# File-Swamp Patterns — Session Detail

> Session-derived detail from 2026-07-08 file-swamp analysis.
> See the main skill SKILL.md §7 for the actionable principles.

## Causal Cascade: Full Trace

From hermes-skill-hq (161 files, 9 skills):

```text
No distribution boundary
  -> per-guide refs/ directories (65 files)
  -> hq-review pipeline to maintain refs (43 files)
  -> ADRs for architecture decisions (10 files)
  -> index/ because frontmatter wasn't trusted as catalog (3 files)
  -> shell+Python pairs in scripts/ (6 files)
  = 161 files for 9 skills
```

Each step made sense given the state at the time. No step included the rule "can a runtime consume the skill without this file?"

## How the Bridge Plan Cut Each Driver

By declaring skills/ as the shipping surface:

| Driver | Bridge decision | Evidence basis |
|--------|----------------|---------------|
| Per-guide refs/ | No per-skill refs. Inline as code blocks. | addyosmani: 24 skills, no references/, ~68K stars |
| Review pipeline | One rg script (3 lines of logic) | addyosmani: 2 scripts total |
| ADRs | Not created at this scale | No compared ecosystem repo ships ADRs alongside skills |
| index/ | Not created — ls skills/ is the catalog | agentskills.io spec; no runtime reads prose indexes |
| Dual scripts | One language (Python) | addyosmani: all Python |

## Six-Metric Diagnostic Detail

| Metric | Swamp signal | Healthy range | How to measure |
|--------|--------------|---------------|----------------|
| Per-skill ref ratio | > 3:1 ref files per SKILL.md | 0 (addyosmani) to < 1:1 | find skills/*/references/ -name '*.md' | wc -l; ls skills/*/SKILL.md | wc -l |
| Hand-maintained indexes | INDEX.md, DESCRIPTIONS.md prose | Generated JSON or none | test -f INDEX.md |
| Dev artifacts shipped | ADRs, review infra in skills/ dir | Dev in labelled non-shipping area | ls for adr/, dev/, plan.md, todos.md |
| Script-to-skill ratio | > 2:1 | 0.1-0.3:1 (2-4 total) | ls scripts/*.sh scripts/*.py 2>/dev/null | wc -l; ls skills/*/SKILL.md | wc -l |
| Root items | > 12 | 6-8 | ls -1d * | wc -l |
| Agent instruction length | > 100 lines | ~20 lines | wc -l AGENTS.md 2>/dev/null |

## Ecosystem Benchmark Detail

Data from 2026-07-01 cold reads via GitHub API:

| Repo | Stars | Skills | Total files | Ref files | Scripts | Per-skill ref ratio | Root items |
|------|-------|--------|-------------|-----------|---------|--------------------|------------|
| addyosmani/agent-skills | ~68K | 24 | 137 | 0 | 2 | 0:1 | 19 |
| cybersecurity-skills | ~23K | 817 | ~3,700 | 1,453 | 22 | 1.8:1 | ~12 |
| wondelai/skills | ~1.5K | 50 | ~55 | 0 | 0 | 0:1 | 12 |
| OpenMontage | ~29K | 124 | ~590 | 459 | 22 | 3.7:1 | ~15 |
| skill-discovery | — | 1 | 12 | 0 | 3 | 0:1 | 7 |
| py-review-skill | — | 6 | ~25 | 0 | 4 | 0:1 | 8 |

Key takeaways:
- Zero per-skill refs viable up to at least 24 skills (addyosmani)
- index.json helps at 800+ scale but unnecessary below ~50
- Script count should stay under 4 for repos under 25 skills
- Root items above 12 create namespace crowding

## Remediation Sequence Detail

The six-step fix, derived from 161-to-12 file reduction:

**Step 1 — Declare boundary.** Pick one directory (skills/) as product surface. Everything else is dev tooling.

**Step 2 — Identify what runtimes load.** Walk each SKILL.md. Is references/ referenced from the body? Are scripts called at runtime or only from CI?

**Step 3 — Move dev artifacts.** ADRs go to dev/adr/ or design branch. Review pipeline stays in dev/hq-review/. CI stays in .github/.

**Step 4 — Inline.** If references/ contains a single table or list that fits in SKILL.md body, inline it.

**Step 5 — Verify.** `ls skills/` should clearly communicate what exists. If not, fix naming before adding indexes.

**Step 6 — Add CI gate.** Add one check for the most likely drift surface (portability drift, URL status, or file existence).
