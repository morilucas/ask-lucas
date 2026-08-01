# Technical plan 001: grounded single-turn chat

Status: Approved for implementation
Last updated: 2026-08-01

Depends on: `docs/product-brief.md`, `docs/experience-brief.md`, `specs/001-grounded-chat/spec.md`

Implementation tasks: `specs/001-grounded-chat/tasks.md`

## Technical objective

Implement the smallest end-to-end system that demonstrates retrieval, grounded generation, citations, evaluation, and observability while remaining runnable without paid API access.

## Proposed stack

### Web

- Next.js with TypeScript
- One page and a small set of local components
- Native `fetch` to the API
- Typography-first editorial layout implemented from centralized design tokens
- One unified responsive Inspector for Evidence and System Lens modes
- No authentication, analytics SDK, or broad component library

### API and AI system

- Python 3.12+
- FastAPI
- Pydantic request and response schemas
- SQLite with FTS5 for the baseline content index
- Provider and retriever protocols with deterministic test doubles
- Pytest for API, ingestion, retrieval, and behavior tests

### Observability

- OpenTelemetry Python tracing
- Console/local exporter during development
- Structured JSON application logs correlated by trace ID
- Sanitized per-request trace summary returned by the answer endpoint

OpenTelemetry currently describes Python traces as stable, while its Python logs signal remains in development. The first build therefore uses OpenTelemetry for traces and ordinary structured application logging rather than depending on the OpenTelemetry logs SDK.

### Evaluation

- Private YAML cases supplied at deployment and synthetic examples in `examples/evals/`
- Python evaluation command
- JSON result artifact consumed by System Lens
- Deterministic checks first; human and model grading later

## Proposed repository shape

```text
ask-lucas/
  apps/
    api/
      ask_lucas/
      tests/
      pyproject.toml
    web/
      app/
      components/
      lib/
      package.json
  examples/
    content/
    evals/
    fixtures/
  docs/
  deploy/
  specs/
    001-grounded-chat/
  AGENTS.md
  README.md
```

## Request path

```text
Browser
  → Next.js page
  → POST /v1/answer
  → validate question
  → SQLite FTS5 top-3 retrieval
  → answer provider (mock initially)
  → citation validation
  → structured response + sanitized trace
  → answer, evidence drawer, trace disclosure
```

## Interfaces to define first

### Retriever

```text
retrieve(question, limit) -> ranked evidence chunks
```

### Answer provider

```text
answer(question, evidence) -> grounded claim blocks or abstention, usage
```

### Trace summary

One provider-neutral schema matching the feature specification.

These boundaries allow SQLite retrieval and mock generation to be replaced independently without changing the UI contract.

## Implementation phases

### Phase A: contracts and fixtures

- Define API schemas and stable source IDs.
- Define retriever and answer-provider interfaces.
- Create deterministic fixtures for three grounded questions and abstention.
- Add contract tests before UI implementation.

### Phase B: content ingestion and retrieval

- Parse reviewed Markdown by level-two section.
- Build the SQLite FTS5 index deterministically.
- Implement top-three retrieval and retrieval tests.
- Run the initial retrieval evaluation and record the baseline.

### Phase C: observable answer API

- Implement `/health`, `/v1/system`, and `/v1/answer`.
- Add citation allow-list validation.
- Add trace IDs, retrieval and generation spans, stage timings, and structured logs.
- Verify that provider failure cannot fall through to an ungrounded answer.

### Phase D: minimal web experience

- Implement the page, suggested questions, form states, answer state, and abstention state.
- Implement the unified Inspector with Evidence and System Lens modes.
- Back System Lens with sanitized traces and the generated evaluation summary.
- Verify keyboard and mobile use.

### Phase E: evaluation and review

- Complete deterministic evaluation coverage.
- Run privacy and injection cases.
- Scan the repository for blocked PII and secrets.
- Capture baseline screenshots and evaluation results.
- Review the implementation against the feature specification before selecting a real model provider.

## Deferred architecture

The following are intentionally not in the first plan:

- Managed platform deployment
- PostgreSQL/pgvector
- Embedding generation
- Hybrid retrieval or reranking
- Hosted telemetry collector or dashboard
- Streaming transport
- Session state or conversation persistence

## Decision gates after the baseline

1. Confirm OpenAI or Anthropic API billing and set a small spending limit.
2. Add one real answer provider and compare it with deterministic expected behavior.
3. Measure lexical retrieval gaps using the existing cases.
4. Begin the committed PostgreSQL/pgvector experiment as a separate milestone.
5. Compare lexical, semantic, and hybrid retrieval on the same versioned cases; select the production default from evidence.
6. Deploy the deterministic slice with private content mounted at runtime and verify the public path.
