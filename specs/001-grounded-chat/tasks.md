# Tasks 001: grounded single-turn chat

Status: Ready — first development pass approved
Depends on: `spec.md`, `plan.md`, `docs/experience-brief.md`, ADRs 0001–0003
Last updated: 2026-08-01

## Execution rules

- Work in dependency order unless a task explicitly says otherwise.
- Keep most tasks between approximately 30 and 120 focused minutes.
- A task is complete only when its verification passes and its documentation still matches.
- Add tests in the same task as behavior.
- Commit small coherent checkpoints after Lucas reviews the diff.
- Update the specification before changing user-visible behavior or adding a major dependency.
- Feature 001 remains local and deterministic: no provider key, production deployment, PostgreSQL, vector search, or streaming transport.

## Gate 0: build-ready review

- [x] **G001 — Approve the implementation baseline.** Lucas approved the product brief, experience brief, public content for the first version, evaluation direction, feature specification, and ADRs 0001–0003 on 2026-08-01.
- [x] **G002 — Create the documentation baseline commit.** Confirm no private data or raw résumé is present and create the first intentional Git commit. Verification: the repository secret/PII scan passes and Git status is clean. Do not publish a remote without Lucas's direction.

## Work packet 1: executable API contract

- [x] **T101 — Pin the backend toolchain.** Add the CPython 3.12 requirement and `.python-version`; document that `uv` manages the missing local interpreter. Verification: `uv` resolves the interpreter and environment reproducibly without Docker.
- [x] **T102 — Scaffold the API package.** Create the minimal FastAPI source package, settings object, `/health`, Ruff, Mypy, and Pytest configuration. Verification: lint, type-check, and health tests pass through `uv run`.
- [x] **T103 — Implement domain and error schemas.** Add the grounded/abstained discriminated union, claim blocks, sources, retrieval-score semantics, trace summary, system summary, and safe error envelope. Verification: schema tests cover bounds, required claim sources, forbidden extra fields, and every documented response mode.
- [x] **T104 — Define narrow backend protocols.** Add retriever and answer-provider protocols plus an application dependency bundle for test doubles. Verification: deterministic doubles satisfy the protocols without a framework or vendor SDK.
- [x] **T105 — Serve one deterministic answer fixture.** Implement `GET /v1/system` and `POST /v1/answer` for one approved showcase question using one exact curated excerpt. Verification: API tests cover grounded response, source validation, abstention, HTTP 422 validation, safe HTTP 503 failure, and secret-free health/system output.
- [x] **T106 — Export the API contract.** Add deterministic OpenAPI export with a drift-check command. Verification: two exports are byte-stable after normalizing generated metadata.

Checkpoint: one command runs the API tests, and the actual HTTP endpoint returns one schema-conformant answer with one exact approved source. No database or provider SDK exists yet.

## Work packet 2: first user-visible vertical slice

- [x] **T201 — Pin and scaffold the web application.** Create a minimal Next.js App Router app with Node 24 metadata, npm lockfile, strict TypeScript, ESLint, no Tailwind, and no template visual content. Document the Windows `npm.cmd` invocation. Verification: lint, type-check, and production build pass.
- [x] **T202 — Generate web contract types.** Use development-only `openapi-typescript` and the committed OpenAPI artifact; add one small native-fetch client. Verification: generated types are stable and no response type is duplicated by hand.
- [x] **T203 — Build the static editorial shell.** Add semantic landmarks, design tokens, provisional optimized fonts, header, opening, configured suggestion rows, composer, and footer. Verification: the empty state follows the experience hierarchy at 320 px and common desktop widths.
- [x] **T204 — Connect one suggestion end to end.** Submit the canonical showcase question, render one honest pending state, display ordered plain-text claim blocks, and render adjacent citation buttons. Verification: the API—not a frontend fixture—provides the visible answer.
- [x] **T205 — Open one citation in the Inspector.** Implement the minimal native-dialog Evidence mode with exact excerpt, explicit close, Escape, focus return, and mobile-safe layout. Verification: one Playwright smoke test covers suggestion → API → answer → evidence → close.
- [x] **T206 — Document local execution.** Add safe `.env.example` files, ports 3000/8000, exact CORS origins, and two-process startup instructions. Verification: a clean environment starts in mock mode without secrets or Docker.

Checkpoint: a visitor can complete the principal interaction locally before deeper backend work begins.

## Work packet 3: approved content and lexical retrieval

