"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import {
  ApiError,
  AnswerResponse,
  ConversationMessage,
  GroundedAnswer,
  Source,
  continueConversation,
} from "@/lib/api";
import { SUGGESTED_QUESTIONS } from "@/lib/questions";

import styles from "./answer-workspace.module.css";

type ExchangeState =
  | { status: "pending" }
  | { status: "complete"; answer: AnswerResponse }
  | { status: "error"; message: string; traceId?: string };

type Exchange = {
  id: string;
  question: string;
  state: ExchangeState;
};

function answerText(answer: AnswerResponse): string {
  return answer.kind === "grounded"
    ? answer.blocks.map((block) => block.text).join("\n")
    : answer.message;
}

function conversationMessages(exchanges: Exchange[], question: string): ConversationMessage[] {
  const history: ConversationMessage[] = [];
  let remainingCharacters = Math.max(0, 6000 - question.length);

  for (const exchange of exchanges.toReversed()) {
    if (exchange.state.status !== "complete") continue;
    const answer = answerText(exchange.state.answer);
    const pairCharacters = exchange.question.length + answer.length;
    if (pairCharacters > remainingCharacters || history.length >= 10) break;
    history.unshift(
      { role: "user", content: exchange.question },
      { role: "assistant", content: answer },
    );
    remainingCharacters -= pairCharacters;
  }

  return [...history, { role: "user", content: question }];
}

