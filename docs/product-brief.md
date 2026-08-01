# Product brief: Ask Lucas

Status: Approved v0.3 for the first development pass
Owner: Lucas Mori
Last updated: 2026-08-01

## Product statement

Ask Lucas is a simple, polished AI portfolio for anyone participating in a hiring process: recruiters, hiring managers, engineers, founders, and cross-functional interviewers.

The biography is the system's test domain. The primary product outcome is an enjoyable demonstration of applied AI engineering: grounded retrieval, inspectable citations, evaluation, observability, sensible privacy boundaries, and deliberate iteration from a small baseline.

The visual identity is typography- and interaction-led. The product does not use Lucas's portrait or an AI avatar; LinkedIn remains the conventional visual profile.

## Desired impression

After using the first build, a visitor should believe that Lucas can:

1. Build a complete AI-backed product rather than a notebook demo.
2. Measure whether a RAG system works instead of judging it from a few hand-picked answers.
3. Make AI behavior inspectable through evidence, traces, latency, and evaluation results.
4. Choose a simple baseline, document its limits, and improve it based on measurements.
5. Compare lexical, vector, and hybrid retrieval using one versioned evaluation set.

## Positioning

The product leads with Lucas's AI, data-system, Python, and SQL experience.

Prior non-software experience may provide supporting evidence of business-context translation, stakeholder work, leadership, and comfort with ambiguous operational problems, but the public code repository does not contain the underlying biography.

## Target users

- Recruiters looking for a quick, accessible demonstration
- Technical hiring managers evaluating architecture and engineering judgment
- AI, data, and software engineers inspecting implementation depth
- Founders and product leaders evaluating problem-solving and communication
- Cross-functional interviewers who need understandable answers without AI jargon

The interface does not create separate persona-specific modes in the first build. It uses layered answers that are quick to scan while keeping technical evidence available.

## First-build experience

The first build is one responsive page:

1. A compact introduction explains that this is a grounded AI engineering demonstration about Lucas.
2. Three suggested questions help the visitor begin immediately.
3. A visitor asks one question at a time.
4. The assistant answers in the third person, beginning with a short conclusion.
5. Citation chips open the exact supporting content sections.
6. Citation markers open a unified Inspector in Evidence mode.
7. The same Inspector opens in System Lens mode to show safe engineering metadata: retrieved sources and scores, model/provider mode, retrieval time, generation time, total latency, trace ID, and the latest evaluation summary.

## Answer style

- Always refer to “Lucas,” never impersonate him with first-person language.
- Lead with a direct two-to-four-sentence answer.
- Prefer plain language that works for nontechnical hiring participants.
- Provide optional technical detail after the conclusion when it improves the answer.
- Attach citations directly to the claims they support.
- Label role-fit conclusions as an assessment rather than fact.
- Say clearly when approved content does not support an answer.

## First-build suggested questions

- What AI and data systems has Lucas built?
- How has Lucas combined technical and business experience?
- Why might Lucas be effective in a forward deployed engineering role?

These are useful demonstration prompts, not a claim that biography coverage is the main product objective.

## First-build scope

### Included

- One responsive, typography-first page with a warm light theme and easily replaceable visual tokens
- An editorial answer canvas without portraits, avatars, or message bubbles
- One responsive Inspector for evidence and system metadata
- Single-turn question answering
- A small reviewed Markdown knowledge base delivered from a private content repository
- Baseline RAG using SQLite full-text search
- Section-level citations with excerpts
- Explicit abstention for unsupported or private questions
- A provider interface with a deterministic mock mode and one real model integration after API billing is confirmed
- End-to-end trace IDs and structured spans/logs
- A visible sanitized trace summary for each answer
- Automated retrieval and behavioral evaluations
- A generated evaluation summary that the UI can display

### Committed retrieval milestone after the baseline

