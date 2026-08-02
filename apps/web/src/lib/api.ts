import type { components } from "./api-schema";

export type GroundedAnswer = components["schemas"]["GroundedAnswer"];
export type AbstainedAnswer = components["schemas"]["AbstainedAnswer"];
export type AnswerResponse = GroundedAnswer | AbstainedAnswer;
export type Source = components["schemas"]["Source"];
export type ErrorEnvelope = components["schemas"]["ErrorEnvelope"];
export type ConversationMessage = components["schemas"]["ConversationMessage"];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly code: string;
  readonly traceId: string;
  readonly retryable: boolean;
  readonly retryAfterSeconds?: number;

  constructor(payload: ErrorEnvelope) {
    super(payload.message);
    this.name = "ApiError";
    this.code = payload.code;
    this.traceId = payload.trace_id;
    this.retryable = payload.retryable;
    this.retryAfterSeconds = payload.retry_after_seconds ?? undefined;
  }
}

export async function askQuestion(question: string, signal?: AbortSignal): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });

  const payload: unknown = await response.json();
  if (!response.ok) {
    throw new ApiError(payload as ErrorEnvelope);
  }

  return payload as AnswerResponse;
}

export async function continueConversation(
  messages: ConversationMessage[],
  signal?: AbortSignal,
): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });

  const payload: unknown = await response.json();
  if (!response.ok) {
    throw new ApiError(payload as ErrorEnvelope);
  }

  return payload as AnswerResponse;
}
