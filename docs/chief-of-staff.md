# Chief of staff: directing specialist sessions

> **Hiring pool:** [`../toolkit/env/agents/`](../toolkit/env/agents/). The `superpowers:subagent-driven-development` skill comes from the `superpowers` plugin, see [plugins](plugins.md).

One session cannot hold many streams of work. Its context fills up, and its focus drifts. This page describes a pattern for running several streams at once. One session acts as the chief of staff (CoS). It directs. It builds nothing. Each stream runs in its own specialist session.

## The model

1. **The CoS directs and builds nothing.** It keeps the plan, the roster, the state log and the decisions. It passes the human's answers on word for word. It checks every report against the real system before it says something is done.
2. **One session per stream.** Release, each build area, finance, records and hiring can each be a stream. Start each as its own session. A stream session survives when the CoS session closes or hits a limit.
3. **Subagent-driven development inside each session.** Use `superpowers:subagent-driven-development`. One fresh subagent takes each task. A review happens between tasks. A reviewer never reviews its own work.
4. **Hire the narrowest agent type. Never a generalist.** Every task goes to the agent built for it. Use `general-purpose` only when nothing fits, and write why in the task note.
5. **One owner per PR, one merger per repo.** Only the release session merges to a production branch. Every other session opens a PR and hands it over.

## Why not just use subagents in the CoS session?

A subagent started by the CoS lives inside the CoS session. It stops when that session closes. It also stops at the account usage limit and on a network drop. A separate session does not depend on the CoS staying alive.

Use subagents for tasks inside a session. Use sessions for streams of work that must outlast any one conversation.

## Hiring map

The toolkit ships these agents. Pick by the job, not by habit.

| Agent | Hire it for |
|-------|-------------|
| `implementer` | Writing code |
| `tester` | Tests and browser proof |
| `reviewer` | Reviewing diffs (read-only) |
| `supabase` | Database, auth and edge functions |
| `scout` | Quick lookups and file searches |
| `architect` | Structure and system design |
| `quickfix` | One small, targeted fix |
| `research` | Investigation and documentation analysis |

Need a specialty that is not listed, such as money or outbound drafts? Write a new agent file for it. Do not stretch a coder to do it.

## The CoS files

Keep these in one folder per business or project. The names are a suggestion. The jobs are what matter.

| File | Holds |
|------|-------|
| `ROSTER.md` | Each session: name, specialty, what it owns, what it never touches. Also the hiring map. |
| `COMMON-BRIEF.md` | What every session reads first, and the rules it follows. |
| `STATE.md` | One stamped line per event. Read the clock first, then write the line. Sessions post lines addressed to the CoS. |
| `RESUME.md` | The prompt that starts the next CoS. Keep it current at every phase, not only at the end. |
| `UNFINISHED-WORK.md` | Every open item, each with exactly one owner or one proof it is done. The count of unowned items stays at zero. |

Add a verification file when you re-check facts at their primary sources. Re-reading beats remembering.

## Failure modes

Each of these cost real hours before it became a rule.

- **Lanes stop when the session closes.** A handoff that says lanes are "still running" is only a claim. Check the last-write time on each transcript. If it is old, the lane is dead. Commit work in progress before any restart.
- **Limits and network drops stop lanes too.** Subagents inside the CoS session stop at the usage limit and when the network drops.
- **Auto-continue is not reliable.** A setting that says "continue when limits reset" may never restart the CoS. Never plan around it. Put the restart in the resume prompt.
- **A blocking question holds the coordinator.** A question popup waits until the human answers. Nothing else moves, and the wait can last hours. Put the facts in chat first. Ask last. Ask only what the human alone can decide.
- **Some tools limit who can start a session.** In some setups a session starts only from the human's own message. When an automated event wakes the CoS, have it propose the session as a card or note instead.
- **Records must leave the laptop.** Copy the CoS folder to the project repo by PR. Copy it to encrypted cloud storage. Write a dated handoff note to your notes vault. One disk is one failure.
- **The CoS context is the scarce resource.** Sessions report in five lines or fewer. Long output goes to files, and the CoS reads the file only when it needs to.

## Scheduled upkeep

A pattern that is not checked drifts. Schedule two jobs with whatever scheduler you use (cron, launchd or a built-in scheduled task).

- **Daily, early morning: health check.** Are the sessions alive? List them, then check transcript times. Is `STATE.md` fresh? Is the unowned count in `UNFINISHED-WORK.md` still zero? Are the records copied off the laptop? Is the live site healthy? Fix what it can. Report the rest.
- **Weekly, Monday morning: standard review.** Do the files that point at this pattern still agree with it? Does `ROSTER.md` still match the real sessions? Fold the week's lessons from `STATE.md` back into the pattern.

## Start small

1. Make a folder with `ROSTER.md` and `STATE.md`.
2. List your streams. Give each its own session and one line in the roster.
3. Write the common brief. Keep it to what every session must know.
4. Name the one session that merges. Tell the others to open PRs only.
5. Write `RESUME.md` before you close the CoS session, then schedule the daily check.
