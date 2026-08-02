# ADR 0006: Use local guards for single-instance model access

Status: Accepted
Date: 2026-08-02

## Context

The public assistant now calls a paid model from one FastAPI container. It needs abuse and cost
controls, but the current traffic and deployment do not justify another hosted service.

## Decision

Use an in-memory rolling limiter for per-client requests, a process-local semaphore for concurrent
live generations, and a small SQLite ledger in the existing persistent data volume for the UTC-day
generation ceiling. Trust forwarded addresses only when the direct peer belongs to an explicitly
configured proxy network. Keep visitor addresses out of persistent storage and logs.

## Alternatives considered

- Redis or a hosted edge limiter would coordinate multiple replicas, but adds cost and operational
  surface before the application has multi-replica traffic.
- A memory-only daily counter is simpler but resets on every deployment and is not a reliable cost
  circuit breaker.
- Provider spend controls alone cap money at the vendor, but cannot create a useful application
  response or protect local capacity.

## Consequences

The design is inexpensive, inspectable, and restart-safe for one API process. Per-client and
concurrency state do not coordinate across replicas, so moving to multiple API instances requires a
shared limiter. The SQLite ledger counts attempts rather than exact cost, intentionally failing
toward a conservative bound.
