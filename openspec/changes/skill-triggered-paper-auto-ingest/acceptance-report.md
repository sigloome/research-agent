## Acceptance Report: skill-triggered-paper-auto-ingest

Date: 2026-03-12

## Scope

- Disable default text-mention-based paper ingest fallback.
- Trigger auto-ingest from skill events (`knowledge.paper_ingest`) in `/api/chat` stream path.
- Add BDD + TDD to prevent regression.

## Verification Commands

1. `pytest -q tests/backend/test_skill_ingest_trigger.py tests/backend/test_bdd_chat_flow.py tests/backend/test_bdd_paper_ingest_flow.py tests/skills/paper/test_ingest_contract.py tests/backend/test_codex_sdk_runtime.py`
   - Result: `19 passed`

2. `openspec validate --changes skill-triggered-paper-auto-ingest`
   - Result: this change passes (`change/skill-triggered-paper-auto-ingest` ✓)
   - Note: repository has unrelated pre-existing failed changes (`_templates`, `runtime-simplify-and-stability-hardening`, `support-multi-chat`).

## Behavior Confirmation

- Skill event ingest path:
  - `tool-input-available` + `toolName=...knowledge.paper_ingest...` leads to ingest trigger after stream completion.
- Text fallback default:
  - disabled unless `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true`.
- Stream contract:
  - unchanged completion markers (`finish`, `[DONE]`) remain intact.

## Risk / Rollback

- If skill event extraction misses runtime variants and ingest trigger rate drops, set `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true` as temporary rollback.
