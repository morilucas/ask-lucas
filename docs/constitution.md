# Project constitution

Version: 0.1
Adopted: 2026-08-01

These principles govern product specifications, architecture, implementation, evaluation, and deployment. Exceptions require an explicit documented decision.

## 1. Evidence before eloquence

The assistant must prefer a limited, supported answer over a persuasive unsupported answer. Material claims require traceable evidence from approved content.

## 2. Curated public knowledge only

Raw resumes, LinkedIn exports, private messages, internal documents, personal contact details, and credentials are never public retrieval sources. Production ingestion reads only a reviewed directory supplied outside the public code repository; `examples/` contains synthetic development data.

## 3. Privacy and employer confidentiality

The system must not reveal or infer sensitive personal information or nonpublic employer information. Public descriptions of named internal products are allowed only at the level approved by Lucas; underlying data, prompts, documentation, metrics, and implementation details remain out of scope.

## 4. Specifications are the source of intent

Each meaningful feature begins with user value, behavioral requirements, acceptance criteria, edge cases, and non-goals. Architecture and code implement the specification rather than replacing it.

## 5. Evaluation-driven AI development

Representative evaluation cases exist before optimization. Changes to models, prompts, retrieval, chunking, or orchestration are compared against the same cases for correctness, citation quality, abstention, latency, and cost.

## 6. Small, reviewable vertical slices

Build the thinnest end-to-end behavior that creates user value. Avoid whole-application generation, speculative abstractions, and large unreviewed AI-produced diffs.

## 7. Simplicity with recorded tradeoffs

Choose the least complex design that satisfies measured requirements. New frameworks, databases, services, and agent patterns require a stated problem and a documented tradeoff.

## 8. Secure and observable by design

Threat modeling, secret handling, dependency review, rate limiting, auditability, backups, and useful operational telemetry are part of the design. They are not post-launch polish.

## 9. Provider and model flexibility

Application behavior must not depend unnecessarily on one model identifier or vendor-specific response shape. Provider-specific capabilities may be used behind a narrow interface when they deliver measured value.

## 10. Human accountability for AI-generated work

AI may research, propose, implement, test, and document. A human remains accountable for product intent, architecture, security boundaries, factual approval, diff review, and acceptance.

## 11. Accessible, honest communication

The employer experience should be clear to technical and nontechnical users, accessible on common devices, transparent about limitations, and explicit that the assistant is an AI representation based on approved sources.

## Definition of ready

A feature is ready for implementation when it has:

- A user and user need
- Clear in-scope and out-of-scope behavior
- Testable acceptance criteria
- Known privacy and security implications
- Representative evaluation or test cases
- Resolved decisions or explicitly bounded unknowns

## Definition of done

A feature is done when:

- Acceptance criteria pass
- Automated tests and relevant AI evaluations pass
- Loading, error, empty, and unsafe-input states work
- Security and privacy impacts were reviewed
- Logging is sufficient to diagnose failures without recording sensitive content unnecessarily
- Documentation and decisions match the implementation
- The deployed behavior was manually verified
