---
description: Turn a one-line idea into spec.md / task.md / progress.md through an interview. Does not implement.
argument-hint: "<one line: what you want to build>"
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# /aml:new — draw the map through conversation

The user's idea: $ARGUMENTS

You're working with a beginner. They can't read code, but they can answer questions and react to what they see. The goal of this command is to move the beginner's mental picture onto a map called spec.md — implementation is /aml:go's job. Match the language the user writes in — conversation and outputs (spec.md·task.md·progress.md, including the template headings) in the user's language, in plain words a beginner understands. This language becomes the baseline that /aml:go·/aml:status·/aml:doctor follow. (Only the machine-appended measure line stays language-neutral — see the outputs below.)

## 1. Check for existing work

If spec.md and task.md exist at the project root with unfinished tasks, ask the user whether to continue (point to /aml:go) or start fresh. If starting fresh, leave a summary of the earlier work in progress.md, then rewrite spec.md and task.md.

## 2. Survey the territory

If there's existing code, skim it to learn the language, framework, and structure. Skip this for an empty project.

## 3. Mine the unknowns — the interview

A beginner's map has four regions, each drawn out a different way:

- **KK (known knowns)** — what the user already said. Don't re-ask; just capture it.
- **UU (unknown unknowns)** — decision points they haven't even considered. **Blind Spot Pass**: first show a list of "things people usually decide when building this." Just seeing them turns a UU into a KU.
- **KU (known unknowns)** — things that need deciding but aren't decided yet. Ask one at a time, without jargon, with options. Give every question a "Not sure — recommend one" choice, and if they pick it, decide the choice and the reason for them.
- **UK (unknown knowns)** — things they can't put into words but recognize on sight. When the screen/design matters and the user can't describe their taste, build 3–4 wildly different screen mockups in a single HTML file and let them pick. The chosen mockup becomes a reference (part of the map).

Scale the number of questions to the size — about 3 for a small feature, about 7 for a new app or a framework choice. Prioritize questions that could change the architecture.

## 4. Write the outputs

Following the three templates in ${CLAUDE_PLUGIN_ROOT}/templates/, create these at the project root:

- **spec.md** — holds the interview results. Write "Done when" as statements the beginner can check themselves by trying it — this checklist is /aml:go's verification criteria. Record interview decisions in the "Decisions" table, and chosen mockups/screenshots/"like app X" under "Reference (the map)".
- **task.md** — coarse tasks to run in order. One task = one chunk finished in a single go.
- **progress.md** — create it from the template if absent, and log a "planning" entry with today's date.

## 5. Confirm

Show a plain-language summary of spec.md and get it reviewed. Once confirmed, tell them: "Run /aml:go to start implementation."
