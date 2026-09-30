# Gravity Stack workspace

The toolkit sets up a development environment; the site explains its supported behavior.
Optional environment assets are examples, not proof that a service or hook is active.
Read CLAUDE.md to choose one room before changing files.

## Inputs

- Current toolkit code, site data and docs, routed by CLAUDE.md.
- An approved goal and fresh check results. Dated plans are context only.
- Missing behavior proof remains pending rather than inferred from configuration.

## Process

1. Start an isolated branch or worktree and read the selected room's contract.
2. Reproduce the reported behavior, then make the smallest change and test it.
3. Run repository tests, scans and affected site checks; read their results.
4. Use a PR with exact-commit CI and record independent review limitations.

## Outputs

- Toolkit behavior, public site and documentation in their named rooms.
- Tests under tests/ and optional evaluation results kept outside tracked credentials.
- Current work status in .planning/; GitHub PRs record release review and CI.

## Human check

Alex compares changed behavior with the stated goal and proof.
Passing static tests does not prove a live connection, model choice or hook invocation.
Failures and unavailable checks remain visible before release.
