# File-Swamp and Ownership Patterns

File-swamp is an ownership problem, not a file-count threshold. It appears when
files lack a clear consumer, canonical source, or deletion condition.

## Diagnostic questions

For each suspicious file or directory, ask:

1. Which of the four boundaries owns it?
2. What reads, executes, installs, publishes, or validates it?
3. Is it canonical, generated, or historical?
4. What concrete failure occurs if it disappears or drifts?
5. Is the same information maintained elsewhere?

## Strong signals

- Tracked replicas without a generator and drift check.
- Runtime references that `SKILL.md` never routes to.
- Maintainer plans, research, fixtures, or CI helpers inside the payload.
- Hand-maintained indexes that duplicate filesystem or manifest discovery.
- Scripts with no caller in runtime instructions, package scripts, CI, or docs.
- Several sources claiming ownership of the same workflow.
- Validators that enforce prose layout without protecting behavior or an artifact.
- Generated artifacts committed even though installation can consume the source.

## Archetype-sensitive interpretation

| Observation                | Healthy possibility                                   | Unhealthy possibility                     |
| -------------------------- | ----------------------------------------------------- | ----------------------------------------- |
| Many scripts, one skill    | Tool-backed skill with tested runtime code            | Static skill with speculative helpers     |
| Many references, one skill | Conditional domain variants with direct routing       | Historical notes copied into payload      |
| Large maintainer surface   | Operational or released product with owned invariants | Checks added without failure evidence     |
| Duplicate payload tree     | Required package/install artifact with drift test     | Convenience copy with no install consumer |
| Several skills             | Independently loadable pack with router tests         | Accidental fragmentation of one procedure |

## Remediation order

1. Classify the repository and declare all four boundaries.
2. Choose one canonical authoring source for every concept.
3. Remove unconsumed files and relocate maintainer-only material.
4. Inline small fragments; route genuinely conditional detail to references.
5. Eliminate tracked replicas when clients can install the canonical payload.
6. Where replication is required, generate it and test the installed artifact.
7. Add only the smallest check needed to prevent the observed recurrence.

Report counts as evidence, but base findings on ownership, consumers, and failure
modes rather than a universal ratio.
