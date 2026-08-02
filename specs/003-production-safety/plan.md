# Plan 003: Public endpoint production safety

1. Add a memory-only rolling client limiter with trusted-proxy address handling.
2. Wrap only the live provider with a nonblocking semaphore and persistent SQLite daily ledger.
3. Run synchronous retrieval and generation in a worker thread so slow model calls do not block the
   API event loop.
4. Extend the safe error contract and browser states with explicit retry guidance.
5. Emit privacy-safe structured request outcomes and add deterministic tests for every guard.
6. Build, deploy, and verify healthy, grounded, abstained, and limited behaviors.
