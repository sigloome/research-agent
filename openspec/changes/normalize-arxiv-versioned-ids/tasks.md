## 1. SDD

- [x] 1.1 新建 OpenSpec 变更，定义 vN 兼容目标、指标与回滚条件。

## 2. BDD

- [x] 2.1 场景：访问 `/api/paper/<id>v1` 返回 canonical 论文。
- [x] 2.2 场景：`paper_ingest(<id>vN)` 走 canonical ID。

## 3. TDD

- [x] 3.1 ID 工具函数测试：裸 ID/带版本/URL 统一归一。
- [x] 3.2 API 路由测试：versioned ID 和 canonical ID 一致。

## 4. Implementation

- [x] 4.1 新增 ID canonicalization 工具并接入后端 API。
- [x] 4.2 接入 `paper_ingest` 与 fetcher。
- [x] 4.3 前端路由参数 canonical redirect。

## 5. Verification

- [x] 5.1 运行新增与相关回归测试。
- [x] 5.2 补充 acceptance 报告。
