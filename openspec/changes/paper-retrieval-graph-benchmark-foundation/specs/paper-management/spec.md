## ADDED Requirements

### Requirement: Paper Retrieval Tasks MUST Produce Structured Evidence Sets

Paper retrieval flows used for related-work, comparison, and cross-validation tasks MUST produce structured evidence sets that can be scored deterministically, rather than relying only on free-form answer text.

#### Scenario: Comparison flow emits facet-bearing evidence
- **WHEN** a paper comparison retrieval flow completes
- **THEN** the resulting evidence set contains structured fields for comparison facets such as `method`, `dataset`, `metric`, and `limitation` when available
- **AND** missing facets are distinguishable from unsupported claims

#### Scenario: Cross-validation flow distinguishes evidence polarity
- **WHEN** a cross-validation retrieval flow completes
- **THEN** the resulting evidence set distinguishes `support`, `contradict`, `neutral`, or `unknown` polarity when available
- **AND** the flow records whether counter-evidence search was attempted

### Requirement: Paper Retrieval Coverage Audit MUST Be Observable

Paper retrieval flows used in benchmarked paper tasks MUST expose coverage audit markers that indicate whether important evidence classes were covered.

#### Scenario: Related-work coverage audit identifies baseline and follow-up presence
- **WHEN** a related-work retrieval flow finishes
- **THEN** the audit output indicates whether classic baselines and recent follow-up papers are present in the result set

#### Scenario: Comparison audit identifies non-comparable conditions
- **WHEN** a comparison retrieval flow finds evidence from mismatched settings
- **THEN** the audit output indicates that a comparability warning is required
- **AND** deterministic benchmark grading can detect whether that warning was surfaced

### Requirement: Paper Retrieval Benchmark Fixtures MUST Remain Frozen and Immutable

Paper retrieval benchmark fixtures used by blocking tiers MUST be loaded from versioned frozen datasets and MUST NOT be mutated during a run.

#### Scenario: Blocking tier fixture immutability
- **WHEN** a blocking paper retrieval benchmark run executes
- **THEN** fixture records are loaded from a frozen versioned dataset
- **AND** the run does not write back mutations into the frozen fixture source

#### Scenario: Frozen fixture version is auditable
- **WHEN** a paper retrieval benchmark report is generated
- **THEN** the report includes frozen fixture version and hash metadata
- **AND** missing version or hash metadata causes blocking tiers to fail

### Requirement: Blocking Paper Retrieval Benchmark Inputs MUST Use Restored Snapshot State

Blocking paper retrieval benchmark runs MUST execute against a restored fixed snapshot state rather than ambient runtime state.

#### Scenario: Restored snapshot enforces comparable search outcomes
- **WHEN** two blocking runs use the same snapshot ID and benchmark signature
- **THEN** their benchmark outputs are comparable without state-drift disclaimers

#### Scenario: Missing snapshot restore invalidates blocking run
- **WHEN** snapshot restore is skipped or fails
- **THEN** the blocking benchmark run fails before executing cases
