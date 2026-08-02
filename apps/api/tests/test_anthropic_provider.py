"""Unit tests for the Claude provider boundary without making paid API calls."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from anthropic import Anthropic

from ask_lucas.anthropic_provider import AnthropicAnswerProvider, StructuredProviderOutput
from ask_lucas.fixtures import AnswerUnavailable
from ask_lucas.ports import AbstainedDraft, GroundedDraft
from ask_lucas.schemas import AnswerBlock, ConversationMessage, Source

SOURCE = Source(
    source_id="experience:example",
    title="Experience",
    section="Example role",
    excerpt="Lucas built a grounded assistant.",
    content_path="content/experience.md",
)


def provider_with_response(
    output: StructuredProviderOutput,
) -> tuple[AnthropicAnswerProvider, MagicMock]:
    client = MagicMock(spec=Anthropic)
    client.messages.parse.return_value.parsed_output = output
    provider = AnthropicAnswerProvider(
        api_key="test-key",
        model="claude-haiku-4-5",
        timeout_seconds=1,
        client=cast(Anthropic, client),
    )
    return provider, client


def test_provider_sends_bounded_context_and_returns_grounded_draft() -> None:
    output = StructuredProviderOutput(
        kind="grounded",
        blocks=[AnswerBlock(text="He built a grounded assistant.", source_ids=[SOURCE.source_id])],
    )
    provider, client = provider_with_response(output)
    history = [ConversationMessage(role="user", content=f"Question {index}") for index in range(10)]

    draft = provider.answer("What did he build?", [SOURCE], history)

    assert isinstance(draft, GroundedDraft)
    request = client.messages.parse.call_args.kwargs
    assert request["model"] == "claude-haiku-4-5"
    assert request["output_format"] is StructuredProviderOutput
    assert "Question 0" not in request["messages"][0]["content"]
    assert "Question 9" in request["messages"][0]["content"]


def test_provider_returns_abstention_without_calling_claude_when_evidence_is_empty() -> None:
    provider, client = provider_with_response(
        StructuredProviderOutput(kind="abstained", message="Insufficient evidence.")
    )

    draft = provider.answer("What is his favorite movie?", [])

    assert isinstance(draft, AbstainedDraft)
    client.messages.parse.assert_not_called()


def test_provider_converts_sdk_failure_to_safe_domain_error() -> None:
    provider, client = provider_with_response(
        StructuredProviderOutput(kind="abstained", message="Insufficient evidence.")
    )
    client.messages.parse.side_effect = RuntimeError("provider detail")

    with pytest.raises(AnswerUnavailable):
        provider.answer("What did he build?", [SOURCE])
