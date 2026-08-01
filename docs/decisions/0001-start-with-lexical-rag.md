# ADR 0001: start with an observable lexical RAG baseline

Status: Accepted
Date: 2026-08-01

## Context

The project needs to showcase RAG, evaluation, and observability while remaining inexpensive and achievable at approximately five development hours per week. Local Docker availability and model API billing are not yet confirmed. The approved knowledge base is small.

## Decision

The first build will use SQLite FTS5 to retrieve up to three Markdown sections. Generation will sit behind a provider interface with deterministic mock mode. Retrieval and generation will emit separate trace spans and use the same evaluation cases planned for future semantic retrieval.

PostgreSQL and `pgvector` remain the expected semantic/hybrid retrieval experiment, not a first-build dependency.

## Why

- Produces a complete RAG-shaped system without embeddings or an external database.
- Uses SQL and creates an inspectable relevance baseline.
- Allows evaluation work to begin before model-provider spending.
- Keeps local setup simple while Docker availability is unresolved.
- Makes a later vector-search decision measurable rather than cosmetic.

## Alternatives considered

### PostgreSQL/pgvector immediately

Better resembles the likely deployed architecture and provides vector search, but introduces database operations, embeddings, and deployment work before a retrieval baseline exists.

### Hosted file search

Provides a fast managed path but hides more ingestion and retrieval behavior, adds provider coupling, and weakens the planned retrieval comparison.

### In-memory vector store

Avoids database setup but still requires embeddings and offers less opportunity to demonstrate SQL or durable source identity.

### Put all content in the prompt

Would likely work for the tiny corpus but would not demonstrate retrieval behavior or provide a meaningful retrieval evaluation baseline.

## Consequences

- The first retriever is lexical and will miss some semantic matches.
- FTS scores are not directly comparable to vector similarity scores.
- The UI and evaluation artifacts must describe the baseline honestly.
- Retriever and provider interfaces must be narrow enough to support later replacement.

## Revisit when

- Baseline Recall@3 exposes semantic failures.
- API billing and embedding cost limits are confirmed.
- Local or VPS PostgreSQL operations are ready.
- The same evaluation suite can compare lexical, semantic, and hybrid retrieval.
