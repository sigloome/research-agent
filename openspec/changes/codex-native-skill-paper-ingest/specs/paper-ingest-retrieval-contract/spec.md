## ADDED Requirements

### Requirement: Paper Ingest SHALL Persist Local Artifact and Key Info
The `knowledge.paper_ingest` capability SHALL only report success when paper content is persisted locally and key information is stored in the database.

#### Scenario: ingest succeeds with durable state
- **WHEN** `knowledge.paper_ingest` is executed for a valid paper source
- **THEN** system stores local content path for the paper
- **AND** system upserts key summary fields in paper storage
- **AND** system returns success with paper identifier and persistence metadata

### Requirement: Ingested Papers SHALL Be Retrievable by Local Search
Ingested paper key information SHALL be retrievable via local retrieval interfaces used by agent skill workflows.

#### Scenario: retrieval can find ingested paper
- **WHEN** a query matches ingested paper title, summary, or key info
- **THEN** local retrieval returns the paper in top results
- **AND** returned payload includes stable paper identifier and summary fields

### Requirement: Ingest Failure SHALL Not Produce False Success
If local persistence or key-info DB upsert fails, ingest SHALL return failure status and SHALL NOT mark operation successful.

#### Scenario: persistence fails
- **WHEN** local write or DB upsert fails during ingest
- **THEN** operation returns explicit failure status
- **AND** failure details are recorded for diagnostics
- **AND** operation does not report successful ingest completion
