## ADDED Requirements

### Requirement: Paper Retrieval Evidence MUST Preserve Comparison and Verification Structure

Paper retrieval evidence used for comparison and cross-validation tasks MUST preserve structured fields needed for deterministic rerank and grading.

#### Scenario: Comparison evidence remains structured after rerank
- **WHEN** comparison retrieval passes through `graph_verify`
- **THEN** evidence items retain comparison-bearing fields such as `method`, `dataset`, `metric`, `value`, and `limitation` when available
- **AND** rerank does not collapse the output back into free-form text only

#### Scenario: Verification evidence retains polarity-bearing structure
- **WHEN** cross-validation retrieval passes through `graph_verify`
- **THEN** evidence items retain polarity-bearing fields such as `support`, `contradict`, `neutral`, or `unknown` when available
- **AND** deterministic benchmark scoring can still compute support and contradict recall from the result
