"""Content-operation command tests for safe output and preserved indexes."""

import os
import subprocess
import sys
from pathlib import Path

from ask_lucas.ingestion import corpus_fingerprint, load_approved_content
from ask_lucas.retrieval import read_index_records

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PRIVATE_TITLE = "Confidential Portfolio Dossier"
PRIVATE_SECTION = "Acmé — AI & Data Engineer"
PRIVATE_BODY = "Lucas earned a zorbulant retention lift for the internal forecasting platform."


def write_private_corpus(tmp_path: Path) -> Path:
    content_dir = tmp_path / "private-content"
    content_dir.mkdir()
    (content_dir / "experience.md").write_text(
        f"# {PRIVATE_TITLE}\n\n## {PRIVATE_SECTION}\n\n{PRIVATE_BODY}\n",
        encoding="utf-8",
    )
    (content_dir / "profile.md").write_text(
        "# Approved profile\n\n## Working style\n\nCollaborative and measured.\n",
        encoding="utf-8",
    )
    return content_dir


def run_script(name: str, content_dir: Path, index_path: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["ASK_LUCAS_CONTENT_DIR"] = str(content_dir)
    environment["ASK_LUCAS_INDEX_PATH"] = str(index_path)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def test_validation_prints_only_safe_corpus_metadata(tmp_path: Path) -> None:
    content_dir = write_private_corpus(tmp_path)
    index_path = tmp_path / "data" / "content.db"

    result = run_script("validate_content.py", content_dir, index_path)
    output = result.stdout + result.stderr

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "Approved sections: 2",
        "  experience:acme-ai-data-engineer",
        "  profile:working-style",
        f"Corpus fingerprint: {corpus_fingerprint(load_approved_content(content_dir))}",
    ]
    assert PRIVATE_BODY not in output
    assert "zorbulant" not in output
    assert PRIVATE_TITLE not in output
    assert PRIVATE_SECTION not in output
    assert str(content_dir) not in output
    assert not index_path.exists()


def test_validation_reports_invalid_content_without_revealing_its_location(tmp_path: Path) -> None:
    content_dir = tmp_path / "private-content"
    content_dir.mkdir()
    (content_dir / "profile.md").write_text(
        "# Profile\n\n## FP&A\n\nFirst.\n\n## FPA\n\nSecond.\n",
        encoding="utf-8",
    )

    missing = run_script("validate_content.py", tmp_path / "absent", tmp_path / "content.db")
    duplicated = run_script("validate_content.py", content_dir, tmp_path / "content.db")

    assert missing.returncode == 1
    assert "<content-dir>" in missing.stderr
    assert str(tmp_path) not in missing.stdout + missing.stderr
    assert duplicated.returncode == 1
    assert "Duplicate canonical source ID: profile:fpa" in duplicated.stderr
    assert str(tmp_path) not in duplicated.stdout + duplicated.stderr


def test_rebuild_publishes_the_index_and_prints_only_safe_metadata(tmp_path: Path) -> None:
    content_dir = write_private_corpus(tmp_path)
    index_path = tmp_path / "data" / "content.db"

    result = run_script("rebuild_index.py", content_dir, index_path)
    output = result.stdout + result.stderr

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "Indexed 2 approved sections as content.db",
        f"Corpus fingerprint: {corpus_fingerprint(load_approved_content(content_dir))}",
    ]
    assert PRIVATE_BODY not in output
    assert PRIVATE_TITLE not in output
    assert str(content_dir) not in output
    assert [record[0] for record in read_index_records(index_path)] == [
        "experience:acme-ai-data-engineer",
        "profile:working-style",
    ]
    assert sorted(path.name for path in index_path.parent.iterdir()) == ["content.db"]


def test_rebuild_keeps_the_previous_index_when_content_is_invalid(tmp_path: Path) -> None:
    content_dir = write_private_corpus(tmp_path)
    index_path = tmp_path / "data" / "content.db"
    assert run_script("rebuild_index.py", content_dir, index_path).returncode == 0
    (content_dir / "profile.md").write_text(
        "# Profile\n\n## FP&A\n\nFirst.\n\n## FPA\n\nSecond.\n",
        encoding="utf-8",
    )

    result = run_script("rebuild_index.py", content_dir, index_path)

    assert result.returncode == 1
    assert "The index was not replaced" in result.stderr
    assert str(content_dir) not in result.stdout + result.stderr
    assert [record[0] for record in read_index_records(index_path)] == [
        "experience:acme-ai-data-engineer",
        "profile:working-style",
    ]
    assert sorted(path.name for path in index_path.parent.iterdir()) == ["content.db"]
