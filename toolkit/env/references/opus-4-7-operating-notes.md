# Opus 4.7 Operating Notes

**Source of truth** — referenced from `~/.claude/CLAUDE.md`, `~/CLAUDE.md`, `~/.carl/opus-4-7`, and per-project CLAUDE.md files. Update this file when a new Claude model ships; pointers stay stable.

Released 2026-04-16. See Anthropic's migration guide for the authoritative reference.

---

## Current Model IDs

| Tier   | ID                    | Use for                                       |
|--------|-----------------------|-----------------------------------------------|
| Opus   | `claude-opus-4-7`     | Deep reasoning, agentic loops, production coding |
| Sonnet | `claude-sonnet-4-6`   | Standard implementation, review, research, multi-round tool use |
| Haiku  | `claude-haiku-4-5`    | Fast/cheap work, scout, quickfix, classification |

Pricing unchanged from 4.6: Opus $5/$25 per MTok, 1M context at standard pricing, 128k max output. New tokenizer yields **1.0–1.35× more tokens per input** — re-budget `max_tokens` upward.

---

## Breaking Changes vs 4.6 (Messages API)

1. **Extended thinking removed.** `thinking: {type: "enabled", budget_tokens: N}` returns **400**. Use `thinking: {type: "adaptive"}` and control depth via `output_config.effort`.
2. **Sampling params removed.** `temperature`, `top_p`, `top_k` non-default values return **400**. Omit them; guide via prompting.
3. **Thinking content hidden by default.** `thinking.display` now defaults to `"omitted"` (silent change). If you stream reasoning to users, set `"summarized"` or the UI looks hung.
4. **Prefill removed.** No assistant-message prefills. Use structured outputs or system instructions.
5. **New tokenizer.** Add ≥35% headroom to `max_tokens` vs pre-4.7 defaults. Minimum **64k at `xhigh`/`max`**.

---

## Effort Levels

| Level  | Use for                                                        |
|--------|----------------------------------------------------------------|
| low    | Short scoped tasks, subagents, latency-sensitive              |
| medium | Cost-sensitive "drop-in"                                       |
| high (default) | Intelligence-sensitive baseline                        |
| xhigh  | Coding, agentic, exploratory work (repeated tool calls, detailed web/KB search) |
| max    | Frontier problems only — often overthinks on structured outputs |

**Opus 4.7 respects effort strictly at low/medium** (bigger change from 4.6). If reasoning is shallow, raise effort — don't prompt around it.

**Alex's house rule:** global default `high`. Promote to `xhigh` only on deep-reasoning skills (`/planning-stack --deep`, `/research-stack --deep`, `/build-stack`, `/design-stack --generate|--critique`, `/brainstorm-stack`, `/gsd:debug`, `/review-stack`).

---

## Behavior Changes (Not Breaking — May Need Prompt Updates)

- **Literal instruction-following.** Won't generalize from one item to another. Tuned prompts perform better.
- **Calibrated response length.** Length matches task complexity; remove old length-control scaffolding (e.g., "be concise"), then re-tune if needed.
- **Fewer tool calls, more reasoning.** Raise effort to increase tool usage.
- **More direct tone, fewer emoji.** Re-evaluate voice prompts.
- **Built-in progress updates during long agentic traces.** Remove "after every N tool calls, summarize" scaffolding.
- **Fewer subagents by default.** Steerable via explicit prompting.
- **Real-time cyber safeguards.** Apply to `https://claude.com/form/cyber-use-case` for legit security work.

---

## Vision: 3.75 MP Images

First Claude with high-res: **2576 px / 3.75 MP** (up from 1568 px / 1.15 MP). Coordinates are **1:1 with actual pixels** — no scale-factor math. Up to 4,784 tokens per full-res image (~3× prior). Downsample when you don't need the fidelity. Matters for: computer use, screenshot/artifact understanding, chart transcription.

---

## Task Budgets (Public Beta)

`output_config.task_budget` gives Claude an advisory token countdown across the full agentic loop (thinking + tool calls + tool results + output). The model sees it and paces itself.

```python
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=128000,
    output_config={
        "effort": "xhigh",
        "task_budget": {"type": "tokens", "total": 128000},
    },
    betas=["task-budgets-2026-03-13"],
    messages=[...],
)
```

- **Minimum:** 20k. Below → 400.
- **Soft cap**, not hard — `max_tokens` is still the ceiling.
- **Too-small budget causes refusal-like behavior.** Size from your actual p99 task spend.
- **Not available on Claude Code / Cowork** yet — Messages API only.
- **Pilot recommendation:** introduce on one direct-SDK workload with Langfuse (or equivalent) observability before broader adoption.

---

## Minimal Opus 4.7 Call Shape

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=64000,                    # ≥64k at xhigh/max
    thinking={"type": "adaptive"},       # OFF by default — must opt in
    output_config={"effort": "xhigh"},   # start here for coding; else "high"
    messages=[{"role": "user", "content": "..."}],
)
```

For UIs that stream reasoning: `thinking={"type": "adaptive", "display": "summarized"}`.

---

## Migration Checklist (4.6 → 4.7)

- [ ] Swap `claude-opus-4-6` → `claude-opus-4-7`
- [ ] Remove `temperature` / `top_p` / `top_k`
- [ ] Replace `thinking: {enabled, budget_tokens}` → `thinking: {adaptive}` + `output_config.effort`
- [ ] Remove assistant prefills
- [ ] If surfacing thinking to users: add `thinking.display: "summarized"`
- [ ] Re-tune `max_tokens` (≥64k at xhigh/max; add ≥35% headroom elsewhere)
- [ ] Re-budget image tokens; remove coordinate scale-factor conversions
- [ ] Remove deprecated beta headers: `effort-2025-11-24`, `interleaved-thinking-2025-05-14`, `fine-grained-tool-streaming-2025-05-14`
- [ ] Remove forced-progress scaffolding and length-control prompts; re-baseline
- [ ] Optional: adopt `task_budget` (beta) for agentic loops

Claude Code shortcut: `/claude-api migrate this project to claude-opus-4-7`.

---

## Claude Code Specifics

- **Default effort in Claude Code is now `xhigh`.** API still defaults to `high` — set it explicitly for direct SDK calls.
- `/ultrareview` — dedicated review session, catches what a careful human reviewer would.
- `/claude-api migrate` — bundled skill automates the migration above.
- Auto mode extended to Max users.

---

## Sources

- https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6 — primary (docs name appears wrong but content is 4.7)
- https://platform.claude.com/docs/en/about-claude/models/overview
- https://platform.claude.com/docs/en/about-claude/models/migration-guide
- https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://platform.claude.com/docs/en/build-with-claude/task-budgets
- https://www.anthropic.com/news/claude-opus-4-7
- https://support.claude.com/en/articles/12138966-release-notes
