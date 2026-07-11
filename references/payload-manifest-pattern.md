# Payload Manifest Pattern  # portability: allow-platform-ref

Implementation reference for maintaining a Hermes skill payload with a JSON
manifest and bash sync script, mechanically enforcing the declared shipping
boundary in CI.

## Manifest format

`scripts/payload-manifest.json`:

```json
{
  "files": ["SKILL.md", ".repo-health.json"],
  "scripts": ["check-commit-body.py", "check-commit-trailers.py", "check-portability.py"],
  "references": "*"
}
```

| Key | Value type | Semantics |
|-----|-----------|-----------|
| `files` | Array of strings | Root-level files declared by relative path from repo root |
| `scripts` | Array of strings | Files under `scripts/` declared by basename only |
| `references` | `"*"` or array of strings | `"*"` mirrors entire `references/` directory; array selects specific files |

## Sync script contract

`scripts/sync-payload.sh` reads the manifest and copies source files into
`skills/<skill-name>/` at the same relative path (e.g., `scripts/foo.py` in
root goes to `skills/<skill>/scripts/foo.py` in the payload).

### Operation modes

| Mode | Command | Behavior |
|------|---------|----------|
| Normal | `bash scripts/sync-payload.sh` | Rebuild payload, report drift but exit 0 |
| CI | `bash scripts/sync-payload.sh --ci` | Rebuild payload, exit 1 on any drift |
| Self-check | (included in verify.sh) | Run manifest check + staged-install smoke test |

### What drift means

- A file in the manifest is missing from source (MISSING)
- A file exists in the payload directory but is not in the manifest (ORPHANED)
- A file in the manifest has execute permission in source but was copied without it (or vice versa)

### Exit paths

Every `exit` must emit enough context to fix the problem:
- ORPHANED: print the relative path and the command to remove it
- MISSING: print the relative path and the manifest entry

## Reference mirroring

When `"references": "*"` is used, the entire `references/` directory is
mirrored to the payload. The sync script must:

1. Delete ALL existing files under `payload/references/` before copying
2. Copy `source/references/*.md` to `payload/references/`
3. Leave the payload references/ directory empty if source references/ is empty
   (clean empty dirs are removed by the cleanup pass)

This means renaming or deleting a reference file in the source automatically
removes it from the payload on the next sync. No manifest update needed for
reference changes.

## Orphan cleanup algorithm

```
find payload_dir -type f
for each file:
    compute relative path (strip payload_dir prefix)
    check if relative path matches any manifest entry
    if not matched:
        if path starts with "references/" and manifest.references == "*": skip
        else: orphan → delete
```

## CI enforcement

```yaml
- name: Payload sync check
  run: bash scripts/sync-payload.sh --ci
- name: Staged-install smoke test
  run: |
    python3 skills/<skill>/scripts/check-commit-trailers.py --self-test
    python3 skills/<skill>/scripts/check-commit-body.py --self-test
```

The staged-install smoke test runs the payload's scripts from their installed
location, proving they work without the root repo's development tooling.

## Pitfalls

### Reference removal cascade

When `"references": "*"` is declared and a reference file is deleted from
source, the sync script's deletion pass removes it from the payload
automatically. This means branches that delete reference files will show a
payload diff even though no manifest changed. This is correct behavior —
the payload must match source — but be aware that the CI drift check will
fire on branches that delete reference files, even if SKILL.md cross-refs
were already updated.

### Hub security scanner interaction

The Hermes hub scanner (community source) marks **any** shipped script
containing `~/.hermes/config.yaml` as CRITICAL persistence, even if it's
only a comment. Scripts shipped in the payload must NOT mention config
paths in their comments. Put configuration instructions in SKILL.md or
README.md instead.

### No post-install lifecycle for skills

Hermes has no `post_install` event hook for skills. A script shipped in the
payload cannot run automatically after install. The user must manually register
hooks in config.yaml (e.g., for post-write Markdown checks). This is by design
— auto-registering tool interceptors would be a security boundary violation.
