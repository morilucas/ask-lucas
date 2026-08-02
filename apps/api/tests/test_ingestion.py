"""Approved Markdown parsing and canonical source-ID tests."""

from pathlib import Path

import pytest

from ask_lucas.ingestion import (
    ContentIngestionError,
    corpus_fingerprint,
    heading_slug,
    load_approved_content,
    redact_content_paths,
)


def write_markdown(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_heading_slug_follows_canonical_normalization() -> None:
    assert heading_slug("Acmé — AI & Data / Engineer") == "acme-ai-data-engineer"
    assert heading_slug("FP&A") == "fpa"


def test_loader_indexes_only_direct_nonempty_level_two_markdown_sections(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    write_markdown(
        content_dir / "profile.md",
        """# Approved profile

Root prose must not be indexed.

## Public section

Approved body.

## Empty section

## Explicit exclusions

Private instructions.
""",
    )
    (content_dir / "resume.pdf").write_bytes(b"not a real PDF")
    nested = content_dir / "nested"
    nested.mkdir()
    write_markdown(nested / "private.md", "# Private\n\n## Hidden\n\nDo not load.")

    chunks = load_approved_content(content_dir)

    assert [chunk.source_id for chunk in chunks] == ["profile:public-section"]
    assert chunks[0].body == "Approved body."
    assert chunks[0].indexed_text == "Public section\n\nApproved body."
    assert chunks[0].content_path == "content/profile.md"


def test_duplicate_canonical_ids_fail_instead_of_receiving_suffixes(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    write_markdown(
        content_dir / "profile.md",
        "# Profile\n\n## FP&A\n\nFirst.\n\n## FPA\n\nSecond.\n",
    )

    with pytest.raises(ContentIngestionError, match="Duplicate canonical source ID"):
        load_approved_content(content_dir)


def test_source_ids_are_stable_when_unrelated_body_text_changes(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    document_path = content_dir / "projects.md"
    write_markdown(document_path, "# Projects\n\n## Retrieval demo\n\nVersion one.\n")
    first = load_approved_content(content_dir)

    write_markdown(document_path, "# Projects\n\n## Retrieval demo\n\nVersion two.\n")
    second = load_approved_content(content_dir)

    assert first[0].source_id == second[0].source_id == "projects:retrieval-demo"
    assert corpus_fingerprint(first) != corpus_fingerprint(second)


def test_missing_content_directory_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ContentIngestionError, match="does not exist"):
        load_approved_content(tmp_path / "missing")


def test_editorial_control_sections_never_enter_the_corpus(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    write_markdown(
        content_dir / "profile.md",
        "# Profile\n\n## Public positioning\n\nApproved.\n\n"
        "## Explicit exclusions\n\nPrivate boundary instructions.\n",
    )
    write_markdown(
        content_dir / "projects.md",
        "# Projects\n\n## Public project\n\nApproved evidence.\n\n"
        "## Evidence gaps to resolve\n\nInternal editorial checklist.\n",
    )

    chunks = load_approved_content(content_dir)

    assert [chunk.source_id for chunk in chunks] == [
        "profile:public-positioning",
        "projects:public-project",
    ]


def test_redaction_removes_configured_and_resolved_content_locations(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    unresolved_dir = tmp_path / "link" / ".." / "content"
    message = f"Approved content directory does not exist: {content_dir}"

    assert redact_content_paths(message, content_dir) == (
        "Approved content directory does not exist: <content-dir>"
    )
    assert str(tmp_path) not in redact_content_paths(f"read {content_dir}/profile.md", content_dir)
    assert str(tmp_path) not in redact_content_paths(message, unresolved_dir)
    assert redact_content_paths("Duplicate canonical source ID: a:b", content_dir) == (
        "Duplicate canonical source ID: a:b"
    )
