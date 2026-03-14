## MODIFIED Requirements

### Requirement: Paper Processing MUST Guarantee Durable Ingest State
Paper processing SHALL guarantee durable ingest state that includes local content persistence and structured key information stored for retrieval.

#### Scenario: analyzed paper is durably stored
- **WHEN** user or agent triggers paper analysis/ingest
- **THEN** system stores local content path in paper record
- **AND** system stores key summary fields (`main_ideas`, `methods`, `results`, `limitations`)
- **AND** paper record is retrievable through paper APIs and local search

### Requirement: Paper Retrieval MUST Prefer Local Knowledge After Ingest
After ingest completion, agent retrieval workflows SHALL use local paper data as primary source before external fetch for matching queries.

#### Scenario: local-first retrieval for ingested paper
- **WHEN** query can be answered from ingested paper data
- **THEN** system returns local paper result without requiring external paper fetch
- **AND** response includes stable local paper identifier for citation/reference
