# Feature 006: dark-first adaptive chat theme

Status: Implemented and deployed
Date: 2026-08-02

## Intent

Ask Lucas should open as a refined dark chat and offer an equally complete light appearance. The
visual language may borrow the clarity of iMessage—system blue, distinct message roles, rounded
surfaces, and translucent chrome—without copying Apple assets or hiding the product's evidence and
engineering controls.

## Requirements

1. A visitor with no saved preference sees the dark appearance on first paint.
2. A visible header control switches between dark and light appearances, has an accurate accessible
   name, works by keyboard, and persists the choice in local browser storage.
3. A saved choice is applied before the page becomes visible so reloads do not flash the other theme.
4. Both appearances use semantic design tokens for canvas, text, surfaces, borders, states, message
   roles, overlays, and shadows; components must not depend on a simple color inversion.
5. User messages use a blue outgoing-message treatment. Assistant messages use a quiet neutral
   incoming-message treatment while preserving citations, metadata, errors, and pending states.
6. The header and composer use restrained translucency while remaining legible without blur support.
7. Empty, conversation, evidence, System Lens, error, and mobile states remain usable in both themes.
8. Theme persistence is the only new client-side storage; questions and conversations remain
   unpersisted.

## Non-goals

- Following the operating-system preference automatically; dark is an intentional product default.
- Reproducing the Messages application or using Apple-owned assets.
- Adding a component library, animation library, or persistent user profile.
- Changing retrieval, answer generation, citations, or telemetry.

## Acceptance

- Automated browser coverage proves dark default, light switching, and persistence across reload.
- Existing chat, inspector, validation, slow-response, rate-limit, and mobile overflow journeys pass.
- Lint, strict TypeScript, and the production build pass.
- Desktop and 320-pixel screenshots are reviewed in dark and light appearances.
- Production at `ask.lkmori.com` is manually verified after deployment.

## Verification record

- Lint, strict TypeScript, and the production Next.js build passed.
- Fourteen Edge journeys passed across desktop and 320-pixel mobile projects.
- Dark empty and light conversation states were visually reviewed at both viewport sizes.
- Production returned HTTP 200 with the dark default and theme control in the rendered document.
- The unchanged API returned HTTP 200 with build version `652f14c`.
- Web release commit: `fa581a3`.
