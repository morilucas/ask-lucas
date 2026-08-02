"""SQLite FTS5 rebuild, atomic-replacement, query-safety, and ranking tests."""

import os
import sqlite3
import threading
from pathlib import Path

import pytest

from ask_lucas import retrieval
from ask_lucas.ingestion import ContentChunk, corpus_fingerprint, load_approved_content
from ask_lucas.retrieval import (
    RetrievalError,
    SQLiteRetriever,
    build_fts_query,
    read_index_records,
    rebuild_index,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
APPROVED_CONTENT = REPOSITORY_ROOT / "examples" / "content"
EXAMPLE_SOURCE_ID = "experience:acme-ai-data-engineer"


def make_chunk(source_id: str, body: str) -> ContentChunk:
    section = source_id.split(":", 1)[-1]
    return ContentChunk(
        source_id=source_id,
        title="Profile",
        section=section,
        body=body,
        indexed_text=f"{section}\n\n{body}",
        content_path="content/profile.md",
    )


def stored_metadata(database_path: Path) -> dict[str, str]:
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute("SELECT key, value FROM index_metadata").fetchall()
    finally:
        connection.close()
    return {str(key): str(value) for key, value in rows}


def test_query_builder_emits_only_quoted_literal_terms() -> None:
    query = build_fts_query('" OR secret* NEAR(data) --')

    assert query == '"secret" OR "near" OR "data"'
    assert build_fts_query("what about Lucas and the") is None
    assert build_fts_query("café café") == '"café"'


def test_two_rebuilds_produce_identical_logical_records(tmp_path: Path) -> None:
    database_path = tmp_path / "content.db"
    chunks = load_approved_content(APPROVED_CONTENT)

    first_fingerprint = rebuild_index(database_path, chunks)
    first_records = read_index_records(database_path)
    first_metadata = stored_metadata(database_path)
    second_fingerprint = rebuild_index(database_path, chunks)
    second_records = read_index_records(database_path)

    assert first_fingerprint == second_fingerprint == corpus_fingerprint(chunks)
    assert first_records == second_records
    assert first_metadata == stored_metadata(database_path)
    assert first_metadata["corpus_fingerprint"] == first_fingerprint
    assert len(first_records) == len(chunks)


def test_successful_rebuild_atomically_replaces_the_active_index(tmp_path: Path) -> None:
    database_path = tmp_path / "content.db"
    first_fingerprint = rebuild_index(database_path, [make_chunk("profile:first", "Alpha.")])
    replaced_inode = database_path.stat().st_ino

    second_fingerprint = rebuild_index(database_path, [make_chunk("profile:second", "Beta.")])

    assert second_fingerprint != first_fingerprint
    assert [record[0] for record in read_index_records(database_path)] == ["profile:second"]
    assert stored_metadata(database_path)["corpus_fingerprint"] == second_fingerprint
    assert database_path.stat().st_ino != replaced_inode
    assert sorted(path.name for path in tmp_path.iterdir()) == ["content.db"]


def read_source_ids(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT source_id FROM content_chunks").fetchall()
    return [str(row[0]) for row in rows]


def test_replacing_the_index_under_an_open_reader_follows_platform_rules(tmp_path: Path) -> None:
    """POSIX replaces beneath an open reader; Windows refuses until that reader closes."""

    database_path = tmp_path / "content.db"
    rebuild_index(database_path, [make_chunk("profile:first", "Alpha.")])
    replacement = [make_chunk("profile:second", "Beta.")]
    reader = sqlite3.connect(database_path)
    try:
        assert read_source_ids(reader) == ["profile:first"]

        if os.name == "nt":
            # Windows refuses to rename over a file another handle still holds open.
            with pytest.raises(RetrievalError):
                rebuild_index(database_path, replacement)

            assert read_source_ids(reader) == ["profile:first"]
            assert [record[0] for record in read_index_records(database_path)] == ["profile:first"]
            assert sorted(path.name for path in tmp_path.iterdir()) == ["content.db"]
        else:
            rebuild_index(database_path, replacement)

            # The open handle keeps serving the file it opened, not the published one.
            assert read_source_ids(reader) == ["profile:first"]
            assert [record[0] for record in read_index_records(database_path)] == ["profile:second"]
    finally:
        reader.close()

    if os.name == "nt":
        # Retrying the same rebuild succeeds once the reader has released the file.
        rebuild_index(database_path, replacement)

    assert [record[0] for record in read_index_records(database_path)] == ["profile:second"]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["content.db"]


def raise_validation_error(database_path: Path, expected_records: int, fingerprint: str) -> None:
    raise RetrievalError("Injected validation failure.")


def raise_replacement_error(source: object, destination: object) -> None:
    raise OSError("Injected replacement failure.")


@pytest.mark.parametrize("failing_stage", ["schema", "insertion", "validation", "replacement"])
def test_a_failed_rebuild_preserves_the_previous_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failing_stage: str,
) -> None:
    database_path = tmp_path / "content.db"
    previous_fingerprint = rebuild_index(database_path, [make_chunk("profile:first", "Alpha.")])
    replacement = [make_chunk("profile:second", "Beta.")]

    if failing_stage == "schema":
        monkeypatch.setattr(retrieval, "SCHEMA", "CREATE TABLE content_chunks (")
    elif failing_stage == "insertion":
        replacement = [
            make_chunk("profile:second", "Beta."),
            make_chunk("profile:second", "Gamma."),
        ]
    elif failing_stage == "validation":
        monkeypatch.setattr(retrieval, "_validate_index", raise_validation_error)
    else:
        monkeypatch.setattr(os, "replace", raise_replacement_error)

    with pytest.raises(RetrievalError):
        rebuild_index(database_path, replacement)

    assert [record[0] for record in read_index_records(database_path)] == ["profile:first"]
    assert stored_metadata(database_path)["corpus_fingerprint"] == previous_fingerprint
    assert sorted(path.name for path in tmp_path.iterdir()) == ["content.db"]


def test_concurrent_rebuilds_never_share_a_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "content.db"
    chunks = load_approved_content(APPROVED_CONTENT)
    create_temporary_index_path = retrieval._create_temporary_index_path
    observed: list[Path] = []
    guard = threading.Lock()

    def record_temporary_path(destination: Path) -> Path:
        temporary_path = create_temporary_index_path(destination)
        with guard:
            observed.append(temporary_path)
        return temporary_path

    monkeypatch.setattr(retrieval, "_create_temporary_index_path", record_temporary_path)
    failures: list[Exception] = []

    def rebuild() -> None:
        try:
            rebuild_index(database_path, chunks)
        except Exception as error:
            with guard:
                failures.append(error)

    workers = [threading.Thread(target=rebuild) for _ in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert failures == []
    assert len(observed) == 4
    assert len(set(observed)) == 4
    assert read_index_records(database_path) == [
        (
            chunk.source_id,
            chunk.title,
            chunk.section,
            chunk.body,
            chunk.indexed_text,
            chunk.content_path,
        )
        for chunk in chunks
    ]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["content.db"]


def test_retriever_returns_ranked_bm25_evidence_for_showcase_question(tmp_path: Path) -> None:
    retriever = SQLiteRetriever(tmp_path / "content.db", APPROVED_CONTENT)

    result = retriever.retrieve("What AI and data systems has Lucas built?", limit=3)
    evidence = result.evidence

    assert result.strategy == "sqlite-fts5"
    assert result.score_kind == "bm25"
    assert result.score_order == "lower_is_better"
    assert evidence
    assert EXAMPLE_SOURCE_ID in {item.source.source_id for item in evidence}
    assert [item.rank for item in evidence] == list(range(1, len(evidence) + 1))
    assert all(isinstance(item.raw_score, float) for item in evidence)
    assert len(evidence) <= 3


def test_retriever_returns_no_hits_for_unsupported_terms(tmp_path: Path) -> None:
    retriever = SQLiteRetriever(tmp_path / "content.db", APPROVED_CONTENT)

    assert retriever.retrieve("What is Lucas's favorite movie?", limit=3).evidence == []


def test_retrieval_limit_is_enforced(tmp_path: Path) -> None:
    retriever = SQLiteRetriever(tmp_path / "content.db", APPROVED_CONTENT)

    evidence = retriever.retrieve("Python SQL data", limit=1).evidence

    assert len(evidence) == 1
    assert evidence[0].rank == 1


def test_adversarial_fts_syntax_is_safe_and_deterministic(tmp_path: Path) -> None:
    retriever = SQLiteRetriever(tmp_path / "content.db", APPROVED_CONTENT)
    question = '" OR * NEAR(data) NOT (sql) column:secret --'

    first = retriever.retrieve(question, limit=3).evidence
    second = retriever.retrieve(question, limit=3).evidence

    assert [(item.source.source_id, item.raw_score) for item in first] == [
        (item.source.source_id, item.raw_score) for item in second
    ]


def test_retriever_rebuilds_when_approved_content_changes(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    document_path = content_dir / "profile.md"
    document_path.write_text("# Profile\n\n## First\n\nAlpha evidence.\n", encoding="utf-8")
    retriever = SQLiteRetriever(tmp_path / "content.db", content_dir)

    assert retriever.retrieve("alpha", limit=3).evidence[0].source.source_id == "profile:first"
    document_path.write_text("# Profile\n\n## Second\n\nBeta evidence.\n", encoding="utf-8")

    assert retriever.retrieve("alpha", limit=3).evidence == []
    assert retriever.retrieve("beta", limit=3).evidence[0].source.source_id == "profile:second"
