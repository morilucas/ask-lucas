# Feature 003: Public endpoint production safety

Status: Approved for implementation
Date: 2026-08-02

## User value

Employers can use the public assistant reliably while Lucas can expose a paid model without allowing
one visitor, a traffic burst, or a provider failure loop to create unbounded cost.

## In scope

- Per-client rolling request limits on answer endpoints
- A global nonblocking live-generation concurrency limit
- A restart-safe UTC-day live-generation attempt ceiling
- Retry hints in the API contract and calm, specific browser error states
- Structured operational logs without conversation content or visitor identifiers
- Provider calls outside the async server event loop

## Out of scope

- Redis, a hosted rate-limit service, or multiple API replicas
- User accounts, CAPTCHA, browser fingerprinting, or persistent visitor identifiers
- Conversation analytics or raw prompt logging
- Exact token-cost accounting
- Replacing provider-side workspace budget controls

## Acceptance criteria

1. A client exceeding the rolling window receives HTTP 429, a `Retry-After` header, a trace ID,
   and a useful retry message.
2. More simultaneous paid generations than configured fail quickly without entering the provider.
3. The daily ceiling persists across application restarts and counts attempted paid calls.
4. Evidence-free abstentions do not consume the daily paid-generation ceiling.
5. Public errors never expose provider exceptions, prompts, credentials, or private content.
6. Answer telemetry records only route, trace ID, outcome, status, provider/model, and duration.
7. The browser preserves the question and shows retry only when the error is retryable.
8. Backend tests, strict typing, frontend lint/type checks, and the production build pass.

## Default limits

- 12 answer requests per client per rolling 60 seconds
- 2 simultaneous live generations
- 100 live generation attempts per UTC day

All limits are environment-configurable. The defaults favor a usable interview conversation while
bounding a small portfolio project's exposure.
