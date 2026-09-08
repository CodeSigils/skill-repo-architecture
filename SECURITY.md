# Security Policy

## Supported Versions

This repository does not publish versioned runtime releases. Security fixes are
applied to the default branch. Use the latest commit from that branch when
installing the skill payload.

## Reporting a Vulnerability

Report vulnerabilities privately through a
[GitHub security advisory](https://github.com/CodeSigils/repo-architecture-skill/security/advisories/new).
Include the affected path, impact, reproduction conditions, and a suggested fix
when available. Do not place exploit details, credentials, or secret-like values
in a public issue. Public issues are appropriate only for non-security bugs.

## Repository Security Scope

This repository ships a Markdown methodology and conditional references. The
runtime payload contains no executable code. Python scripts at the repository
root are maintainer-only validation and external-monitoring tools.

Unsafe actions or trust assumptions recommended by the runtime methodology,
payload-boundary mistakes that unintentionally ship maintainer files, and
vulnerabilities in maintainer tooling are in scope.

## Shipped Payload Inventory

The install artifact is exactly `skills/repo-architecture-skill/` with:

- one `SKILL.md`;
- eight Markdown files directly under `references/`;
- one `LICENSE.txt` containing the MIT notice that must travel with copies;
- no symlinks, executable files, nested directories, runtime scripts,
  configuration, dependency manifests, or generated files.

The deterministic validator rejects additions outside that allowlist. Repository
CI, evaluation fixtures, documentation, and Python tooling are maintainer
infrastructure and must not be copied into the installed payload.

## Runtime Trust Guarantees

- The installed payload is declarative Markdown and cannot execute by itself.
- Discovery paths are separate trust boundaries. Review their ownership,
  permissions, symlink targets, and client write behavior before connecting
  them to canonical source.
- The methodology defaults to inspection and recommendations; it does not grant
  permission for destructive Git operations, privilege escalation, approval
  bypass, publication, or credential access.
- Runtime instructions must not print raw secret-like matches, secret files, or
  commit bodies as evidence.
- Maintainer scripts are never runtime dependencies and are not invoked by the
  installed skill.
- The Python validators use assertions for their explicitly requested
  self-tests, `yaml.BaseLoader` to preserve workflow scalars as text, and
  subprocesses only for controlled local Git/Codex evaluation commands. These
  are maintainer-only paths; they do not process untrusted runtime input.
- External URL checks accept only absolute HTTP(S) URLs, bound response sizes,
  and retry only a finite set of transient failures. Persistent network or
  content drift remains a monitor failure.
- CI actions use immutable revisions, read-only repository permissions, and do
  not persist checkout credentials.

These guarantees describe the repository payload, not the behavior of every
agent or host that may load it. Host permissions and user approval boundaries
still apply.

## Sensitive Evidence

Treat repository content, commit metadata, configuration, transcripts, and tool
output as potentially sensitive. Report a plausible secret exposure using only
its type and affected path; never echo the matched value. Recommend revocation
or rotation when exposure may have occurred. Deleting a local value does not
remove it from published history.

## Maintainer Security Checklist

Before merging a payload or tooling change:

1. Run `uv sync --locked` and the deterministic verification suite in the
   README.
2. Run the pinned `skills-ref validate` command to verify Agent Skills format
   conformance independently of the repository's custom validator.
3. Confirm the payload inventory contains only the declared Markdown files and
   bundled license notice.
4. Review runtime instructions for destructive commands, privilege escalation,
   approval bypass, and sensitive-output requests.
5. Review dependency and GitHub Action updates; keep the uv lockfile and action
   revisions current.
6. Keep external URL monitoring separate from deterministic pull-request checks.
7. Update this policy when the artifact boundary or threat model changes.

Last reviewed: 2026-07-22.
