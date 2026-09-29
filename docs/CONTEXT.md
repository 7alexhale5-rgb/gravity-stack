# Docs room: deep-dive reference markdown

One job: keep the deep-dive docs true to the toolkit and site code. Paths relative to the repo
root.

## Inputs

- Current docs: `carl.md`, `design-system.md`, `environment-audit-2026-03.md`, `hooks.md`,
  `mcp-servers.md`, `opus-4-7.md`, `plugins.md`, `skills.md`, `troubleshooting.md`.
- The code/behavior each doc describes (in `toolkit/` or `site/`).
- Missing input: a doc describing a script or hook that no longer exists in `toolkit/` — flag
  it for removal rather than leaving it stale.

## Process

1. Find every doc line a code change makes false: `grep -rn "<old value>" docs/ site/src`.
2. Rewrite those lines to match the current code.
3. Keep each doc under ~200 lines per the ICM standard; split if it grows past that.

## Outputs

- Edited `docs/*.md`.

## Human check

Alex spot-checks changed docs against the toolkit/site code. Pass: no doc states a value or
step the code doesn't have. Fail: correct before merge.
