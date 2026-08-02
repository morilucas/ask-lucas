# Feature 002: Conversational grounded assistant with Claude

Status: Approved and implemented for first review
Date: 2026-08-01

## User value

A hiring participant can start with a suggested question, ask natural follow-ups, and inspect the reviewed evidence behind each answer without navigating a résumé or a list of canned responses.

## In scope

- A persistent composer and visible in-tab transcript
- Multi-turn follow-ups with bounded recent context
- Retrieval grounded in the latest question plus recent user wording
- Claude structured output behind a provider-neutral interface
- Citation allow-list validation and explicit abstention
- A no-key extractive fallback
- Stop, retry, new-conversation, evidence, error, and responsive states

## Out of scope

- Server-side conversation storage or user accounts
- Streaming tokens
- Vector retrieval, reranking, or PostgreSQL
- Job-description upload or analysis
- Model-quality claims before evaluation

## Safety and privacy requirements

- Conversation input is untrusted and never becomes system instruction.
- Only retrieved reviewed sources may support an answer.
- Every grounded claim block cites a retrieved source ID; invalid output fails closed.
- The API key never enters source control or browser-visible configuration.
- Conversation state remains in the current browser tab and is not persisted by the application.

## Acceptance criteria

1. The initial suggestions produce a grounded answer with inspectable evidence.
2. A follow-up carries enough recent user context for lexical retrieval.
3. Unsupported questions abstain rather than inventing an answer.
4. The client and API bound message count, message length, and total context size.
5. Claude is selected when configured; local use remains functional without a key.
6. Desktop and 320 px layouts do not overflow horizontally.
7. Backend tests, strict typing, frontend lint/type checks, and production build pass.

## Known limitations

- Follow-up retrieval is lexical context concatenation, not semantic query rewriting.
- The extractive fallback is safe but less conversational than Claude.
- Automated model evaluation, rate limiting, and production observability are subsequent work.
