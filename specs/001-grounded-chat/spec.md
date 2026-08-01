# Feature specification 001: grounded single-turn chat

Status: Approved for implementation
Depends on: `docs/product-brief.md`, `docs/experience-brief.md`, `docs/constitution.md`
Last updated: 2026-08-01

## User story

As a participant in a hiring process, a visitor wants to ask a question about Lucas and receive a concise answer with inspectable evidence, while also seeing enough system metadata to recognize that the experience is an evaluated AI engineering project.

## Demonstration flow

1. The visitor opens the page and sees the title, one-sentence explanation, three suggested questions, and the question input.
2. The visitor selects a suggestion or writes a question.
3. The interface shows a clear pending state and prevents duplicate submission.
4. The API retrieves up to three approved content sections.
5. The answer provider returns either grounded claim blocks with source IDs or an abstention.
6. The API validates every source ID on every claim block against the retrieved sources and fails closed on invalid output.
7. The interface renders the answer, citation chips, and trace ID.
8. Selecting a citation opens the unified Inspector in Evidence mode and reveals the source title, section, and exact retrieved excerpt.
9. Opening System Lens reuses the Inspector shell and shows sanitized retrieval and timing metadata.
10. System Lens also shows the baseline architecture, its known limitations, and the last generated evaluation summary.

## Page structure

### Header

- Product name: Ask Lucas
- Descriptor: “A grounded AI engineering portfolio”
- System Lens control
- Small link to GitHub when a public repository exists
- No navigation menu, portrait, avatar, or theme switcher

### Introduction

One short paragraph explains that answers are generated from reviewed public material about Lucas and that citations, traces, and evaluations are visible by design.

### Suggested questions

Three editorial action rows populated from configuration, not hard-coded inside presentation components. They must remain recognizable and operable as buttons without adopting generic prompt-pill styling.

### Answer canvas

- Question input
- Submit button
- Empty state
- Pending state
- Answer state
- Abstention state
- Recoverable error state

The first build displays only the current question and response. Questions render as headings and answers as readable prose rather than message bubbles. It does not create conversational memory.

### Unified Inspector: Evidence mode

Opened from a citation chip. Displays:

- Human-readable document title
- Section heading
- Exact excerpt passed to the answer provider
- Stable source ID
- Previous and next citation controls when multiple citations exist

On wide screens the Inspector is a right-side overlay. On narrow screens it is a full-height bottom sheet or full-screen panel. It traps focus, closes with Escape, and returns focus to its trigger.

### Unified Inspector: System Lens mode

Displays:

- Trace ID
- Retrieval strategy
- Retrieved source IDs and scores
- Provider mode and model identifier when applicable
- Retrieval duration
- Generation duration
- Total duration
- Token usage and estimated cost only when supplied by the provider

It must not display hidden reasoning, system prompts, secrets, private data, or raw internal exceptions.

Also displays:

- A compact request-flow diagram
- The reason for starting with lexical retrieval
- Latest retrieval Recall@3
- Behavioral evaluation pass count
- Date and version of the evaluation run
- Known limitations and planned next experiment

Evidence and System Lens must reuse one overlay system rather than creating competing panels.

The header System Lens control loads the system summary even when no answer has been requested. After an answer, the same view combines the system summary with that request's sanitized trace.

## API contract

### `GET /health`

Returns service status and build version without dependency secrets.

### `GET /v1/system`

Returns cacheable, non-secret information needed by System Lens before an answer exists:

```json
{
  "build_version": "local",
  "retrieval": {
    "strategy": "sqlite-fts5",
    "limit": 3,
    "score_kind": "bm25",
    "score_order": "lower_is_better"
  },
  "evaluation": {
    "version": "0.1",
    "generated_at": "2026-08-01T00:00:00Z",
    "retrieval_recall_at_3": 0.0,
    "behavior_passed": 0,
    "behavior_total": 0
  },
  "limitations": [
    "The baseline uses lexical rather than semantic retrieval."
  ],
  "next_experiment": "Compare lexical, semantic, and hybrid retrieval."
}
```

Unavailable evaluation results use explicit `null` values and a status label rather than invented zeros.

### `POST /v1/answer`

Request:

```json
{
  "question": "What AI systems has Lucas built?"
}
```

