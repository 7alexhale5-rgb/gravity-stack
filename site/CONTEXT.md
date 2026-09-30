# Docs-site room: the public Next.js documentation site

One job: change what the public site shows. Paths relative to the repo root.

## Inputs

- Content to document: `docs/*.md` (the deep-dive source), `toolkit/` behavior for any
  toolkit-facing page.
- Code: `site/src/lib/data/` (single source of truth for the data layer per root `CLAUDE.md`),
  `site/src/` app routes and components.
- Convention: Tailwind v4 uses CSS `@theme` blocks — no `tailwind.config.ts`; Server Components
  by default, Client only when interactivity is required.
- Missing input: a page describing a toolkit/docs behavior that has no source in `docs/` or
  `toolkit/` — stop, the site must not state a behavior the code doesn't have.

## Process

1. `cd site && npm run dev` to preview.
2. Change the route/component; keep data in `site/src/lib/data/`, not scattered inline.
3. `cd site && npm run build` before considering the change done.

## Outputs

- Changed files under `site/src/`.

## Human check

Alex spot-checks each changed page against its source in `docs/` or `toolkit/`. Pass: no page
states a behavior the code doesn't have. Fail: correct before merge.
