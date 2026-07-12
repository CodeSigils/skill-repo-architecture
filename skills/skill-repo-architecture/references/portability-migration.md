# Portability Migration — From Platform-Specific to Cross-Platform  # portability: allow-platform-ref

> Session-derived technique from 2026-07-10.
> Applied to: repo-health-and-sync-skill (B0 quality-skill fallback).

## The Problem

A Hermes skill relies on `skill_view(name)` as the primary probe for
tool availability. On Claude Code, Codex CLI, or Gemini CLI, this call
is meaningless — the agent either fails silently or skips the check
entirely. The skill declares `compatibility: hermes` honestly but the
B1-B11 detection logic is agent-agnostic except for this one probe.

## The Quad-Layer Cross-Platform Probe

Replace any agent-specific first-probe (`skill_view`, `hermes skills`,
`Claude()`) with this fallback chain:

```
1. command -v <tool>      — PATH check (works on every system)
2. Config/project file    — look for ecosystem-equivalent config
   (.pylintrc, .flake8, .ruff.toml, .prettierrc, etc.)
3. skill_view(name)        — Hermes-only optimization (skip on non-Hermes)
4. Degraded mode           — skip the check, log the reason
```

**Rules:**
- If step 1 succeeds, use the tool directly. Do not chain further.
- Only fall through to step 2 when the binary is absent.
- Only try step 3 when steps 1 and 2 both fail AND the agent is Hermes.
- Step 4 is always available — skipping a check is better than fabricating
  a pass or a fail.

## The Coordination Principle

When making a skill cross-platform, the key insight is:

> **Detection logic is agent-agnostic. Only the activation mechanism
> and the tool-availability probe are platform-specific.**

In repo-health-and-sync-skill, B1-B11 detection commands (`git log`,
`find . -name '*.sh'`, `shellcheck`, etc.) are all agent-agnostic.
Only the quality-skill fallback (how to decide whether a tool is
available) and the C-phase sync targets (where to deploy) are Hermes-
specific. This means ~90% of the skill was already portable — the fix
was one section.

## README Per-Platform Install Pattern

After fixing the probe, update the README to show all platforms.
Pattern (from skill-discovery and repo-health-and-sync-skill):

```
Clone this repo and make the skill discoverable:

  git clone --filter=blob:none https://github.com/CodeSigils/<repo>

Then choose your platform:

<details>
<summary><b>Hermes Agent</b></summary>
  ... hermes-specific instructions ...
</details>
<details>
<summary><b>Claude Code (Anthropic)</b></summary>
  ... cp to .claude/skills/ ...
</details>
<details>
<summary><b>Codex CLI (OpenAI)</b></summary>
  ... cp to .codex/skills/ ...
</details>
<details>
<summary><b>OpenCode CLI</b></summary>
  ... cp or ln -s to .opencode/skills/ ...
</details>
<details>
<summary><b>Gemini CLI (Google)</b></summary>
  ... cp to .agents/skills/ ...
</details>
<details>
<summary><b>Cursor</b></summary>
  ... cp to .cursor/rules/ ...
</details>
<details>
<summary><b>Generic agentskills.io client</b></summary>
  ... cp to <your-skills-dir>/ ...
</details>
```

## Verify Before Shipping

After patching the probe:
1. Check that every agent-specific reference (`skill_view`, `hermes`,
   `~/.hermes/`) still present is intentional (documentation of
   platform-specific features, not detection logic)
2. The Forge-awareness line in SKILL.md should say "platform-specific
   CLI registration" not "hermes skills install"
3. README should declare the portability tier explicitly — "Works on
   any agentskills.io-compatible agent" not "For Hermes agents"
4. B12 portability gate should be optional for single-platform skills
   but required once any cross-platform claim is made

## See Also

- `references/portability-patterns.md` — Three-tier gradation framework
- `references/operational-patterns.md` — CI gate for portability
- The quad-layer probe was validated in repo-health-and-sync-skill
  commit 3fb6118
