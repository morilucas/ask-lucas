"""Retrieval-first orchestration and fail-closed behavior tests."""

from collections.abc import Sequence

import pytest

from ask_lucas.fixtures import InvalidAnswerOutput, RetrievalUnavailable
from ask_lucas.ports import GroundedDraft, RetrievalResult, RetrievedEvidence
from ask_lucas.retrieval import RetrievalError
from ask_lucas.schemas import AnswerBlock, ConversationMessage, Source
from ask_lucas.service import RetrievalAnswerService

SOURCE = Source(
    source_id="profile:approved",
    title="Profile",
    section="Approved",
    excerpt="Approved evidence.",
    content_path="content/profile.md",
)


class StaticRetriever:
    def retrieve(self, question: str, limit: int) -> RetrievalResult:
        del question, limit
        return RetrievalResult(
            strategy="test",
            score_kind="test-score",
            score_order="lower_is_better",
            evidence=[RetrievedEvidence(source=SOURCE, rank=1, raw_score=-1.0)],
        )


class UnknownCitationProvider:
    mode: str = "mock"
    model: str | None = None

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> GroundedDraft:
        del question, evidence, history
        return GroundedDraft(
            blocks=[AnswerBlock(text="Unsupported.", source_ids=["profile:unknown"])]
        )


class BrokenRetriever:
    def retrieve(self, question: str, limit: int) -> RetrievalResult:
        del question, limit
        raise RetrievalError("broken")


def test_provider_cannot_cite_outside_retrieved_evidence() -> None:
    service = RetrievalAnswerService(StaticRetriever(), UnknownCitationProvider())

    with pytest.raises(InvalidAnswerOutput, match="outside the retrieval allow-list"):
        service.answer("Question", "trace-id")


def test_retrieval_failure_never_falls_through_to_generation() -> None:
    service = RetrievalAnswerService(BrokenRetriever(), UnknownCitationProvider())

    with pytest.raises(RetrievalUnavailable):
        service.answer("Question", "trace-id")
