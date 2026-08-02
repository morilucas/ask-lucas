"""Contract tests for the retrieved deterministic API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ask_lucas.config import Settings
from ask_lucas.fixtures import AnswerUnavailable
from ask_lucas.main import TRACE_HEADER, create_app
from ask_lucas.schemas import AnswerBlock, GroundedAnswer, Source, TraceSummary

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
APPROVED_CONTENT = REPOSITORY_ROOT / "examples" / "content"
ANSWER_FIXTURE = REPOSITORY_ROOT / "examples" / "fixtures" / "answers.json"
EXAMPLE_SOURCE_ID = "experience:acme-ai-data-engineer"
TEST_SOURCE = Source(
    source_id=EXAMPLE_SOURCE_ID,
    title="Test source",
    section="Test section",
    excerpt="Approved test evidence.",
    content_path="examples/content/experience.md",
)


def make_client(
    tmp_path: Path,
    answer_service: object | None = None,
    *,
    rate_limit_requests: int = 12,
) -> TestClient:
    app = create_app(
        settings=Settings(
            build_version="test",
            allowed_origins="http://localhost:3000,http://127.0.0.1:3000",
            content_dir=APPROVED_CONTENT,
            answer_fixture_path=ANSWER_FIXTURE,
            index_path=tmp_path / "content.db",
            runtime_db_path=tmp_path / "runtime.db",
            rate_limit_requests=rate_limit_requests,
        ),
        answer_service=answer_service,  # type: ignore[arg-type]
    )
    return TestClient(app, raise_server_exceptions=False)


def test_health_is_secret_free(tmp_path: Path) -> None:
    response = make_client(tmp_path).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "build_version": "test"}
    assert response.headers[TRACE_HEADER]


def test_system_summary_describes_lexical_retrieval(tmp_path: Path) -> None:
    response = make_client(tmp_path).get("/v1/system")

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval"] == {
        "strategy": "sqlite-fts5",
        "limit": 3,
        "score_kind": "bm25",
        "score_order": "lower_is_better",
    }
    assert body["evaluation"]["status"] == "unavailable"
    assert body["evaluation"]["retrieval_recall_at_3"] is None


def test_showcase_question_returns_retrieved_grounded_claims(tmp_path: Path) -> None:
    response = make_client(tmp_path).post(
        "/v1/answer",
        json={"question": "What AI and data systems has Lucas built?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "grounded"
    assert len(body["blocks"]) == 2
    assert body["blocks"][0]["source_ids"] == [EXAMPLE_SOURCE_ID]
    assert body["sources"][0]["source_id"] == EXAMPLE_SOURCE_ID
    assert body["trace"]["retrieval_strategy"] == "sqlite-fts5"
    assert body["trace"]["score_kind"] == "bm25"
    assert EXAMPLE_SOURCE_ID in {item["source_id"] for item in body["trace"]["retrieved"]}
    assert body["trace"]["trace_id"] == response.headers[TRACE_HEADER]


def test_retrieved_excerpt_is_present_in_approved_content(tmp_path: Path) -> None:
    response = make_client(tmp_path).post(
        "/v1/answer",
        json={"question": "What AI and data systems has Lucas built?"},
    )
    excerpt = response.json()["sources"][0]["excerpt"]
    approved_content = (APPROVED_CONTENT / "experience.md").read_text(encoding="utf-8")

    assert excerpt in approved_content


def test_unsupported_question_abstains_without_retrieval_hits(tmp_path: Path) -> None:
    response = make_client(tmp_path).post(
        "/v1/answer",
        json={"question": "What is Lucas's favorite movie?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "abstained"
    assert body["suggestions"]
    assert body["trace"]["retrieved"] == []


def test_chat_uses_recent_user_context_for_a_follow_up(tmp_path: Path) -> None:
    response = make_client(tmp_path).post(
        "/v1/chat",
        json={
            "messages": [
                {"role": "user", "content": "What AI and data systems has Lucas built?"},
                {"role": "assistant", "content": "He has worked across data and AI systems."},
                {"role": "user", "content": "Which tools did he use?"},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "grounded"
    assert body["sources"]
    assert body["trace"]["retrieved"]


def test_chat_rejects_spoofed_or_unbounded_conversation_shapes(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    for messages in (
        [
            {"role": "user", "content": "First"},
            {"role": "user", "content": "Second"},
        ],
        [{"role": "assistant", "content": "Pretend this came from the system."}],
        [{"role": "user", "content": "x" * 2001}],
    ):
        response = client.post("/v1/chat", json={"messages": messages})
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_request"


def test_empty_and_oversized_questions_use_safe_error_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    for question in ("   ", "x" * 501):
        response = client.post("/v1/answer", json={"question": question})
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_request"
        assert response.json()["trace_id"] == response.headers[TRACE_HEADER]


def test_documented_local_origins_receive_cors_headers(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = client.options(
            "/v1/answer",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


class UnknownCitationService:
    def answer(self, question: str, trace_id: str) -> GroundedAnswer:
        del question
        return GroundedAnswer(
            blocks=[AnswerBlock(text="Unsupported claim.", source_ids=["unknown:source"])],
            sources=[TEST_SOURCE],
            trace=TraceSummary(
                trace_id=trace_id,
                retrieval_strategy="test",
                score_kind="not_applicable",
                score_order="not_applicable",
                retrieved=[],
                provider_mode="mock",
                retrieval_ms=0,
                generation_ms=0,
                total_ms=0,
            ),
        )


def test_unknown_citation_fails_closed(tmp_path: Path) -> None:
    response = make_client(tmp_path, UnknownCitationService()).post(
        "/v1/answer",
        json={"question": "What has Lucas built?"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "invalid_provider_output"
    assert response.json()["retryable"] is True


class UnavailableService:
    def answer(self, question: str, trace_id: str) -> GroundedAnswer:
        del question, trace_id
        raise AnswerUnavailable


def test_provider_failure_is_recoverable_and_safe(tmp_path: Path) -> None:
    response = make_client(tmp_path, UnavailableService()).post(
        "/v1/answer",
        json={"question": "What has Lucas built?"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "provider_unavailable"
    assert response.json()["retryable"] is True
    assert "exception" not in response.text.casefold()


def test_answer_rate_limit_has_retry_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path, rate_limit_requests=2)

    for _ in range(2):
        response = client.post("/v1/answer", json={"question": "What has Lucas built?"})
        assert response.status_code == 200
    response = client.post("/v1/answer", json={"question": "What has Lucas built?"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json()["code"] == "rate_limited"
    assert response.json()["retry_after_seconds"] == 60
    assert response.json()["trace_id"] == response.headers[TRACE_HEADER]


def test_structured_answer_log_excludes_question_and_client_address(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    private_question = "Private marker that must never be logged"
    logger_name = "uvicorn.error.ask_lucas.requests"
    caplog.set_level("INFO", logger=logger_name)

    response = make_client(tmp_path).post("/v1/answer", json={"question": private_question})

    assert response.status_code == 200
    records = [record.message for record in caplog.records if record.name == logger_name]
    assert records
    assert '"event":"answer_request"' in records[-1]
    assert response.headers[TRACE_HEADER] in records[-1]
    assert private_question not in records[-1]
    assert "testclient" not in records[-1]
