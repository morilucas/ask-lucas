"""FastAPI application factory and public routes."""

import json
import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from ask_lucas.anthropic_provider import AnthropicAnswerProvider
from ask_lucas.config import Settings, get_settings
from ask_lucas.fixtures import (
    AnswerUnavailable,
    FixtureAnswerProvider,
    GroundedExtractiveProvider,
    InvalidAnswerOutput,
    RetrievalUnavailable,
    validate_answer_sources,
)
from ask_lucas.ports import AnswerProvider, AnswerService
from ask_lucas.retrieval import SQLiteRetriever
from ask_lucas.runtime_safety import (
    DailyGenerationLedger,
    DailyGenerationLimitExceeded,
    GenerationCapacityExceeded,
    GuardedLiveAnswerProvider,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    request_client_key,
)
from ask_lucas.schemas import (
    AnswerRequest,
    AnswerResponse,
    ChatRequest,
    ConversationMessage,
    ErrorEnvelope,
    EvaluationSummary,
    GroundedAnswer,
    HealthResponse,
    RetrievalSummary,
    SystemSummary,
)
from ask_lucas.service import RetrievalAnswerService

TRACE_HEADER = "X-Trace-ID"
LOGGER = logging.getLogger("uvicorn.error.ask_lucas.requests")


def contextual_retrieval_query(messages: list[ConversationMessage]) -> str:
    """Carry recent user wording into lexical retrieval for follow-up questions."""

    recent_user_messages = [message.content for message in messages if message.role == "user"][-3:]
    return " ".join(recent_user_messages)


def configured_provider(
    settings: Settings,
) -> AnswerProvider:
    fixtures = FixtureAnswerProvider.from_path(settings.answer_fixture_path)
    provider = settings.provider.casefold()
    if provider not in {"auto", "anthropic", "claude", "extractive", "fixture"}:
        raise ValueError(
            "ASK_LUCAS_PROVIDER must be auto, anthropic, claude, extractive, or fixture."
        )

    api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    if provider in {"anthropic", "claude"} and not api_key:
        raise ValueError("ASK_LUCAS_ANTHROPIC_API_KEY is required for the Claude provider.")
    if provider in {"anthropic", "claude"} or (provider == "auto" and api_key):
        live_provider = AnthropicAnswerProvider(
            api_key=api_key or "",
            model=settings.anthropic_model,
            timeout_seconds=settings.anthropic_timeout_seconds,
        )
        return GuardedLiveAnswerProvider(
            live_provider,
            max_concurrent_generations=settings.max_concurrent_generations,
            ledger=DailyGenerationLedger(
                settings.runtime_db_path,
                limit=settings.daily_live_generation_limit,
            ),
        )
    if provider == "fixture":
        return fixtures
    return GroundedExtractiveProvider(fixtures)


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", uuid4().hex))


def _error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    retry_after_seconds: int | None = None,
) -> JSONResponse:
    trace_id = _trace_id(request)
    payload = ErrorEnvelope(
        code=code,
        message=message,
        trace_id=trace_id,
        retryable=retryable,
        retry_after_seconds=retry_after_seconds,
    )
    request.state.outcome = code
    headers = {TRACE_HEADER: trace_id}
    if retry_after_seconds is not None:
        headers["Retry-After"] = str(retry_after_seconds)
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )


