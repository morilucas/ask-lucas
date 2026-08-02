# Plan 002: Conversational Claude slice

1. Extend the public contract with bounded alternating conversation messages.
2. Carry recent user context into the existing SQLite FTS5 retriever.
3. Add Claude structured generation behind `AnswerProvider` and preserve a no-key fallback.
4. Replace the single-answer canvas with a small, polished transcript and persistent composer.
5. Test request bounds, contextual retrieval, provider failures, citations, and key interaction states.
6. Build, publish, deploy with private content mounted read-only, and smoke-test the live route.

The slice deliberately does not add storage, an agent framework, a vector database, or streaming.
