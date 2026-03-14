## 1. SDD

- [x] 1.1 新建 OpenSpec 变更并定义目标行为、收益、风险指标。

## 2. BDD

- [x] 2.1 场景：`fetch_papers` 拉取新论文时会触发 `paper_ingest`。
- [x] 2.2 场景：已完整论文不会重复触发 ingest。

## 3. TDD

- [x] 3.1 `summarizer.generate_summary` 在 Codex 成功输出 JSON 时返回结构化字段。
- [x] 3.2 `summarizer.generate_summary` 在 Codex 失败时返回 fallback。

## 4. Implementation

- [x] 4.1 新增 Node summary adapter，接入 `@openai/codex-sdk`。
- [x] 4.2 重写 Python summarizer 为 Codex-native 调用。
- [x] 4.3 调整 `fetch_papers` 自动 ingest 逻辑。

## 5. Verification

- [x] 5.1 运行新增测试 + 相关回归并记录结果。
- [x] 5.2 补充 acceptance 报告。
