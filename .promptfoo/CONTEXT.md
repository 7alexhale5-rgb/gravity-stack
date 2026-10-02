# Eval room: golden-dataset regression tests for the stack skills

One job: keep each skill's golden dataset scoring its prompt against the output contract the
skill really ships. Paths relative to `.promptfoo/` unless noted.

## Inputs

- `promptfooconfig.yaml`: the planning-stack config (the default `promptfoo eval` target).
- `configs/<skill>.yaml`: one config per other skill (`auto-diagram`, `morning-health`,
  `research-stack`, `review-stack`), each naming its provider, prompt, golden file and
  `outputPath`.
- `prompts/<skill>.txt`: the system prompt under test, with `{{topic}}`/`{{task}}`-style vars.
- `golden/<skill>.yaml`: test cases (`description`, `vars`, `assert` with `contains-any`,
  `not-contains`, `llm-rubric`).
- `run-all.sh`: runs every config and prints a pass/fail summary.
- The upstream skill's canonical output. For research-stack that is the report format and
  focus addenda in `github.com/7alexhale5-rgb/research-stack` (`focus/tags.json` holds the
  focus tags, addendum headings and source tags); `prompts/research-stack.txt` and
  `golden/research-stack.yaml` mirror it.
- `ANTHROPIC_API_KEY` in the environment (providers are `anthropic:messages:*`). Never commit
  it or put it in a config.
- Missing input: a golden case asserting a heading or source tag the upstream skill doesn't
  emit — stop, check the upstream format first; the golden must not invent a contract.

## Process

1. One skill: `cd .promptfoo && npx promptfoo eval -c configs/<skill>.yaml`
   (planning-stack: `npx promptfoo eval -c promptfooconfig.yaml`).
2. All skills: `bash .promptfoo/run-all.sh` (needs `promptfoo` on `PATH`).
3. Add a golden case: append an entry to `golden/<skill>.yaml` with `description`, `vars`
   and at least one deterministic assert (`contains-any`) plus an `llm-rubric`; accept the
   heading variants the skill uses (e.g. `"## Coverage gaps"`, `"## Coverage Gaps"`).
4. Upstream format changed (e.g. a new research-stack focus tag or source tag): update
   `prompts/<skill>.txt` and `golden/<skill>.yaml` together, using the upstream wording.
5. New skill: add `prompts/`, `golden/` and `configs/<skill>.yaml` (paths relative to
   `configs/`, `outputPath: ../reports/<skill>-latest.json`); `run-all.sh` picks it up.
6. Keep the default `temperature`/`top_p`/`top_k` in provider configs; `claude-sonnet-5-5`
   rejects non-default values (see `CHANGELOG.md`).

## Outputs

- Changed `prompts/`, `golden/` or `configs/` files.
- Run results in `.promptfoo/reports/<skill>-latest.json` (gitignored, never committed).

## Human check

Alex reads the failing cases in the latest report and compares changed goldens against the
upstream skill's format. Pass: every assert matches what the skill emits, and the run shows
no failures or errors. Fail: fix the prompt or the golden before merge.
