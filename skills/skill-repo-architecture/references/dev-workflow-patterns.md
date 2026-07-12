# Development Workflow Patterns  # portability: allow-platform-ref

**Purpose:** Operational patterns discovered during a cross-repo refactoring
session (2026-07-11) across 5 CodeSigils skill repositories. These patterns
emerged from hands-on work, not static analysis — they represent the *practice*
of maintaining cross-agent skill repos.

**Source repos:** `zero-md-formatter`, `repo-health-and-sync-skill`,
`skill-discovery`, `py-review-skill`, `python-project-workflow`

---

## 1. No-Copy Development Principle

**Problem:** The installed mirror of a skill (at `~/.hermes/skills/<name>/`)
drifts from the repo source. When the repo restructures (deletes files, changes
frontmatter, inlines references), the installed copy silently stays behind.
This is not payload drift (derived file out of sync with source) — it is
*mirror staleness* (installed copy predates a restructuring).

**Pattern:** Use `external_dirs` during development so the agent reads the
repo directly. No copy exists to drift.  # portability: allow-platform-ref

```yaml
# ~/.hermes/config.yaml
skills:
  external_dirs:
    - /path/to/my-skill-repo/skills
```

| Approach | Drift class | Fix cost |
|----------|-------------|----------|
| `external_dirs` | None — no copy created | Zero |
| `hermes skills install --force` | Mirror staleness | Detect → reinstall |
| Manual `cp -r` | Mirror staleness + payload drift | Detect → diff → cp |

**Evidence:** `python-project-workflow` had an installed mirror that predated
a restructuring commit (57cec93). The installed copy had `project-orientation.md`
and a different SKILL.md structure, while the repo had inlined that content and
deleted the reference. The mirror was stale not because of a sync failure, but
because no mechanism existed to propagate the restructuring. Using `external_dirs`
eliminates the class entirely.

**Trade-off:** `external_dirs` loads from the repo's working tree. Uncommitted
changes, temporary branches, and experimental edits are visible to the agent.
Use a dedicated clone or a stable branch for production agent sessions.

---

## 2. README Install Section Structure

**Problem:** README install instructions that mix Hermes and cross-agent setup
in unstructured paragraphs make it hard for each platform's users to find their
path. Inline code blocks with Hermes-specific commands in the global quickstart
also break the cross-agent promise.

**Pattern:** Every skill repo README should use a consistent three-part Hermes
section:

```markdown
<details>
<summary><b>Hermes Agent</b></summary>

**Recommended for development — clone the repo and add to `external_dirs`:**
```yaml
skills:
  external_dirs:
    - /path/to/repo/skills
```
Every commit is immediately reflected without reinstalling.

**For end users — install from hub:**
```bash
hermes skills install Owner/repo
```

*Other agents: see sections below for their native setup commands.*
</details>
```

Then one `<details>` block per other platform, each with a single `cp` command.

**Evidence:** This pattern was applied to all 5 repos in a single session.
It produces the same outcome for every platform with zero cross-agent
contamination — each platform's block is self-contained.

---

## 3. Schema Gate vs Portability Gate Separation

**Problem:** A single CI check that validates frontmatter schema AND scans for
portability hazards conflates two concerns. When the frontmatter schema needs
to expand (from `{name, description}` to include `version`, `ref`, `metadata`
for hub publishing), the portability check falsely triggers because the same
script searches the full file text for patterns like `metadata:`.

**Pattern:** Maintain two independent CI checks:

| Gate | What it checks | Scope | Failure mode |
|------|---------------|-------|-------------|
| **Schema gate** (validate.py) | Frontmatter fields, required sections, file existence, reference counts | SKILL.md + references | Field not in ALLOWED_FIELDS set |
| **Portability gate** (check-portability.py) | Agent-specific tool names, config paths, CLI commands in body only | Skill files only | Platform-specific reference found |

The schema gate's `ALLOWED_FIELDS` set defines what frontmatter is accepted.
Keep it broad enough for hub publishing:

```python
ALLOWED_FIELDS = {
    "name", "description", "version", "author", "license",
    "tier", "ref", "compatibility", "metadata",
}
```

The portability gate scans only the body (not frontmatter) for agent-specific
patterns. Structural frontmatter fields (`metadata:`, `version:`, `ref:`) must
never appear in its forbidden list — they are valid schema, not portability
hazards. The real CI portability gate (`check-portability.py`) independently
catches agent-specific references regardless.

