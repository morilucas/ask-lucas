# SQLite lexical retrieval baseline

Status: Implemented locally
Last updated: 2026-08-01

This document records the first real retrieval path behind Ask Lucas. It implements ADR 0001 without adding embeddings, a hosted database, or model-provider spending.

## Request and evidence flow

```text
configured reviewed Markdown directory
  → direct-file allowlist loader
  → level-two Markdown sections
  → stable source IDs and corpus fingerprint
  → SQLite content table + FTS5 index
  → safe quoted-term query builder
  → top-three BM25-ranked evidence
  → deterministic answer provider
  → citation allow-list validation
  → existing API response contract
```

The API builds the local index on the first retrieval request and rebuilds it when the logical corpus fingerprint changes. Developers can also rebuild it explicitly with:

```powershell
cd apps/api
uv run python scripts/rebuild_index.py
```

The generated database lives at `apps/api/data/content.db` and is ignored by Git.

## Ingestion boundary

Only direct `*.md` children of the configured content directory are considered. The loader does not recurse, inspect PDFs, or scan the repository. Root-level Markdown prose is ignored; only nonempty level-two sections become chunks. `profile:explicit-exclusions` is explicitly denied. Local defaults point to synthetic files under `examples/content/`; production points to the separately deployed private repository.

Each source ID has the form `<document-stem>:<heading-slug>`. The ID depends on the path and heading, not body text or section order. Duplicate IDs stop ingestion rather than receiving unstable suffixes.

## Query safety

Visitor text is normalized into a bounded list of Unicode word tokens. Common question words are removed, repeated terms are deduplicated, and remaining terms are passed to FTS5 only as quoted literals joined by an application-created `OR`. Quotes, FTS operators, column syntax, wildcard characters, and parentheses from visitor input never reach the `MATCH` expression as syntax.

## Ranking semantics

The retriever returns at most three records ordered by SQLite FTS5 BM25 score, then stable source ID as a tie-breaker. Lower BM25 values rank first. These values describe lexical ranking only: the API labels them `bm25` and `lower_is_better`, never confidence.

## Current limitations

- Lexical retrieval can miss semantically related wording.
- The tiny corpus is parsed to verify its fingerprint before each retrieval.
- The deterministic provider has one reviewed grounded answer; other questions abstain.
- There is no relevance threshold yet because it must be selected from evaluation evidence.

The next measurement pass will calculate Recall@3 against the versioned employer-question cases before semantic or hybrid retrieval is introduced.
