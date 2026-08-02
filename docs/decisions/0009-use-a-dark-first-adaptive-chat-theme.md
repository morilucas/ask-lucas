# ADR 0009: use a dark-first adaptive chat theme

Status: Accepted
Date: 2026-08-02

## Context

The first chat redesign established the correct product structure, but its near-white visual system
did not express the familiar, focused quality Lucas wanted from a modern messaging experience. Ask
Lucas also needs to demonstrate polish without introducing a UI framework or turning appearance into
an architectural dependency.

## Decision

Ask Lucas defaults to a custom dark appearance and provides a persistent light option in the global
header. A small pre-hydration script reads only the appearance preference and applies it before the
page is painted. Questions and conversation history remain in memory only.

The interface uses semantic CSS variables for both appearances. The palette and message roles draw
on iMessage conventions—system blue outgoing messages, neutral incoming messages, soft grays,
rounded geometry, and translucent chrome—but use original components and retain Ask Lucas branding,
citations, telemetry, and evidence surfaces.

The theme control remains a narrow client component. All styling continues to use CSS Modules and
web-platform primitives under ADR 0003.

## Alternatives considered

### Follow the operating system automatically

This is conventional, but it conflicts with the intentional dark first impression. It may be added
later as a third `System` choice if user feedback justifies the extra control complexity.

### Dark mode only

This is simpler but removes visitor choice and makes it harder to demonstrate that all semantic
states were designed across appearances.

### Install a theme or component library

The application needs one preference and a small token set. A dependency would add more surface area
than value and weaken the implementation's inspectability.

## Consequences

- Every new color must be expressed through a semantic token and checked in both appearances.
- Appearance is the only value stored in the visitor's browser.
- A small inline initializer is necessary to avoid a light/dark flash on reload.
- Visual regression review must cover dark and light desktop and mobile states.