Successful grounded response:

```json
{
  "kind": "grounded",
  "blocks": [
    {
      "text": "Lucas has built data and AI systems used by business teams.",
      "source_ids": [
        "experience:acme-ai-data-engineer"
      ]
    }
  ],
  "sources": [
    {
      "source_id": "experience:acme-ai-data-engineer",
      "title": "Approved public experience",
      "section": "Acme — AI & Data Engineer",
      "excerpt": "Currently focuses on internal AI applications ...",
      "content_path": "content/experience.md"
    }
  ],
  "trace": {
    "trace_id": "opaque-id",
    "retrieval_strategy": "sqlite-fts5",
    "score_kind": "bm25",
    "score_order": "lower_is_better",
    "retrieved": [
      {
        "source_id": "experience:acme-ai-data-engineer",
        "rank": 1,
        "raw_score": -1.0
      }
    ],
    "provider_mode": "mock",
    "model": null,
    "retrieval_ms": 0,
    "generation_ms": 0,
    "total_ms": 0,
    "input_tokens": null,
    "output_tokens": null,
    "estimated_cost_usd": null
  }
}
```

Grounded and abstained responses form a discriminated union on `kind`. Every grounded block contains plain text and one or more supporting source IDs. The UI never parses provider-authored Markdown or HTML.

Abstention response:

```json
{
  "kind": "abstained",
  "message": "The approved public sources do not provide that information.",
  "suggestions": [
    "What AI and data systems has Lucas built?",
    "How has Lucas combined technical and business experience?"
  ],
  "trace": {
    "trace_id": "opaque-id",
    "retrieval_strategy": "sqlite-fts5",
    "score_kind": "bm25",
    "score_order": "lower_is_better",
    "retrieved": [],
    "provider_mode": "mock",
    "model": null,
    "retrieval_ms": 0,
    "generation_ms": 0,
    "total_ms": 0,
    "input_tokens": null,
    "output_tokens": null,
    "estimated_cost_usd": null
  }
}
```

Safe error response:

```json
{
  "code": "provider_unavailable",
  "message": "The answer could not be completed. Please try again.",
  "trace_id": "opaque-id",
  "retryable": true
}
```

Question text is trimmed and must contain between 1 and 500 Unicode characters. Validation errors use HTTP 422. Dependency failures use HTTP 503 when retryable. Unexpected failures use HTTP 500 with a generic message. Error bodies and the `X-Trace-ID` response header carry the trace ID; no response exposes a stack trace.

All non-success responses use the documented safe error envelope, including request-validation errors. CORS exposes `X-Trace-ID` only to the configured web origin.

## Content ingestion

- Only Markdown files inside `content/` are eligible.
- The loader splits documents at level-two headings.
- Each chunk receives a stable ID derived from the relative file path and heading slug.
- Canonical source IDs use `<document-stem>:<heading-slug>`, for example `experience:acme-ai-data-engineer`.
- Heading slugs are lowercase ASCII: Unicode is normalized, punctuation is removed without adding words, whitespace and separator runs become one hyphen, and leading/trailing hyphens are removed.
- The source record separately retains the repository-relative content path and original heading.
- Duplicate canonical IDs fail ingestion rather than receiving order-dependent suffixes.
- The stored text includes the section heading and body.
- Empty sections and configured exclusion sections, including `profile:explicit-exclusions`, are not indexed.
- Rebuilding the local index is deterministic.
- Raw PDFs and files ignored by Git are never scanned.

## Retrieval baseline

- SQLite with FTS5 is the first retrieval implementation.
- The retriever returns at most three chunks.
- Source IDs, ranks, and scores are retained for evaluation and tracing.
- Raw scores are always accompanied by a score kind and ordering direction; the UI never labels them as confidence or compares scores from different retrievers directly.
- Visitor text is never passed directly as an FTS `MATCH` expression. A tested query builder converts it to safe literal terms and handles quotes, operators, punctuation, and an empty token result.
- Retrieval code implements a narrow interface so a later semantic or hybrid retriever can use the same API contract and evaluation set.
- No relevance threshold is selected without evaluation evidence. The initial threshold is configurable and documented in the evaluation output.

## Answer-provider behavior

