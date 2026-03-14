## ADDED Requirements

### Requirement: Paper Retrieval Benchmark Tiers MUST Remain Frozen and Bounded

The system MUST execute paper retrieval benchmark runs against versioned frozen `core`, `full`, and `audit` tiers with fixed sample counts and MUST reject blocking runs that violate dataset hash or snapshot expectations.

#### Scenario: Core tier uses frozen bounded sample set
- **WHEN** a PR paper retrieval benchmark run starts
- **THEN** the runner loads the configured frozen `core` dataset version
- **AND** the runner validates the dataset hash before executing cases
- **AND** the run fails before execution if the dataset hash does not match

#### Scenario: Blocking tier requires restored snapshot
- **WHEN** a blocking paper retrieval benchmark tier starts
- **THEN** a fixed snapshot restore completes before case execution begins
- **AND** the snapshot ID is recorded in the benchmark signature

#### Scenario: Nightly tier without frozen metadata is non-comparable
- **WHEN** a nightly paper retrieval benchmark run starts without frozen dataset metadata
- **THEN** the run is marked non-comparable
- **AND** the blocking nightly tier fails before regression comparison is claimed

### Requirement: Benchmark Reports MUST Emit Comparable Retrieval Signatures

Each paper retrieval benchmark report MUST emit a signature payload containing `dataset_version`, `dataset_hash`, `snapshot_id`, `seed`, `params_signature`, and `git_commit`.

#### Scenario: Complete signature enables comparison
- **WHEN** a benchmark report contains all required signature fields
- **THEN** the report is eligible for regression comparison against prior reports with the same signature basis

#### Scenario: Missing signature blocks blocking tiers
- **WHEN** any required signature field is missing in a blocking tier report
- **THEN** the run is marked non-comparable
- **AND** the blocking tier fails

### Requirement: Paper Retrieval Benchmark MUST Enforce Tier Budget Gates

The system MUST enforce per-tier budget limits for sample count, token usage, p95 latency, and timeout rate, with blocking behavior for `core` and `full` and warning-only behavior for `audit`.

#### Scenario: Blocking tier exceeds budget
- **WHEN** a `core` or `full` benchmark run exceeds configured budget thresholds
- **THEN** the run fails with explicit budget violation details
- **AND** execution may terminate early to cap additional cost

#### Scenario: Audit tier records warnings only
- **WHEN** an `audit` benchmark run exceeds configured budget thresholds
- **THEN** the report includes budget warning annotations
- **AND** the run remains non-blocking

### Requirement: Paper Retrieval Benchmark MUST Check Repeat-Run Stability

The system MUST support a repeat-run stability check for key deterministic retrieval metrics under an identical signature.

#### Scenario: Identical signature run compares metric variance
- **WHEN** two benchmark runs use the same dataset version, snapshot ID, seed, and params signature
- **THEN** the runner compares key retrieval metrics across both runs
- **AND** reports whether variance remains within the configured tolerance

### Requirement: Paper Retrieval Benchmark Governance MUST Be Synced Into Repository Policy

The repository MUST document paper retrieval benchmark tiering, frozen input rules, and budget semantics in shared policy docs so implementation and evaluation remain aligned.

#### Scenario: Evaluation standard documents frozen benchmark policy
- **WHEN** paper retrieval benchmark governance changes
- **THEN** `docs/specs/agent-evaluation-standard.md` is updated to reflect frozen tier, deterministic, and comparability requirements

#### Scenario: Auto-evolving policy documents rollout and budget gates
- **WHEN** paper retrieval benchmark governance changes
- **THEN** `docs/specs/auto-evolving-backend.md` is updated to reflect blocking and non-blocking benchmark rollout policy