def create_app(
    settings: Settings | None = None,
    answer_service: AnswerService | None = None,
) -> FastAPI:
    """Create an app with explicit dependencies for deterministic tests."""

    resolved_settings = settings or get_settings()
    service = answer_service or RetrievalAnswerService(
        retriever=SQLiteRetriever(resolved_settings.index_path, resolved_settings.content_dir),
        provider=configured_provider(resolved_settings),
    )
    app = FastAPI(title="Ask Lucas API", version="0.1.0")
    app.state.answer_service = service
    app.state.rate_limiter = SlidingWindowRateLimiter(
        requests=resolved_settings.rate_limit_requests,
        window_seconds=resolved_settings.rate_limit_window_seconds,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=[TRACE_HEADER],
    )

    @app.middleware("http")
    async def add_trace_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.trace_id = uuid4().hex
        started = perf_counter()
        response = await call_next(request)
        response.headers[TRACE_HEADER] = _trace_id(request)
        if request.url.path in {"/v1/answer", "/v1/chat"}:
            LOGGER.info(
                json.dumps(
                    {
                        "event": "answer_request",
                        "trace_id": _trace_id(request),
                        "route": request.url.path,
                        "status_code": response.status_code,
                        "outcome": getattr(request.state, "outcome", "unknown"),
                        "provider_mode": getattr(request.state, "provider_mode", None),
                        "model": getattr(request.state, "model", None),
                        "total_ms": round((perf_counter() - started) * 1000, 2),
                    },
                    separators=(",", ":"),
                )
            )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return _error(
            request,
            status_code=422,
            code="invalid_request",
            message="Enter a valid question and keep the conversation within its size limit.",
            retryable=False,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        return _error(
            request,
            status_code=error.status_code,
            code="not_found" if error.status_code == 404 else "http_error",
            message="The requested resource was not found."
            if error.status_code == 404
            else "The request could not be completed.",
            retryable=False,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, _: Exception) -> JSONResponse:
        return _error(
            request,
            status_code=500,
            code="internal_error",
            message="The request could not be completed.",
            retryable=True,
        )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(build_version=resolved_settings.build_version)

    @app.get("/v1/system", response_model=SystemSummary)
    async def system_summary() -> SystemSummary:
        return SystemSummary(
            build_version=resolved_settings.build_version,
            retrieval=RetrievalSummary(
                strategy="sqlite-fts5",
                limit=3,
                score_kind="bm25",
                score_order="lower_is_better",
            ),
            evaluation=EvaluationSummary(status="unavailable", version="0.2"),
            limitations=[
                "The baseline uses lexical rather than semantic retrieval.",
                "Without an API key, answers use a grounded extractive fallback.",
            ],
            next_experiment="Measure Recall@3, then compare lexical and semantic retrieval.",
        )

    async def execute_answer(
        request: Request,
        question: str,
        *,
        retrieval_question: str | None = None,
        history: tuple[ConversationMessage, ...] = (),
    ) -> Any:
        try:
            client_key = request_client_key(
                request, resolved_settings.trusted_proxy_cidr_list
            )
            app.state.rate_limiter.check(client_key)
            if retrieval_question is None and not history:
                result = await run_in_threadpool(
                    app.state.answer_service.answer, question, _trace_id(request)
                )
            else:
                result = await run_in_threadpool(
                    app.state.answer_service.answer,
                    question,
                    _trace_id(request),
                    retrieval_question=retrieval_question,
                    history=history,
                )
            if isinstance(result, GroundedAnswer):
                validate_answer_sources(result)
            request.state.outcome = result.kind
            request.state.provider_mode = result.trace.provider_mode
            request.state.model = result.trace.model
            return result
        except RateLimitExceeded as error:
            return _error(
                request,
                status_code=429,
                code="rate_limited",
                message=(
                    "You've asked several questions quickly. "
                    f"Please wait about {error.retry_after_seconds} seconds and try again."
                ),
                retryable=True,
                retry_after_seconds=error.retry_after_seconds,
            )
        except GenerationCapacityExceeded:
            return _error(
                request,
                status_code=503,
                code="generation_busy",
                message="Ask Lucas is helping other visitors right now. Please try again shortly.",
                retryable=True,
                retry_after_seconds=2,
            )
        except DailyGenerationLimitExceeded as error:
            return _error(
                request,
                status_code=503,
                code="daily_generation_limit",
                message="Ask Lucas has reached today's AI usage limit. Please come back tomorrow.",
                retryable=False,
                retry_after_seconds=error.retry_after_seconds,
            )
        except InvalidAnswerOutput:
            return _error(
                request,
                status_code=503,
                code="invalid_provider_output",
                message="The answer could not be safely validated. Please try again.",
                retryable=True,
            )
        except AnswerUnavailable:
            return _error(
                request,
                status_code=503,
                code="provider_unavailable",
                message="The answer could not be completed. Please try again.",
                retryable=True,
            )
        except RetrievalUnavailable:
            return _error(
                request,
                status_code=503,
                code="retrieval_unavailable",
                message="The approved sources could not be searched. Please try again.",
                retryable=True,
            )

    @app.post(
        "/v1/answer",
        response_model=AnswerResponse,
        responses={
            422: {"model": ErrorEnvelope},
            429: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
        },
    )
    async def answer(request: Request, payload: AnswerRequest) -> Any:
        return await execute_answer(request, payload.question)

    @app.post(
        "/v1/chat",
        response_model=AnswerResponse,
        responses={
            422: {"model": ErrorEnvelope},
            429: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
        },
    )
    async def chat(request: Request, payload: ChatRequest) -> Any:
        question = payload.messages[-1].content
        history = tuple(payload.messages[:-1])
        return await execute_answer(
            request,
            question,
            retrieval_question=contextual_retrieval_query(payload.messages),
            history=history,
        )

    return app


app = create_app()
