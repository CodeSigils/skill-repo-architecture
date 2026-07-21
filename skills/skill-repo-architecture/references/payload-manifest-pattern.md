# Payload Manifest Pattern

Use a payload manifest only when an install, package, plugin, or release process
must assemble an artifact that differs from the canonical source tree. A static
skill already stored in its installable directory does not need a second tracked
copy or a sync script.

## Admission gate

Before adding a manifest, answer:

1. Which distribution consumer cannot use the canonical tree directly?
2. Is the output generated during packaging, or must it be tracked?
3. What proves the installed artifact contains exactly the runtime payload?
4. Which file owns the artifact version?

If the only motivation is convenient browsing or copying, keep the payload
canonical and omit the manifest.

## Manifest contract

The format may be ecosystem-native (`package.json` files, wheel metadata, plugin
manifest) or a small project manifest. It should declare exact runtime files by
category, for example:

```json
{
  "entrypoints": ["SKILL.md"],
  "references": ["references/policy.md"],
  "scripts": ["scripts/check.py"]
}
```

Avoid a wildcard when the artifact is security-sensitive or separately
published. Exact inventories make additions reviewable.

## Required checks

- Every declared source exists.
- Every installed file is declared.
- No declared file is omitted from the artifact.
- Generated files match their canonical sources.
- Executable permissions are preserved when relevant.
- The artifact works from a staging directory without maintainer-only files.
- Version fields agree across manifests, tags, and release metadata when used.

Prefer generating artifacts into an ignored staging directory during tests.
Track generated replicas only when the downstream distribution mechanism
requires them in version control.

## Tool-backed skills

When a skill wraps a separately installable CLI, the package manifest should own
the executable inventory and the skill should describe how to locate it. Do not
copy the tool implementation into the skill directory merely to make the skill
self-contained. If an offline bundled mode is a real requirement, treat it as a
separate artifact and test it explicitly.

## Release integrity

Published artifacts may justify staged-install tests, version-alignment checks,
checksums, attestations, dependency audits, and immutable CI action revisions.
Apply those controls to the release artifact, not automatically to every static
skill repository.
