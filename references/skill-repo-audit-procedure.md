# Skill Repo Audit Procedure  # portability: allow-platform-ref

> Session-derived procedure from 2026-07-08 py-review-skill audit.
> See the main skill SKILL.md for the ten design principles this procedure checks against.

A structured sequence for auditing a skill repository — combining CI review,
portability verification, structure metrics, provenance checks, and GitHub
metadata verification into a single repeatable audit.

## When to Use This

- Before publishing a new skill repo publicly
- After significant structural changes to an existing skill repo
- When reviewing a skill repo for file-swamp, portability drift, or CI gaps
- Before adding new CI checks (to understand what already exists)

## Audit Procedure

### Phase 1: Pre-Audit — Git and Repository State

Run these at the repo root before examining internal structure:

```shell
git status --porcelain       # dirty tree?
git branch --show-current    # correct branch?
git remote -v                # remotes correct?
git log origin/main..HEAD    # un-pushed commits?
git tag -l                   # any tags exist?
git log --oneline -10        # recent commit pattern

find . -not -path './.git/*' -type f | wc -l   # total file count
ls -1d *                                       # root items (count them)
find skills -name 'SKILL.md' | wc -l           # skill count
find scripts -type f 2>/dev/null | wc -l       # script count
```

**Check against file-swamp metrics** (see `references/file-swamp-patterns.md`):
- Per-skill ref ratio (should be 0:1 to < 1:1 for repos < 50 skills)
- Script-to-skill ratio (should be < 1:1 for repos < 25 skills)
- Root items (should be < 12)

---

### Phase 2: CI Workflow Review

Read `.github/workflows/ci.yml` and evaluate:

| Aspect | What to check | Finding if healthy |
|--------|---------------|-------------------|
| Trigger paths | Does `push.paths` cover all directories that affect the shipping surface? | `skills/`, `.github/scripts/`, `.github/workflows/ci.yml` present |
| Check selection | Does each check catch a failure mode no runtime catches? | Every check passes the two-question test |
| Check ordering | Fastest/cheapest checks first? | Portability gate before schema validation |
| Scheduled runs | Weekly cron for URL drift? | `schedule: - cron: '0 9 * * 1'` |

**Two-question test for each CI check:**
1. "What evidence says this is necessary at our scale?"
2. "Will a human or runtime catch this faster than our CI?"

---

### Phase 3: Portability Verification

Run the portability gate (if one exists) or scan manually:

```shell
python3 .github/scripts/check-portability.py  2>/dev/null || \
  grep -rn 'skill_view\|skill_manage\|hermes \|~/.hermes\|\.claude/\|\.cursor/' skills/
```

If the repo has no portability gate, that is itself a finding for Phase 9.

**Frontmatter schema check:**

```shell
for f in skills/*/SKILL.md; do
  extra=$(sed -n '2,/^---/p' "$f" | grep -v '^name:\|^description:\|^---' | grep -v '^$')
  if [ -n "$extra" ]; then echo "$f: extra fields: $extra"; fi
done
```

---

### Phase 4: Structure Metrics

```shell
wc -l skills/*/SKILL.md                       # per-skill line counts
find skills -name 'references' -type d        # per-skill ref directories

# Check skill names match directory names
for dir in skills/*/; do
  name=$(grep '^name:' "$dir/SKILL.md" | sed 's/name: *//')
  basename=$(basename "$dir")
  if [ "$name" != "$basename" ]; then echo "MISMATCH: $basename declares name $name"; fi
done
```

**Information density check:** Estimate proportion of code blocks and
template commentary vs. unique procedural guidance in SKILL.md files.
If > 50% is low-density content, note whether it serves as executable
floor for weaker models or is simply waste (see skill-repo-architecture §9).

---

### Phase 5: Provenance and Documentation Audit

**Extraction log** (if exists): Check for local filesystem paths (common),
unresolvable commit hashes, missing license attribution.

**Methodology alignment doc** (if exists): Check that stated design
principles match actual repo structure.

**README:** CI badge live? Install instructions for primary platform?
Portability commitment stated? File tree matches actual repo?

**AGENTS.md:** Exists? Under ~20 lines? References router skill first?
No imperative directives (MUST/must not)?

---

### Phase 6: .gitignore and Security

```shell
grep -c '\.DS_Store' .gitignore              # OS junk
grep -c '__pycache__\|\.pyc\|dist\|build' .gitignore  # build artifacts
grep -c '\.venv\|venv' .gitignore            # virtual environments
```

**Instruction file conflict check:** Only one of AGENTS.md, CLAUDE.md,
GEMINI.md, .rules should exist as canonical instruction file.

**SECURITY.md** and **LICENSE** should exist.

---

### Phase 7: Run All Local Checks

```shell
python3 scripts/validate.py                  # schema/structure
python3 scripts/extract-tests.py --check     # generated artifact freshness
python3 scripts/check-expiry.py              # freshness markers
python3 scripts/verify-urls.py               # URL reachability
python3 .github/scripts/check-portability.py # portability gate
```

---

### Phase 8: GitHub Metadata

```shell
gh repo view <owner>/<repo> --json description,visibility,repositoryTopics
```

Description set? Topics at minimum include target platforms + domain?
Visibility correct?

---

### Phase 9: Findings Documentation

| Category | Finding | Severity | Fix |
|----------|---------|----------|-----|
| CI triggers | Missing directory in paths | HIGH | Add to push + PR paths |
| Portability | No CI gate | MEDIUM | Add check-portability.py |
| Provenance | Local path in extraction log | LOW | Replace with public ref |
| Structure | File-swamp metrics in warning | MEDIUM | Remediate per sequence |
| Metadata | Empty description | MEDIUM | Set with gh repo edit |

Severity:
- **HIGH** — silent breakage (portability drift, missing trigger)
- **MEDIUM** — discoverability/friction gap (missing gate, empty metadata)
- **LOW** — cosmetic or theoretical (local paths, optional patterns)

Each finding includes specific evidence (path, line, command output) and
concrete fix recommendation.
