"""Report safe corpus metadata for the approved content directory.

This command never opens the index and never prints titles, section headings,
excerpts, bodies, or the absolute location of the approved content.
"""

import sys

from ask_lucas.config import get_settings
from ask_lucas.ingestion import (
    ContentIngestionError,
    corpus_fingerprint,
    load_approved_content,
    redact_content_paths,
)


def main() -> None:
    settings = get_settings()
    try:
        chunks = load_approved_content(settings.content_dir)
    except (ContentIngestionError, OSError) as error:
        detail = redact_content_paths(str(error), settings.content_dir)
        print(f"Approved content is not valid: {detail}", file=sys.stderr)
        raise SystemExit(1) from error

    print(f"Approved sections: {len(chunks)}")
    for source_id in sorted(chunk.source_id for chunk in chunks):
        print(f"  {source_id}")
    print(f"Corpus fingerprint: {corpus_fingerprint(chunks)}")


if __name__ == "__main__":
    main()
