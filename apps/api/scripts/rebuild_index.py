"""Rebuild the deterministic approved-content SQLite index."""

from ask_lucas.config import get_settings
from ask_lucas.ingestion import load_approved_content
from ask_lucas.retrieval import rebuild_index


def main() -> None:
    settings = get_settings()
    chunks = load_approved_content(settings.content_dir)
    fingerprint = rebuild_index(settings.index_path, chunks)
    print(f"Indexed {len(chunks)} approved sections at {settings.index_path}")
    print(f"Corpus fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()
