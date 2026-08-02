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
3. Run:

```bash
docker compose --env-file /opt/ask-lucas/code/deploy/.env \
  -f /opt/ask-lucas/code/deploy/compose.yml \
  --project-directory /opt/ask-lucas/code/deploy \
  up -d --build --remove-orphans
```

4. Add the block in `Caddyfile.example` to the existing Caddyfile, validate it, and reload Caddy.
5. Check `https://ask.lkmori.com/api/health`, then exercise a grounded and unsupported question in the browser.

## Rollback

Check out the previous public-code commit, leave the compatible private content revision in place, and rerun the Compose command. The index is regenerated when its content fingerprint changes.
