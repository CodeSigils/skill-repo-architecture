# npm Publishing for Agent-First Tools

Methodology for evaluating and publishing an agent skill as an npm package.
Covers landscape analysis, naming strategy, and dual-use repo design.

## When to consider npm publishing

An agent skill may outgrow its skill-only delivery channel when:

- The CLI is useful outside any agent runtime (standalone formatting, linting,
  CI pipelines, pre-commit hooks)
- The tool has zero runtime dependencies and can be installed instantly
  (`npx <package>`)
- Users cannot or will not run the agent's skill installer
- The tool is referenced in non-agent documentation (CI configs, Makefiles,
  VS Code task definitions)

## Landscape survey methodology

Before publishing, survey existing npm packages in the same functional space
to understand positioning, discoverability, and differentiation.

### Discovery commands

```bash
# Broad keyword search
npm search <keyword1> <keyword2> --json | python3 -c "
import json, sys
for pkg in json.load(sys.stdin)[:30]:
    print(f\"{pkg['name']:40} {pkg['description'][:80]}\")
"

# Check specific names
for name in "candidate-name" "@scope/candidate-name"; do
  result=$(curl -s "https://registry.npmjs.org/$name" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); \
    print('TAKEN' if d.get('name') else 'AVAILABLE')" 2>/dev/null)
  echo "$name: $result"
done
```

### What to evaluate per competitor

| Dimension | What to check | Command |
|-----------|---------------|---------|
| Description & keywords | Positioning | `npm view <pkg> description keywords` |
| Version & freshness | Active maintenance | `npm view <pkg> time --json` → min/max dates |
| Download count | Adoption | `curl -s 'https://api.npmjs.org/downloads/point/last-month/<pkg>'` |
| Dependencies | Weight, risk | `npm view <pkg> dependencies` |
| Runtime engine | Node.js req | `npm view <pkg> engines` |
| Binary/CLI presence | Install-and-run | `npm view <pkg> bin` |
| Native deps | Platform risk | `npm view <pkg> optionalDependencies` (binary addons) |
| Peer deps | Version conflict | `npm view <pkg> peerDependencies` |

### Market-positioning analysis

For each competitor, rate:

1. **Feature overlap** — does it do what your tool does?
2. **Dependency weight** — zero-dependency vs remark/unified stack (12-60+ packages)
3. **Agent-awareness** — does it have pipe safety, structural drift detection, or
   any agent-specific guardrails?
4. **Platform scope** — native binary (per-platform), WASM, or pure JS?

**Key insight:** Pure-JS-zero-dep is rare. Most popular formatters (hongdown,
markdownlint-rs) ship compiled native binaries. The remark/unified-based ones
pull in 12-60+ packages. A zero-dep pure-JS formatter with agent guardrails
occupies a unique niche that nothing on npm covers.

## Name strategy

| Consideration | Question to ask |
|---------------|-----------------|
| Audience | Is this a "formatter for agents" or "a formatter that supports agents"? |
| Scope | Does the name cover all supported dialects (GFM, MDX, plain Markdown)? |
| Redundancy | "gfm-md-formatter" → "GFM Markdown Markdown formatter" (like PIN number) |
| Discoverability | Will people search for this by workflow (e.g., "agent markdown") or by function (e.g., "gfm formatter")? |
| Scalability | Does the name box you in if you add Obsidian wiki links, Mermaid, or other dialects later? |
| Scope ownership | Bare name vs `@scope/name` — scoped names are safer but less discoverable from fresh `npm search` |

### Real survey results (July 2026)

From the agents-markdown-formatter analysis:

| Name | Status | Notes |
|------|--------|-------|
| `markdown-formatter` | Taken | Chinese tool, 2019, 11 remark deps, last pub Nov 2025 |
| `agents-markdown-formatter` | Available | Descriptive, honest about audience |
| `@codesigils/markdown-formatter` | Available | Clean, scoped, covers all dialects |
| `@codesigils/agents-markdown-formatter` | Available | Scoped + specific |
| `gfm-md-formatter` | Available | Short but redundant (GFM = GitHub Flavored Markdown) |
| `gfm-formatter` | Available | Cleaner than gfm-md-formatter |
| `markdown-formatter-cli` | Available | Generic, longer |

## Dual-use repo design (skill + npm package)

When a repo ships both an agent skill AND an npm package from the same code,
the design tension is between:

- The **development environment** (tests, CI, fixtures, scripts, staged-install-verify)
- The **shipping surface** (7 runtime files under `skills/markdown-formatter/`)
- The **npm tarball** (only what `files` allows + package.json, README, LICENSE)

### Approach comparison

| Approach | Pros | Cons |
|----------|------|------|
| **Same repo, `files` allowlist** (`"files": ["skills/markdown-formatter/"]`) | Single source of truth, one CI, one issue tracker, no version sync | `bin` path is nested (`skills/markdown-formatter/src/index.js`); needs a shim; dev-only files visible on npm webpage but not in tarball |
| **Separate npm wrapper repo** | Clean npm root, publishable from day one | Two CI pipelines, two tag histories, version sync headache, duplicate READMEs |
| **Restructure: flatten skill to root** (move `skills/markdown-formatter/src/` up to `src/` in root) | Clean npm root, single repo | Breaking change for the skill install path; need backward-compat symlink |

### Recommended: same repo with shim

Changes needed in `package.json`:

```json
{
  "private": false,
  "files": [
    "skills/markdown-formatter/SKILL.md",
    "skills/markdown-formatter/src/",
    "skills/markdown-formatter/scripts/"
  ],
  "bin": {
    "markdown-formatter": "bin/mdfmt"
  }
}
```

Create `bin/mdfmt` (thin shim — no code duplication):

```js
#!/usr/bin/env node
require('../skills/markdown-formatter/src/index.js');
```

The runtime payload verification (`staged-install-verify.sh`) continues to
validate the exact files under `skills/markdown-formatter/`. The npm `files`
field serves as the secondary allowlist — anything not in `files` stays local.

### What doesn't change

- **Skill install path** — still `skills/markdown-formatter/`
- **CI** — still runs from repo root, tests same files
- **Release process** — `npm run release` still runs `bash scripts/release.sh`
- **Anti-drift checks** — `check-consistency.js` still validates cross-doc version alignment

### Package name alignment

If the npm package name differs from the repo name, add a comment in
`package.json`:

```json
{
  "name": "gfm-formatter",
  "repository": "github:CodeSigils/agents-markdown-formatter"
}
```

The repo URL is the canonical source. The npm name is the distribution label.
They don't need to match. Document the relationship in the repo README so
users can find the npm package from the GitHub repo and vice versa.