export function AnswerWorkspace() {
  const [draft, setDraft] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const lastTriggerRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const isPending = exchanges.some((exchange) => exchange.state.status === "pending");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (activeSource && dialog && !dialog.open) dialog.showModal();
  }, [activeSource]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [exchanges]);

  async function submitQuestion(nextQuestion: string, retryId?: string) {
    const normalized = nextQuestion.trim();
    if (!normalized || isPending) return;

    const id = retryId ?? crypto.randomUUID();
    const priorExchanges = retryId
      ? exchanges.filter((exchange) => exchange.id !== retryId)
      : exchanges;
    const pendingExchange: Exchange = { id, question: normalized, state: { status: "pending" } };
    setExchanges([...priorExchanges, pendingExchange]);
    setDraft("");

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const answer = await continueConversation(
        conversationMessages(priorExchanges, normalized),
        controller.signal,
      );
      setExchanges((current) =>
        current.map((exchange) =>
          exchange.id === id ? { ...exchange, state: { status: "complete", answer } } : exchange,
        ),
      );
    } catch (error) {
      if (controller.signal.aborted) {
        setExchanges((current) => current.filter((exchange) => exchange.id !== id));
        setDraft(normalized);
        return;
      }
      const state: ExchangeState =
        error instanceof ApiError
          ? { status: "error", message: error.message, traceId: error.traceId }
          : {
              status: "error",
              message: "The assistant could not be reached. Please try again.",
            };
      setExchanges((current) =>
        current.map((exchange) => (exchange.id === id ? { ...exchange, state } : exchange)),
      );
    } finally {
      abortRef.current = null;
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion(draft);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion(draft);
    }
  }

  function openSource(source: Source, trigger: HTMLButtonElement) {
    lastTriggerRef.current = trigger;
    setActiveSource(source);
  }

  function newConversation() {
    abortRef.current?.abort();
    setExchanges([]);
    setDraft("");
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }

  return (
    <section className={styles.workspace} aria-label="Conversation with Ask Lucas">
      <div className={styles.chatHeader}>
        <div>
          <span className={styles.statusDot} aria-hidden="true" />
          Grounded assistant
        </div>
        {exchanges.length > 0 ? (
          <button type="button" onClick={newConversation}>
            New conversation
          </button>
        ) : null}
      </div>

      {exchanges.length === 0 ? (
        <div className={styles.suggestions} aria-label="Suggested questions">
          {SUGGESTED_QUESTIONS.map((suggestion, index) => (
            <button
              key={suggestion.id}
              type="button"
              onClick={() => void submitQuestion(suggestion.text)}
            >
              <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
              <span>{suggestion.text}</span>
              <span aria-hidden="true">↗</span>
            </button>
          ))}
        </div>
      ) : (
        <div className={styles.transcript} aria-live="polite">
          {exchanges.map((exchange) => (
            <div className={styles.exchange} key={exchange.id}>
              <div className={styles.userMessage}>
                <p className={styles.speaker}>You</p>
                <p>{exchange.question}</p>
              </div>
              <article className={styles.assistantMessage} aria-busy={exchange.state.status === "pending"}>
                <p className={styles.speaker}>Ask Lucas</p>
                {exchange.state.status === "pending" ? (
                  <p className={styles.pending}>Reviewing the evidence…</p>
                ) : null}
                {exchange.state.status === "complete" ? (
                  exchange.state.answer.kind === "grounded" ? (
                    <GroundedContent answer={exchange.state.answer} onOpenSource={openSource} />
                  ) : (
                    <div className={styles.answerProse}>
                      <p>{exchange.state.answer.message}</p>
                    </div>
                  )
                ) : null}
                {exchange.state.status === "error" ? (
                  <div className={styles.error}>
                    <p>{exchange.state.message}</p>
                    {exchange.state.traceId ? <p>Trace {exchange.state.traceId}</p> : null}
                    <button
                      type="button"
                      onClick={() => void submitQuestion(exchange.question, exchange.id)}
                    >
                      Try again
                    </button>
                  </div>
                ) : null}
              </article>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      )}

      <form className={styles.composer} onSubmit={handleSubmit}>
        <label htmlFor="question">Message Ask Lucas</label>
        <div className={styles.composerSurface}>
          <textarea
            ref={inputRef}
            id="question"
            name="question"
            value={draft}
            rows={2}
            maxLength={2000}
            disabled={isPending}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder={exchanges.length ? "Ask a follow-up…" : "Ask about his experience, projects, or approach…"}
          />
          {isPending ? (
            <button type="button" className={styles.stopButton} onClick={() => abortRef.current?.abort()}>
              Stop
            </button>
          ) : (
            <button type="submit" className={styles.sendButton} disabled={!draft.trim()} aria-label="Send message">
              ↗
            </button>
          )}
        </div>
        <p>Conversation stays in this browser tab. Answers are limited to reviewed sources.</p>
      </form>

      <dialog
        ref={dialogRef}
        className={styles.inspector}
        aria-labelledby="evidence-title"
        onClose={() => {
          setActiveSource(null);
          lastTriggerRef.current?.focus();
        }}
      >
        <div className={styles.inspectorInner}>
          <header>
            <div>
              <p>Evidence</p>
              <h2 id="evidence-title">{activeSource?.section}</h2>
            </div>
            <button type="button" onClick={() => dialogRef.current?.close()} aria-label="Close evidence">
              Close
            </button>
          </header>
          {activeSource ? (
            <div className={styles.sourceBody}>
              <p className={styles.sourceTitle}>{activeSource.title}</p>
              <blockquote>{activeSource.excerpt}</blockquote>
              <dl>
                <div><dt>Source ID</dt><dd>{activeSource.source_id}</dd></div>
                <div><dt>Reviewed file</dt><dd>{activeSource.content_path}</dd></div>
              </dl>
            </div>
          ) : null}
        </div>
      </dialog>
    </section>
  );
}

function GroundedContent({
  answer,
  onOpenSource,
}: {
  answer: GroundedAnswer;
  onOpenSource: (source: Source, trigger: HTMLButtonElement) => void;
}) {
  return (
    <div className={styles.answerProse}>
      {answer.blocks.map((block, blockIndex) => (
        <p key={`${block.text}-${blockIndex}`}>
          {block.text}{" "}
          {block.source_ids.map((sourceId) => {
            const source = answer.sources.find((candidate) => candidate.source_id === sourceId);
            if (!source) return null;
            const sourceNumber = answer.sources.indexOf(source) + 1;
            return (
              <button
                key={sourceId}
                type="button"
                className={styles.citation}
                aria-label={`Open source ${sourceNumber} for claim ${blockIndex + 1}: ${source.section}`}
                onClick={(event) => onOpenSource(source, event.currentTarget)}
              >
                {sourceNumber}
              </button>
            );
          })}
        </p>
      ))}
      <p className={styles.metadata}>
        {answer.sources.length} source{answer.sources.length === 1 ? "" : "s"} · {Math.max(1, Math.round(answer.trace.total_ms))} ms · {answer.trace.provider_mode === "live" ? answer.trace.model : "grounded extractive mode"}
      </p>
    </div>
  );
}
