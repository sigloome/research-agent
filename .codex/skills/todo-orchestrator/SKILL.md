---
name: todo-orchestrator
description: Resume unfinished local todos and convert new ideas into surveyed design notes plus backlog entries. Use when user says "continue unfinished todos", "/todo:continue", "/todo:idea ...", or asks to survey/design an idea then add it to the todo list.
license: MIT
metadata:
  short-description: Continue todos + idea to backlog
---

# TODO Orchestrator Skill

Use this skill to maintain seamless cross-session continuity and fast-start workflows.

## Supported Quick Triggers

1. `/todo:continue`
2. `continue unfinished todos`
3. `/todo:idea <idea text>`
4. `survey and design this idea, then add it to todo`

## Workflow A: Continue Unfinished TODOs

When triggered by `/todo:continue` or equivalent:

1. Read local continuity files:
   - `/Users/bytedance/code/anti-demo/tmp/todos/active.md`
   - `/Users/bytedance/code/anti-demo/tmp/todos/handoff.md`
2. Pick the first unfinished `P0` item unless user overrides priority.
3. Execute exactly one feature scope at a time.
4. Validate before commit.
5. Before ending session:
   - update `handoff.md` with current state and next action
   - move completed items from `active.md` to `done.md`

## Workflow B: Idea -> Survey -> Design -> TODO

When triggered by `/todo:idea <text>` or equivalent:

1. Survey context:
   - inspect relevant code/spec/eval files
   - identify risks, dependencies, and measurable benefits
2. Create a design note under:
   - `tmp/proposals/ideas/<timestamp>-<slug>.md`
3. Add backlog item to `tmp/todos/active.md` with:
   - reason
   - expected benefit
   - success metric candidates
4. Update `tmp/todos/handoff.md` with the new first-next-task if priority is high.

## Script Helpers

Use bundled scripts for deterministic file updates.

### Add idea to backlog

```bash
bash .codex/skills/todo-orchestrator/scripts/add_idea_to_todo.sh \
  --title "Trigger engine for evolution" \
  --priority P0 \
  --idea "Auto-detect failures and scaffold OpenSpec change" \
  --benefit "Reduce manual kickoff latency"
```

### Generate continuation prompt

```bash
bash .codex/skills/todo-orchestrator/scripts/print_continue_prompt.sh
```

## Guardrails

1. Keep one feature per commit.
2. Do not modify unrelated files.
3. Preserve local continuity files on every session.
4. Promote durable decisions into tracked OpenSpec artifacts before merge.
