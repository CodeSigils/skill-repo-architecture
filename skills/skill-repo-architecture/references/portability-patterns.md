# Portability Patterns — Session Detail  # portability: allow-platform-ref

> Session-derived detail from 2026-07-08 portability analysis.
> See the main skill SKILL.md §8 for the actionable principles.

## Frontmatter Portability: Field-by-Field

The agentskills.io specification defines the portable baseline. Platform extensions are additive:

| Field | Portable? | Notes |
|-------|-----------|-------|
| `name` | Yes | Required by all platforms |
| `description` | Yes | Required by all platforms |
| `metadata.*` | Yes | Ignored by non-Hermes clients; harmless |
| `compatibility` | Yes | Ignored by clients that don't recognize the value |
| `context: fork` | Claude Code only | Silently ignored by Hermes; may affect behavior on Codex |
| `allowed-tools` | Claude Code only | Same risk |
| `globs` / `alwaysApply` | Cursor only | Cursor .mdc format, not SKILL.md |

Safe rule: stick to `name`, `description`, and `metadata.*` for portable skills. Add platform-specific fields only when verified that they're silently ignored by other clients.

## Body-Content Portability: Forbidden Patterns

From ci-check.py in skill-discovery, generalized:

```python
FORBIDDEN_PATTERNS = [
    (r"\bskill_(?:view|manage)\b", "Hermes tool name"),
    (r"\bhermes\s+(?:skills?|config)\b", "Hermes CLI command"),
    (r"HERMES_CONFIG_DIR", "Hermes config path"),
    (r"\bClaude\(\)", "Claude Code tool"),
    (r"\bcodex\s+run\b", "Codex CLI command"),
    (r"\bgemini\s+skills\b", "Gemini CLI command"),
]
```

A truly portable skill uses only generic shell commands (`git`, `python3`, `node`, `curl`, `find`, `grep -E`) and avoids any agent-specific tool, config path, or CLI command.

## Platform Adapter Anti-Pattern Detail

| Approach | Drift surface | Maintenance cost | User experience |
|----------|---------------|------------------|-----------------|
| Ship all adapters in repo | High — each platform path change breaks one | High — update N files per release | Best — copy-paste one dir |
| Ship zero adapters, document in README | None | Low — one doc update per platform change | Good — user reads README |
| Ship .agents/skills/ symlink only | None | Zero | Good — auto-discovery for .agents/-aware clients |

## Portability Decision Tree Detail

```text
Does the skill need agent-specific tooling?
  No -> Fully portable
    Frontmatter: name + description only
    Body: prose rules, no tool commands
    Ships: skills/<name>/SKILL.md
    Coverage: 42+ agentskills.io clients

  Yes, but generic CLI suffice -> Tools-portable
    Frontmatter: name + description + metadata.*
    Body: git, python3, curl commands only
    Ships: skills/<name>/SKILL.md + optional scripts/
    Coverage: any agent with shell access

  Yes, requires agent-specific API -> Platform-specific
    Frontmatter: name + description + compatibility: <agent>
    Body: platform CLI, tool names, config paths
    Ships: skills/<name>/SKILL.md
    Coverage: one agent runtime
    Note: document which agent is required
```

## Portability Testing (Three-Layer)

| Layer | What it checks | How to test | Catches |
|-------|---------------|-------------|---------|
| Frontmatter | Parses correctly on all clients | Validate against agentskills.io spec | Client-side parse failures |
| Body references | No agent-specific tool names | Portability gate scan | Silent misreads on non-target agents |
| Shell commands | Cross-platform compatibility | CI matrix on Linux + macOS | grep -P, which, BSD/GNU incompatibility |

For tools-portable skills, the most common failure is non-portable shell commands. A CI matrix running key commands on both Ubuntu and macOS catches `which` vs `command -v`, `grep -P` vs `grep -E`, and `sed -i` portability issues.
