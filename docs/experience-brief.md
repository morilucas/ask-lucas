# Experience brief: typography-first MVP

Status: Approved for the first browser prototype
Owner: Lucas Mori
Last updated: 2026-08-01

## Experience decision

Ask Lucas will use typography, writing, spacing, and interaction as its identity. It will not use a portrait, avatar, hero illustration, decorative AI imagery, or photography in the first release. LinkedIn remains the place for Lucas's photograph and conventional professional profile.

The product should feel like an editorial answer canvas rather than a conventional chat application or technical dashboard.

## Desired first impression

Within five seconds, a visitor should understand:

1. They can ask about Lucas's work immediately.
2. Answers come from reviewed public evidence.
3. The experience is restrained, intentional, and technically credible.

After one answer, a visitor should notice that the product makes evidence and system quality inspectable without requiring technical knowledge.

## Experience principles

### Simple in scope, complete in behavior

The page has one primary action and displays only the current question and answer. Polish comes from hierarchy, responsive behavior, copy, states, and details—not feature count.

### Answer canvas, not chat transcript

Questions become headings and answers render as editorial prose. There are no avatars, speech bubbles, artificial personas, or permanent conversation history.

### Evidence beside claims

Citation markers sit next to the claims they support. A visitor can inspect the exact approved excerpt without losing their place.

### Complexity on demand

The default view is calm and nontechnical. Evidence and engineering metadata live in one reusable Inspector opened by citations or the System Lens control.

### Honest system feedback

The interface displays only backend states it actually knows. The deterministic first slice uses one pending state instead of simulating retrieval and generation stages. Streaming may be added with the real provider if it measurably improves perceived latency.

### Fast before decorative

Typography, whitespace, and immediate feedback create the visual quality. Motion explains state or spatial relationships and never delays interaction.

## Page anatomy

### Compact header

- `Ask Lucas` wordmark
- Descriptor: `Grounded AI portfolio`
- `System Lens` control
- GitHub link when the repository is public
- No navigation menu, portrait, or theme switcher

### Opening

Draft interface copy:

- Eyebrow: `AI ENGINEERING PORTFOLIO`
- Heading: `Ask about Lucas's work.`
- Explanation: `Explore his experience, projects, and approach through answers grounded in reviewed public sources.`

The heading, explanation, composer, and suggestions fit within the initial desktop viewport at common laptop sizes.

### Question composer

- A visible label, not placeholder-only identification
- Placeholder: `Ask about his experience, projects, or approach…`
- One submit control with a text or locally drawn arrow treatment
- Input stays at least 16 CSS pixels to avoid mobile zoom
- The submitted question remains visible while the answer is pending

### Suggested questions

The suggestions look like three editorial rows rather than rounded prompt pills. Each one previews a different system capability:

1. Direct evidence retrieval: `What AI and data systems has Lucas built?`
2. Cross-source synthesis: `How has Lucas combined technical and business experience?`
3. Labeled assessment: `Why might Lucas be effective in a forward deployed engineering role?`

### Answer canvas

- Submitted question as a compact heading
- Direct conclusion first
- Optional supporting detail second
- Inline citation markers adjacent to material claims
- Quiet metadata row: source count, total duration, and `Inspect answer`
- `Ask another question` returns focus to the composer and replaces the current answer only after the next submission

The readable answer column is approximately 680–720 CSS pixels wide. It must not expand into long desktop lines.

### Unified Inspector

Evidence and System Lens reuse one overlay shell with two modes. This avoids two competing panel systems.

On wide screens, it opens as a right-side drawer without reflowing the answer. On narrow screens, it becomes a full-height bottom sheet or full-screen panel.

Evidence mode displays:

- Source title
- Section heading
- Exact approved excerpt supplied to the model
- Stable source ID as secondary metadata
- Previous and next controls when an answer has multiple citations

System Lens mode displays:

- Request flow: `Retrieve → Validate citations → Answer`
- Retrieval method and retrieved source IDs/scores
- Provider mode and model identifier
- Real retrieval, generation, and total durations
- Trace ID with copy control
- Latest evaluation version, pass count, and Recall@3
- One plain-language limitation and the next planned experiment

The Inspector never exposes system prompts, hidden reasoning, chain-of-thought, credentials, private inputs, or raw exceptions.

### Minimal footer

- Disclosure that this is an AI representation using reviewed public sources
- LinkedIn link
- GitHub link when public
- Short privacy statement: conversation content is not persisted by default

## Responsive wireframes

These wireframes define hierarchy rather than final dimensions or decoration.

### Initial desktop state

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Ask Lucas  ·  Grounded AI portfolio             System Lens     GitHub    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                 AI ENGINEERING PORTFOLIO                                   │
│                 Ask about Lucas's work.                                    │
│                 Explore his experience, projects, and approach             │
│                 through reviewed public evidence.                          │
│                                                                            │
│                 Ask a question                                             │
│                 ┌───────────────────────────────────────────┬─────┐         │
│                 │ Ask about his experience or projects…    │  ↑  │         │
│                 └───────────────────────────────────────────┴─────┘         │
│                                                                            │
│                 01  What AI and data systems has Lucas built?              │
│                 02  How has he combined technical and business work?       │
│                 03  Why might he fit forward deployed engineering?         │
│                                                                            │
│                 Answers cite reviewed public sources.                      │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ AI disclosure                                      LinkedIn     GitHub     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Answer with Inspector open

