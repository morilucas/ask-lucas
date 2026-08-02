"""Deterministic SQLite FTS5 indexing and lexical retrieval."""

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
import threading
import unicodedata
from collections.abc import Sequence
from contextlib import closing, suppress
from pathlib import Path

from ask_lucas.ingestion import (
    ContentChunk,
    ContentIngestionError,
    corpus_fingerprint,
    load_approved_content,
)
from ask_lucas.ports import RetrievalResult, RetrievedEvidence
from ask_lucas.schemas import Source

STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "can",
        "did",
        "do",
        "does",
        "for",
        "has",
        "have",
        "how",
        "in",
        "is",
        "it",
        "lucas",
        "me",
        "of",
        "on",
        "or",
        "tell",
        "the",
        "there",
        "to",
        "what",
        "why",
        "with",
    }
)
TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
MAX_QUERY_TERMS = 24
TOKEN_ALIASES = {"built": "build"}
INDEX_SCHEMA_VERSION = "1"

SCHEMA = """
CREATE TABLE content_chunks (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    section TEXT NOT NULL,
    body TEXT NOT NULL,
    indexed_text TEXT NOT NULL,
    content_path TEXT NOT NULL
);
CREATE VIRTUAL TABLE content_fts USING fts5(
    source_id UNINDEXED,
    title,
    section,
    indexed_text,
    tokenize = 'porter unicode61 remove_diacritics 2'
);
CREATE TABLE index_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class RetrievalError(RuntimeError):
    """Raised when the lexical index cannot be built or queried safely."""


def build_fts_query(question: str) -> str | None:
    """Convert visitor text to a bounded OR expression of quoted literal terms."""

    normalized = unicodedata.normalize("NFKC", question).casefold()
    terms: list[str] = []
    seen: set[str] = set()
    for token in TOKEN_PATTERN.findall(normalized):
        if len(token) < 2:
            continue
        token = TOKEN_ALIASES.get(token, token)
        if token in STOP_WORDS or token in seen:
            continue
        seen.add(token)
        terms.append(token)
        if len(terms) == MAX_QUERY_TERMS:
            break

    if not terms:
        return None
    return " OR ".join(f'"{term}"' for term in terms)


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def assert_fts5_available(connection: sqlite3.Connection) -> None:
    """Fail with a useful error when the managed Python lacks FTS5."""

    try:
        connection.execute("CREATE VIRTUAL TABLE temp.fts5_probe USING fts5(value)")
        connection.execute("DROP TABLE temp.fts5_probe")
    except sqlite3.OperationalError as error:
        raise RetrievalError("This Python SQLite build does not provide FTS5.") from error


def _create_temporary_index_path(destination: Path) -> Path:
    """Reserve an unpredictable temporary file beside the active index."""

    handle, name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".rebuild",
        dir=destination.parent,
    )
    os.close(handle)
    return Path(name)


def _discard_temporary_index(temporary_path: Path) -> None:
    """Remove a temporary index and any SQLite sidecar file it produced."""

    for suffix in ("", "-journal", "-wal", "-shm"):
        with suppress(OSError):
            Path(f"{temporary_path}{suffix}").unlink(missing_ok=True)


def _write_index(
    database_path: Path,
    chunks: Sequence[ContentChunk],
    fingerprint: str,
) -> None:
    """Populate an empty database with deterministic, source-ID-ordered records."""

    with closing(_connect(database_path)) as connection, connection:
        assert_fts5_available(connection)
        connection.executescript(SCHEMA)
        for chunk in sorted(chunks, key=lambda item: item.source_id):
            values = (
                chunk.source_id,
                chunk.title,
                chunk.section,
                chunk.body,
                chunk.indexed_text,
                chunk.content_path,
            )
            connection.execute(
                "INSERT INTO content_chunks VALUES (?, ?, ?, ?, ?, ?)",
                values,
            )
            connection.execute(
                "INSERT INTO content_fts VALUES (?, ?, ?, ?)",
                (chunk.source_id, chunk.title, chunk.section, chunk.indexed_text),
            )
        connection.execute(
            "INSERT INTO index_metadata (key, value) VALUES ('corpus_fingerprint', ?)",
            (fingerprint,),
        )
        connection.execute(
            "INSERT INTO index_metadata (key, value) VALUES ('schema_version', ?)",
            (INDEX_SCHEMA_VERSION,),
        )


def _validate_index(database_path: Path, expected_records: int, fingerprint: str) -> None:
    """Refuse to publish an index that is corrupt, incomplete, or mislabeled."""

    with closing(_connect(database_path)) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        chunk_count = connection.execute("SELECT count(*) FROM content_chunks").fetchone()[0]
        fts_count = connection.execute("SELECT count(*) FROM content_fts").fetchone()[0]
        metadata = dict(connection.execute("SELECT key, value FROM index_metadata").fetchall())

    if integrity is None or str(integrity[0]) != "ok":
        raise RetrievalError("The rebuilt index failed its integrity check.")
    if int(chunk_count) != expected_records or int(fts_count) != expected_records:
        raise RetrievalError("The rebuilt index does not hold every approved section.")
    if metadata.get("corpus_fingerprint") != fingerprint:
        raise RetrievalError("The rebuilt index recorded an unexpected corpus fingerprint.")
    if metadata.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise RetrievalError("The rebuilt index recorded an unexpected schema version.")


def rebuild_index(database_path: Path, chunks: Sequence[ContentChunk]) -> str:
    """Publish a fully built index over the active one in a single atomic step."""

    database_path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = corpus_fingerprint(list(chunks))
    temporary_path = _create_temporary_index_path(database_path)

    try:
        _write_index(temporary_path, chunks, fingerprint)
        _validate_index(temporary_path, len(chunks), fingerprint)
        os.replace(temporary_path, database_path)
    except RetrievalError:
        _discard_temporary_index(temporary_path)
        raise
    except (sqlite3.Error, OSError) as error:
        _discard_temporary_index(temporary_path)
        raise RetrievalError("The approved-content index could not be rebuilt.") from error

    return fingerprint


def read_index_records(database_path: Path) -> list[tuple[str, str, str, str, str, str]]:
    """Read logical records in canonical order for deterministic rebuild tests."""

    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT source_id, title, section, body, indexed_text, content_path "
            "FROM content_chunks ORDER BY source_id"
        ).fetchall()
    return [
        (
            str(row[0]),
            str(row[1]),
            str(row[2]),
            str(row[3]),
            str(row[4]),
            str(row[5]),
        )
        for row in rows
    ]


class SQLiteRetriever:
    """Keep a local FTS5 index synchronized with the approved Markdown corpus."""

    def __init__(self, database_path: Path, content_dir: Path) -> None:
        self.database_path = database_path
        self.content_dir = content_dir
        self._index_lock = threading.Lock()

    def _stored_fingerprint(self) -> str | None:
        if not self.database_path.is_file():
            return None
        try:
            with closing(_connect(self.database_path)) as connection:
                metadata = dict(
                    connection.execute("SELECT key, value FROM index_metadata").fetchall()
                )
        except sqlite3.Error:
            return None
        if metadata.get("schema_version") != INDEX_SCHEMA_VERSION:
            return None
        fingerprint = metadata.get("corpus_fingerprint")
        return str(fingerprint) if fingerprint else None

    def ensure_index(self) -> None:
        try:
            chunks = load_approved_content(self.content_dir)
        except (ContentIngestionError, OSError) as error:
            raise RetrievalError("The approved content could not be loaded.") from error
        expected_fingerprint = corpus_fingerprint(chunks)
        if self._stored_fingerprint() == expected_fingerprint:
            return

        with self._index_lock:
            if self._stored_fingerprint() != expected_fingerprint:
                rebuild_index(self.database_path, chunks)

    def retrieve(self, question: str, limit: int) -> RetrievalResult:
        if limit < 1:
            raise ValueError("Retrieval limit must be positive.")
        query = build_fts_query(question)
        if query is None:
            return RetrievalResult(
                strategy="sqlite-fts5",
                score_kind="bm25",
                score_order="lower_is_better",
                evidence=[],
            )

        self.ensure_index()
        try:
            with closing(_connect(self.database_path)) as connection:
                rows = connection.execute(
                    """
                    SELECT
                        chunks.source_id,
                        chunks.title,
                        chunks.section,
                        chunks.body,
                        chunks.content_path,
                        bm25(content_fts, 0.0, 1.0, 2.0, 1.0) AS score
                    FROM content_fts
                    JOIN content_chunks AS chunks
                      ON chunks.source_id = content_fts.source_id
                    WHERE content_fts MATCH ?
                    ORDER BY score ASC, chunks.source_id ASC
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
        except sqlite3.Error as error:
            raise RetrievalError("The approved-content index could not be queried.") from error

        return RetrievalResult(
            strategy="sqlite-fts5",
            score_kind="bm25",
            score_order="lower_is_better",
            evidence=[
                RetrievedEvidence(
                    source=Source(
                        source_id=str(row["source_id"]),
                        title=str(row["title"]),
                        section=str(row["section"]),
                        excerpt=str(row["body"]),
                        content_path=str(row["content_path"]),
                    ),
                    rank=rank,
                    raw_score=float(row["score"]),
                )
                for rank, row in enumerate(rows, start=1)
            ],
        )
