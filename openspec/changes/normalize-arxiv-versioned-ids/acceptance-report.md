## Acceptance Report

Date: 2026-03-12  
Change: `normalize-arxiv-versioned-ids`

## Delivered

1. Added canonical ID utility for modern arXiv IDs with optional `vN` suffix:
   - `skills/knowledge/paper/id_utils.py`
2. Integrated canonicalization into backend paper endpoints:
   - `GET /api/paper/{paper_id}`
   - `POST /api/paper/{paper_id}/analyze`
   - `POST /api/paper/{paper_id}/fetch`
   - `GET /api/papers/{paper_id}`
3. Integrated canonicalization in ingest/fetch chain:
   - `skills/knowledge/paper/core.py`
   - `skills/knowledge/paper_search/fetcher.py`
4. Added frontend route canonical redirect for `/paper/:id`:
   - `frontend/src/pages/PaperDetail.tsx`
5. Added deterministic tests for canonicalization and versioned-ID compatibility.

## Verification Evidence

1. `pytest -q tests/skills/paper/test_id_utils.py tests/backend/test_paper_id_canonicalization.py tests/skills/paper/test_ingest_contract.py tests/backend/test_bdd_paper_ingest_flow.py tests/backend/test_bdd_chat_flow.py`
   - Result: `17 passed`
2. `cd frontend && npm run build`
   - Result: pass
3. `cd frontend && npx playwright test tests/e2e/paper-canonical.spec.ts --project=chromium`
   - Result: `1 passed`

## Notes

- This change addresses versioned-ID canonical routing and lookup behavior.
- Network-level upstream fetch constraints (e.g., local SSL chain issues) are out-of-scope for this change.
