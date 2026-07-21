# automix-light (aml)

> automix's light edition. Beginners want one thing — **fast, accurate implementation**.

automix (am) is a full harness with spec verification, code review, team mode, a pattern library, and external observability. Someone building their first app doesn't need most of that yet. automix-light keeps only what a beginner actually needs:

- **3 files** — `spec.md` (what to build), `task.md` (the to-dos), `progress.md` (the log). All at the project root, all in plain words — **they follow the language you use in the conversation** (only the machine-appended measure line stays language-neutral English).
- **4 commands** — `/aml:new` → `/aml:go` → `/aml:status`, plus `/aml:doctor` for checks.
- **md-first** — commands, templates, and outputs are all markdown. The one exception is a single observability script, `scripts/observe.py` (Python standard library only) — it measures the model, duration, tokens, and estimated cost for each task, logs them to progress.md, and optionally sends them to Langfuse. Even if this script fails, implementation never stops.

The design roots itself in "A Field Guide to Fable": small prompts, context first, and **mine the unknowns before you start**. Beginners start out not even knowing what they don't know (Unknown Unknowns) — so the first command isn't implementation, it's an interview.

## Install

```bash
cd automix-light
./install.sh          # stages to ~/.claude-marketplaces/automix-light
```

Then, inside Claude Code:

```
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

If `/aml:new`, `/aml:go`, `/aml:status`, `/aml:doctor` show up in `/help`, you're set.

## The flow

### 1. `/aml:new "one line: what you want to build"`

Claude builds your map through an interview, mining four regions in turn:

| Region | Meaning | How it's drawn out |
|---|---|---|
| KK (known knowns) | what you already said | just captured |
| UU (unknown unknowns) | decisions you haven't considered | shown first as a "people usually decide this" list |
| KU (known unknowns) | decisions still open | questions with options, "recommend one" available |
| UK (unknown knowns) | can't describe, but recognize on sight | pick from 3–4 mockups in different styles |

At the end you get `spec.md` (with a "Done when" checklist) and `task.md`, and you review them.

### 2. `/aml:go`

Implements `task.md` in order. For each task:

1. **Implement** — using spec.md's decisions and references as the map.
2. **Verify** — confirm behavior with tests or an actual run.
3. **Log** — add an entry to the top of `progress.md`: what you did / verification / **implementation notes** (what changed from the plan and why) / **the measure line** / next.

The **measure line** is this edition's new feature — each task leaves one:

```
- metrics: claude-opus-4-8 · 4m 32s · tokens 12.3k in / 4.1k out (cache 88k r / 2.1k w) · est. cost $0.42
```

How to read it: which model · how long · how many tokens (conversation volume) it took to finish the task, and roughly what it cost. Cost is an estimate from public pricing and may differ from your bill. Where python3 is unavailable, this line reads `metrics: unavailable` but implementation continues.

If you get stuck on the same problem 3 times, it stops and asks you. When everything's done, it checks each spec.md "Done when" item for real, then reports.

### 3. `/aml:status`

Summarizes how far along you are, whether anything's blocked, and what to do next. If you want, a **quiz** — to check whether you can explain what you built to someone else.

### 4. `/aml:doctor`

A status check before you start (or when something seems off). Read-only — it fixes nothing.

- ❌ **Blocking**: spec.md/task.md/progress.md missing, no "Done when" or task checkboxes → points to `/aml:new`
- ⚠️ **Advisory only**: no git, no python3 (measure line is skipped), Langfuse config issues

Langfuse never blocks, under any circumstances.

## Turn on Langfuse (optional, off by default)

[Langfuse](https://langfuse.com) is an observability tool that shows LLM work on a dashboard. Turn it on and each task's measure data (model·tokens·time·verification result) is sent, so you can see a timeline grouped by feature on the web. **It makes no difference if you leave it off** — the progress.md log is always there.

1. Get a public/secret key from a Langfuse project (cloud or self-hosted).
2. Set the keys **as environment variables only** (don't put them in the config file):
   ```bash
   export LANGFUSE_PUBLIC_KEY=pk-...
   export LANGFUSE_SECRET_KEY=sk-...
   export LANGFUSE_HOST=https://cloud.langfuse.com   # your address if self-hosted
   ```
3. Create `.aml/config.yaml` at the project root:
   ```yaml
   langfuse: "on"        # "off" or no file = no sending (default)
   langfuse_host: ""     # empty → LANGFUSE_HOST, or cloud.langfuse.com if that's unset too
   ```
4. Verify the connection with `/aml:doctor` — if you see "OK: Langfuse connection verified", you're done.

Sending is best-effort: if the network drops or a key is wrong, it leaves one warning and implementation continues. To turn it off, delete `.aml/config.yaml` or set `langfuse: "off"`.

## Example session

```
/aml:new "a kanban-style to-do app, as a single HTML file"
  → "People usually decide: how many columns, due dates, where completed cards go, drag to move…"
  → 5 questions (with options) → 4 mockups → pick #3
  → spec.md + task.md created, review requested

/aml:go
  → 1.1 board screen → verify → log to progress.md (metrics: claude-opus-4-8 · 3m 11s · …)
  → 1.2 add-card modal → …
  → all 7 "Done when" items checked → "Open todo.html in your browser"

/aml:status
  → "7 of 7 done. Want a quiz to check?"
```

## When to graduate to automix (am)

When you're going to build apps **regularly** — once you need an independent verification gate (goal), code review, team execution, or a pattern library that spans projects, am has all of it. The spec → task → verify skeleton is the same, so the flow you learned in aml carries straight over. am's Langfuse integration (`/am:observe`) uses the same environment variables.