- The provider receives the question and retrieved chunks as untrusted evidence.
- The provider must answer in the third person.
- It returns ordered plain-text claim blocks and may attach only supplied source IDs.
- Every material grounded block must contain at least one source ID.
- It must abstain when the evidence is insufficient.
- The application rejects the complete provider result when a block contains an unknown or missing required source ID. It never silently drops or repairs citations.
- Mock mode returns deterministic fixture responses for the suggested questions and abstention cases.
- This first deterministic slice returns one complete response and uses one honest pending state; it does not simulate streaming stages.
- One real provider adapter is added only after API billing is confirmed.

## Evaluation requirements

The evaluation runner reads the configured evaluation path and writes a versioned JSON summary. Public tests use `examples/evals/employer-questions.yaml`; production cases are supplied by the private content checkout.

First-build metrics:

- Retrieval Recall@3 as fractional required-source coverage per answerable case, macro-averaged across those cases
- Citation-ID validity
- Citation presence for grounded answers
- Correct abstention for privacy, unsupported, confidentiality, and injection cases
- API schema validity
- Latency distribution in real-provider mode when available

The first build does not claim that an LLM judge is ground truth. Model-graded quality can be added later alongside human review.

`required_sources` contains canonical section source IDs. Document-level IDs are invalid. Retrieval Recall@3 is a measurement, not a binary behavioral pass: a case score is `required sources present in the top 3 / required sources listed`. Deterministic safety/schema checks and human semantic review are reported separately.

## Observability requirements

- Every answer request receives one trace ID.
- Retrieval and generation are separate spans.
- Python tracing uses the OpenTelemetry API/SDK with a console or local exporter initially.
- Structured application logs correlate with the trace ID.
- Full user questions are not persisted by default.
- The UI receives only the sanitized trace summary in the response schema.
- Export to a hosted observability backend is deferred.

## Visual constraints

- Portrait-free, typography-led editorial composition
- One warm light theme; no first-release dark mode or theme switcher
- One body family, one optional display family, and a native monospace stack
- Combined critical self-hosted font payload target of 100 KB or less
- Spacing, type, radius, shadow, motion, and color values centralized as tokens
- No decorative imagery, gradients, glass effects, looping motion, shimmer skeletons, or fake progress
- No dependency on a large component library for the first page
- Readable prose column approximately 680–720 CSS pixels wide
- Responsive without horizontal scrolling from 320 CSS pixels through desktop
- Visible keyboard focus, semantic form controls, reduced-motion support, and WCAG 2.2 AA target
- Internal production targets: LCP ≤ 1.8 seconds, INP ≤ 150 milliseconds, CLS ≤ 0.03, and mobile Lighthouse Performance ≥ 95

## Error behavior

- Empty questions are rejected client-side and server-side.
- Oversized questions receive a clear validation message.
- Provider failure returns a recoverable error with the trace ID.
- After eight seconds, a pending request displays a calm slow-response message.
- Retrieval failure does not silently become an ungrounded model call.
- Unknown citations never render.
- Invalid FTS syntax in visitor text cannot produce an unhandled server error.
- Health failures never expose stack traces or secrets.

## Acceptance criteria

1. The complete page and API run locally in mock mode without API credentials.
2. All three suggested questions return deterministic grounded responses with valid citations.
3. At least one unsupported question returns the designed abstention state.
4. At least one prompt-injection case returns the designed refusal/abstention state.
5. Citation selection reveals the exact indexed excerpt.
6. The trace disclosure shows a trace ID, retrieval results, and stage timings.
7. The system panel reads a generated evaluation-summary artifact.
8. Automated tests cover ingestion IDs, retrieval shape, citation validation, privacy abstention, API schema, and the principal UI states.
9. A repository scan confirms that the raw resume, address, phone number, personal email, and credentials are absent.
10. The implementation contains no conversation database, authentication, feedback form, semantic vector database, or agent framework.
11. The principal ask, answer, citation, Inspector, close, and reset flow works by keyboard at mobile and desktop widths.
12. The page contains no portrait, avatar, hero illustration, conventional chat bubbles, or theme switcher.

## Out of scope

Anything listed as explicitly deferred in the product brief is out of scope for this feature even if a template or library makes it easy to add.
