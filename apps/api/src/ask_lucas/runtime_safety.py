"""Local production guards for public, paid model access."""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict, deque
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from ipaddress import ip_address, ip_network
from pathlib import Path
from threading import BoundedSemaphore, Lock
from time import monotonic

from fastapi import Request

from ask_lucas.ports import AnswerProvider, ProviderDraft
from ask_lucas.schemas import ConversationMessage, Source


class RateLimitExceeded(Exception):
    """A client exceeded the bounded request window."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Request rate limit exceeded.")
        self.retry_after_seconds = retry_after_seconds


class GenerationCapacityExceeded(Exception):
    """All paid-generation slots are currently occupied."""


class DailyGenerationLimitExceeded(Exception):
    """The configured UTC-day paid-generation ceiling was reached."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Daily live-generation limit exceeded.")
        self.retry_after_seconds = retry_after_seconds


class SlidingWindowRateLimiter:
    """Bound requests per client without persisting visitor identifiers."""

    def __init__(
        self,
        *,
        requests: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if requests < 1 or window_seconds < 1:
            raise ValueError("Rate-limit requests and window must be positive.")
        self.requests = requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._checks = 0

    def check(self, client_key: str) -> None:
        """Record one allowed request or raise with a deterministic retry delay."""

        now = self.clock()
        cutoff = now - self.window_seconds
        with self._lock:
            self._checks += 1
            if self._checks % 256 == 0:
                self._discard_inactive_clients(cutoff)
            events = self._events[client_key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.requests:
                retry_after = max(1, math.ceil(events[0] + self.window_seconds - now))
                raise RateLimitExceeded(retry_after)
            events.append(now)

    def _discard_inactive_clients(self, cutoff: float) -> None:
        inactive = [
            key for key, events in self._events.items() if not events or events[-1] <= cutoff
        ]
        for key in inactive:
            del self._events[key]


def request_client_key(request: Request, trusted_proxy_cidrs: Sequence[str]) -> str:
    """Use a forwarded address only when the direct peer is an explicitly trusted proxy."""

    direct_host = request.client.host if request.client else "unknown"
    try:
        direct_address = ip_address(direct_host)
        trusted = any(
            direct_address in ip_network(network, strict=False) for network in trusted_proxy_cidrs
        )
    except ValueError:
        trusted = False

    if trusted:
        forwarded = request.headers.get("x-forwarded-for", "").split(",", maxsplit=1)[0].strip()
        if forwarded:
            try:
                return str(ip_address(forwarded))
            except ValueError:
                pass
    return direct_host


class DailyGenerationLedger:
    """Atomically reserve paid-generation attempts in a restart-safe SQLite ledger."""

    def __init__(
        self,
        path: Path,
        *,
        limit: int,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if limit < 1:
            raise ValueError("Daily live-generation limit must be positive.")
        self.path = path
        self.limit = limit
        self.now = now
        self._initialize_lock = Lock()
        self._initialized = False

    def reserve(self) -> None:
        current = self.now().astimezone(UTC)
        day = current.date().isoformat()
        self._initialize()
        with sqlite3.connect(self.path, timeout=5) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT attempts FROM daily_generation_usage WHERE day = ?", (day,)
            ).fetchone()
            attempts = int(row[0]) if row else 0
            if attempts >= self.limit:
                connection.rollback()
                raise DailyGenerationLimitExceeded(_seconds_until_next_utc_day(current))
            connection.execute(
                "INSERT INTO daily_generation_usage(day, attempts) VALUES (?, 1) "
                "ON CONFLICT(day) DO UPDATE SET attempts = attempts + 1",
                (day,),
            )
            connection.commit()

    def _initialize(self) -> None:
        if self._initialized:
            return
        with self._initialize_lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path, timeout=5) as connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS daily_generation_usage ("
                    "day TEXT PRIMARY KEY, attempts INTEGER NOT NULL CHECK(attempts >= 0))"
                )
            self._initialized = True


def _seconds_until_next_utc_day(current: datetime) -> int:
    tomorrow: date = current.date() + timedelta(days=1)
    reset = datetime.combine(tomorrow, datetime.min.time(), tzinfo=UTC)
    return max(1, math.ceil((reset - current).total_seconds()))


class GuardedLiveAnswerProvider:
    """Protect a live provider with nonblocking capacity and a durable daily ceiling."""

    mode: str = "live"

    def __init__(
        self,
        provider: AnswerProvider,
        *,
        max_concurrent_generations: int,
        ledger: DailyGenerationLedger,
    ) -> None:
        if max_concurrent_generations < 1:
            raise ValueError("Maximum concurrent generations must be positive.")
        self.provider = provider
        self.model = provider.model
        self._capacity = BoundedSemaphore(max_concurrent_generations)
        self._ledger = ledger

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        if not evidence:
            return self.provider.answer(question, evidence, history)
        if not self._capacity.acquire(blocking=False):
            raise GenerationCapacityExceeded
        try:
            self._ledger.reserve()
            return self.provider.answer(question, evidence, history)
        finally:
            self._capacity.release()
