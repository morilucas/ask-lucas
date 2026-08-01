# ADR 0002: application stack and service boundary

Status: Accepted
Date: 2026-08-01

## Context

Ask Lucas must demonstrate applied AI engineering, Python, SQL, system design, and product-quality frontend delivery while remaining inexpensive and workable at approximately five hours per week.

The initial assets suggested a split deployment: Vercel for the web experience and the Hostinger VPS for the Python API and, later, PostgreSQL/pgvector. The first deterministic slice must run locally without Docker, a model API key, or a hosted database. ADR 0004 supersedes the deployment portion for the first public milestone: both containers run on the VPS behind one Caddy ingress.

The local workstation audit found:

- Node.js 24.12.0
- npm 11.6.2, invoked as `npm.cmd` in PowerShell because the script execution policy blocks `npm.ps1`
- `uv` 0.11.3
- no standalone Python executable currently on `PATH`
- no local Docker or Docker Compose command

`uv` can manage the pinned Python interpreter and environment, so missing global Python does not block the first slice. Docker remains unnecessary until deployment or the PostgreSQL milestone.

## Decision

Use a small two-application repository without a monorepo orchestration framework.

```text
Browser
  → Next.js web application
  → FastAPI HTTP API
  → retriever
  → answer provider
```

### Web application

- Next.js App Router
- TypeScript in strict mode
- Node.js 24.x
- npm with a committed `package-lock.json`
- Server-render the static page shell
- Use client components only for the composer, request state, citations, and Inspector
- Native `fetch` through one narrow API client module
- Playwright for browser behavior, accessibility checks, and viewport coverage once the first integrated slice exists
- No JavaScript unit-test framework until client-only logic justifies one

The web application lives under `apps/web`. It does not contain retrieval or provider logic and never receives model credentials.

### Python API

- CPython 3.12, managed and pinned by `uv`
- FastAPI and Pydantic
- A `pyproject.toml` and committed `uv.lock`
- Standard-library `sqlite3` with FTS5 for the baseline
- Explicit retriever and answer-provider protocols
- Pytest for unit, contract, API, retrieval, and behavioral tests
- Ruff for linting and formatting
- Mypy for static type checks

The API lives under `apps/api`. It owns approved-content ingestion, retrieval, answer orchestration, citation validation, evaluation, and sanitized telemetry.

No ORM, agent framework, queue, or dependency-injection framework is introduced in the first slice. PostgreSQL tooling is selected in the pgvector milestone rather than carried by the SQLite baseline.

### Contract boundary

FastAPI's OpenAPI document is the HTTP contract source.

- Pydantic defines request, success, abstention, error, citation, and trace schemas.
- A deterministic script exports the OpenAPI artifact.
- `openapi-typescript` generates compile-time types for the web API client.
- Generated types are committed so frontend development does not require a running Python server.
- CI fails when regeneration produces an uncommitted contract change.
- Runtime schema validation remains on the API; TypeScript types do not replace it.

This adds one development-only generator while avoiding hand-maintained duplicate contracts.

### Local execution

- Next.js runs on `localhost:3000`.
- FastAPI runs on `localhost:8000`.
- CORS allows only the configured web origin and exposes the trace-ID response header.
- Mock mode is the default until a real provider is explicitly configured.
- Both applications run as normal local processes; Docker is not required.
- `.env.example` files document configuration, while secrets remain outside Git.

### Production direction

This is a later deployment milestone, not part of feature 001 acceptance:

- `ask.lkmori.com` → Next.js on Vercel
- `api.ask.lkmori.com` → containerized FastAPI on the Hostinger VPS
- Cloudflare manages DNS, TLS edge policy, and an initial abuse-control layer
- The API permits the exact public web origin and also enforces server-side input limits and rate limits
- SQLite is local to the API container/volume for the baseline
- PostgreSQL/pgvector later runs on a private Docker network and is not exposed publicly

The browser calls the public read-only API directly for the initial deployment. A Next.js backend-for-frontend proxy is not added unless direct API exposure creates a measured security, streaming, or operational problem.

### Observability

- OpenTelemetry manual spans for request, retrieval, and generation boundaries
- W3C trace context
- Structured JSON application logs correlated by trace ID
- Console/local export first
- No full question persistence by default
- No hosted observability SDK until a service is deliberately selected

### Continuous integration

GitHub Actions runs independent web and API jobs:

- web: install from lockfile, lint, type-check, production build, then browser tests after integration exists
- API: sync from lockfile, lint/format check, type-check, tests, evaluation smoke test
- contract: regenerate OpenAPI/TypeScript types and verify a clean diff
- browser tests are added after the integrated vertical slice exists

## Why this boundary

- It makes Lucas's strongest implementation language, Python, central to the AI system.
- It still demonstrates modern TypeScript product engineering.
- Retrieval, evaluation, and model logic remain runnable outside a frontend framework.
- The public contract makes the two-service cost visible and testable.
- Each side can be deployed or replaced independently without a broad platform framework.
- Mock mode and SQLite keep the first slice free and locally reproducible.

## Alternatives considered

### Next.js-only full stack

This would minimize services and simplify Vercel deployment. It was rejected because it would make Python, SQL-oriented retrieval, and the evaluation pipeline less central to the showcase.

### FastAPI with server-rendered templates or HTMX

This would keep the entire project in Python. It was rejected because the interface is a major product artifact and should demonstrate contemporary TypeScript/React delivery.

### Next.js backend-for-frontend proxy from the start

This could hide the API origin and eliminate browser CORS. It was deferred because it adds another runtime hop and failure boundary before a need is measured. It remains an option for protected server-to-server credentials or streaming constraints.

### Docker for all local development

This would improve environment parity. It was deferred because Docker is not installed locally and neither the deterministic API nor SQLite requires it. A production container and local Compose setup arrive when deployment/PostgreSQL makes them useful.

### Turborepo, Nx, or another monorepo orchestrator

These tools can coordinate large multi-package repositories. They are unnecessary for one web application and one Python service, and they do not remove the cross-language commands that matter here.

## Consequences

- Local development requires two processes.
- Cross-origin behavior must be configured and tested.
- The API contract needs a regeneration workflow.
- VPS deployment has more operational work than a Vercel-only application.
- The boundary creates strong, inspectable evidence of API and system design.

## Revisit when

- Streaming through the direct API is unreliable.
- The public API abuse surface requires server-to-server mediation.
- More applications need shared packages or coordinated builds.
- PostgreSQL and background evaluation jobs introduce real orchestration needs.

## Supporting documentation

- [Next.js installation and Node requirements](https://nextjs.org/docs/app/getting-started/installation)
- [Vercel supported Node.js versions](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions)
- [FastAPI virtual environment guidance](https://fastapi.tiangolo.com/virtual-environments/)
- [uv project workflow](https://docs.astral.sh/uv/guides/projects/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
