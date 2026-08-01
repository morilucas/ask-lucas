# AI engineering skills showcase

Status: Working scope
Last updated: 2026-08-01

## Purpose

This document maps current applied AI and forward deployed engineering signals to evidence the Ask Lucas project can honestly produce. It is a prioritization tool, not a checklist of fashionable technologies.

A skill counts as showcased only when a visitor or repository reviewer can inspect working evidence: product behavior, code, tests, evaluation results, traces, deployment artifacts, or a documented tradeoff. A dependency listed in `package.json` or `pyproject.toml` is not evidence by itself.

## Directional market signal

The roles reviewed consistently emphasize:

- owning discovery, scoping, system design, implementation, rollout, and measurement;
- building full-stack AI products with Python and JavaScript or TypeScript;
- RAG, data ingestion, retrieval, structured outputs, and model integration;
- evaluations, monitoring, auditability, security, and production reliability;
- product judgment, communication, and translating ambiguous business needs;
- making explicit tradeoffs among scope, speed, quality, cost, and operational risk.

This is a directional sample of current roles, not a statistical survey of the complete labor market.

## Priority matrix

| Capability companies seek | Evidence Ask Lucas will produce | Project priority | Decision |
|---|---|---:|---|
| Product discovery and problem framing | Product brief, narrow hiring use case, user journeys, success measures, and scope decisions | Essential | Include from the start |
| System design and tradeoff judgment | Architecture boundaries, ADRs, baseline-to-improvement experiments, and cost/reliability decisions | Essential | Include from the start |
| End-to-end product delivery | Public responsive product spanning browser, API, retrieval, model, and deployment | Essential | Include from the start |
| Python backend engineering | Typed FastAPI service, ingestion pipeline, retrievers, provider adapters, tests | Essential | Include from the start |
| TypeScript and product-quality frontend | Next.js interface, truthful asynchronous states, citations, accessibility, and performance budgets | Essential | Include from the start; measure streaming with the real provider |
| SQL and relational data modeling | Deterministic content schema, queries, migrations, and retrieval analytics | Essential | Start with SQLite; deepen with PostgreSQL |
| LLM integration and context engineering | Provider-neutral adapter, grounded prompt contract, structured output, citation validation, abstention | Essential | Include from the start |
| RAG fundamentals | Ingestion, chunking, retrieval, evidence assembly, citations, and grounding tests | Essential | Include from the start |
| Vector databases and embeddings | PostgreSQL with pgvector, embedding pipeline, semantic search, index choices, and measured comparison | High | Committed second retrieval milestone |
| Hybrid retrieval and reranking | Compare FTS5, vector, and hybrid retrieval on the same cases; add reranking only if useful | High | Include in retrieval experiment |
| AI evaluation | Versioned dataset, Recall@k, citation correctness, abstention, groundedness rubric, regression gate | Essential | Include from the start |
| Observability and LLMOps | Trace IDs, stage spans, structured logs, latency/token/cost metrics, sanitized System Lens | Essential | Include from the start |
| Reliability engineering | Timeouts, bounded retries, schema validation, failure states, health checks, and graceful degradation | High | Include before public launch |
| AI safety and security | Prompt-injection tests, untrusted-context boundary, privacy rules, secret scanning, input limits, rate limiting | Essential | Include before public launch |
| Deployment and operations | Docker, CI/CD, Vercel web deployment, VPS API/database, backups, migrations, rollback notes | High | Include before public launch |
| Performance engineering | Web Vitals budget, immediate feedback, payload/JavaScript budget, API latency measurement, and measured streaming when useful | High | Include before public launch |
| Accessibility and UX quality | Keyboard navigation, semantic controls, contrast, reduced motion, mobile behavior, automated checks | High | Include before public launch |
| Documentation and communication | Brief, specs, ADRs, architecture diagram, runbook, limitations, and concise case study | Essential | Continuous |
| Cost engineering | Per-request cost capture, budgets, caching decisions, model comparison, low-cost deployment | High | Include with real model integration |
| Model/provider evaluation | Same cases run across at least two models when budget permits | Medium | Later experiment, not an architectural dependency |
| User feedback and product analytics | Privacy-conscious events and explicit answer feedback connected to eval cases | Medium | Add after real visitors exist |
| Tool calling and MCP | A real, permissioned tool with tests and audit trail | Low for this use case | Defer until a genuine user workflow needs it |
| Agent workflows | Bounded multi-step workflow with checkpoints, evaluation, and recovery | Low for the initial use case | Do not add solely for the keyword |
| Asynchronous queues and durable workflows | Background ingestion/evaluation or another real long-running job | Low at current scale | Defer until synchronous operation is insufficient |
| Authentication and authorization | Identity, roles, permissions, and protected operations | Low for a public read-only portfolio | Exclude unless an admin workflow is added |
| Fine-tuning | Dataset, baseline, trained model, and measured improvement over prompting/RAG | Low | Exclude; poor fit for the problem and budget |
| Self-hosted model inference | Serving, batching, GPU utilization, scaling, and model operations | Low | Exclude; expensive and distracts from applied AI delivery |
| Kubernetes and multi-cloud | Operationally justified orchestration and portability | Low | Exclude; unjustified for one small service |

