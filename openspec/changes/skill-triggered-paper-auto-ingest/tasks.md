## 1. SDD

- [x] 1.1 新建 OpenSpec 变更并声明目标行为：默认关闭文本兜底，skill 触发为主。
- [x] 1.2 明确成功指标、回滚策略与 kill criteria。

## 2. BDD

- [x] 2.1 场景：出现 `knowledge.paper_ingest` tool 事件时，触发 ingest。
- [x] 2.2 场景：仅文本提及论文 ID 且 fallback 关闭时，不触发 ingest。

## 3. TDD

- [x] 3.1 helper 解析测试：正确提取 `tool-input-available` 中的 source。
- [x] 3.2 开关测试：fallback 默认关闭，仅 env 开启时生效。

## 4. Implementation

- [x] 4.1 在 `/api/chat` 流解析中收集 skill-triggered ingest source。
- [x] 4.2 关闭默认文本兜底，改为 env 显式开启。
- [x] 4.3 保持与现有 SSE 协议兼容。

## 5. Verification

- [x] 5.1 运行新增 BDD/TDD 与相关回归测试。
- [x] 5.2 更新 acceptance 记录。
