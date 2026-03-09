# CARL

CARL (Context-Aware Rule Layer) is a 1,073-line Python governance engine that monitors Claude Code's context window and dynamically adjusts its behavior. It runs on every user prompt via the `UserPromptSubmit` hook, measuring how much context remains and injecting rules that match the current situation.

Without CARL, Claude Code has no awareness of its own context limits. It will attempt ambitious multi-file refactors with 10% context remaining, then fail mid-task. CARL prevents this by enforcing governance brackets that match behavior to available resources.

## The 5 Functions

### 1. Measure Context

CARL estimates the percentage of context window remaining by analyzing the current session transcript size. It reads the session file, calculates token usage, and produces a percentage.

```
context_remaining = (max_tokens - used_tokens) / max_tokens * 100
```

### 2. Select Bracket

Based on the measured context, CARL assigns one of three governance brackets:

| Bracket | Context Remaining | Behavior |
|---------|------------------|----------|
| **FRESH** | > 60% | Full autonomy. Claude can plan ambitiously, explore multiple approaches, and work on complex multi-file tasks. |
| **MODERATE** | 40% - 60% | Focused execution. Claude should avoid exploration and stick to the current task. No new planning. Finish what is started. |
| **DEPLETED** | < 40% | Conservation mode. Claude must delegate complex work to subagents, avoid large file reads, and wrap up or hand off. |

### 3. Inject Rules

CARL injects governance rules into the system prompt based on the selected bracket and the current context. Rules come from three domains:

**GLOBAL rules** (always injected):
- Follow CLAUDE.md instructions
- Confirm before irreversible actions
- Read files before editing

**ROUTING rules** (injected when agent spawning is relevant):
- FRESH: Spawn agents freely for parallel work
- MODERATE: Only spawn if the current task requires it
- DEPLETED: Force all complex work to subagents via `/plan`

**COMMANDS rules** (injected on demand when specific skills are invoked):
- Planning protocols (shallow vs. deep)
- Cost management thresholds
- Project-specific conventions

### 4. Route Decisions

CARL includes a planning router that determines the appropriate level of planning for any given task:

| Task Type | Planning Level | What Happens |
|-----------|---------------|-------------|
| Trivial (< 10 LOC, single file) | Skip | No planning. Implement directly. |
| Bug fix / small change | Shallow | Quick analysis, identify root cause, fix. `/planning-stack --shallow` |
| Standard feature (multi-file) | Standard | Full planning cycle with architecture review. `/planning-stack` |
| Architecture / system design | Deep | Thorough technical analysis with alternatives. `/planning-stack --deep --tech` |
| Context depleted (< 40%) | Subagent | Delegate to isolated subagent with full context. `/plan` |

The router runs automatically. You do not need to choose a planning level manually.

### 5. Enforce Governance

CARL enforces its rules by injecting them as `<carl-rules>` blocks into the system prompt. Claude Code is instructed to follow these rules via the `CLAUDE.md` configuration. Enforcement is passive (injected instructions) rather than active (blocking operations), which means Claude follows the rules because they are part of its instructions, not because a gate prevents it from acting.

## Context Brackets in Detail

### FRESH (> 60%)

You have plenty of room. CARL allows:
- Multi-file refactoring
- Exploratory code reading
- Architecture planning
- Parallel agent spawning
- Detailed code review

### MODERATE (40% - 60%)

Context is getting scarce. CARL restricts:
- No new planning sessions (finish current work)
- No exploratory file reading (only read what you need)
- Summarize rather than quote when reporting
- Complete the current task before starting anything new

### DEPLETED (< 40%)

Context is critically low. CARL enforces:
- Delegate complex tasks to subagents via `/plan`
- No large file reads (use targeted grep instead)
- Wrap up current work with a summary
- Save progress to CLAUDE.md or memory before session ends
- No multi-file changes (one file at a time)

## Building Custom CARL

CARL is configured through a YAML manifest that defines rules, brackets, and domains.

### Manifest Structure

```yaml
# carl-manifest.yaml
engine:
  version: "1.0"
  max_tokens: 200000

brackets:
  FRESH:
    threshold: 60
    rules:
      - "Full autonomy for planning and execution"
      - "Spawn subagents for parallel work"
  MODERATE:
    threshold: 40
    rules:
      - "Focus on current task only"
      - "No new planning sessions"
  DEPLETED:
    threshold: 0
    rules:
      - "Delegate complex work to subagents"
      - "Wrap up and save progress"

domains:
  GLOBAL:
    always: true
    rules:
      - "Follow CLAUDE.md instructions"
      - "Confirm before irreversible actions"
  ROUTING:
    trigger: "agent_spawn"
    rules_by_bracket:
      FRESH: "Spawn agents freely"
      MODERATE: "Only spawn if required"
      DEPLETED: "Force subagent delegation"
  COMMANDS:
    trigger: "on_demand"
    rules:
      planning: "Use planning router"
      cost: "Enforce budget thresholds"
```

### Customization Points

- **Add new domains**: Define project-specific rule sets (e.g., a `SECURITY` domain for fintech projects)
- **Adjust thresholds**: Change bracket boundaries (e.g., set DEPLETED at 30% instead of 40%)
- **Add custom rules**: Inject project conventions that should always be followed
- **Modify routing**: Change planning level triggers for your workflow

## Using /carl-manager

The `/carl-manager` skill provides a CLI-like interface for managing CARL:

```
/carl-manager status        -- Show current bracket, context %, active rules
/carl-manager rules         -- List all rules by domain
/carl-manager brackets      -- Show bracket thresholds and rules
/carl-manager override      -- Temporarily override the current bracket
/carl-manager reset         -- Reset to automatic bracket selection
```

### Common Workflows

**Check why Claude is being conservative**:
```
/carl-manager status
```
If the bracket is DEPLETED, Claude is conserving context. Start a new session or delegate to a subagent.

**Force full autonomy for a critical task**:
```
/carl-manager override FRESH
```
Use sparingly. Overriding to FRESH when context is actually low risks session failure.

**Review what rules are active**:
```
/carl-manager rules
```
Shows all injected rules grouped by domain. Useful for debugging unexpected behavior.

## File Structure

```
~/.claude/carl/
  carl_engine.py          # Main engine (1,073 lines)
  carl_manifest.yaml      # Rule definitions
  carl_state.json         # Current session state (bracket, context %)
```

## How CARL Integrates

1. User sends a prompt
2. `UserPromptSubmit` hook fires
3. CARL engine runs (`python3 ~/.claude/carl/carl_engine.py`)
4. CARL measures context, selects bracket, generates rules
5. Rules are injected as `<carl-rules>` block into the system prompt
6. Claude reads the rules and follows them

The entire cycle completes in under 500ms and is invisible to the user. You only notice CARL when Claude starts behaving differently as context depletes -- that is CARL working as intended.
