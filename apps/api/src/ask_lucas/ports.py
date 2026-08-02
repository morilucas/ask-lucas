"""Narrow interfaces for retrieval and answer generation."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ask_lucas.schemas import AnswerBlock, AnswerResponse, ConversationMessage, ScoreOrder, Source


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    source: Source
    rank: int
    raw_score: float


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    strategy: str
    score_kind: str
    score_order: ScoreOrder
    evidence: Sequence[RetrievedEvidence]


@dataclass(frozen=True, slots=True)
class GroundedDraft:
    blocks: Sequence[AnswerBlock]


@dataclass(frozen=True, slots=True)
class AbstainedDraft:
    message: str
    suggestions: Sequence[str]


ProviderDraft = GroundedDraft | AbstainedDraft


class Retriever(Protocol):
    def retrieve(self, question: str, limit: int) -> RetrievalResult:
        """Return ranked approved evidence with provider-neutral score semantics."""


class AnswerProvider(Protocol):
    mode: str
    model: str | None

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        """Return an answer draft that may cite only supplied evidence."""


class AnswerService(Protocol):
    def answer(
        self,
        question: str,
        trace_id: str,
        *,
        retrieval_question: str | None = None,
        history: tuple[ConversationMessage, ...] = (),
    ) -> AnswerResponse:
        """Execute the complete answer workflow."""
