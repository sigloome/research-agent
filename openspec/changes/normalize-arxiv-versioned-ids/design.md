## Context

- 数据库存储的 arXiv ID 以不带版本号为主（例如 `2602.04879`）。
- 用户输入可能包含 `v1/v2`，也可能是 `abs/pdf/html` URL。

## Design

1. 统一工具函数
- 新增 `skills/knowledge/paper/id_utils.py`：
  - `canonicalize_arxiv_id(raw)`：识别 modern arXiv ID 并去掉版本号。
  - `resolve_paper_id(raw)`：若可识别 arXiv 则返回 canonical，否则返回原始 trimmed 值。

2. 后端接入点
- `backend/app.py`:
  - `/api/paper/{paper_id}`、`/api/paper/{paper_id}/analyze`、`/api/paper/{paper_id}/fetch`、`/api/papers/{paper_id}` 使用 `resolve_paper_id`。
  - 自动提取 `ARXIV_ID_RE` 支持可选 `vN`，并存储 canonical 值。

3. Skill 接入点
- `skills/knowledge/paper/core.py`:
  - `paper_ingest`、`_extract_arxiv_id` 接受 versioned ID 与 URL。
- `skills/knowledge/paper_search/fetcher.py`:
  - `get_arxiv_paper_by_id` 在请求前 canonicalize。

4. 前端接入点
- `frontend/src/pages/PaperDetail.tsx`:
  - 若 URL 参数可 canonicalize 且与当前不同，`navigate('/paper/<canonical>', { replace: true })`。

## Risks

- 风险：将某些非 arXiv 本地 ID 错误 canonicalize。
- 缓解：仅匹配严格 modern arXiv 模式 `\d{4}\.\d{4,5}(v\d+)?` 与对应 arXiv URL。
