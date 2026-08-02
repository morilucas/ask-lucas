"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import {
  ApiError,
  AnswerResponse,
  ConversationMessage,
  GroundedAnswer,
  Source,
  SystemSummary,
  continueConversation,
  getSystemSummary,
} from "@/lib/api";
import { SUGGESTED_QUESTIONS } from "@/lib/questions";

import styles from "./answer-workspace.module.css";

const MAX_QUESTION_LENGTH = 500;
const SLOW_RESPONSE_MS = 8_000;

type ExchangeState =
  | { status: "pending"; slow: boolean }
  | { status: "complete"; answer: AnswerResponse }
  | {
      status: "error";
      message: string;
      traceId?: string;
      retryable: boolean;
      retryAfterSeconds?: number;
    };

type Exchange = {
  id: string;
  question: string;
  state: ExchangeState;
};

type InspectorState =
  | { mode: "evidence"; sources: Source[]; sourceIndex: number }
  | { mode: "system" }
  | null;

type SystemState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "complete"; summary: SystemSummary }
  | { status: "error"; message: string };

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
  const [validationMessage, setValidationMessage] = useState("");
  const [liveMessage, setLiveMessage] = useState("Ready for a question.");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [inspector, setInspector] = useState<InspectorState>(null);
  const [systemState, setSystemState] = useState<SystemState>({ status: "idle" });
  const [copiedTrace, setCopiedTrace] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const lastTriggerRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const isPending = exchanges.some((exchange) => exchange.state.status === "pending");
  const draftLength = draft.trim().length;
  const activeSource =
    inspector?.mode === "evidence" ? inspector.sources[inspector.sourceIndex] : null;
  const latestAnswer = exchanges
    .toReversed()
    .find((exchange) => exchange.state.status === "complete")?.state;
  const latestCompleteAnswer =
    latestAnswer?.status === "complete" ? latestAnswer.answer : undefined;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (inspector && dialog && !dialog.open) dialog.showModal();
  }, [inspector]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [exchanges]);

  function validateQuestion(question: string): string | null {
    const normalized = question.trim();
    if (!normalized) return "Enter a question before sending.";
    if (normalized.length > MAX_QUESTION_LENGTH) {
      return `Keep the question to ${MAX_QUESTION_LENGTH} characters or fewer.`;
    }
    return null;
  }

  async function submitQuestion(nextQuestion: string, retryId?: string) {
    const problem = validateQuestion(nextQuestion);
    if (problem) {
      setValidationMessage(problem);
      setLiveMessage(problem);
      inputRef.current?.focus();
      return;
    }
    if (isPending) return;

    const normalized = nextQuestion.trim();
    const id = retryId ?? crypto.randomUUID();
    const priorExchanges = retryId
      ? exchanges.filter((exchange) => exchange.id !== retryId)
      : exchanges;
    const pendingExchange: Exchange = {
      id,
      question: normalized,
      state: { status: "pending", slow: false },
    };
    setValidationMessage("");
    setLiveMessage("Reviewing approved sources.");
    setExchanges([...priorExchanges, pendingExchange]);
    setDraft("");

    const controller = new AbortController();
    abortRef.current = controller;
    const slowTimer = window.setTimeout(() => {
      setExchanges((current) =>
        current.map((exchange) =>
          exchange.id === id && exchange.state.status === "pending"
            ? { ...exchange, state: { status: "pending", slow: true } }
            : exchange,
        ),
      );
      setLiveMessage("The answer is taking longer than usual.");
    }, SLOW_RESPONSE_MS);

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
      setLiveMessage(
        answer.kind === "grounded"
          ? "Grounded answer ready."
          : "The reviewed sources do not support that answer.",
      );
    } catch (error) {
      if (controller.signal.aborted) {
        setExchanges((current) => current.filter((exchange) => exchange.id !== id));
        setDraft(normalized);
        setLiveMessage("Request stopped. Your question is ready to edit.");
        window.requestAnimationFrame(() => inputRef.current?.focus());
        return;
      }
      const state: ExchangeState =
        error instanceof ApiError
          ? {
              status: "error",
              message: error.message,
              traceId: error.traceId,
              retryable: error.retryable,
              retryAfterSeconds: error.retryAfterSeconds,
            }
          : {
              status: "error",
              message: "The connection was interrupted before a complete answer arrived.",
              retryable: true,
            };
      setExchanges((current) =>
        current.map((exchange) => (exchange.id === id ? { ...exchange, state } : exchange)),
      );
      setLiveMessage(state.message);
    } finally {
      window.clearTimeout(slowTimer);
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

  function openSource(answer: GroundedAnswer, source: Source, trigger: HTMLButtonElement) {
    lastTriggerRef.current = trigger;
    setInspector({
      mode: "evidence",
      sources: answer.sources,
      sourceIndex: answer.sources.indexOf(source),
    });
  }

  async function openSystemLens(trigger: HTMLButtonElement) {
    lastTriggerRef.current = trigger;
    setCopiedTrace(false);
    setInspector({ mode: "system" });
    if (systemState.status === "complete" || systemState.status === "loading") return;
    setSystemState({ status: "loading" });
    try {
      setSystemState({ status: "complete", summary: await getSystemSummary() });
    } catch (error) {
      setSystemState({
        status: "error",
        message: error instanceof Error ? error.message : "System information is unavailable.",
      });
    }
  }

  function newConversation() {
    abortRef.current?.abort();
    setExchanges([]);
    setDraft("");
    setValidationMessage("");
    setLiveMessage("New conversation ready.");
    window.requestAnimationFrame(() => inputRef.current?.focus());
  }

  function closeInspector() {
    dialogRef.current?.close();
  }

  async function copyTraceId(traceId: string) {
    try {
      await navigator.clipboard.writeText(traceId);
      setCopiedTrace(true);
      setLiveMessage("Trace ID copied.");
    } catch {
      setLiveMessage("The trace ID could not be copied. It remains visible in System Lens.");
    }
  }

  return (
    <section className={styles.workspace} aria-label="Conversation with Ask Lucas">
      <p className={styles.visuallyHidden} aria-live="polite" aria-atomic="true">
        {liveMessage}
      </p>

      <div className={styles.chatHeader}>
        <div className={styles.chatContext}>
          <span>Conversation</span>
          <span>Ask about Lucas&apos;s work and experience</span>
        </div>
        <div className={styles.chatActions}>
          <button
            type="button"
            className={styles.toolbarButton}
            onClick={(event) => void openSystemLens(event.currentTarget)}
          >
            <SystemIcon />
            System lens
          </button>
          {exchanges.length > 0 ? (
            <button type="button" className={styles.toolbarButton} onClick={newConversation}>
              <NewChatIcon />
              New conversation
            </button>
          ) : null}
        </div>
      </div>

      {exchanges.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyContent}>
            <div className={styles.assistantMark} aria-hidden="true">
              <SparkIcon />
            </div>
            <p className={styles.eyebrow}>Ask Lucas</p>
            <h1>What would you like to know?</h1>
            <p className={styles.emptyDescription}>
              Explore Lucas&apos;s experience, selected work, and approach through answers grounded in
              reviewed sources.
            </p>
            <div className={styles.suggestions} aria-label="Suggested questions">
              {SUGGESTED_QUESTIONS.map((suggestion) => (
                <button
                  key={suggestion.id}
                  type="button"
                  aria-label={suggestion.text}
                  onClick={() => void submitQuestion(suggestion.text)}
                >
                  <span className={styles.suggestionIcon} aria-hidden="true">
                    <PromptIcon />
                  </span>
                  <span className={styles.suggestionCopy}>
                    <span>{suggestion.text}</span>
                    <span>{suggestion.description}</span>
                  </span>
                  <span className={styles.suggestionArrow} aria-hidden="true">
                    <ArrowUpIcon />
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className={styles.transcript} data-testid="chat-transcript">
          {exchanges.map((exchange) => (
            <div className={styles.exchange} key={exchange.id}>
              <div className={styles.userMessage}>
                <div className={styles.userBubble}>
                  <p className={styles.speaker}>You</p>
                  <p>{exchange.question}</p>
                </div>
              </div>
              <article
                className={styles.assistantMessage}
                aria-busy={exchange.state.status === "pending"}
              >
                <div className={styles.assistantIdentity}>
                  <span aria-hidden="true">L</span>
                  <p className={styles.speaker}>Ask Lucas</p>
                </div>
                <div className={styles.assistantContent}>
                  {exchange.state.status === "pending" ? (
                    <div className={styles.pending}>
                      <p>Reviewing approved sources&hellip;</p>
                      {exchange.state.slow ? (
                        <p>The answer is taking longer than usual, but it is still working.</p>
                      ) : null}
                    </div>
                  ) : null}
                  {exchange.state.status === "complete" ? (
                    exchange.state.answer.kind === "grounded" ? (
                      <GroundedContent answer={exchange.state.answer} onOpenSource={openSource} />
                    ) : (
                      <AbstainedContent
                        answer={exchange.state.answer}
                        onSuggestion={(question) => void submitQuestion(question)}
                      />
                    )
                  ) : null}
                  {exchange.state.status === "error" ? (
                    <div className={styles.error}>
                      <p>{exchange.state.message}</p>
                      {exchange.state.traceId ? <p>Trace {exchange.state.traceId}</p> : null}
                      {exchange.state.retryable ? (
                        <button
                          type="button"
                          onClick={() => void submitQuestion(exchange.question, exchange.id)}
                        >
                          {exchange.state.retryAfterSeconds
                            ? `Try again in about ${exchange.state.retryAfterSeconds}s`
                            : "Try again"}
                        </button>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </article>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      )}

      <form
        className={styles.composer}
        onSubmit={handleSubmit}
        noValidate
      >
        <label htmlFor="question">Message Ask Lucas</label>
        <div className={styles.composerSurface}>
          <textarea
            ref={inputRef}
            id="question"
            name="question"
            value={draft}
            rows={1}
            maxLength={2000}
            disabled={isPending}
            aria-describedby="composer-help composer-validation"
            aria-invalid={Boolean(validationMessage)}
            onChange={(event) => {
              setDraft(event.target.value);
              if (validationMessage) setValidationMessage("");
            }}
            onKeyDown={handleComposerKeyDown}
            placeholder={
              exchanges.length
                ? "Ask a follow-up..."
                : "Ask about his experience, projects, or approach..."
            }
          />
          {isPending ? (
            <button
              type="button"
              className={styles.stopButton}
              onClick={() => abortRef.current?.abort()}
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className={styles.sendButton}
              disabled={draftLength > MAX_QUESTION_LENGTH}
              aria-label="Send message"
            >
              <ArrowUpIcon />
            </button>
          )}
        </div>
        <div className={styles.composerFooter}>
          <p id="composer-help">
            <span className={styles.groundedDot} aria-hidden="true" />
            Reviewed sources only · Questions aren&apos;t stored
          </p>
          <p className={draftLength > MAX_QUESTION_LENGTH ? styles.characterError : undefined}>
            <span className={styles.composerHint}>Enter to send · Shift + Enter for a new line</span>
            {draftLength ? ` · ${draftLength}/${MAX_QUESTION_LENGTH}` : ""}
          </p>
        </div>
        <p id="composer-validation" className={styles.validation}>
          {validationMessage}
        </p>
      </form>

      <dialog
        ref={dialogRef}
        className={styles.inspector}
        aria-labelledby="inspector-title"
        onClose={() => {
          setInspector(null);
          lastTriggerRef.current?.focus();
        }}
      >
        <div className={styles.inspectorInner}>
          <header>
            <div>
              <p>{inspector?.mode === "system" ? "System lens" : "Evidence"}</p>
              <h2 id="inspector-title">
                {inspector?.mode === "system" ? "How this answer was made" : activeSource?.section}
              </h2>
            </div>
            <button type="button" onClick={closeInspector} aria-label="Close inspector">
              Close
            </button>
          </header>

          {inspector?.mode === "evidence" && activeSource ? (
            <EvidencePanel
              source={activeSource}
              sourceIndex={inspector.sourceIndex}
              sourceCount={inspector.sources.length}
              onNavigate={(sourceIndex) => setInspector({ ...inspector, sourceIndex })}
            />
          ) : null}

          {inspector?.mode === "system" ? (
            <SystemPanel
              state={systemState}
              answer={latestCompleteAnswer}
              copiedTrace={copiedTrace}
              onCopyTrace={copyTraceId}
            />
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
  onOpenSource: (answer: GroundedAnswer, source: Source, trigger: HTMLButtonElement) => void;
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
                onClick={(event) => onOpenSource(answer, source, event.currentTarget)}
              >
                {sourceNumber}
              </button>
            );
          })}
        </p>
      ))}
      <p className={styles.metadata}>
        {answer.sources.length} source{answer.sources.length === 1 ? "" : "s"} &middot;{" "}
        {Math.max(1, Math.round(answer.trace.total_ms))} ms &middot;{" "}
        {answer.trace.provider_mode === "live" ? answer.trace.model : "grounded extractive mode"}
      </p>
    </div>
  );
}

function AbstainedContent({
  answer,
  onSuggestion,
}: {
  answer: Extract<AnswerResponse, { kind: "abstained" }>;
  onSuggestion: (question: string) => void;
}) {
  return (
    <div className={styles.abstention}>
      <p>{answer.message}</p>
      {answer.suggestions.length ? (
        <div className={styles.followUps} aria-label="Supported questions">
          <p>Try a question supported by the reviewed sources:</p>
          {answer.suggestions.slice(0, 2).map((suggestion) => (
            <button type="button" key={suggestion} onClick={() => onSuggestion(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function EvidencePanel({
  source,
  sourceIndex,
  sourceCount,
  onNavigate,
}: {
  source: Source;
  sourceIndex: number;
  sourceCount: number;
  onNavigate: (sourceIndex: number) => void;
}) {
  return (
    <div className={styles.sourceBody}>
      <p className={styles.sourceTitle}>{source.title}</p>
      <blockquote>{source.excerpt}</blockquote>
      {sourceCount > 1 ? (
        <nav className={styles.sourceNavigation} aria-label="Answer evidence">
          <button
            type="button"
            disabled={sourceIndex === 0}
            onClick={() => onNavigate(sourceIndex - 1)}
          >
            Previous
          </button>
          <span>
            {sourceIndex + 1} of {sourceCount}
          </span>
          <button
            type="button"
            disabled={sourceIndex === sourceCount - 1}
            onClick={() => onNavigate(sourceIndex + 1)}
          >
            Next
          </button>
        </nav>
      ) : null}
      <dl>
        <div>
          <dt>Source ID</dt>
          <dd>{source.source_id}</dd>
        </div>
        <div>
          <dt>Reviewed file</dt>
          <dd>{source.content_path}</dd>
        </div>
      </dl>
    </div>
  );
}

function SystemPanel({
  state,
  answer,
  copiedTrace,
  onCopyTrace,
}: {
  state: SystemState;
  answer?: AnswerResponse;
  copiedTrace: boolean;
  onCopyTrace: (traceId: string) => Promise<void>;
}) {
  if (state.status === "idle" || state.status === "loading") {
    return <p className={styles.panelStatus}>Loading safe system details&hellip;</p>;
  }
  if (state.status === "error") {
    return <p className={styles.panelStatus}>{state.message}</p>;
  }

  const { summary } = state;
  return (
    <div className={styles.systemBody}>
      <p className={styles.flow}>Retrieve <span aria-hidden="true">&rarr;</span> validate citations <span aria-hidden="true">&rarr;</span> answer</p>

      <section aria-labelledby="retrieval-heading">
        <h3 id="retrieval-heading">Retrieval</h3>
        <dl>
          <div><dt>Strategy</dt><dd>{summary.retrieval.strategy}</dd></div>
          <div><dt>Limit</dt><dd>Top {summary.retrieval.limit}</dd></div>
          <div><dt>Score</dt><dd>{summary.retrieval.score_kind}, {summary.retrieval.score_order.replaceAll("_", " ")}</dd></div>
        </dl>
        {answer?.trace.retrieved.length ? (
          <ol className={styles.retrievedList}>
            {answer.trace.retrieved.map((item) => (
              <li key={item.source_id}>
                <code>{item.source_id}</code>
                <span>rank {item.rank}{item.raw_score == null ? "" : ` / ${item.raw_score.toFixed(3)}`}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className={styles.quiet}>Ask a question to inspect its retrieved evidence.</p>
        )}
      </section>

      <section aria-labelledby="generation-heading">
        <h3 id="generation-heading">Answer</h3>
        {answer ? (
          <>
            <dl>
              <div><dt>Provider</dt><dd>{answer.trace.provider_mode}</dd></div>
              <div><dt>Model</dt><dd>{answer.trace.model ?? "extractive fallback"}</dd></div>
              <div><dt>Retrieval</dt><dd>{Math.round(answer.trace.retrieval_ms)} ms</dd></div>
              <div><dt>Generation</dt><dd>{Math.round(answer.trace.generation_ms)} ms</dd></div>
              <div><dt>Total</dt><dd>{Math.round(answer.trace.total_ms)} ms</dd></div>
              <div><dt>Trace</dt><dd>{answer.trace.trace_id}</dd></div>
            </dl>
            <button
              type="button"
              className={styles.copyTrace}
              onClick={() => void onCopyTrace(answer.trace.trace_id)}
            >
              {copiedTrace ? "Trace ID copied" : "Copy trace ID"}
            </button>
          </>
        ) : (
          <p className={styles.quiet}>Timing and provider details appear after an answer.</p>
        )}
      </section>

      <section aria-labelledby="evaluation-heading">
        <h3 id="evaluation-heading">Evaluation</h3>
        <p>
          {summary.evaluation.status === "available"
            ? `${summary.evaluation.behavior_passed ?? 0} of ${summary.evaluation.behavior_total ?? 0} checks passed.`
            : "The factual evaluation set is not available yet."}
        </p>
        {summary.evaluation.retrieval_recall_at_3 != null ? (
          <p>Recall@3: {(summary.evaluation.retrieval_recall_at_3 * 100).toFixed(0)}%</p>
        ) : null}
      </section>

      <section aria-labelledby="limits-heading">
        <h3 id="limits-heading">Current limit</h3>
        <p>{summary.limitations[0] ?? "No limitation was reported."}</p>
        <p className={styles.nextExperiment}>Next: {summary.next_experiment}</p>
      </section>
    </div>
  );
}

function ArrowUpIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M10 15V5m0 0L6.5 8.5M10 5l3.5 3.5" />
    </svg>
  );
}

function NewChatIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M10 4.25H5.75a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10" />
      <path d="M12.5 3.75h3.75V7.5M16 4l-6.25 6.25" />
    </svg>
  );
}

function SystemIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="6.25" />
      <path d="M10 7.25v3.5M10 13.35v.1" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.5c.5 4.8 3.2 7.5 8 8-4.8.5-7.5 3.2-8 8-.5-4.8-3.2-7.5-8-8 4.8-.5 7.5-3.2 8-8Z" />
      <path d="M19 3v3M20.5 4.5h-3" />
    </svg>
  );
}

function PromptIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M4 5.75A1.75 1.75 0 0 1 5.75 4h8.5A1.75 1.75 0 0 1 16 5.75v5.5A1.75 1.75 0 0 1 14.25 13H9l-3.75 3v-3.05A1.75 1.75 0 0 1 4 11.25v-5.5Z" />
    </svg>
  );
}
