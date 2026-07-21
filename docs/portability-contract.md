# Portability and Runtime Evidence Contract

Status: normative maintainer contract. This file is not shipped in the runtime
payload.

## Canonical payload

`skills/skill-repo-architecture/` is the sole runtime source and installable
artifact. Adapters may point at it or add required metadata, but must not copy
its methodology.

## Evidence levels

Use these claims consistently:

| Claim             | Required evidence                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| Payload portable  | Canonical files parse under the claimed format and have no known platform-only runtime dependency |
| Install verified  | A named runtime and version discovers or installs the exact payload through a recorded procedure  |
| Workflow verified | That runtime completes representative positive and negative tasks against the behavioral contract |

Evidence at one level does not establish the next.

## Runtime states

Use `candidate`, `install_verified`, `workflow_verified`, `limited`, or
`unsupported`. Record the runtime version, date, installation path, explicit and
implicit selection, scenarios, evidence or grading criteria, and limitations.

Do not extrapolate a result to untested runtimes or later versions. A material
change to `SKILL.md`, the behavioral contract, prompt, or grader starts a new
evidence baseline.

## Current status

The canonical payload passes deterministic format, frontmatter, reference,
portability-marker, and behavioral-contract validation. No named runtime has a
recorded installation and positive/negative workflow certification for this
payload revision. Current runtime status is therefore `candidate`.

## Adding runtime evidence

1. Select one runtime as an active target.
2. Record its exact version and discovery or installation path.
3. Test explicit and implicit selection with positive and negative scenarios.
4. Preserve reproducible or raw evidence without exposing sensitive values.
5. Grade against `evals/cases/architecture-audit.json`.
6. Record limitations and the narrowest supported state.

Keep model evaluation non-blocking. Reuse this contract and fixture vocabulary
before creating a runtime-specific runner. Extract a generic harness only after
two concrete uses share the same lifecycle and grading needs.
