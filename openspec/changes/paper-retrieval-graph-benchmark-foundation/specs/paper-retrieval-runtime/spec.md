## ADDED Requirements

### Requirement: Active Chat Runtime MUST Honor Paper Retrieval Profiles

The active `/api/chat` path MUST interpret supported paper retrieval runtime profiles and MUST build a structured retrieval context before answer synthesis whenever a profile is provided.

#### Scenario: Runtime profile produces structured retrieval context
- **WHEN** a chat request includes a supported paper retrieval runtime profile
- **THEN** the runtime builds a structured retrieval context before answer synthesis
- **AND** the context includes `profile`, `intent`, `candidate_papers`, `evidence_items`, and `coverage_audit`
- **AND** the runtime does not silently discard the requested profile

#### Scenario: Unsupported runtime profile remains bounded
- **WHEN** a chat request includes an unsupported runtime profile string
- **THEN** the runtime falls back to the default chat behavior without crashing
- **AND** the response does not claim graph-expanded retrieval was executed

### Requirement: Paper Retrieval Profiles MUST Follow Layered Semantics

The system MUST support layered paper retrieval semantics that distinguish low-cost baseline recall from graph-based expansion and verification.

#### Scenario: Baseline profile stays low-cost and local-first
- **WHEN** the `baseline` profile executes
- **THEN** retrieval uses local lexical and metadata-first recall
- **AND** the retrieval context is eligible for deterministic benchmark scoring without graph-only fields

#### Scenario: Graph expand profile supplements candidate coverage
- **WHEN** the `graph_expand` profile executes
- **THEN** the system augments baseline or hybrid candidates with graph-based expansion
- **AND** the retrieval context records the expansion source or reason for newly added candidates

#### Scenario: Graph verify profile adds evidence validation
- **WHEN** the `graph_verify` profile executes
- **THEN** the system applies verification or critic logic over candidate evidence
- **AND** the retrieval context records comparison or polarity-oriented evidence fields when available

### Requirement: Retrieval Context MUST Support Coverage Audit

The structured retrieval context MUST expose coverage audit fields needed for related-work, comparison, and cross-validation tasks.

#### Scenario: Related-work context includes coverage markers
- **WHEN** a related-work query completes under a structured retrieval profile
- **THEN** the retrieval context reports whether classic baseline and recent follow-up coverage are present

#### Scenario: Cross-validation context exposes support and counter-evidence coverage
- **WHEN** a cross-validation query completes under a structured retrieval profile
- **THEN** the retrieval context reports whether supporting evidence and counter-evidence were found
- **AND** absence of counter-evidence is distinguishable from a failure to search for it
