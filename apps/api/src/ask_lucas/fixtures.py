"""File-backed deterministic provider for the no-API-key development mode."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError, model_validator

from ask_lucas.ports import AbstainedDraft, GroundedDraft, ProviderDraft
from ask_lucas.schemas import AnswerBlock, GroundedAnswer, Source, StrictModel


class AnswerUnavailable(RuntimeError):
    """Raised when the answer dependency cannot complete a request."""


class RetrievalUnavailable(RuntimeError):
    """Raised when retrieval fails so generation cannot proceed ungrounded."""


class InvalidAnswerOutput(RuntimeError):
    """Raised when provider output violates grounding requirements."""


class FixtureAnswer(StrictModel):
    question: str
    blocks: list[AnswerBlock]


class FixtureAbstention(StrictModel):
    message: str
    suggestions: list[str]


class FixtureCatalog(StrictModel):
    version: str
    answers: list[FixtureAnswer]
    abstention: FixtureAbstention

    @model_validator(mode="after")
    def questions_are_unique(self) -> FixtureCatalog:
        questions = [answer.question.casefold() for answer in self.answers]
        if len(questions) != len(set(questions)):
            raise ValueError("Fixture questions must be unique.")
        return self


class FixtureAnswerProvider:
    """Load reviewed deterministic drafts without embedding biography in code."""

    def __init__(self, catalog: FixtureCatalog) -> None:
        self.catalog = catalog

    @classmethod
    def from_path(cls, path: Path) -> FixtureAnswerProvider:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            catalog = FixtureCatalog.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as error:
            raise AnswerUnavailable("The reviewed answer fixture could not be loaded.") from error
        return cls(catalog)

    def answer(self, question: str, evidence: Sequence[Source]) -> ProviderDraft:
        evidence_ids = {source.source_id for source in evidence}
        fixture = next(
            (
                answer
                for answer in self.catalog.answers
                if answer.question.casefold() == question.casefold()
            ),
            None,
        )

        if fixture is not None:
            cited_ids = {source_id for block in fixture.blocks for source_id in block.source_ids}
            if cited_ids and cited_ids.issubset(evidence_ids):
                return GroundedDraft(blocks=fixture.blocks)

        return AbstainedDraft(
            message=self.catalog.abstention.message,
            suggestions=self.catalog.abstention.suggestions,
        )


def validate_answer_sources(
    response: GroundedAnswer,
    *,
    allowed_source_ids: set[str] | None = None,
) -> None:
    """Fail closed when a grounded block points outside an evidence allow-list."""

    source_ids = [source.source_id for source in response.sources]
    if len(source_ids) != len(set(source_ids)):
        raise InvalidAnswerOutput("The answer contained duplicate source records.")

    allowed = allowed_source_ids if allowed_source_ids is not None else set(source_ids)
    for block in response.blocks:
        if not set(block.source_ids).issubset(allowed):
            raise InvalidAnswerOutput("The answer cited a source outside the evidence allow-list.")
