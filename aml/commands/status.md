---
description: Summarize progress from spec.md / task.md / progress.md in plain language. Read-only.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# /aml:status — check progress

Read spec.md, task.md, and progress.md at the project root and summarize. If all three are missing, tell the user to start with /aml:new.

Report (in the language used in the outputs, in plain words):

- **How far along** — done/remaining task counts, one line on the most recent work
- **What's blocked** — if progress.md has a blocker recorded, its content and the question the user needs to answer
- **Next action** — /aml:go if tasks remain, /aml:new for the next feature once everything's done

End with an offer — if they want, a **quiz**: about 3 easy questions on what's been built so far, to check whether the user can explain it to someone else. Staying in the loop isn't about reading code — it's about confirming understanding.
