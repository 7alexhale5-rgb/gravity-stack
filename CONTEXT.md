# Gravity Stack workspace

The toolkit sets up a development environment; the site explains its supported behavior.
Optional assets are examples, not proof that a service or hook is active.
Read [the project map](CLAUDE.md), then the selected room's contract before changing files.
Source and tooling paths stay where they are.

## Rooms

- [The public docs site](site/CONTEXT.md)
- [Idempotent setup scripts](toolkit/CONTEXT.md)
- [Deep-dive reference docs](docs/CONTEXT.md)
- [Implementation plan and phase handoffs](.planning/CONTEXT.md)
- [Installer and public-file safety tests](tests/CONTEXT.md)
- [Golden-dataset eval harness](.promptfoo/CONTEXT.md)
- [Design tokens and spec](design-system/CONTEXT.md)
- [CI workflows](.github/CONTEXT.md)

## Inputs

- Current toolkit code, site data and docs, routed by the project map.
- An approved goal and fresh check results. Dated plans are context only.
- The selected room's Inputs, Process, Outputs and Human check.
- Missing behavior proof remains pending rather than inferred from configuration.

## Process

1. Resume the existing named task or record; do not start a duplicate.
2. Inspect and reuse suitable isolation. Preserve existing source, records and paths.
3. Reproduce reported behavior, make the smallest change, then test it.
4. Run repository tests, scans and affected site checks; read their results.
5. Use a PR with exact-commit CI and record independent review limitations.

## Outputs

- Toolkit behavior, public site and documentation in their named rooms.
- Tests under tests/ and optional evaluation results outside tracked credentials.
- Working artifacts in the selected room's Outputs locations.
- Current work status in .planning/; GitHub PRs record release review and CI.

## Human check

Alex compares changed behavior with the stated goal and proof.
Static tests do not prove a live connection, model choice or hook invocation.
New filing does not authorize moves, publication or changes to approved decisions.
Failures and unavailable checks remain visible before release.

## Start or resume check

Read [.planning/IMPLEMENTATION-GUIDE.md](.planning/IMPLEMENTATION-GUIDE.md) and the newest
`.planning/HANDOFF-*.md`, then compare claims with current files, CHANGELOG.md and tests.
A file existing is not approval or proof of current operation.

Run `python3 -m unittest discover -s tests -p 'test_*.py'` and
`bash tests/test_sanitization.sh` from this checkout.
Record the command and result in the pull request; keep failed work open.
