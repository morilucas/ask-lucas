"""SQLite FTS5 rebuild, query-safety, and ranking tests."""

from pathlib import Path

from ask_lucas.ingestion import load_approved_content
from ask_lucas.retrieval import (
    SQLiteRetriever,
    build_fts_query,
    read_index_records,
    rebuild_index,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
APPROVED_CONTENT = REPOSITORY_ROOT / "examples" / "content"
EXAMPLE_SOURCE_ID = "experience:acme-ai-data-engineer"


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
    second_fingerprint = rebuild_index(database_path, chunks)
    second_records = read_index_records(database_path)

    assert first_fingerprint == second_fingerprint
    assert first_records == second_records
    assert len(first_records) == len(chunks)


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
