# Security Policy

## Reporting a Vulnerability

Open an issue on GitHub with details of the finding. Do not include exploit
code in the public issue. If the finding is sensitive, note that and we will
establish a private channel.

## Scope

This repository ships a Markdown methodology and conditional references. The
runtime payload contains no executable code. Python scripts at the repository
root are maintainer-only validation and external-monitoring tools.

Unsafe actions or trust assumptions recommended by the runtime methodology,
payload-boundary mistakes that unintentionally ship maintainer files, and
vulnerabilities in maintainer tooling are in scope.
