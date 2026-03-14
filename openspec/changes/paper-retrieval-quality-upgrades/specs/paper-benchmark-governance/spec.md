## ADDED Requirements

### Requirement: Paper Benchmark Runtime Profiles MUST Maintain Parity with Supported Retrieval Profiles

Frozen paper benchmark manifests MUST include parameter signatures for every supported benchmarked retrieval profile.

#### Scenario: Hybrid profile is benchmark-addressable
- **WHEN** the runtime supports `hybrid` as a paper retrieval profile
- **THEN** the paper benchmark manifest includes a `hybrid` parameter signature
- **AND** the runner can execute `paper_core` using that signature without falling back to another profile

### Requirement: Paper Benchmark Reports MUST Surface Profile Quality Deltas

Paper benchmark execution reports MUST expose enough aggregate metrics to compare retrieval profile quality deltas on the same frozen dataset.

#### Scenario: Profile comparison uses comparable aggregate metrics
- **WHEN** `baseline`, `hybrid`, `graph_expand`, and `graph_verify` are run on the same frozen paper tier
- **THEN** each report includes comparable aggregate metrics for recall, cluster coverage, support recall, contradict recall, and balanced evidence rate
- **AND** missing aggregate fields invalidate the comparison report
