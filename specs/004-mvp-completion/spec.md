# Feature 004: MVP completion and content operations

Status: Implemented and deployed
Date: 2026-08-02

## User value

A hiring participant can use Ask Lucas as a complete conversational product: every normal, slow,
unsupported, failed, and evidence-inspection state is understandable, while Lucas can validate and
refresh the private knowledge base without an unsafe partial index.

## Existing contract

Feature 002 already provides bounded in-tab multi-turn conversation through `POST /v1/chat` and
Feature 003 provides production request and cost controls. This feature preserves those public API
shapes. The existing `GET /v1/system` response supplies the safe metadata required by System Lens.

## Stream A: safe content operations

This stream is assigned to the isolated Claude worker and may change only the backend ingestion,
retrieval, rebuild scripts, their focused tests, and backend content-operation documentation.

### Requirements

1. Provide a read-only validation command for an approved content directory.
2. Validation reports only safe metadata: chunk count, stable source IDs, and corpus fingerprint. It
   must not print content bodies.
3. Rebuilding creates a complete temporary SQLite index in the destination directory and atomically
   replaces the active index only after the new index succeeds.
4. A failed rebuild preserves the last valid index and cleans up its temporary file.
5. Repeated rebuilds over unchanged content remain logically deterministic.
6. Existing automatic refresh behavior and the `Retriever` protocol remain compatible.

## Stream B: complete conversation experience

This stream is implemented by Codex locally and may change only the web application, web tests, and
frontend-specific documentation.

### Requirements

1. Preserve the in-tab transcript and persistent composer established by Feature 002.
2. Validate empty and over-limit questions next to the composer and preserve focus.
3. Show the truthful pending state immediately and calm slow-response copy after eight seconds.
4. Treat abstention as a successful outcome and make its supported suggestions actionable.
5. Preserve questions across retryable API and connection errors; never display partial answers as
   complete.
6. Evidence inspection supports previous/next navigation for every cited source and returns focus to
   the invoking citation.
7. System Lens uses `GET /v1/system` plus the selected answer trace to show safe retrieval strategy,
   retrieved source IDs and scores, provider/model mode, real timings, trace ID, evaluation
   availability, limitation, and next experiment.
8. The transcript remains editorial rather than imitating avatars or conventional message bubbles.
9. Keyboard operation, reduced motion, live-region announcements, 320-pixel layout, lint, strict
   typing, production build, and focused browser journeys pass.

## Parallel-work boundary

- Claude must not modify `apps/web`, public API schemas, generated OpenAPI files, deployment files,
  or production infrastructure.
- Codex must not modify `apps/api` while Claude's task is active.
- Any discovered need to cross the boundary pauses that stream for coordinator review.
- Claude produces a local branch commit only. Codex reviews its entire diff and independently reruns
  all relevant checks before integration.

## Explicit non-goals

- Final biography authoring or factual evaluation cases
- PostgreSQL, `pgvector`, embeddings, hybrid retrieval, or reranking
- Token streaming
- Server-side conversation storage, accounts, or analytics
- New hosted services or browser dependencies
- Changes to the private content repository during this code pass

## Why vector retrieval remains later

ADR 0001 requires the real, versioned content and its lexical Recall@3 baseline before choosing a
semantic or hybrid production path. Once Lucas completes the private biography, the same benchmark
will justify and compare PostgreSQL/`pgvector` rather than adding it only as portfolio decoration.

## Acceptance

1. Both streams satisfy their file ownership and focused tests.
2. The complete backend lint, type, and test suite passes after integration.
3. The complete frontend lint, type, build, and browser suite passes after integration.
4. The private-content validation and atomic rebuild commands succeed against synthetic content and
   can be exercised safely against the mounted production content.
5. The deployed site passes grounded, follow-up, abstention, evidence, System Lens, error, mobile,
   and health smoke checks.

## Verification record

Implemented in release `652f14c` and deployed on 2026-08-02. The integrated code passed backend
formatting, lint, strict typing, and 49 tests; frontend lint, strict typing, production build, and 12
Playwright journeys across desktop and 320-pixel mobile layouts. Production validation accepted 20
private sections, rebuilt the index atomically, and passed live health, grounded-answer, abstention,
citation, System Lens, and page smoke checks.