- [x] **T301 — Parse approved Markdown.** Load only `content/*.md`, split on level-two headings, and skip empty/configured exclusion sections. Verification: raw PDFs, ignored paths, root-level prose, and `profile:explicit-exclusions` cannot enter the corpus.
- [x] **T302 — Generate canonical source IDs.** Implement the specified document-stem and normalized-heading algorithm, retain provenance separately, and reject duplicates. Verification: repeated ingestion and unrelated body edits produce identical IDs.
- [x] **T303 — Build the SQLite FTS5 index.** Add an explicit schema and deterministic rebuild command using standard-library SQLite. Verification: FTS5 availability is checked clearly and two rebuilds produce the same logical records.
- [x] **T304 — Build safe FTS queries.** Convert visitor text into safe literal terms rather than raw `MATCH` syntax. Verification: quotes, operators, punctuation, Unicode, empty-token input, and adversarial FTS expressions cannot create SQL or FTS syntax errors.
- [x] **T305 — Implement the retriever protocol.** Return top-three evidence with canonical source ID, exact excerpt, rank, raw score, score kind, and score order. Verification: tests cover expected matches, no hits, limits, deterministic ranking, and honest non-confidence labels.
- [x] **T306 — Replace the manual fixture evidence with retrieval.** Route the existing answer through the real retriever without changing the API response contract. Verification: the first Playwright journey still passes against the rebuilt index.

Checkpoint: two deterministic rebuilds yield the same approved corpus, and representative questions retrieve expected section IDs safely.

## Work packet 4: complete deterministic orchestration

- [ ] **T401 — Add deterministic mock coverage.** Implement fixtures for all three suggestions, supported variants, required privacy/injection/confidentiality cases, abstention, and provider failure. Key fixtures by stable case/config ID rather than UI copy alone. Verification: outputs are stable and material claims use only retrieved source IDs.
- [ ] **T402 — Validate every claim block.** Require at least one retrieved source on every material grounded block, deduplicate returned source records, and reject the whole provider result on unknown/missing IDs. Verification: the application never drops, repairs, or renders an invalid citation.
- [ ] **T403 — Complete orchestration failure behavior.** Cover no results, retrieval failure, provider failure, invalid provider shape, timeout, and no ungrounded fallback. Verification: each path returns the specified safe response/error and trace ID.
- [ ] **T404 — Freeze contract fixtures.** Add representative grounded, abstained, validation, system, and error JSON fixtures and regenerate web types. Verification: Python contract tests and TypeScript compilation use the same committed contract artifacts.

Checkpoint: the deterministic API demonstrates grounding and fail-closed behavior rather than hardcoded happy-path output.

## Work packet 5: evaluation and observability

- [ ] **T501 — Validate evaluation cases.** Enforce canonical section IDs, reject document-level requirements, distinguish retrieval cases from behavioral-only cases, and ensure no case requires more than top three sources. Verification: malformed evaluation data fails early with useful messages.
- [ ] **T502 — Report the lexical baseline.** Calculate fractional per-case Recall@3 and its macro average; report citation validity, citation presence, abstention, schema, and deterministic behavior separately. Verification: machine-readable JSON and console summaries agree and are labeled `deterministic mock`.
- [ ] **T503 — Record retrieval error analysis.** Describe missed sources and query patterns without rewriting cases to improve the score. Verification: findings become explicit inputs to the later pgvector comparison.
- [ ] **T504 — Add request tracing.** Create W3C trace IDs and OpenTelemetry spans for request, retrieval, and generation with real timings. Verification: spans correlate while tests avoid exact-duration assertions.
- [ ] **T505 — Add privacy-conscious structured logs.** Emit allowlisted JSON fields correlated by trace ID; omit full questions, prompts, excerpts, and secrets by default. Verification: captured logs contain useful diagnostics and no blocked fields.
- [ ] **T506 — Back System Lens with real artifacts.** Load the generated evaluation summary and static limitation/next-experiment metadata in `GET /v1/system`. Verification: missing or stale artifacts are labeled explicitly rather than replaced with invented results.

Checkpoint: one command produces the evaluation artifact shown by the product, and logs/traces diagnose requests without storing their content.

## Work packet 6: complete product behavior

