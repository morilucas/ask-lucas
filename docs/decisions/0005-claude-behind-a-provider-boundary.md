# ADR 0005: Claude behind a provider boundary

Status: Accepted
Date: 2026-08-01

## Context

The deterministic vertical slice proved retrieval, citations, and abstention, but it could not produce natural grounded follow-up answers. Lucas has Anthropic API credits and wants the portfolio to demonstrate a real model integration without making paid access mandatory for local development.

## Decision

- Keep generation behind the existing `AnswerProvider` protocol.
- Add Anthropic's official Python SDK as the only provider-specific runtime dependency.
- Use Claude's structured-output helper with the provider-neutral Pydantic result schema.
- Default to `claude-haiku-4-5` for its current cost and latency profile; keep the model configurable.
- Select Claude automatically when an Anthropic key exists.
- Retain a deterministic grounded extractive provider when no key exists.
- Store the production key only in the ignored VPS deployment environment file.

## Alternatives considered

- Direct HTTP calls would avoid an SDK, but would duplicate authentication, error handling, and structured-output request details.
- A higher-capability Claude model may improve synthesis, but costs more before evaluation demonstrates a need.
- Removing the no-key path would make learning, CI, and public-repository verification depend on paid credentials.

## Consequences

The application demonstrates a real Claude integration while remaining inexpensive and locally reproducible. Vendor-specific code is confined to one adapter. Model quality, latency, and cost still need a versioned evaluation before changing the default.
