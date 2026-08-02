"""Deterministic tests for public paid-model safeguards."""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Event

import pytest
from starlette.requests import Request

from ask_lucas.fixtures import AnswerUnavailable
from ask_lucas.ports import AbstainedDraft, GroundedDraft, ProviderDraft
from ask_lucas.runtime_safety import (
    DailyGenerationLedger,
    DailyGenerationLimitExceeded,
    GenerationCapacityExceeded,
    GuardedLiveAnswerProvider,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    request_client_key,
)
from ask_lucas.schemas import AnswerBlock, ConversationMessage, Source

SOURCE = Source(
    source_id="profile:approved",
    title="Profile",
    section="Approved",
    excerpt="Approved evidence.",
    content_path="content/profile.md",
)


class RecordingProvider:
    mode = "live"
    model = "test-model"

    def __init__(self, *, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        del question, history
        self.calls += 1
        if self.fail:
            raise AnswerUnavailable
        if not evidence:
            return AbstainedDraft(message="Insufficient evidence.", suggestions=[])
        return GroundedDraft(
            blocks=[AnswerBlock(text="Supported answer.", source_ids=[SOURCE.source_id])]
        )


def ledger(path: Path, *, limit: int) -> DailyGenerationLedger:
    return DailyGenerationLedger(
        path,
        limit=limit,
        now=lambda: datetime(2026, 8, 2, 12, tzinfo=UTC),
    )


def test_sliding_window_reports_when_the_client_can_retry() -> None:
    current = 100.0
    limiter = SlidingWindowRateLimiter(
        requests=2,
        window_seconds=60,
        clock=lambda: current,
    )

    limiter.check("client")
    limiter.check("client")
    with pytest.raises(RateLimitExceeded) as raised:
        limiter.check("client")

    assert raised.value.retry_after_seconds == 60


def test_forwarded_address_is_used_only_for_a_trusted_direct_proxy() -> None:
    forwarded_headers = [(b"x-forwarded-for", b"203.0.113.8")]
    trusted_request = Request(
        {"type": "http", "client": ("127.0.0.1", 5000), "headers": forwarded_headers}
    )
    untrusted_request = Request(
        {"type": "http", "client": ("198.51.100.9", 5000), "headers": forwarded_headers}
    )

    assert request_client_key(trusted_request, ["127.0.0.1/32"]) == "203.0.113.8"
    assert request_client_key(untrusted_request, ["127.0.0.1/32"]) == "198.51.100.9"


def test_daily_limit_persists_across_guard_instances(tmp_path: Path) -> None:
    runtime_db = tmp_path / "runtime.db"
    first_provider = RecordingProvider()
    first_guard = GuardedLiveAnswerProvider(
        first_provider,
        max_concurrent_generations=1,
        ledger=ledger(runtime_db, limit=1),
    )
    first_guard.answer("Question", [SOURCE])

    second_provider = RecordingProvider()
    second_guard = GuardedLiveAnswerProvider(
        second_provider,
        max_concurrent_generations=1,
        ledger=ledger(runtime_db, limit=1),
    )
    with pytest.raises(DailyGenerationLimitExceeded):
        second_guard.answer("Question", [SOURCE])

    assert first_provider.calls == 1
    assert second_provider.calls == 0


def test_failed_paid_attempt_still_uses_the_daily_budget(tmp_path: Path) -> None:
    runtime_db = tmp_path / "runtime.db"
    provider = RecordingProvider(fail=True)
    guard = GuardedLiveAnswerProvider(
        provider,
        max_concurrent_generations=1,
        ledger=ledger(runtime_db, limit=1),
    )

    with pytest.raises(AnswerUnavailable):
        guard.answer("Question", [SOURCE])
    with pytest.raises(DailyGenerationLimitExceeded):
        guard.answer("Question", [SOURCE])

    assert provider.calls == 1


def test_evidence_free_abstention_does_not_use_the_daily_budget(tmp_path: Path) -> None:
    runtime_db = tmp_path / "runtime.db"
    provider = RecordingProvider()
    guard = GuardedLiveAnswerProvider(
        provider,
        max_concurrent_generations=1,
        ledger=ledger(runtime_db, limit=1),
    )

    draft = guard.answer("Unsupported", [])

    assert isinstance(draft, AbstainedDraft)
    assert provider.calls == 1
    assert not runtime_db.exists()


class BlockingProvider(RecordingProvider):
    def __init__(self, entered: Event, release: Event) -> None:
        super().__init__()
        self.entered = entered
        self.release = release

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        self.entered.set()
        self.release.wait(timeout=2)
        return super().answer(question, evidence, history)


def test_concurrency_limit_fails_fast_without_entering_provider(tmp_path: Path) -> None:
    entered = Event()
    release = Event()
    provider = BlockingProvider(entered, release)
    guard = GuardedLiveAnswerProvider(
        provider,
        max_concurrent_generations=1,
        ledger=ledger(tmp_path / "runtime.db", limit=10),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(guard.answer, "First", [SOURCE])
        assert entered.wait(timeout=1)
        with pytest.raises(GenerationCapacityExceeded):
            guard.answer("Second", [SOURCE])
        release.set()
        first.result(timeout=1)

    assert provider.calls == 1