- [ ] **T601 — Complete composer behavior.** Add custom questions, 1–500-character validation, immediate feedback, duplicate prevention, and reset focus. Verification: Playwright covers keyboard and pointer submission.
- [ ] **T602 — Complete pending and slow states.** Preserve the submitted question, announce one truthful pending message, and show calm slow-response copy after eight seconds. Verification: intercepted delays exercise both states without fake backend stages.
- [ ] **T603 — Complete grounded and abstention canvases.** Render claim blocks, inline citation controls, quiet metadata, assessment labels, and two supported next questions after abstention. Verification: no provider-authored Markdown/HTML, message bubbles, or history render.
- [ ] **T604 — Complete the unified Inspector.** Add Evidence navigation and System Lens mode, responsive drawer/sheet styling, controlled initial focus, Escape, focus return, scroll behavior, and plain-language score semantics. Verification: browser tests cover mouse, keyboard, desktop, and mobile.
- [ ] **T605 — Complete recoverable error and offline behavior.** Preserve the question, expose Retry and safe trace ID, and distinguish network interruption from API failure. Verification: route interception exercises all error modes and no partial answer appears complete.

Checkpoint: every state in the experience brief works against the deterministic API and remains secondary to the answer.

## Work packet 7: visual and interaction quality

- [ ] **T701 — Refine typography and hierarchy.** Tune font loading, scale, line length, spacing, rules, and accent usage across every state. Verification: font payload remains within budget and typography works without imagery or decorative filler.
- [ ] **T702 — Verify responsive behavior.** Test all required viewports, 320 px overflow, the mobile software-keyboard scenario, Inspector sizing, and content growth. Verification: reviewed screenshots show no clipped action or horizontal scroll.
- [ ] **T703 — Verify accessibility.** Run axe, keyboard-only flows, focus checks, contrast review, reduced motion, and a screen-reader smoke test. Verification: zero serious/critical automated findings and manual results are recorded.
- [ ] **T704 — Record visual regression baselines.** Capture reviewed empty, pending, answer, abstention, error, Evidence, and System Lens states at representative desktop/mobile widths. Verification: future changes require intentional screenshot review.
- [ ] **T705 — Measure performance.** Record a production build, JavaScript/CSS/font transfer, local API p95, Web Vitals, and Lighthouse. Verification: experience budgets pass or an explicit decision records the measured exception.

Checkpoint: polish is supported by screenshots and measurements, not subjective completion claims.

## Work packet 8: feature acceptance

- [ ] **T801 — Run integrated browser journeys.** Execute Playwright against the real local web/API pair for suggestion, custom question, citation, System Lens, abstention, retry, and reset at desktop and mobile widths.
- [ ] **T802 — Complete security and privacy review.** Run injection/privacy/confidentiality evals, input-limit/FTS safety tests, secret scanning, dependency audit, and repository/index PII checks.
- [ ] **T803 — Run the complete verification suite.** Execute API lint/type/tests/evals, contract drift, web lint/type/build, browser tests, accessibility, and artifact checks.
- [ ] **T804 — Map acceptance criteria to evidence.** Link every criterion to a test, evaluation result, screenshot, measurement, or manual review; update README, limitations, and task status.
- [ ] **T805 — Complete Lucas's acceptance review.** Lucas checks factual answers, citations, public content, visual result, architecture evidence, and the final diff.

Checkpoint: feature 001 is complete locally in deterministic mock mode and ready for a separately specified real-provider/prelaunch milestone.

## Planning map for five hours per week

This is a sequencing hypothesis, not a deadline:

| Focus | Likely work packet |
|---|---|
| Week 1 | Gate 0 and executable API contract |
| Week 2 | First user-visible vertical slice |
| Week 3 | Approved-content ingestion and FTS5 |
| Week 4 | Complete deterministic orchestration |
| Week 5 | Evaluation, tracing, logs, and system summary |
| Week 6 | All product states and responsive Inspector |
| Week 7 | Typography, accessibility, visual, and performance polish |
| Week 8 | Integrated acceptance and documentation |

Allow additional time for learning, review, and environment issues. Change the schedule by reducing scope or moving a milestone—not by skipping verification.

## Explicit later specifications

1. Real model adapter, model evaluation, cost controls, and measured streaming decision
2. Public deployment, rate limiting, backups, and operational runbook
3. PostgreSQL/pgvector semantic retrieval and lexical/semantic/hybrid comparison
4. Production feedback loop only after real visitor needs are understood

## First coding checkpoint

After Gate 0, execute T101–T106 only. Review the executable API contract before scaffolding the web application. This validates the highest-leverage boundary in one small implementation diff.
