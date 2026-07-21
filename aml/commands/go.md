---
description: Implement task.md in order, verify, and log to progress.md. When done, do a final check against spec.md's "Done when".
---

# /aml:go — implement

Read spec.md, task.md, and progress.md (latest entry) at the project root. If they're missing, tell the user to start with /aml:new and stop. If the state looks off, mention they can check with /aml:doctor.

You're working with a beginner. Write reports and logs in the language used in spec.md·progress.md, in words a non-programmer can understand.

## Task loop

For each unchecked task in task.md, in order:

1. **Implement** — at the start, record the start time with `date -Is` (or any other way to produce an ISO8601 timestamp). Implement using spec.md's decisions ("Decisions") and references (mockups/screenshots) as your map.
2. **Verify** — run the tests if there are any; otherwise actually run it and check the behavior. Compare against the spec.md "Done when" items relevant to this task.
3. **Log** — check the task off in task.md and add an entry to the top of progress.md: what you did / verification result / **implementation notes** (what you did differently from the plan and why — this log is what the beginner reads instead of the code) / **the measure line** / next. Get the measure line in one call:

   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/observe.py" task-done --since <start time> --label "<task number and name>" --feature "<spec.md title>" --note "<one-line verification>"`

   Paste the printed "metrics: …" line as-is — this line is language-neutral (English labels) and is not translated into the user's language (if Langfuse is configured on, the same call also sends it — ignore send failures and continue). If the call itself fails (no python3, etc.), write `metrics: unavailable` and continue.

If the same problem doesn't resolve after 3 tries, stop: record the sticking point in progress.md, explain the situation in plain words, and ask the user.

## When everything is done

1. Check each spec.md "Done when" item for real and tick it off. If something fails, fix it and check again.
2. If it's a git repo, commit. Otherwise skip quietly.
3. Wrap-up report — what got built, how to check it yourself (how to run it), and an offer: "Want a quick quiz to confirm you really understand what we built? You can also do it from /aml:status."
