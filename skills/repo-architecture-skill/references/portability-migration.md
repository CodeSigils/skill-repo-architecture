# Portability Migration

Use this procedure to extract a portable runtime core from a skill that currently
depends on one client's commands, paths, hooks, or APIs.

## 1. Inventory platform coupling

Search the runtime payload for:

- client-specific tool or API names;
- installation and configuration paths;
- hook, plugin, or lifecycle assumptions;
- platform-only frontmatter or metadata;
- commands whose output or availability is client-specific.

Classify each occurrence as runtime-essential, optional optimization,
installation documentation, or historical example.

## 2. Separate the portable core

Move task reasoning, filesystem inspection, general CLI use, and reporting into
the portable `SKILL.md`. Prefer capability checks such as executable discovery,
project manifests, or observed files over asking one agent runtime whether a
tool exists.

Keep platform adapters outside the portable core. If an adapter is essential,
declare the skill platform-specific rather than hiding the dependency behind a
fallback.

## 3. Move install detail to the README

Document client-specific discovery and installation paths in clearly separated
README sections. Installation paths may vary without changing the runtime
methodology. Verify current client documentation before publishing commands.

Do not place every client's setup instructions in the activated skill unless the
runtime procedure must configure those clients.

## 4. Define degraded behavior

For optional capabilities, state what the skill can still do when a tool, API,
network connection, or credential is unavailable. Report skipped checks; do not
fabricate passes or silently substitute a materially different workflow.

## 5. Validate the claim

- Parse the portable frontmatter using the claimed skill format.
- Scan runtime files for unapproved platform markers.
- Run the procedure using only the tools declared by its portability tier.
- Test referenced files from an installed copy, not only the repository root.
- Keep platform examples marked and conditional.
- Add a negative fixture showing that ordinary tasks do not trigger a migration.

Read `portability-patterns.md` for tier selection and `operational-patterns.md`
for CI lane design.
