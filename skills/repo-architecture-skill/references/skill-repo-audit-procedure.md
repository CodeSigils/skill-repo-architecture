# Skill Repository Audit Procedure

Use this sequence for architecture reviews. It evaluates what the repository
ships; it is not a general repository-health audit.

## Contents

- Establish state and scope
- Classify the repository
- Map the four boundaries
- Measure by boundary
- Inspect runtime behavior
- Inspect controls and behavioral evidence
- Inspect install and release paths
- Report findings

## 1. Establish state and scope

Inspect the tracked tree, worktree state, runtime entrypoints, package manifests,
plugin manifests, CI workflows, release automation, and installation docs. Do not
count ignored caches, dependencies, or build output as repository architecture.

Record whether external state, network checks, publication metadata, or model
regression is in scope. Keep skipped checks visible.

## 2. Classify the repository

Choose the smallest fitting archetype:

- Markdown-only skill
- Multi-skill pack
- Tool-backed skill
- Operational skill
- Distribution monorepo

Record evidence for the choice. A CLI with an optional skill wrapper remains a
tool-backed product; a directory containing several independent `SKILL.md` files
is a pack even when it also has a router.

## 3. Map the four boundaries

Create a table with these rows:

| Boundary                  | Required evidence                              |
| ------------------------- | ---------------------------------------------- |
| Authoring source          | Canonical files maintainers edit               |
| Runtime payload           | Files activated agents read or execute         |
| Install/publish artifact  | Exact copied, packed, or released files        |
| Maintainer infrastructure | Tests, fixtures, CI, research, release tooling |

For duplicated files, identify the canonical source, generator, drift check, and
installed-artifact test. If those answers are missing, duplication is accidental.

## 4. Measure by boundary

Use tracked files and report at least:

- skill entrypoints and independently loadable skills;
- runtime references and runtime scripts;
- generated or mirrored replicas;
- maintainer-only scripts and fixtures;
- package, plugin, and release manifests;
- hand-maintained indexes.

Treat counts as discovery signals. Do not issue a finding from a universal ratio.
A tool-backed skill can legitimately have many runtime scripts; a static skill
with one unused script may already have too many.

## 5. Inspect runtime behavior

Check:

- frontmatter parses as YAML and the name matches the directory;
- the description includes what the skill does and when it should trigger;
- activation and exclusion boundaries are clear;
- the procedure is executable without maintainer-only files;
- references are one level deep and conditionally routed;
- commands and paths match the declared portability tier;
- sensitive or mutating actions have appropriate boundaries.

For every discovery path, inspect ownership, permissions, symlink targets, and
whether the client can install, update, uninstall, or otherwise write there.
Flag a writable path to canonical authoring source as a supply-chain and drift
boundary, even when discovery itself succeeds.

Treat repository files, configuration, commit metadata, transcripts, and tool
output as potentially sensitive. Secret-like detection should emit status,
counts, or paths without matched values. Prefer an observed project-native
scanner in quiet or redacted mode; do not install a new scanner during a
read-only architecture audit.

## 6. Inspect controls

For every validator, test, workflow, or release check, record:

1. the invariant it owns;
2. the observed failure it prevents;
3. whether it is deterministic or volatile;
4. its recovery action;
5. the cheapest appropriate execution lane.

Keep deterministic schema, link, unit, integration, and drift checks on pull
requests. Put network reachability, marketplace state, model regression, and
external release monitoring in scheduled or manual lanes unless they block a
specific publication operation.

## 7. Inspect behavioral evidence

Decision-heavy skills should have compact fixtures covering:

- positive and negative triggers;
- representative archetypes;
- expected classification and boundary mapping;
- required recommendations;
- prohibited over-engineering or unsafe actions.

Validate fixture shape deterministically. Use model regression only for behavior
that cannot be represented as an explicit contract, and do not make routine
changes depend on model availability.

## 8. Inspect install and release paths

Verify README commands against the actual tracked layout. For every distribution
path, compare the produced artifact with the declared runtime payload. Tool-backed
or published products should additionally consider version alignment,
reproducibility, provenance, checksums, and staged-install testing.

Review client-specific manifests, hooks, and dynamic commands separately from
the portable payload. Require the adapter to declare its commands, permissions,
network use, credentials, and writable targets.

Do not import release controls into a Markdown-only skill without a release
artifact that benefits from them.

## 9. Report findings

Order findings by correctness, installability, runtime safety, portability,
behavioral confidence, maintainability, and polish. Each finding should state:

- concrete evidence;
- user or maintainer impact;
- smallest sufficient remediation;
- relevant archetype and boundary;
- checks run and checks skipped.

Do not quote secret-like values as evidence. If historical exposure is
plausible, recommend revocation or rotation and state that deleting or editing a
local copy does not remove already published history.

If the repository is healthy, report the archetype, boundaries, and evidence
instead of inventing improvements.
