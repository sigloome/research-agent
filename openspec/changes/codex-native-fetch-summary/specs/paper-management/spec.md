## ADDED Requirements

### Requirement: Fetch Pipeline MUST Attempt Durable Ingest

`fetch_papers` MUST attempt `paper_ingest` for each fetched paper unless the existing local record is already complete (`full_text_local_path` + required summary fields).

#### Scenario: New fetched paper triggers ingest
- **WHEN** a paper is fetched and does not yet have a complete local record
- **THEN** system invokes ingest flow to persist local text and key summary fields
- **AND** fetch call still returns list result even if ingest fails for some items

#### Scenario: Complete record skips ingest
- **WHEN** existing paper already has `full_text_local_path` and all key summary fields
- **THEN** `fetch_papers` does not invoke ingest again

### Requirement: Summarizer MUST Use Codex-Native Runtime

Structured paper summary generation MUST use the same Codex runtime family as chat path, and must not require `ANTHROPIC_AUTH_TOKEN`.

#### Scenario: Codex summary success
- **WHEN** Codex adapter returns valid JSON summary payload
- **THEN** summary is persisted with required keys (`tags`, `summary_main_ideas`, `summary_methods`, `summary_results`, `summary_limitations`)

#### Scenario: Codex summary failure fallback
- **WHEN** Codex adapter errors or returns malformed output
- **THEN** system returns deterministic fallback summary object instead of crashing
