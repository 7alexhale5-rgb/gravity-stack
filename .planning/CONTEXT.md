# Planning room: implementation guide and phase handoffs

One job: hold the current implementation plan and phase handoffs. Paths relative to the repo
root.

## Inputs

- `IMPLEMENTATION-GUIDE.md`, `HANDOFF-BUILD-PHASE-20260309.md`,
  `HANDOFF-DESIGN-POLISH-20260309.md`.
- Missing input: a new phase with no acceptance criterion — use `/planning-stack` to write one
  before starting.

## Process

1. Use `/planning-stack` to write or update the implementation guide for a new phase.
2. When a phase ends, write a dated `HANDOFF-<PHASE>-<YYYYMMDD>.md` summarizing what shipped
   and what's next.

## Outputs

- Updated `IMPLEMENTATION-GUIDE.md`; new `HANDOFF-*.md` files per completed phase.

## Human check

Alex confirms the handoff accurately reflects what shipped (cross-check against `CHANGELOG.md`
and `git log`). Pass: handoff matches shipped code. Fail: correct before archiving the phase.
