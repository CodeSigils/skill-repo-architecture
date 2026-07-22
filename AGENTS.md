# Repository Instructions

> Scope: maintainer routing only. This file is not part of the runtime payload.

This repository ships one portable skill from
`skills/repo-architecture-skill/`; that directory is both canonical source and
installable payload.

- Use `SKILL.md` for runtime triggers and procedure.
- Use runtime references only for conditionally loaded detail.
- Use `evals/` for intended classification and recommendation behavior.
- Use `README.md` for installation, layout, and maintainer verification.
- Treat `docs/` and research notes as evidence, not runtime authority.

Do not recreate a root reference mirror or payload sync step unless a concrete
distribution consumer requires a generated artifact. Run the deterministic
verification commands in `README.md` before claiming completion.
