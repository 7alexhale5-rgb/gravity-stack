# Skills

Skills are slash-command workflows that Claude Code executes on demand. Each skill is a structured prompt template that guides Claude through a specific task with best practices baked in. Gravity Stack includes 53 skills across 12 categories.

Invoke a skill by typing its name with a `/` prefix:
```
/planning-stack
/tdd
/code-review
```

Some skills accept arguments:
```
/planning-stack --deep --tech
/feature-dev "Add user authentication"
/quickfix "The login button is not responding"
```

---

## Planning (8 skills)

Skills for thinking before coding.

| Skill | What It Does |
|-------|-------------|
| `/brainstorming` | Open-ended ideation. Generates options, explores trade-offs, avoids premature commitment. |
| `/planning-stack` | The primary planning skill. Analyzes requirements, designs architecture, creates implementation plan. Supports `--shallow` (quick), `--deep` (thorough), and `--tech` (technical focus) flags. |
| `/init-project` | Scaffolds a new project from scratch: directory structure, CLAUDE.md, package.json, git init, README. |
| `/plan-phase` | Executes a single phase from a planning-stack plan. Used for incremental implementation. |
| `/verify-phase` | Verifies that a completed phase meets its acceptance criteria. Runs tests, checks types, reviews output. |
| `/next-phase` | Advances to the next phase in the plan. Shows progress and upcoming work. |
| `/challenge` | Devil's advocate mode. Pokes holes in a plan, finds edge cases, identifies risks. Use before committing to an approach. |
| `/brainstorm-stack` | Structured brainstorming with constraints. Like `/brainstorming` but with framework (SCAMPER, Six Hats, etc.). |

---

## Development (10 skills)

Skills for writing and improving code.

| Skill | What It Does |
|-------|-------------|
| `/feature-dev` | Guided feature development: explore codebase, plan architecture, implement incrementally, verify. The most-used development skill. |
| `/quickfix` | Fast bug fixes. Describe the problem, Claude finds the root cause and patches it. No planning overhead. |
| `/simplify` | Analyze code for unnecessary complexity. Suggests simpler alternatives, removes dead code, flattens abstractions. |
| `/review` | Code review with severity levels (critical, warning, suggestion). Covers correctness, security, performance, style. |
| `/commit` | Smart commit workflow: stage changes, generate conventional commit message, run pre-commit checks, commit. |
| `/playground` | Experimental sandbox. Try ideas without committing to them. Creates a temporary branch, lets you experiment, then cleans up or merges. |
| `/supabase-patterns` | Supabase-specific patterns: RLS policies, edge functions, auth flows, database queries, migrations. |
| `/agentation` | Agent orchestration patterns: multi-agent workflows, task delegation, parallel execution, result aggregation. |
| `/jr-dev` | Explains code at a junior developer level. Adds comments, breaks down complex logic, teaches while implementing. |
| `/skill-creator` | Build new skills from natural language descriptions. Outputs YAML skill definition files. |

---

## Testing (2 skills)

Skills for writing and running tests.

| Skill | What It Does |
|-------|-------------|
| `/test-driven-development` (or `/tdd`) | Red-green-refactor loop: write failing test, implement until it passes, refactor. Enforces TDD discipline. |
| `/e2e-testing-patterns` (or `/e2e`) | End-to-end testing with Playwright: page objects, fixtures, assertions, visual regression, CI integration. |

---

## Design (4 skills)

Skills for UI/UX and visual design.

| Skill | What It Does |
|-------|-------------|
| `/frontend-design` | High-quality UI component generation. Avoids generic AI aesthetics. Produces production-grade React components with proper styling. |
| `/ui-ux-pro-max` | Advanced UI/UX analysis: accessibility audit, interaction design, responsive behavior, animation, micro-interactions. |
| `/web-design-guidelines` | Web design fundamentals: typography, color theory, spacing, layout, visual hierarchy. Reference guide for design decisions. |
| `/tailwind-design-system` | Build and maintain a Tailwind CSS design system: tokens, component variants, responsive utilities, dark mode. |

---

## Frontend (2 skills)

Skills for React and Next.js patterns.

| Skill | What It Does |
|-------|-------------|
| `/vercel-react-best-practices` | React best practices from Vercel: Server Components, streaming, Suspense, data fetching, caching, ISR. |
| `/vercel-composition-patterns` | Component composition patterns: slots, render props, compound components, polymorphic components, headless UI. |

---

## Research (3 skills)

Skills for gathering information.

| Skill | What It Does |
|-------|-------------|
| `/research-stack` | Structured research workflow: define question, gather sources, synthesize findings, produce report. |
| `/defuddle` | Cut through confusion. When you are stuck or overwhelmed, this skill helps untangle the problem into manageable pieces. |
| `/last30days` | Summarize what happened in the last 30 days: commits, issues closed, features shipped, patterns emerging. |