## Why vector retrieval belongs in the project

### Benefits

- It appears directly in many RAG-oriented AI engineering descriptions.
- It demonstrates embeddings, semantic similarity, PostgreSQL, indexes, ingestion, and data migrations.
- It gives Lucas a concrete experiment to discuss rather than a generic architecture claim.
- Hybrid retrieval is especially relevant because résumé questions contain both exact entities and semantic intent.
- `pgvector` can run inside the existing PostgreSQL deployment instead of adding a specialized hosted database.

### Costs and risks

- It adds an embedding model, versioning, re-indexing, database operations, and potentially API cost.
- The content set is small enough that semantic search may not improve answer quality.
- Adding it before a baseline can hide retrieval problems behind extra machinery.
- A vector database without retrieval metrics looks like résumé-driven architecture.

### Decision

Build it as a measured second retrieval implementation. The project will compare:

1. SQLite FTS5 lexical retrieval;
2. PostgreSQL/pgvector semantic retrieval;
3. a hybrid strategy combining both;
4. reranking only if the error analysis identifies a reason for it.

The best measured strategy becomes the production default. The comparison remains documented regardless of the winner.

## Scope rule

Add a skill when all three conditions hold:

1. It is meaningfully requested by target roles.
2. The product has a natural use for it.
3. We can create visible, testable evidence of competence.

Defer or remove it when it exists mainly to increase the technology count, cannot be evaluated, or makes the product less reliable and polished within the five-hour-per-week constraint.

## Sources reviewed

- [OpenAI — Forward Deployed Engineer](https://openai.com/careers/forward-deployed-engineer-%28fde%29-seattle-seattle/)
- [OpenAI — Software Engineer, Enterprise AI Platform](https://openai.com/careers/software-engineer-enterprise-ai-platform-san-francisco/)
- [OpenAI — Product Engineer, Enterprise AI Platform](https://openai.com/careers/product-engineer-enterprise-ai-platform-san-francisco/)
- [OpenAI — Solutions Engineer, Core Enterprise](https://openai.com/careers/solutions-engineer-core-enterprise-san-francisco/)
- [Anthropic — Careers and Applied AI roles](https://www.anthropic.com/careers/jobs?lang=us)
- [Palantir — Working Inside Existing Systems](https://www.palantir.com/careers/getting-hired/working-inside-existing-systems/)
- [Jeeves — Senior AI Engineer](https://jobs.lever.co/tryjeeves/66241934-7138-4d7d-8b05-a211ec5d6e24)
- [Ro — Senior AI Engineer](https://jobs.lever.co/ro/81dd41da-ba24-435b-83c4-bd19a312744b)
