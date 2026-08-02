# Feature 007: header profile photo

Status: Approved for delegated implementation
Date: 2026-08-02

## Intent

Replace the abstract `L` mark in the global top-left identity with Lucas's current LinkedIn headshot.
The small photo should make the assistant feel more personal while keeping the interface restrained
and chat-first.

## Requirements

1. Only the top-left global identity mark changes; assistant message monograms and the empty-state
   assistant mark remain unchanged.
2. The UI reads the approved local asset from `/lucas-profile.webp`. It must not hotlink LinkedIn or
   another third-party host.
3. The source is an exact user-provided photo, center-cropped to a square without generated facial
   edits, at least 128 by 128 pixels, and reasonably compressed for the web.
4. The rendered photo is circular, crisp on high-density displays, visually balanced at the current
   2-rem identity-mark size, and separated from dark and light headers by a quiet adaptive border.
5. The image has the accessible name `Lucas Mori`; adjacent identity text and professional links
   retain their current behavior.
6. The 320-pixel header remains on one line without horizontal overflow or reduced touch targets.
7. No raw LinkedIn export, PDF, remote image URL, or additional personal data enters the public
   repository.

## Worker boundary

The supervised worker implements the component, styles, tests, and documentation against the fixed
asset path. The coordinator supplies and reviews the binary asset during integration because the
worker has no private-content or network access.

## Acceptance

- Lint, strict TypeScript, production build, and all existing browser journeys pass.
- Browser coverage verifies one image named `Lucas Mori` with source `/lucas-profile.webp` and no
  horizontal overflow at the mobile viewport.
- Dark and light desktop/mobile screenshots are reviewed after the real asset is added.
- No unrelated interface, retrieval, API, infrastructure, or content behavior changes.

