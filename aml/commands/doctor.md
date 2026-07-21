---
description: Pre-start check — the 3 files and their checkboxes, git/python3, Langfuse config. Read-only.
allowed-tools: Read, Bash, Glob, Grep
---

# /aml:doctor — pre-start check

Check the following in order at the project root and report plainly — in spec.md's language if it exists, otherwise the user's conversation language. Fix nothing.

## Blocking — on failure, report ❌ and how to fix

1. Do spec.md / task.md / progress.md all exist? → if not: "Start with /aml:new"
2. Does spec.md's "Done when" have at least one checkbox (`- [ ]` or `- [x]`)?
3. Does task.md have at least one task checkbox?

## Advisory only — don't block, report ⚠️

4. Is this a git repo (`git rev-parse --is-inside-work-tree`)? — if not: "git isn't required, but it makes mistakes easy to undo"
5. Is python3 available (`command -v python3`)? — if not: "the measure line (model·time·tokens·cost) won't be recorded in progress.md"
6. Langfuse status — report one of three. **Langfuse never blocks, under any circumstances.**
   - If `.aml/config.yaml` is absent or `langfuse:` isn't "on" → "Langfuse export: off (default)". How to turn it on: the README's "Turn on Langfuse" section.
   - If "on" but LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY env vars are missing → ⚠️ "on but keys missing, so sending is skipped" + how to set the keys (never print key values — only present/absent).
   - If "on" and keys are present → verify the connection with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/observe.py" ping`, and report OK/WARN as-is.

## Report format

One ✅/❌/⚠️ line per item. End with one line on the next action — /aml:new if files are missing, /aml:go if tasks remain, "you're clear to start" if there are no problems.
