# ADR 0004: separate public code from private content

Status: Accepted

Date: 2026-08-01

## Context

The application code should be inspectable by employers, while the reviewed biography, exact deterministic answers, operational inventory, and evaluation cases need a narrower access boundary. Removing raw source documents is insufficient if curated personal facts still remain in public Git history.

## Decision

Maintain two repositories:

- a public code repository containing synthetic fixtures and no production biography;
- a private content repository containing reviewed Markdown, answer fixtures, evaluation cases, and private operating notes.

The VPS checks out both repositories. Docker Compose mounts the private checkout read-only into the API container and supplies every path through environment variables. The web container cannot mount the private repository. Neither application container publishes a host port; the existing Caddy service is the only ingress.

The first deployment runs both web and API containers on the VPS. This supersedes the deployment split proposed in ADR 0002 for the current milestone and avoids cross-origin configuration while the system is small.

## Consequences

- The public repository can be shared without exposing the production corpus or its Git history.
- Local contributors can run the complete contract using fictional examples without private access.
- Production deploys must update two compatible revisions and keep private deploy credentials on the VPS.
- A repository being private is an access control, not permission to store credentials or raw unreviewed exports.
