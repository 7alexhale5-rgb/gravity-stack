# Test room

## Inputs

- `toolkit/install.sh` and the repository files scanned by `tests/test_sanitization.sh`.
- Optional external patterns via `GRAVITY_PRIVATE_PATTERNS`; never commit the list.

## Process

1. Run `python3 -m unittest discover -s tests -p 'test_*.py'`.
2. Run the generic scan and the external private profile on the exact release commit.
3. Installer tests isolate the home and stub system setup and network calls.

## Outputs

- `tests/test_sanitization.py`: external-profile path, EOF, error and output regression tests.
- `tests/test_installer.py`: regression tests for optional process-skill installation.
- `tests/test_sanitization.sh` and `tests/sanitization-patterns.txt`: public safety checks.

## Human check

Review CI results on the exact pull request commit. Failures block merging.
