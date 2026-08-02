# ADR 0008: make chat the primary interface

Status: Accepted
Date: 2026-08-02

## Context

The first deployed interface treated the conversation as an element inside an editorial portfolio
page. Its oversized introduction and numbered question list were visually polished, but the product
did not immediately feel like a high-quality AI chat. Lucas's evaluation after using production was
that the interaction should resemble the clarity and finish of Vercel's current chat templates.

The behavioral system was already complete: bounded multi-turn chat, grounded answers, citations,
abstention, error recovery, evidence inspection, and System Lens. The problem was hierarchy and
interaction design rather than the API or retrieval architecture.

## Decision

Ask Lucas uses a viewport-filling chat application shell:

- a compact product header replaces the marketing hero;
- the empty state introduces the assistant and three prompt cards within the first viewport;
- user prompts use restrained right-aligned bubbles;
- assistant answers use a non-photographic `L` monogram, readable prose, inline citations, and quiet
  metadata;
- the composer occupies a stable bottom row and never overlays the transcript;
- Evidence and System Lens remain secondary overlays;
- Geist and Geist Mono replace the editorial serif pairing;
- CSS Modules, local inline SVGs, native dialog, and the existing API remain in place.

The implementation borrows established chat conventions without adopting Vercel AI SDK, AI
Elements, Tailwind, shadcn/ui, persistence, authentication, attachments, or a model picker. Those
features do not improve the current employer-facing use case enough to justify their surface area.

## Consequences

- Visitors immediately understand that the primary action is a conversation.
- The application feels more familiar while its evidence and system transparency remain distinct.
- The page uses available height rather than document length, so the transcript owns scrolling and
  the composer remains stable on desktop and mobile.
- Browser tests run one file per desktop/mobile project so their synthetic concurrency matches the
  production limit of two simultaneous generations.
- The visual direction in the original experience brief and ADR 0003 is superseded; ADR 0003's
  implementation-primitives decision remains active.

## Revisit when

- measured user sessions show that conversation history or navigation is needed;
- streaming is added to the API contract;
- the number of shared interactive primitives makes direct CSS Modules difficult to maintain;
- accessibility testing identifies a native-dialog or viewport-shell defect.

## References

- [Vercel Chatbot template](https://vercel.com/templates/other/chatbot)
- [Vercel AI Elements](https://elements.ai-sdk.dev/)

