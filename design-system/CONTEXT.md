# Design-system room: design tokens and the visual spec

One job: change the site's visual tokens in one place and carry them into `site/`. Paths
relative to the repo root.

## Inputs

- `design_spec.json` (root): the current token spec, "Industrial Technical" (colors,
  typography, layout radius/spacing, component recipes, text and icon conventions). It stays
  at the root; no script reads it, it is the reference the site's CSS is written from.
- `design-system/gravity-stack/MASTER.md`: the generated page-rules master (palette, type,
  spacing, component CSS, anti-patterns, pre-delivery checklist). A
  `design-system/pages/<page>.md` file, when present, overrides it for that page. Its
  generated palette and fonts predate `design_spec.json`; where they differ, the spec and the
  shipped site win, and its anti-patterns and checklist still apply.
- Where tokens ship: the `@theme` and `:root` blocks in `site/src/app/globals.css` and the
  fonts loaded in `site/src/app/layout.tsx`.
- Missing input: a token change with no value in `design_spec.json` — stop, add it to the spec
  first so the spec and the site never disagree.

## Process

1. Change the value in `design_spec.json`.
2. Carry it by hand into `site/src/app/globals.css` (`@theme` block for Gravity Stack tokens,
   `:root` for shadcn bindings) or `site/src/app/layout.tsx` for fonts. Tailwind v4: no
   `tailwind.config.ts`.
3. Update `docs/design-system.md` and `MASTER.md` lines the change makes false.
4. `cd site && npm run build`, then preview with `npm run dev`.

## Outputs

- Changed `design_spec.json`, `site/src/app/globals.css` or `site/src/app/layout.tsx`, and
  any `docs/design-system.md` or `design-system/` lines that described the old value.

## Human check

Alex compares the changed pages against `design_spec.json` and the `MASTER.md`
pre-delivery checklist. Pass: shipped colors and fonts match the spec, contrast stays at 4.5:1
or better and focus states are visible. Fail: correct before merge.
