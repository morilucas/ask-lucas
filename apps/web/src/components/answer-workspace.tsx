"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { ApiError, AnswerResponse, GroundedAnswer, Source, askQuestion } from "@/lib/api";
import { SUGGESTED_QUESTIONS } from "@/lib/questions";

import styles from "./answer-workspace.module.css";

type RequestState =
  | { status: "idle" }
  | { status: "pending"; question: string }
  | { status: "complete"; question: string; answer: AnswerResponse }
  | { status: "error"; question: string; message: string; traceId?: string };

export function AnswerWorkspace() {
  const [question, setQuestion] = useState("");
  const [requestState, setRequestState] = useState<RequestState>({ status: "idle" });
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const lastTriggerRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (activeSource && dialog && !dialog.open) {
      dialog.showModal();
    }
  }, [activeSource]);

  async function submitQuestion(nextQuestion: string) {
    const normalized = nextQuestion.trim();
    if (!normalized || requestState.status === "pending") return;

    setQuestion(normalized);
    setRequestState({ status: "pending", question: normalized });

    try {
      const answer = await askQuestion(normalized);
      setRequestState({ status: "complete", question: normalized, answer });
    } catch (error) {
      if (error instanceof ApiError) {
        setRequestState({
          status: "error",
          question: normalized,
          message: error.message,
          traceId: error.traceId,
        });
        return;
      }

      setRequestState({
        status: "error",
        question: normalized,
        message: "The API could not be reached. Confirm that the local service is running.",
      });
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion(question);
  }

  function openSource(source: Source, trigger: HTMLButtonElement) {
    lastTriggerRef.current = trigger;
    setActiveSource(source);
  }

  function closeInspector() {
    dialogRef.current?.close();
  }

  function handleDialogClose() {
    setActiveSource(null);
    lastTriggerRef.current?.focus();
  }

  function reset() {
    setRequestState({ status: "idle" });
    setQuestion("");
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }

  const isPending = requestState.status === "pending";

  return (
    <section className={styles.workspace} aria-label="Ask Lucas">
      <form className={styles.composer} onSubmit={handleSubmit}>
        <label htmlFor="question">Ask a question</label>
        <div className={styles.inputRow}>
          <input
            ref={inputRef}
            id="question"
            name="question"
            value={question}
            minLength={1}
            maxLength={500}
            disabled={isPending}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about his experience, projects, or approach…"
            autoComplete="off"
          />
          <button type="submit" disabled={isPending || question.trim().length === 0}>
            <span className={styles.submitLabel}>Ask</span>
            <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>

      {requestState.status === "idle" ? (
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
      ) : null}

      <div className={styles.statusRegion} aria-live="polite" aria-atomic="true">
        {requestState.status === "pending" ? (
          <article className={styles.answer} aria-busy="true">
            <p className={styles.question}>{requestState.question}</p>
            <p className={styles.pending}>Reviewing approved sources…</p>
          </article>
        ) : null}

        {requestState.status === "complete" ? (
          <article className={styles.answer}>
            <p className={styles.question}>{requestState.question}</p>

            {requestState.answer.kind === "grounded" ? (
              <GroundedContent answer={requestState.answer} onOpenSource={openSource} />
            ) : (
              <div className={styles.prose}>
                <p>{requestState.answer.message}</p>
                <div className={styles.followUps}>
                  {requestState.answer.suggestions.map((suggestion) => (
                    <button key={suggestion} type="button" onClick={() => void submitQuestion(suggestion)}>
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button type="button" className={styles.reset} onClick={reset}>
              Ask another question
            </button>
          </article>
        ) : null}

        {requestState.status === "error" ? (
          <article className={`${styles.answer} ${styles.error}`}>
            <p className={styles.question}>{requestState.question}</p>
            <p>{requestState.message}</p>
            {requestState.traceId ? <p className={styles.trace}>Trace {requestState.traceId}</p> : null}
            <button type="button" className={styles.reset} onClick={() => void submitQuestion(requestState.question)}>
              Try again
            </button>
          </article>
        ) : null}
      </div>

      <p className={styles.trustNote}>Answers cite reviewed public sources. No conversation is stored.</p>

      <dialog
        ref={dialogRef}
        className={styles.inspector}
        aria-labelledby="evidence-title"
        onClose={handleDialogClose}
      >
        <div className={styles.inspectorInner}>
          <header>
            <div>
              <p>Evidence</p>
              <h2 id="evidence-title">{activeSource?.section}</h2>
            </div>
            <button type="button" onClick={closeInspector} aria-label="Close evidence">
              Close
            </button>
          </header>

          {activeSource ? (
            <div className={styles.sourceBody}>
              <p className={styles.sourceTitle}>{activeSource.title}</p>
              <blockquote>{activeSource.excerpt}</blockquote>
              <dl>
                <div>
                  <dt>Source ID</dt>
                  <dd>{activeSource.source_id}</dd>
                </div>
                <div>
                  <dt>Public file</dt>
                  <dd>{activeSource.content_path}</dd>
                </div>
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
    <div className={styles.prose}>
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
        {answer.sources.length} source{answer.sources.length === 1 ? "" : "s"} ·{" "}
        {Math.max(1, Math.round(answer.trace.total_ms))} ms · deterministic mock
      </p>
    </div>
  );
}
