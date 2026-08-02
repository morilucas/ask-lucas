"""Load reviewed Markdown into stable, provenance-preserving sections."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

HEADING_PATTERN = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
TITLE_PATTERN = re.compile(r"^#[ \t]+(.+?)[ \t]*$", re.MULTILINE)
DEFAULT_EXCLUDED_SOURCE_IDS = frozenset({"profile:explicit-exclusions"})


class ContentIngestionError(ValueError):
    """Raised when approved content cannot produce an unambiguous corpus."""


@dataclass(frozen=True, slots=True)
class ContentChunk:
    """One approved level-two Markdown section."""

    source_id: str
    title: str
    section: str
    body: str
    indexed_text: str
    content_path: str


def heading_slug(heading: str) -> str:
    """Create the canonical lowercase ASCII slug defined by the feature spec."""

    normalized = unicodedata.normalize("NFKD", heading)
    separated = "".join(
        "-"
        if character.isspace() or unicodedata.category(character) == "Pd" or character in {"_", "/"}
        else character
        for character in normalized
        if not unicodedata.combining(character)
    )
    ascii_text = separated.encode("ascii", "ignore").decode("ascii").lower()
    punctuation_removed = re.sub(r"[^a-z0-9-]", "", ascii_text)
    return re.sub(r"-+", "-", punctuation_removed).strip("-")


def load_approved_content(
    content_dir: Path,
    *,
    excluded_source_ids: frozenset[str] = DEFAULT_EXCLUDED_SOURCE_IDS,
) -> list[ContentChunk]:
    """Load only direct ``*.md`` children of the approved content directory."""

    if not content_dir.is_dir():
        raise ContentIngestionError(f"Approved content directory does not exist: {content_dir}")

    chunks: list[ContentChunk] = []
    seen_ids: set[str] = set()

    for path in sorted(content_dir.glob("*.md"), key=lambda candidate: candidate.name.casefold()):
        document = path.read_text(encoding="utf-8")
        title_match = TITLE_PATTERN.search(document)
        title = title_match.group(1).strip() if title_match else path.stem.replace("-", " ").title()
        matches = list(HEADING_PATTERN.finditer(document))

        for index, match in enumerate(matches):
            section = match.group(1).strip()
            slug = heading_slug(section)
            if not slug:
                raise ContentIngestionError(f"Heading cannot produce a source ID: {path.name}")

            source_id = f"{path.stem.casefold()}:{slug}"
            if source_id in excluded_source_ids:
                continue
            if source_id in seen_ids:
                raise ContentIngestionError(f"Duplicate canonical source ID: {source_id}")

            body_start = match.end()
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
            body = document[body_start:body_end].strip()
            if not body:
                continue

            seen_ids.add(source_id)
            chunks.append(
                ContentChunk(
                    source_id=source_id,
                    title=title,
                    section=section,
                    body=body,
                    indexed_text=f"{section}\n\n{body}",
                    content_path=f"content/{path.name}",
                )
            )

    return sorted(chunks, key=lambda chunk: chunk.source_id)


def redact_content_paths(message: str, content_dir: Path) -> str:
    """Remove approved-content locations from operator-facing text."""

    candidates = {str(content_dir), str(Path(content_dir).expanduser().resolve())}
    redacted = message
    for candidate in sorted(candidates, key=len, reverse=True):
        redacted = redacted.replace(candidate, "<content-dir>")
    return redacted


def corpus_fingerprint(chunks: list[ContentChunk]) -> str:
    """Return a stable digest of the exact logical records in an index."""

    serialized = json.dumps(
        [asdict(chunk) for chunk in chunks],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
