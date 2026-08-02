# Content operations

Status: Implemented locally
Last updated: 2026-08-02

This document describes how the approved content directory is validated and how the lexical index is
refreshed. Both commands are operational tools for Lucas. They are not part of the public API and
they never expose approved content to a visitor.

Both commands read their locations from environment configuration (`ASK_LUCAS_CONTENT_DIR` and
`ASK_LUCAS_INDEX_PATH`), so the same command text works against synthetic examples, a private local
checkout, and the mounted production content.

## Validate approved content

```powershell
cd apps/api
uv run python scripts/validate_content.py
```

Validation parses the configured directory exactly as ingestion does and then stops. It never opens,
creates, or replaces the index, so it is safe to run against production content at any time.

A successful run prints only:

- `Approved sections: <count>` — how many level-two sections were accepted
- One indented stable source ID per section, in sorted order, such as `profile:working-style`
- `Corpus fingerprint: <digest>` — the digest of the exact logical records ingestion produced

It intentionally omits everything else: document titles, section headings, bodies, excerpts, file
names, and the configured or resolved location of the content directory.

When content is invalid the command writes `Approved content is not valid: <reason>` to standard
error and exits with status 1. The reason keeps the diagnostic fact that identifies the problem —
for example `Duplicate canonical source ID: profile:fpa` — but any approved-content location inside
it is replaced with the literal placeholder `<content-dir>`.

## Refresh the index

```powershell
cd apps/api
uv run python scripts/rebuild_index.py
```

A successful run prints only:

- `Indexed <count> approved sections as <file name>` — the index file name, never its directory
- `Corpus fingerprint: <digest>` — the same digest validation reports, so the two commands can be
  compared without inspecting either the content or the database

As with validation, no title, heading, body, excerpt, or content location is printed.

## Atomic build and replacement

A refresh never edits the active index in place. Each run:

1. Reserves a uniquely named temporary file in the **destination directory** — the same directory as
   the configured index — so the finished database and the active one always share a filesystem and
   replacement is a plain rename rather than a copy.
2. Creates the schema and inserts every approved section into that temporary database, ordered by
   stable source ID, together with the corpus fingerprint and the index schema version.
3. Validates the temporary database before publishing it: a SQLite integrity check, a record count
   in both the content table and the full-text table that matches the number of approved sections,
   and the expected fingerprint and schema version.
4. Replaces the active index with the validated temporary file in a single atomic step.

Because each run reserves its own temporary name, concurrent refreshes cannot write over each
other's partial work, and readers never observe a half-written database.

How step 4 behaves when something already has the index open depends on the platform:

- **Linux, including the deployed container.** The replacement succeeds even while the API is
  serving. A process that already had the previous index open continues reading the file it opened
  until it reopens; every connection opened after the replacement sees the new index.
- **Windows, used for local development.** The operating system refuses to rename over a file that
  another process still holds open, so the refresh fails with `The index was not replaced: <reason>`
  while a reader is active. Close whatever has the index open — a running API process or a SQLite
  browser — and run the command again.

The API applies the same procedure when it detects a changed corpus fingerprint during a request, so
an automatic refresh is as safe as an explicit one.

## Failure preserves the last valid index

If ingestion, the build, the validation step, or the replacement itself fails, the active index is
left exactly as it was. The partial database and any SQLite sidecar files it produced are removed,
so the destination directory is left holding only the last index that passed validation. That holds
for a replacement Windows blocks because a reader is open: the previous index stays readable and no
temporary file is left behind, so retrying after the reader closes is the whole recovery.

The command writes `The index was not replaced: <reason>` to standard error and exits with status 1.
Content locations in that message are redacted the same way validation redacts them. Because a
failed refresh changes nothing, the running API keeps answering from the previous index and the
correct recovery is to fix the content and run the command again.

## Local example

Point both variables at a local checkout, then validate before refreshing:

```powershell
cd apps/api
$env:ASK_LUCAS_CONTENT_DIR = "<your-content-checkout>/content"
$env:ASK_LUCAS_INDEX_PATH = "data/content.db"
uv run python scripts/validate_content.py
uv run python scripts/rebuild_index.py
```

The same values can live in the untracked `apps/api/.env` file instead. With no configuration at
all, both commands use the synthetic corpus under `examples/content/`, which is the correct way to
rehearse the workflow before touching private material.

## Container example

The deployed Compose service already supplies the content directory and index path through
environment configuration, and mounts the private content read-only. The published API image ships
the application package but not `scripts/`, so a one-off container mounts them read-only and reuses
the service's environment and index volume:

```bash
docker compose --env-file <code-checkout>/deploy/.env \
  -f <code-checkout>/deploy/compose.yml \
  --project-directory <code-checkout>/deploy \
  run --rm -v <code-checkout>/apps/api/scripts:/app/scripts:ro \
  api python /app/scripts/validate_content.py
```

Swap `validate_content.py` for `rebuild_index.py` to publish the index into the same `/data` volume
the running API reads. Validate first: a validation failure costs nothing, and a refresh that fails
leaves the previous index in place either way.

## Related but separate concerns

These commands only read a directory and publish an index. They deliberately do not:

- **Synchronize Git.** Pulling or checking out the private content repository happens before these
  commands run and is not triggered by them.
- **Handle credentials.** No deploy key, API key, or other secret is read, printed, or required.
- **Deploy.** Building images, starting containers, and reloading the reverse proxy are described in
  [`deploy/README.md`](../deploy/README.md).
- **Author or approve content.** What belongs in the approved corpus is an editorial decision
  recorded with the private content, as described in [`content/README.md`](../content/README.md) and
  governed by [`docs/constitution.md`](constitution.md).
