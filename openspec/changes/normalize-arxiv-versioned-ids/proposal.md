## Why

当前系统对论文 ID 多处采用精确匹配。用户访问 `/paper/<arxiv_id>v1`、`/api/paper/<id>v2` 或通过 `paper_ingest` 传入带版本号 ID 时，无法自动归一到数据库中的 canonical ID（不带 `vN`）。

这会导致同一论文因 URL 形态不同出现“找不到 / 不自动路由 / 不能自动下载”的体验问题。

## What Changes

- 引入统一 arXiv ID canonicalization（去除 `vN`）。
- 后端 `/api/paper/*`、`/api/papers/{paper_id}`、`paper_ingest`、自动提取链路统一使用 canonical ID。
- 前端 `PaperDetail` 访问 `/paper/<id>vN` 时自动重定向到 `/paper/<id>`。
- 增加 BDD/TDD 覆盖带版本号输入场景。

## Expected Benefit

- 提升论文链接兼容性，减少用户访问 404 与误失败。
- 降低同一论文多形态 ID 带来的调用歧义。

## Success Metrics

1. `versioned_id_route_success_rate = 100%`（测试夹具）
2. `paper_ingest_versioned_id_success_rate = 100%`（测试夹具）
3. `canonical_redirect_correctness = 100%`（前端重定向规则测试/断言）

## Rollback / Kill Criteria

- 若 canonicalization 导致非 arXiv 本地 ID 误判 > 1%（测试或监控样本），立即回滚到精确匹配并增加白名单规则。
- 若 `/api/paper/*` 404 率在发布后明显上升（>2%），回滚该变更。
