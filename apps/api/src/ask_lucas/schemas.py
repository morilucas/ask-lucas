"""Public HTTP schemas for the Ask Lucas API."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base model that rejects fields outside the public contract."""

    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    build_version: str


class AnswerRequest(StrictModel):
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ConversationMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ChatRequest(StrictModel):
    messages: list[ConversationMessage] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def conversation_is_bounded_and_ordered(self) -> "ChatRequest":
        if self.messages[0].role != "user" or self.messages[-1].role != "user":
            raise ValueError("A conversation must begin and end with a user message.")
        if any(
            current.role == previous.role
            for previous, current in zip(self.messages, self.messages[1:], strict=False)
        ):
            raise ValueError("Conversation roles must alternate.")
        if sum(len(message.content) for message in self.messages) > 6000:
            raise ValueError("Conversation context is too large.")
        return self


class AnswerBlock(StrictModel):
    text: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)


class Source(StrictModel):
    source_id: str
    title: str
    section: str
    excerpt: str
    content_path: str


class RetrievedItem(StrictModel):
    source_id: str
    rank: int = Field(ge=1)
    raw_score: float | None = None


ScoreOrder = Literal["lower_is_better", "higher_is_better", "not_applicable"]


class TraceSummary(StrictModel):
    trace_id: str
    retrieval_strategy: str
    score_kind: str
    score_order: ScoreOrder
    retrieved: list[RetrievedItem]
    provider_mode: Literal["mock", "live"]
    model: str | None = None
    retrieval_ms: float = Field(ge=0)
    generation_ms: float = Field(ge=0)
    total_ms: float = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class GroundedAnswer(StrictModel):
    kind: Literal["grounded"] = "grounded"
    blocks: list[AnswerBlock] = Field(min_length=1)
    sources: list[Source] = Field(min_length=1)
    trace: TraceSummary


class AbstainedAnswer(StrictModel):
    kind: Literal["abstained"] = "abstained"
    message: str = Field(min_length=1)
    suggestions: list[str]
    trace: TraceSummary


AnswerResponse = Annotated[GroundedAnswer | AbstainedAnswer, Field(discriminator="kind")]


class RetrievalSummary(StrictModel):
    strategy: str
    limit: int = Field(ge=1)
    score_kind: str
    score_order: ScoreOrder


class EvaluationSummary(StrictModel):
    status: Literal["available", "unavailable"]
    version: str
    generated_at: datetime | None = None
    retrieval_recall_at_3: float | None = Field(default=None, ge=0, le=1)
    behavior_passed: int | None = Field(default=None, ge=0)
    behavior_total: int | None = Field(default=None, ge=0)


class SystemSummary(StrictModel):
    build_version: str
    retrieval: RetrievalSummary
    evaluation: EvaluationSummary
    limitations: list[str]
    next_experiment: str


class ErrorEnvelope(StrictModel):
    code: str
    message: str
    trace_id: str
    retryable: bool
    retry_after_seconds: int | None = Field(default=None, ge=1)
