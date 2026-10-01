# CI room: GitHub Actions workflows

One job: keep CI running the repo's own test commands on every push and pull request to
`main`. Paths relative to the repo root.

## Inputs

- `.github/workflows/sanitization.yml`: job `scan` runs `bash tests/test_sanitization.sh`;
  job `installer` runs `python3 -m unittest discover -s tests -p 'test_*.py' -v` on
  `ubuntu-latest` and `macos-latest`.
- The test commands and their contract in `tests/CONTEXT.md`.
- Missing input: a CI step running a command that `tests/` doesn't define — stop, add the
  test to `tests/` first so it runs the same locally and in CI.

## Process

1. Change the workflow; keep `permissions: contents: read` and each job's `timeout-minutes`.
2. Pin third-party actions to a full commit SHA with the version in a comment.
3. Never put secrets or the private pattern list (`GRAVITY_PRIVATE_PATTERNS`) in a workflow.
4. Run both test commands locally before pushing.

## Outputs

- Changed files under `.github/workflows/`.

## Human check

Alex reviews the CI results on the exact pull request commit. Pass: both jobs green on both
operating systems. Fail: failures block merging.
