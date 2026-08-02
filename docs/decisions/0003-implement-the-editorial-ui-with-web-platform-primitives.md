# ADR 0003: implement the editorial UI with web-platform primitives

Status: Partially superseded by ADR 0008
Date: 2026-08-01

ADR 0008 replaces the editorial visual hierarchy and font direction with a chat-first interface.
The decisions here about CSS Modules, web-platform primitives, native dialog, bounded motion, and a
small client boundary remain in force.

## Context

The experience brief calls for a portrait-free editorial answer canvas with a strict performance budget. The implementation needs enough structure for consistent polish without making a design-system framework the project.

The page uses only a handful of interactive primitives: buttons, a composer, citation controls, status messaging, and one modal Inspector. A broad component system, runtime styling library, or animation library would add more surface than the first page needs.

## Decision

### Styling

- Global CSS contains the reset, font declarations, theme tokens, and document-level defaults.
- CSS Modules contain component-scoped layout and state styles.
- CSS custom properties define type, spacing, colors, borders, radii, shadows, motion duration, and easing.
- No Tailwind, Sass, CSS-in-JS runtime, or general component library in feature 001.
- Use native CSS for responsive layout and state transitions.

The project creates only tokens and primitives actually used by the page. It does not build a speculative reusable design system.

### Typography

- Prototype `Newsreader` for the principal display treatment.
- Prototype `Inter` for body and interface text.
- Use the native `ui-monospace` stack for technical metadata.
- Load fonts through Next.js font optimization so browser requests remain first-party.
- Include only required subsets, styles, and weights; verify the combined critical font payload against the 100 KB target.
- Treat the font pairing as provisional until measured in the browser.

### Inspector

- Implement the shared Evidence/System Lens overlay with the native HTML `<dialog>` element and `showModal()`.
- Include an explicit close button, accessible name, controlled initial focus, Escape behavior, scroll locking, and focus return.
- Style the same element as a right drawer on wide screens and a full-height bottom sheet or full-screen surface on narrow screens.
- Add a third-party dialog primitive only if Playwright, keyboard, and screen-reader tests expose a problem we cannot resolve safely.

### Motion and icons

- Animate only opacity and transform for short state/drawer transitions.
- Respect `prefers-reduced-motion`.
- Use text or small local inline SVGs for the few necessary icons.
- Do not add an icon package or animation runtime in the first slice.

### Client JavaScript boundary

- Keep the page shell, header, opening copy, and footer as server components.
- Use one small client-owned answer workspace for form state and the Inspector.
- Avoid global client state and state-management libraries.
- Do not persist questions or responses in browser storage.

## Why

- The interface is small enough for direct CSS to remain understandable.
- CSS Modules and tokens keep visual decisions explicit and inspectable.
- Fewer runtime dependencies protect the JavaScript and interaction budgets.
- Native dialog behavior supplies a strong accessibility baseline, including modal focus and Escape handling, while remaining testable.
- The approach demonstrates frontend fundamentals rather than a recognizable template default.

## Alternatives considered

### Tailwind CSS

Tailwind would accelerate layout work and is well supported by Next.js. It was not selected because the page is small, the design language is bespoke, and direct tokens/CSS make the typography and interaction decisions easier to review. Revisit if stylesheet consistency becomes a measured problem.

### shadcn/ui or a broad component library

This would provide accessible primitives and fast scaffolding. It was not selected because the first page needs too few components and should not inherit a recognizable product aesthetic.

### Radix Dialog

This is a credible targeted fallback for the Inspector. Native `<dialog>` is selected first to reduce client JavaScript and dependencies. Radix can replace it if accessibility testing demonstrates a concrete gap.

### Motion library

A library would help coordinate complex transitions. The planned motion is limited to a drawer and small state changes, which CSS can express directly.

## Consequences

- More CSS behavior is owned by the project rather than delegated to a framework.
- The native dialog must be verified across supported browsers and assistive technology.
- Typography quality depends on disciplined browser testing, not only design tokens.
- Adding a UI dependency later requires a measured problem and a new or amended decision record.

## Revisit when

- The page grows enough that token/style duplication becomes difficult to maintain.
- Browser or assistive-technology testing exposes a native dialog defect.
- Required motion becomes stateful enough that CSS transitions are fragile.

## Supporting documentation

- [Next.js CSS guidance](https://nextjs.org/docs/app/getting-started/css)
- [MDN dialog element and accessibility behavior](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog)
