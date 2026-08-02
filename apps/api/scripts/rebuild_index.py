"""Rebuild the deterministic approved-content SQLite index.

The active index is replaced only after a complete temporary index is built and
validated, so a failed run leaves the previous index in place.
"""

import sys

from ask_lucas.config import get_settings
from ask_lucas.ingestion import (
    ContentIngestionError,
    load_approved_content,
    redact_content_paths,
)
from ask_lucas.retrieval import RetrievalError, rebuild_index


def main() -> None:
    settings = get_settings()
    try:
        chunks = load_approved_content(settings.content_dir)
        fingerprint = rebuild_index(settings.index_path, chunks)
    except (ContentIngestionError, RetrievalError, OSError) as error:
        detail = redact_content_paths(str(error), settings.content_dir)
        print(f"The index was not replaced: {detail}", file=sys.stderr)
        raise SystemExit(1) from error

    print(f"Indexed {len(chunks)} approved sections as {settings.index_path.name}")
    print(f"Corpus fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()
