# ADR 0007: use a supervised Claude Code worker for isolated implementation

Status: Accepted
Date: 2026-08-02

## Context

Ask Lucas is developed part-time and showcases applied AI engineering, including deliberate use of AI as a tool with human oversight. Decisions on architecture, review gates, deployment, and integration must remain under clear human control. Implementation work can be parallelized and distributed, but governance cannot.

The project currently operates in a single working tree with shared development history and access. As implementation scales, coordinating review and preventing accidental state changes becomes harder. Using Claude Code as an implementation assistant in a shared context creates risk: no clear boundary between autonomous changes and supervised work, no isolated artifact for review before integration, and implicit assumptions about access and authority.

## Decision

Implementation work will be split into bounded tasks assigned to Claude Code running in an isolated Git worktree. Claude Code is a non-root implementation worker; Codex, the primary AI coordinator, remains responsible for architecture, code review, integration decisions, deployment, and changes to `main` under Lucas's direction. Lucas retains product authority and final human accountability.

### Worker isolation and scope

- Claude Code works only in a dedicated branch-specific worktree created by the coordinator.
- The worktree contains only the public repository, no private content or secrets.
- The worker may inspect, read, and edit files within its assigned worktree.
- The worker may run approved local checks: linting, formatting, type checking, and tests.
- The worker creates a single local commit for review; it does not push, rebase, or modify branches.
- The worker has no access to Docker, sudo, GitHub credentials, VPN, or production secrets.
- The worker cannot change `main` or other protected branches.
- The worker cannot push to any remote or access any hosting infrastructure.
- These controls are defense in depth, not a complete security boundary; coordinator review remains required.

### Review and integration

- Every worker result—diff, tests, evaluation—is reviewed completely by the coordinator before any action.
- Integration decisions (merge, rebase, squash, discard) remain with the coordinator.
- The coordinator is accountable for all merged code and its consequences.
- Tests required by the project specification must pass before the coordinator considers integration.
- Structural changes or new dependencies trigger documented tradeoff review using the ADR process.

### Task definition

Each task is conveyed as a written contract specifying:

- The objective (what is being built or fixed).
- Required context (which files to read, which specifications to follow).
- Allowed scope (which files may change, which are off-limits).
- Acceptance criteria (how the work will be measured).
- Non-goals (what is explicitly out of scope).
- Handoff requirements (what review and checks must be run before the work is complete).

This structured handoff ensures that implicit assumptions about intent, authority, or risk tolerance are made explicit.

## Why

### Isolation and traceability

- Confining a worker to a clean worktree provides defense-in-depth boundaries: account, permissions, worktree, credential, and tool controls reduce the risk of unintended changes affecting parallel work or the development branch. These boundaries are not a complete security guarantee; coordinator review before integration provides the final gate and remains essential to security and accountability.
- A single local commit becomes a complete, reviewable, and traceable artifact.
- The coordinator retains a clear decision point before any state change.

### Human accountability

- Explicit review gates and documented reasoning ensure that humans remain accountable for product decisions and risk.
- Clear boundaries make it possible to evaluate whether a worker respected its assigned scope.

### Parallelizable work

- Multiple bounded tasks can be assigned to the worker in sequence or (in future) to multiple workers in parallel.
- Each task has a separate, independent worktree, reducing conflicts from parallel changes. Task definition, review, and integration retain coordination cost, but independent worktrees reduce resource blocking and state conflicts.

### Testability and quality

- Isolated environments make it easier to verify that changes are correct and do not have unexpected side effects.
- Structured acceptance criteria and review gates mean that work is measured against the specification, not just against the code the worker happened to write.

### Separation of roles

- Implementation intelligence and code generation are distinct from architecture, product judgment, deployment, and security decisions.
- This mirrors software engineering best practice: review and accountability remain with the maintainer, not the tool.

## Alternatives considered

### Sharing the coordinator's working tree

The coordinator and worker could collaborate in the same working tree on the same branch. This would reduce handoff overhead and allow immediate integration. However:

- The coordinator loses a clear decision point before changes are applied.
- Parallel work becomes difficult; the coordinator and worker cannot work independently.
- Changes are incremental and interleaved, making it harder to review the complete intent or trace responsibility.
- Accidentally committing incomplete work or exposing secrets becomes easier.

This was rejected because the clarity and safety of an isolated boundary outweighs the convenience of in-place collaboration.

### Autonomous push and deployment authority

The worker could be granted push authority to its own branch and (in future) authority to deploy. This would eliminate the handoff step between worker completion and integration. However:

- The coordinator loses visibility and control over what enters the main development history.
- Mistakes or security issues cannot be caught before they are in the version-control history.
- The worker's scope and accountability become ambiguous: is it responsible for choosing when work is ready, or only for writing code?
- Deployment decisions require human judgment about risk, dependencies, and coordinated timing, which cannot be delegated.

This was rejected because the coordinator's explicit decision remains essential for accountability, and automated push introduces risk without corresponding benefit for a part-time project.

### GitHub Actions for implementation

GitHub Actions could run predefined implementation tasks (generate code, refactor, apply linting) autonomously on pull requests. This would:

- Remove the need for interactive Claude Code and a human-assigned task contract.
- Reduce the number of separate tools and integrations.

However:

- GitHub Actions is designed for deterministic, well-defined workflows, not for iterative problem-solving or architectural decisions.
- The assistant would have less ability to reason about product intent, evaluate tradeoffs, or ask clarifying questions.
- Debugging failures and recovering from mistakes becomes harder in a CI environment.
- The approach is better suited to repetitive tasks than to the exploratory, specification-driven work that dominates this project's early phases.

This was rejected in favor of interactive Claude Code, which permits richer dialogue, immediate feedback, and better judgment about ambiguous requirements.

## Consequences

### Handoff overhead

The isolated-worker pattern introduces a handoff step: the coordinator must be available to review and integrate the worker's result, and the worker must wait for feedback or further tasks. On a part-time project, this can introduce scheduling latency. However:

- The cost is acceptable because the project is not blocked by individual task latency; multiple tasks can be staged and batched.
- The clarity gained in review, responsibility, and traceability justifies the delay.
- As the project scales, parallel workers can be assigned to independent tasks simultaneously, amortizing the handoff cost.

### Diff review discipline

Every change requires human review before integration. This means:

- Reviewers must understand the change and its consequences.
- Test results and linting are necessary but not sufficient; human judgment is required.
- The coordinator cannot integrate without reading and approving the diff.

This is a design intent, not a limitation. Review discipline is part of the project's commitment to human accountability.

### No anonymous changes

Every implementation task is explicitly assigned, scoped, and reviewed. There are no silent, automated, or implicit changes to the codebase. This may feel heavier than a fully autonomous system, but it aligns with the project's principle that humans remain accountable for AI-assisted work.

## Revisit when

- The project grows to require multiple simultaneous implementation workers and handoff overhead becomes a measured bottleneck.
- A category of work is so repetitive and well-specified that autonomous action (e.g., dependency updates, automated refactoring) becomes both safe and valuable.
- The coordinator's review capacity becomes the limiting factor in task throughput, justifying a shift toward more autonomous worker authority.

If any of these occurs, the decision should be revisited with a new ADR that documents the measured costs and the specific scope of autonomy being granted.
