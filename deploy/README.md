# VPS deployment

The public code and private content are separate Git repositories. On the server they are checked out as siblings:

```text
/opt/ask-lucas/
  code/       # public morilucas/ask-lucas
  private/    # private morilucas/ask-lucas-content
```

The Compose project mounts `private/` read-only into the API container. The browser never receives the files directly; it receives only API answers and cited excerpts. The SQLite index lives in a Docker volume and neither container publishes a host port. Both join the existing `stack_stack` network so the VPS Caddy instance is the only public ingress.

## Deploy or update

1. Pull both repositories with read-only deploy credentials.
2. Copy `deploy/.env.example` to `deploy/.env`, set the build version, and add
   `ASK_LUCAS_ANTHROPIC_API_KEY`. This file stays only on the VPS and is ignored by Git.
   Keep the documented request, concurrency, and daily-generation limits unless a measured
   traffic pattern justifies changing them. The daily counter persists in `/data/runtime.db`.
3. Run:

```bash
docker compose --env-file /opt/ask-lucas/code/deploy/.env \
  -f /opt/ask-lucas/code/deploy/compose.yml \
  --project-directory /opt/ask-lucas/code/deploy \
  up -d --build --remove-orphans
```

4. Add the block in `Caddyfile.example` to the existing Caddyfile, validate it, and reload Caddy.
5. Check `https://ask.lkmori.com/api/health`, then exercise a grounded and unsupported question in the browser.

## Public endpoint safeguards

- A client may make 12 answer requests per rolling minute by default.
- At most two live Claude generations run at once; excess work fails quickly with a retry hint.
- At most 100 live generation attempts are reserved per UTC day, including provider failures that
  may already have incurred cost. Evidence-free abstentions do not use this budget.
- Forwarded client addresses are accepted only from configured proxy networks and remain in memory.
- Structured answer logs include the trace ID, route, status, outcome, provider mode, model, and
  duration. They do not include questions, answers, visitor addresses, prompts, or evidence.

These application controls complement, rather than replace, a provider-side workspace spend limit.

## Rollback

Check out the previous public-code commit, leave the compatible private content revision in place, and rerun the Compose command. The index is regenerated when its content fingerprint changes.
