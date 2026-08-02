"""File-backed deterministic provider for the no-API-key development mode."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError, model_validator

from ask_lucas.ports import AbstainedDraft, GroundedDraft, ProviderDraft
from ask_lucas.schemas import (
    AnswerBlock,
    ConversationMessage,
    GroundedAnswer,
    Source,
    StrictModel,
)


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

    mode: str = "mock"
    model: str | None = None

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

    def grounded_answer(
        self,
        question: str,
        evidence: Sequence[Source],
    ) -> GroundedDraft | None:
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

        return None

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        del history
        grounded = self.grounded_answer(question, evidence)
        if grounded is not None:
            return grounded

        return AbstainedDraft(
            message=self.catalog.abstention.message,
            suggestions=self.catalog.abstention.suggestions,
        )


class GroundedExtractiveProvider:
    """Use reviewed fixtures first, then quote the best retrieved evidence without invention."""

    mode: str = "mock"
    model: str | None = None

    def __init__(self, fixtures: FixtureAnswerProvider) -> None:
        self.fixtures = fixtures

    def answer(
        self,
        question: str,
        evidence: Sequence[Source],
        history: Sequence[ConversationMessage] = (),
    ) -> ProviderDraft:
        del history
        grounded = self.fixtures.grounded_answer(question, evidence)
        if grounded is not None:
            return grounded
        if not evidence:
            return AbstainedDraft(
                message=self.fixtures.catalog.abstention.message,
                suggestions=self.fixtures.catalog.abstention.suggestions,
            )

        blocks = [
            AnswerBlock(
                text=(
                    f'The closest reviewed evidence is in "{source.section}". '
                    f"It states: {_representative_line(source.excerpt)}"
                ),
                source_ids=[source.source_id],
            )
            for source in evidence[:2]
        ]
        return GroundedDraft(blocks=blocks)


def _representative_line(excerpt: str) -> str:
    lines = [line.removeprefix("- ").strip() for line in excerpt.splitlines()]
    candidates = [
        line
        for line in lines
        if line and not line.casefold().startswith(("status:", "public-content boundary:"))
    ]
    if not candidates:
        return "The reviewed source contains no additional summary text."
    selected = next((line for line in candidates if len(line.split()) >= 5), candidates[0])
    return selected if selected.endswith((".", "!", "?")) else f"{selected}."


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
