# Experience brief: premium chat MVP

Status: Implemented and deployed
Owner: Lucas Mori
Last updated: 2026-08-02

## Experience decision

Ask Lucas is a chat product first and a portfolio page second. The page should feel as considered as
a modern commercial AI interface while staying smaller and more transparent than a general-purpose
assistant. The global header carries the single approved photo of Lucas; no other portrait or photograph
appears, and LinkedIn remains the conventional professional profile elsewhere.

## Desired first impression

Within five seconds, a visitor should understand:

1. They can ask about Lucas immediately.
2. Answers are limited to reviewed public sources.
3. Evidence and safe system details are inspectable.
4. The product is intentionally designed rather than assembled from a generic template.

## Application shell

The interface fills the viewport and has three stable layers:

1. A compact global header with Lucas's photo, the Ask Lucas identity, grounded status, appearance
   control, and professional links.
2. A conversation workspace with a small toolbar and independently scrolling content.
3. A bottom composer that remains available without covering messages.

There is no sidebar, marketing hero, authentication, model picker, attachment control, or persisted
history in the MVP.

## Empty state

The opening state uses a non-photographic assistant mark, one concise heading, a short explanation,
and three prompt cards. The cards preview selected work, cross-functional range, and forward-deployed
role fit. They are shortcuts into the same chat API, not static question-and-answer content.

## Conversation

- User prompts are compact, right-aligned bubbles labeled `You`.
- Assistant responses align to an `L` monogram and use a quiet neutral incoming-message surface.
- Follow-up questions remain in the visible in-tab transcript.
- Inline citation controls sit directly beside supported claims.
- Source count, latency, and model mode appear as quiet metadata after a grounded answer.
- Pending, slow, abstained, retryable, rate-limited, and offline states retain the same spatial role as
  a completed answer so the interface does not jump unpredictably.

## Composer

The composer is the most substantial control on the page. It uses a high-contrast send action,
multi-line input, Enter/Shift+Enter guidance, reviewed-source status, privacy copy, character count,
validation, and a stop action while a request is pending. It occupies its own grid row rather than
floating over the transcript.

## Evidence and System Lens

Evidence and System Lens share a native dialog surface. It is a right-side drawer on wide screens and
a bottom sheet on narrow screens. Evidence includes the reviewed excerpt, stable source metadata, and
previous/next navigation. System Lens includes retrieval, provider/model, timing, trace, evaluation,
limitations, and next-experiment data without exposing prompts or hidden reasoning.

## Visual system

- Geist for interface and answer text; Geist Mono for technical metadata.
- Dark mode is the intentional first-load default; a persistent control exposes a complete light mode.
- The palette uses adaptive semantic tokens rather than inverted colors: true-black and charcoal
  surfaces in dark mode, soft system grays in light mode, and system blue for outgoing messages and
  primary actions.
- Translucent header and composer surfaces borrow the clarity of familiar messaging products without
  reproducing their branding or hiding evidence controls.
- Green communicates the reviewed-source/available state; red is reserved for actionable errors.
- Small inline SVG icons avoid an icon-library dependency.
- Motion is limited to short opacity/transform transitions and is removed for reduced-motion users.
- Compact typography and generous whitespace produce polish without reducing answer readability.

## Responsive behavior

Desktop prompt cards use three columns. Narrow screens collapse them to compact rows, hide secondary
header copy, preserve 44-pixel-class touch targets, and keep the composer available. The transcript,
evidence drawer, validation, and long technical identifiers must not create horizontal overflow at a
320-pixel viewport.

## Accessibility

- One visible page heading exists in the empty state.
- Every icon-only control has an accessible name.
- The appearance control has an accurate action label in both states and is keyboard operable.
- Keyboard submit, focus return, Escape dismissal, live status announcements, and visible focus rings
  are required behavior.
- Color is never the only indication of state.
- Reduced-motion preferences are respected.

## Design references

- [Vercel Chatbot template](https://vercel.com/templates/other/chatbot)
- [Vercel AI Elements](https://elements.ai-sdk.dev/)
- [Apple Human Interface Guidelines: Dark Mode](https://developer.apple.com/design/human-interface-guidelines/dark-mode)
