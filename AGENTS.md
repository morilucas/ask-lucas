# Repository guidance

## Purpose

Build a trustworthy, employer-facing AI portfolio and document the engineering process used to create it.

## Read before changing code

1. `docs/constitution.md`
2. `docs/product-brief.md`
3. `docs/experience-brief.md` for user-facing work
4. The relevant feature specification, plan, tasks, and evaluation cases

## Non-negotiable rules

- Never add a raw resume, LinkedIn export, street address, phone number, private email address, API key, credential, or employer-confidential data.
- Treat only the configured private content directory as approved biographical input. Files under `examples/` are synthetic test data.
- Do not invent biographical facts, metrics, project outcomes, or skill claims.
- Answers must cite supporting content or explicitly say that the evidence is insufficient.
- Distinguish sourced facts from reasonable inference.
- Add or update evaluation cases when behavior changes.
- Prefer a small vertical slice over broad scaffolding.
- Do not add a major framework, hosted service, or persistent dependency without documenting why it is needed and what simpler options were considered.
- Keep model providers replaceable behind a narrow application interface.
- Keep the public database unreachable from the public internet except through the application API.
- AI-generated changes require tests, diff review, and documented verification before they are considered complete.

## Documentation ownership

- Product behavior belongs in `docs/product-brief.md` or a feature specification.
- Non-negotiable engineering principles belong in `docs/constitution.md`.
- Private reviewed facts belong in the separate content repository with provenance notes.
- Public quality examples belong in `examples/evals/`; private evaluation cases stay with private content.
- Technical tradeoffs belong in a future `docs/decisions/` architecture decision record.

## Implementation status

The initial product brief, public content, evaluation direction, feature specification, and ADRs have been reviewed. A deterministic FastAPI-to-Next.js vertical slice is implemented; continue in the dependency order recorded in `specs/001-grounded-chat/tasks.md`.