---

## Management (11 skills)

Skills for project and task management.

| Skill | What It Does |
|-------|-------------|
| `/morning-brief` | Daily standup: yesterday's progress, today's plan, blockers, priorities. Pulls from git log and issues. |
| `/close-day` | End-of-day wrap-up: summarize accomplishments, update docs, create tomorrow's brief, commit WIP. |
| `/focus-update` | Quick progress report for stakeholders. Concise summary of what shipped and what is next. |
| `/pause-work` | Save current work context: branch state, uncommitted changes, mental model, next steps. Enables clean context switching. |
| `/resume-work` | Restore saved work context. Picks up exactly where `/pause-work` left off. |
| `/project-registry` | View and manage all projects: status, type, owner, recent activity. Central project directory. |
| `/project-progress` | Detailed progress report for a specific project: milestones, completion %, velocity, blockers. |
| `/drift` | Detect scope drift. Compares current work against the original plan and flags deviations. |
| `/graduate` | Promote a project from one status to the next (lab to active, active to stable, stable to maintained). |

---

## Governance (2 skills)

Skills for managing Claude's behavior and costs.

| Skill | What It Does |
|-------|-------------|
| `/carl-manager` | Manage the CARL governance engine: check status, view rules, override brackets, reset. See the [CARL guide](./carl.md). |
| `/cost-management` | Track and manage API costs: daily/monthly spend, budget warnings, provider breakdown, optimization suggestions. |

---

## Writing (3 skills)

Skills for written communication.

| Skill | What It Does |
|-------|-------------|
| `/writing-clearly-and-concisely` | Edit text for clarity: remove filler, simplify sentences, improve structure. Based on Federal Plain Language Guidelines. |
| `/writing-skills` | General writing improvement: grammar, tone, structure, audience awareness, persuasion techniques. |
| `/voice-check` | Analyze text against a brand voice guide. Flags inconsistencies and suggests corrections to match the target voice. |

---

## Business (3 skills)

Skills for business operations.

| Skill | What It Does |
|-------|-------------|
| `/ideas` | Idea evaluation framework: market size, feasibility, competition, differentiation, effort estimate. |
| `/gig-generator` | Generate freelance gig proposals: scope, timeline, pricing, deliverables, terms. |
| `/proposal-generator` | Create business proposals: executive summary, approach, timeline, team, pricing, terms. |

---

## Content (1 skill)

Skills for content production.

| Skill | What It Does |
|-------|-------------|
| `/remotion-video-production` | Create videos with Remotion (React-based video framework): scenes, transitions, animations, audio, rendering. |

---

## Utility (7 skills)

Skills for tools, integrations, and miscellaneous workflows.

| Skill | What It Does |
|-------|-------------|
| `/obsidian-cli` | Interact with Obsidian vault from the command line: create notes, search, link, tag, organize. |
| `/vault-context` | Pull relevant context from Obsidian vault into the current session. Searches by topic, tag, or path. |
| `/json-canvas` | Create and edit Obsidian Canvas files (JSON format): nodes, edges, groups, spatial layout. |
| `/obsidian-markdown` | Obsidian-flavored markdown reference: callouts, embeds, dataview queries, templates, frontmatter. |
| `/obsidian-bases` | Obsidian Bases (database views): create filtered, sorted, computed views over vault notes. |
| `/find-skills` | Search available skills by keyword or category. Useful when you cannot remember the exact skill name. |
| `/context-engineering-collection` | Curated collection of context engineering techniques: prompt design, few-shot examples, chain-of-thought, retrieval-augmented generation. |

---

## Debugging (1 skill)

Skills for diagnosing problems.

| Skill | What It Does |
|-------|-------------|
| `/trace` | Systematic debugging: reproduce the issue, isolate the cause, trace the execution path, identify the fix. Step-by-step diagnostic process. |

---

## Creating Custom Skills

Use `/skill-creator` to build new skills, or create them manually:

```yaml
# ~/.claude/skills/my-skill.yaml
name: my-skill
description: "What this skill does"
version: "1.0"
prompt: |
  You are now executing the my-skill workflow.

  ## Steps
  1. First, do this
  2. Then, do that
  3. Finally, verify

  ## Rules
  - Always check types
  - Never skip tests
```

Skills are loaded from `~/.claude/skills/` and any directory listed in your `settings.json` skill paths.

## Finding Skills

If you cannot remember a skill name:

```
/find-skills testing       # Find testing-related skills
/find-skills "code review" # Find review skills
/find-skills planning      # Find planning skills
```

Or just ask Claude: "What skill should I use to review my code?"