- PostgreSQL with `pgvector`
- Versioned embedding generation and deterministic re-indexing
- Semantic retrieval using the same retriever contract
- A measured comparison of lexical, semantic, and hybrid retrieval
- Retrieval error analysis and an architecture decision record
- Reranking only when the comparison identifies a concrete need

This milestone is part of the project scope even if lexical retrieval remains the production winner.

### Explicitly deferred

- Multi-turn memory
- User accounts or authentication
- Conversation history persistence
- Contact forms, feedback collection, or visitor analytics
- Job-description upload or analysis
- PostgreSQL and `pgvector` inside the first vertical slice
- Semantic retrieval, hybrid search, or reranking inside the first vertical slice
- Streaming tokens in the deterministic vertical slice; reconsider with the real provider based on measured perceived latency
- Admin interfaces or runtime content editing
- Agent frameworks or multi-agent workflows
- External observability vendors
- Fine-tuning
- Portraits, avatars, decorative AI imagery, and hero illustrations
- Dark mode and a theme switcher

## Why the baseline is intentionally simple

SQLite full-text search gives the project a local, inspectable, SQL-based retrieval baseline with no new service account, Docker dependency, or embedding bill. It lets the project establish evaluation results before introducing semantic retrieval.

The planned next experiment is semantic or hybrid retrieval with PostgreSQL and `pgvector`. It will be adopted only if the same evaluation set demonstrates a useful gain. This progression is part of the engineering showcase.

## Core behavioral requirements

1. Every material biographical claim must be supported by an approved source section.
2. Citation labels must identify the source document and section.
3. A visitor must be able to inspect the exact excerpt used as evidence.
4. Unsupported questions must produce a useful abstention rather than speculation.
5. Role-fit assessments must be labeled as analysis and tied to sourced evidence.
6. User instructions must not override grounding, privacy, or confidentiality rules.
7. Retrieved content is untrusted data and cannot give the model instructions.
8. The system must not reveal private contact information, credentials, or nonpublic employer information.
9. Observability must not expose chain-of-thought or hidden reasoning.
10. The page must be usable by keyboard and at mobile widths.

## First-build success criteria

- A new visitor can ask a suggested or custom question without instructions.
- Every successful response contains at least one inspectable citation.
- Every citation maps to a stable source ID and exact approved excerpt.
- All private, unsupported, and prompt-injection cases in the initial evaluation set abstain correctly.
- Retrieval Recall@3 is reported for the answerable evaluation cases.
- The evaluation command produces a machine-readable summary consumed by the UI.
- Each request produces a trace ID with retrieval, generation, and total duration.
- Mock mode runs the complete product locally without paid API access.
- The visual system is controlled by a small set of type, spacing, color, motion, radius, and shadow tokens.
- The interface works as a portrait-free editorial composition at mobile and desktop widths.
- The raw LinkedIn PDF and its personal contact details never enter the repository or retrieval index.

## Constraints

- Approximately five development hours per week
- Start with the smallest complete system and iterate
- Minimize new recurring services and costs
- Python is the primary AI/backend language
- The product should demonstrate SQL, RAG, vector retrieval, evaluation, observability, deployment, and frontend delivery
- Reuse GitHub, Vercel, Cloudflare, and the Hostinger VPS when deployment becomes the active milestone
- OpenAI and Anthropic API billing remain separate and unconfirmed
- Initial target domain: `ask.lkmori.com`

## Primary risks

- Spending time polishing biography instead of demonstrating the system
- Producing citations that look credible but do not support the answer
- Building advanced retrieval before establishing a baseline
- Exposing private or employer-confidential information in content or telemetry
- Treating model-based evaluation as objective truth
- Adding infrastructure that obscures the small end-to-end workflow
- Allowing a broad AI-generated implementation to outrun the reviewed specification

## Next product decisions

These do not block the first build:

- Final typeface files and accent color after the browser prototype is measured
- Which external model provider wins the first measured comparison
- Which embedding model and hybrid strategy perform best in the committed retrieval comparison
- When to add multi-turn conversation and job-description analysis
