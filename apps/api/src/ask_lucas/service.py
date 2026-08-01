"""Provider-neutral orchestration for retrieval, generation, and tracing."""

from time import perf_counter

from ask_lucas.fixtures import InvalidAnswerOutput, RetrievalUnavailable, validate_answer_sources
from ask_lucas.ports import AbstainedDraft, AnswerProvider, GroundedDraft, Retriever
from ask_lucas.retrieval import RetrievalError
from ask_lucas.schemas import (
    AbstainedAnswer,
    AnswerResponse,
    GroundedAnswer,
    RetrievedItem,
    TraceSummary,
)


class RetrievalAnswerService:
    """Retrieve approved evidence before asking a replaceable provider for a draft."""

    def __init__(self, retriever: Retriever, provider: AnswerProvider, *, limit: int = 3) -> None:
        self.retriever = retriever
        self.provider = provider
        self.limit = limit

    def answer(self, question: str, trace_id: str) -> AnswerResponse:
        started = perf_counter()
        retrieval_started = perf_counter()
        try:
            retrieval_result = self.retriever.retrieve(question, self.limit)
        except RetrievalError as error:
            raise RetrievalUnavailable from error
        evidence = list(retrieval_result.evidence)
        retrieval_ms = (perf_counter() - retrieval_started) * 1000

        generation_started = perf_counter()
        draft = self.provider.answer(question, [item.source for item in evidence])
        generation_ms = (perf_counter() - generation_started) * 1000
        trace = TraceSummary(
            trace_id=trace_id,
            retrieval_strategy=retrieval_result.strategy,
            score_kind=retrieval_result.score_kind,
            score_order=retrieval_result.score_order,
            retrieved=[
                RetrievedItem(
                    source_id=item.source.source_id,
                    rank=item.rank,
                    raw_score=item.raw_score,
                )
                for item in evidence
            ],
            provider_mode="mock",
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=(perf_counter() - started) * 1000,
        )

        if isinstance(draft, AbstainedDraft):
            return AbstainedAnswer(
                message=draft.message,
                suggestions=list(draft.suggestions),
                trace=trace,
            )
        if not isinstance(draft, GroundedDraft):
            raise InvalidAnswerOutput("The provider returned an unsupported draft type.")

        allowed_source_ids = {item.source.source_id for item in evidence}
        cited_source_ids = {source_id for block in draft.blocks for source_id in block.source_ids}
        if not cited_source_ids or not cited_source_ids.issubset(allowed_source_ids):
            raise InvalidAnswerOutput("The answer cited evidence outside the retrieval allow-list.")
        sources = [item.source for item in evidence if item.source.source_id in cited_source_ids]
        response = GroundedAnswer(blocks=list(draft.blocks), sources=sources, trace=trace)
        validate_answer_sources(response, allowed_source_ids=allowed_source_ids)
        return response
