# Ask Lucas

Ask Lucas is an employer-facing AI portfolio that answers questions from a reviewed knowledge base and exposes the evidence behind each answer. It is also a public engineering case study in building a small, grounded AI product deliberately.

The current vertical slice includes:

- A polished, responsive Next.js interface
- A typed FastAPI contract with safe errors and request trace IDs
- Markdown ingestion with stable source IDs
- SQLite FTS5 top-three lexical retrieval with explicit BM25 semantics
- Multi-turn conversation with bounded context and grounded follow-ups
- A Claude adapter with structured output and citation validation
- A safe System Lens with retrieval, model, timing, and trace metadata
- Metadata-only content validation and atomic SQLite index replacement
- A file-backed extractive fallback that requires no API key
- Clear abstention when evidence is insufficient
- API, retrieval, ingestion, and browser acceptance tests
- Rootless, read-only application containers behind an existing Caddy ingress

## Privacy architecture

This public repository contains code, architecture decisions, and fictional examples only. The reviewed biography, deterministic production answers, and production evaluation cases live in a separate private repository. Deployment mounts that private checkout read-only into the API container:

```text
public code ───────┐
                  ├─ API container → private SQLite index → grounded response
private content ──┘
```

Raw resumes, LinkedIn exports, credentials, personal contact details, and employer-confidential material are never valid retrieval sources. See [`content/README.md`](content/README.md) and [`deploy/README.md`](deploy/README.md).

## Repository map

- `apps/api/` — FastAPI application, ingestion, retrieval, answer orchestration, schemas, and tests
- `apps/web/` — Next.js user experience and Playwright acceptance tests
- `examples/` — synthetic content, answer fixture, and evaluation cases used by public tests
- `deploy/` — Docker images, Compose topology, Caddy route, and operating notes
- `docs/` — product intent, engineering principles, skill map, and architecture decisions
- `specs/` — behavior, plan, and implementation tasks for the grounded-chat slice

## Run locally

Prerequisites are Node.js 24, npm 11+, Microsoft Edge for the current browser projects, and [`uv`](https://docs.astral.sh/uv/). No secrets or paid API are needed for the synthetic mode.

Start the API:

```powershell
cd apps/api
uv sync --dev
uv run uvicorn ask_lucas.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the web app in another terminal:

```powershell
cd apps/web
npm.cmd install
npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000`.

To use a private checkout locally, copy `apps/api/.env.example` to `apps/api/.env` and change the content, fixture, and evaluation paths. Never commit that file.

To use Claude, add `ASK_LUCAS_ANTHROPIC_API_KEY` to that untracked `.env` file. `ASK_LUCAS_PROVIDER=auto` selects Claude when the key exists and the extractive fallback otherwise. The default model is the cost-conscious `claude-haiku-4-5`; override `ASK_LUCAS_ANTHROPIC_MODEL` to run a measured model comparison.

## Verify

```powershell
cd apps/api
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run python scripts/rebuild_index.py
uv run python scripts/export_openapi.py

cd ../web
npm.cmd run generate:api
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
npm.cmd audit
```

The generated index and build artifacts are ignored by Git. Regenerate the TypeScript contract whenever the FastAPI OpenAPI document changes.

## Start with the design record

- [`docs/product-brief.md`](docs/product-brief.md)
- [`docs/experience-brief.md`](docs/experience-brief.md)
- [`docs/constitution.md`](docs/constitution.md)
- [`docs/skills-showcase.md`](docs/skills-showcase.md)
- [`specs/001-grounded-chat/spec.md`](specs/001-grounded-chat/spec.md)
- [`specs/002-conversational-claude/spec.md`](specs/002-conversational-claude/spec.md)
- [`docs/decisions/0001-start-with-lexical-rag.md`](docs/decisions/0001-start-with-lexical-rag.md)
