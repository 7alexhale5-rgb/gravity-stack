# gravity-stack: workspace context

## Purpose and boundary

This system-map organizes the work named in [the project map](CLAUDE.md).
It connects the existing rooms below; source and tooling paths stay where they are.

- [The public docs site](site/CONTEXT.md)
- [Idempotent setup scripts](toolkit/CONTEXT.md)
- [Deep-dive reference docs](docs/CONTEXT.md)
- [Implementation plan and phase handoffs](.planning/CONTEXT.md)
- [Installer and public-file safety tests](tests/CONTEXT.md)
- [Golden-dataset eval harness](.promptfoo/CONTEXT.md)
- [Design tokens and spec](design-system/CONTEXT.md)
- [CI workflows](.github/CONTEXT.md)

## Start or resume work

Read the project map, then the contract for the task. Check its Inputs before writing.
Use its Process, output path and Human check; stop if a required input is absent.
Resume the existing named task or record rather than starting a duplicate.

## Stable rules and changing work

The map and room contracts define routing and review rules. Working artifacts stay
in each room’s Outputs locations. Preserve existing source, records and tooling paths.
New filing does not authorize moves, publication or changes to approved decisions.

## Status and first check

Read [.planning/IMPLEMENTATION-GUIDE.md](.planning/IMPLEMENTATION-GUIDE.md) and the newest
`.planning/HANDOFF-*.md`, then compare their claims with current files, `CHANGELOG.md` and tests.
A file existing is not approval or proof of current operation.

From this checkout, run `python3 -m unittest discover -s tests -p 'test_*.py'` and
`bash tests/test_sanitization.sh`.
Use this worktree’s project path when checking a client branch.
Record the command and result in the task receipt; keep failed work open.
