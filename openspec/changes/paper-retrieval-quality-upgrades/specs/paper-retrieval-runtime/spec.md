## ADDED Requirements

### Requirement: Hybrid Paper Retrieval MUST Use Distinct Lexical and Semantic Recall Paths

The `hybrid` paper retrieval profile MUST execute both lexical recall and semantic recall before candidate fusion.

#### Scenario: Hybrid retrieval produces mixed-source candidates
- **WHEN** the `hybrid` profile executes for a paper query
- **THEN** the retrieval context includes candidates from lexical recall, semantic recall, or both
- **AND** each candidate records its retrieval source or match reason
- **AND** the runtime does not implement `hybrid` as a label-only wrapper over `baseline`

### Requirement: Graph Expand MUST Improve Related-Work Cluster Coverage

The `graph_expand` profile MUST supplement `hybrid` candidates to improve related-work cluster coverage.

#### Scenario: Graph expand adds cluster-bearing candidates
- **WHEN** a related-work query executes under `graph_expand`
- **THEN** the result set includes expansion reasons that distinguish classic baseline, same-family work, or recent follow-up work when such evidence exists locally
- **AND** coverage audit reports which of those cluster classes were present

### Requirement: Graph Verify MUST Operate on Structured Evidence Items

The `graph_verify` profile MUST apply verification or critic logic to structured evidence items rather than only to free-form chunk text.

#### Scenario: Graph verify reranks evidence items
- **WHEN** `graph_verify` executes for comparison or cross-validation intent
- **THEN** the verifier receives structured evidence items with fields such as `paper_id`, `dataset`, `metric`, `value`, and `polarity` when available
- **AND** the resulting retrieval context preserves the reranked evidence items for deterministic scoring

### Requirement: Cross-Validation Retrieval MUST Attempt Counter-Evidence Search

Cross-validation retrieval MUST explicitly attempt counter-evidence search and MUST expose whether that search was performed.

#### Scenario: Counter-evidence search is distinguishable from no contradict hits
- **WHEN** a cross-validation query finishes
- **THEN** coverage audit indicates whether counter-evidence search was attempted
- **AND** the retrieval context distinguishes `no contradict evidence found` from `counter-evidence search not executed`