**Evidence:** `python-project-workflow`'s validate.py originally rejected
extended frontmatter and searched the full text for `metadata:`, `tier:`,
`version:` as "non-portable" — conflating schema enforcement with portability
scanning. Fixing the separation (validate.py accepts extended fields, scopes
forbidden list to body-only portability hazards) made the repo hub-publishable
without weakening the portability gate.

---

## 4. Payload Manifest Pattern

**Problem:** Skill repos with multiple shipped files (SKILL.md + references +
scripts) have no single source of truth for what belongs in the deployable
package. Files accumulate, drift, and get orphaned.

**Pattern:** Maintain a `scripts/payload-manifest.json` declaring shipped files
by category, paired with a `scripts/sync-payload.sh` that rebuilds the payload
and removes orphans. Run `--ci` mode in CI to enforce.

```json
{
  "files": ["SKILL.md"],
  "scripts": ["check-pattern.py"],
  "references": "*"
}
```

Three categories:
- `"files"` — root-level files by relative path (SKILL.md, .repo-health.json)
- `"scripts"` — files under `scripts/` by basename
- `"references"` — `"*"` to mirror entire directory, or explicit array

**Owner:** `scripts/sync-payload.sh` handles orphan cleanup, reference
mirroring, and execute-permission preservation. CI runs `--ci` mode which
exits 1 on any drift.

This pattern replaced the flat-array approach (`RUNTIME_PAYLOAD_FILES` in
zero-md-formatter) because JSON + bash is cross-project portable, handles
reference directories with `"*"`, auto-removes orphans, and needs no test
file updates when the payload changes.

**Evidence:** Implemented in `repo-health-and-sync-skill` (commit 5d76011)
and adopted in this repo. Detected and cleaned 4 stale reference files that
had been deleted from root source but never removed from the payload.

---

## 5. Two Drift Classes — Different Fixes

**Problem:** All drift looks the same on the surface (repo != installed copy),
but the root cause and fix differ. Using the wrong fix makes things worse.

| Drift class | Example | Cause | Fix |
|------------|---------|-------|-----|
| **Payload drift** | `scripts/` source != `skills/*/scripts/` copy | Author edited source but forgot to re-sync | `bash sync-payload.sh` |
| **Mirror staleness** | Installed copy predates repo restructuring | No mechanism propagates repo → installed copy | `external_dirs` (prevents) or `cp -r` (fixes once) |

**Diagnostic question:** "Does the repo have a file that the installed copy
is missing, or does the installed copy have a file the repo doesn't?"

- Repo has it, installed doesn't → **payload drift** — run sync-payload
- Installed has it, repo doesn't → **mirror staleness** — copy from repo
- Both have it but content differs → either — check git log for last edit

**Evidence:** `python-project-workflow` had mirror staleness (installed had
`project-orientation.md` that was deleted from repo months ago). The fix was
not a sync script — it was `cp -r` from repo to installed mirror. The lasting
fix is `external_dirs` which prevents the class from recurring.

---

## 6. Frontmatter Evolution Bridge

**Problem:** A skill's frontmature starts minimal (`{name, description}`) for
maximum portability. When the skill needs hub publishing, it must expand to
include `version`, `author`, `ref`, `metadata`. The validate.py schema gate
blocks the expansion.

**Pattern:** Define `ALLOWED_FIELDS` in validate.py to accept the full
agentskills.io extended set from day one, even if the shipped skill only uses
the minimal subset. This is a *bridge* — it doesn't require expansion, it
allows it without a code change.

```python
ALLOWED_FIELDS = {
    "name", "description", "version", "author", "license",
    "tier", "ref", "compatibility", "metadata",
}
```

The bridge pattern:
1. Allows minimal frontmatter for portable skills
2. Accepts extended frontmatter when hub publishing needs it
3. Does NOT weaken the portability gate (that's a separate CI check)
4. Requires no script change when the frontmatter expands

**Anti-pattern:** Tying frontmatter validation to the current frontmatter
state. The validate.py should accept what *could* be valid, not what *is*
currently present. The portability gate independently ensures no
agent-specific content leaks in.

**Evidence:** `python-project-workflow`'s validate.py was patched from
`{name, description}` to the extended ALLOWED_FIELDS set. The SKILL.md
remained minimal (name + description), but the option to add version and
metadata for hub publishing is now open without touching validate.py.
