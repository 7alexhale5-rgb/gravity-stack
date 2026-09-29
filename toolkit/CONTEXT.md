# Toolkit room: idempotent setup scripts

One job: change what the setup toolkit installs or configures, without breaking idempotency.
Paths relative to the repo root.

## Inputs

- `toolkit/install.sh`, `toolkit/vault-search.sh`, `toolkit/scripts/`, `toolkit/configs/`,
  `toolkit/env/`, `toolkit/templates/`.
- Convention from root `CLAUDE.md`: all toolkit scripts are idempotent — check-before-install,
  every run.
- Missing input: a new install step with no "already installed" check — stop, write the check
  before the install logic.

## Process

1. Change the script; add or keep a check-before-install guard for every action.
2. Run the script twice in a row locally; the second run must be a no-op (idempotency proof).
3. Update `toolkit/templates/` if the change adds a new config template.

## Outputs

- Changed scripts under `toolkit/scripts/`, `toolkit/install.sh`, or `toolkit/vault-search.sh`.

## Human check

Alex confirms the double-run test was actually performed. Pass: second run is a no-op. Fail:
add the missing guard before merge.
