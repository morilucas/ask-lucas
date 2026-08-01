"""FastAPI application factory and public routes."""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from ask_lucas.config import Settings, get_settings
from ask_lucas.fixtures import (
    AnswerUnavailable,
    FixtureAnswerProvider,
    InvalidAnswerOutput,
    RetrievalUnavailable,
    validate_answer_sources,
)
from ask_lucas.ports import AnswerService
from ask_lucas.retrieval import SQLiteRetriever
from ask_lucas.schemas import (
    AnswerRequest,
    AnswerResponse,
    ErrorEnvelope,
    EvaluationSummary,
    GroundedAnswer,
    HealthResponse,
    RetrievalSummary,
    SystemSummary,
)
from ask_lucas.service import RetrievalAnswerService

TRACE_HEADER = "X-Trace-ID"


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", uuid4().hex))


def _error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
) -> JSONResponse:
    trace_id = _trace_id(request)
    payload = ErrorEnvelope(
        code=code,
        message=message,
        trace_id=trace_id,
        retryable=retryable,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers={TRACE_HEADER: trace_id},
    )


def create_app(
    settings: Settings | None = None,
    answer_service: AnswerService | None = None,
) -> FastAPI:
    """Create an app with explicit dependencies for deterministic tests."""

    resolved_settings = settings or get_settings()
    service = answer_service or RetrievalAnswerService(
        retriever=SQLiteRetriever(resolved_settings.index_path, resolved_settings.content_dir),
        provider=FixtureAnswerProvider.from_path(resolved_settings.answer_fixture_path),
    )
    app = FastAPI(title="Ask Lucas API", version="0.1.0")
    app.state.answer_service = service

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
        response = await call_next(request)
        response.headers[TRACE_HEADER] = _trace_id(request)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return _error(
            request,
            status_code=422,
            code="invalid_request",
            message="Enter a question between 1 and 500 characters.",
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
                "The deterministic provider currently supports one reviewed grounded answer.",
            ],
            next_experiment="Measure Recall@3, then compare lexical and semantic retrieval.",
        )

    @app.post(
        "/v1/answer",
        response_model=AnswerResponse,
        responses={422: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    )
    async def answer(request: Request, payload: AnswerRequest) -> Any:
        try:
            result = app.state.answer_service.answer(payload.question, _trace_id(request))
            if isinstance(result, GroundedAnswer):
                validate_answer_sources(result)
            return result
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

    return app


app = create_app()