```text
┌─────────────────────────────────────────────────────┬──────────────────────┐
│ Ask Lucas                              System Lens   │ Evidence         ×   │
├─────────────────────────────────────────────────────┤                      │
│                                                     │ Acme — AI & Data     │
│ What AI and data systems has Lucas built?           │ Solutions Specialist │
│                                                     │                      │
│ Lucas has built … [1] His work also includes … [2]  │ Exact approved       │
│                                                     │ excerpt used as      │
│ Supporting detail continues as readable prose.      │ evidence appears     │
│                                                     │ here.                │
│ 2 sources · 840 ms · Inspect answer                 │                      │
│                                                     │ experience:acme…     │
│ Ask another question                                │ Previous · Next      │
│                                                     │                      │
└─────────────────────────────────────────────────────┴──────────────────────┘
```

### Mobile answer state

```text
┌──────────────────────────────┐
│ Ask Lucas        System Lens │
├──────────────────────────────┤
│ What AI and data systems     │
│ has Lucas built?             │
│                              │
│ Lucas has built … [1]        │
│ Supporting detail … [2]      │
│                              │
│ 2 sources · Inspect answer   │
│                              │
│ Ask another question         │
│                              │
├──────────────────────────────┤
│ Inspector opens as a modal   │
│ bottom sheet/full screen.    │
└──────────────────────────────┘
```

## Interaction states

| State | Required behavior |
|---|---|
| Empty | Composer and suggestions are immediately usable without instructions |
| Invalid input | Explain empty or oversized input next to the composer and preserve focus |
| Pending | Preserve the question, prevent duplicate submission, and show one honest status: `Reviewing approved sources…` |
| Slow response | After eight seconds, calmly report that the answer is taking longer than usual |
| Grounded answer | Render only validated citations and enable Evidence and System Lens inspection |
| Abstention | Treat insufficient evidence as a successful safety outcome, explain it plainly, and suggest two supported questions |
| Recoverable error | Preserve the question and provide Retry plus a copyable trace ID |
| Offline/interrupted | Explain that the connection was interrupted; never present a partial answer as complete |
| Reset | Return focus to the composer without retaining a visible transcript |

## Visual system

### Typography

Prototype direction:

- Display: `Newsreader`, used only for the principal heading and selective answer emphasis
- Interface and body: `Inter`
- Technical metadata: native `ui-monospace` system stack

Use no more than two self-hosted/subset WOFF2 families. The combined critical font payload target is 100 KB or less. Final font selection is accepted only after browser rendering and performance are tested.

Type requirements:

- Body copy is at least 17 CSS pixels on standard layouts
- Form controls are at least 16 CSS pixels
- Prose line height is approximately 1.5–1.65
- Long prose remains between approximately 45 and 75 characters per line
- Hierarchy comes from scale, weight, spacing, and rules—not a collection of decorative cards

### Color

- One warm light canvas
- Near-black text
- One restrained accent color for action and focus
- Muted text and rules that still pass contrast requirements
- No dark mode in the first release; tokens should make a future theme possible
- No gradients, glass effects, glowing decoration, or ornamental background animation

### Motion

- Motion communicates state or where an overlay came from
- Most transitions last 120–220 milliseconds
- Prefer opacity and transform
- No looping animation, fake progress, shimmer skeleton, or letter-by-letter typing effect
- `prefers-reduced-motion` removes movement without hiding state changes

## Accessibility quality bar

- Target WCAG 2.2 AA
- Text contrast at least 4.5:1; control and focus contrast at least 3:1
- Interactive targets at least 44×44 CSS pixels
- Complete ask → answer → citation → close flow by keyboard
- Visible focus, logical order, Escape-to-close, focus trap, and focus return for the Inspector
- Semantic landmarks, real form controls, labeled input, skip link, and useful document title
- One polite live region for status changes; never announce individual streamed tokens
- Zero serious or critical automated accessibility violations
- Manual verification with a screen reader before public release

## Performance quality bar

Internal production targets at the 75th percentile:

| Measure | Target |
|---|---:|
| Largest Contentful Paint | ≤ 1.8 seconds |
| Interaction to Next Paint | ≤ 150 milliseconds |
| Cumulative Layout Shift | ≤ 0.03 |
| Mobile Lighthouse Performance | ≥ 95 |
| Lighthouse Accessibility | 100 |
| Initial route JavaScript | ≤ 150 KB gzip |
| CSS | ≤ 30 KB gzip |
| Cold initial transfer | ≤ 500 KB |
| Visible feedback after submit | ≤ 100 milliseconds |
| Local deterministic response p95 | ≤ 300 milliseconds |

No third-party browser scripts are allowed in the first release. Real-provider latency is measured separately from application overhead.

## Validation viewports

At minimum, manually and visually test:

- 320×568
- 390×844
- 768×1024
- 1280×800
- 1440×900

The page must not scroll horizontally at 320 CSS pixels, and the composer must remain usable when a mobile software keyboard is visible.

## Explicit non-goals

- Personal portrait, avatar, or illustration
- Conventional message bubbles or chat transcript
- Multiple routes or navigation architecture
- Persistent conversation history
- Dark mode or theme switcher
- Dashboard charts
- Animated architecture diagrams
- Rich generative component library
- Decorative loading sequences
- A general-purpose personal AI agent

## Prototype acceptance

The experience direction is ready to leave wireframes when:

1. Empty, pending, answer, abstention, error, and Inspector states are represented.
2. Desktop and mobile compositions preserve the same information hierarchy.
3. A citation can be opened, navigated, closed, and returned from by keyboard.
4. The typography works without imagery or decorative filler.
5. The System Lens remains useful but visually secondary.
6. The implementation can meet the performance budgets without removing core behavior.
