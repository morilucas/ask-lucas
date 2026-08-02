# Feature 005: Premium chat interface

Status: Implemented and verified locally
Date: 2026-08-02

## Intent

Ask Lucas should feel immediately like a high-quality conversational AI product rather than a
portfolio landing page with a form. The interaction takes visual priority; personal content remains
the demonstration domain and evidence remains inspectable without dominating the conversation.

## Visual direction

Use the strongest conventions of current Vercel AI chat interfaces: a viewport-filling application
shell, restrained monochrome surfaces, compact navigation, a centered empty state, clear user and
assistant message roles, suggestion cards, and a substantial floating prompt composer. Preserve a
distinct Ask Lucas identity through precise typography, an `L` monogram, grounded-status language,
and evidence treatment rather than copying a template or adding a generic product sidebar.

## Requirements

1. The chat surface and composer are visible within the first desktop and mobile viewport.
2. The empty state introduces the assistant in one short heading and presents three polished prompt
   cards without the previous numbered editorial-list treatment.
3. User messages appear as compact right-aligned bubbles; assistant responses use an `L` monogram,
   readable prose, inline citations, and quiet metadata.
4. The composer remains visually anchored near the bottom, supports multi-line input, clearly shows
   send/stop state, preserves all existing validation behavior, and never overlaps content.
5. The top bar provides brand, grounded availability, System Lens, GitHub, and new-conversation
   controls without a large marketing hero.
6. Evidence and System Lens retain their existing functionality, keyboard behavior, and safe data,
   with styling aligned to the new application shell.
7. Existing slow, abstained, offline, rate-limited, retry, mobile, reduced-motion, and focus behavior
   remains truthful and test-covered.
8. The redesign adds no runtime UI library, chat persistence, authentication, file uploads, model
   picker, or streaming contract.

## Acceptance

- Lint, strict TypeScript, and production build pass.
- Existing Playwright journeys pass after intentional selector updates.
- Added browser assertions cover the chat-first empty state and message-role layout.
- Desktop and 320-pixel visual inspection show no overflow, overlap, clipped composer, or hidden
  primary action.

## Design references

- [Vercel Chatbot template](https://vercel.com/templates/other/chatbot)
- [Vercel AI Elements](https://elements.ai-sdk.dev/)
