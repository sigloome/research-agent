## MODIFIED Requirements

### Requirement: Paper Auto Ingest Trigger MUST Be Skill-Driven By Default
Chat ingest automation SHALL be triggered by skill tool events by default, not by plain text mentions in assistant output.

#### Scenario: skill event triggers ingest
- **WHEN** stream includes `tool-input-available` for `knowledge.paper_ingest`
- **THEN** system extracts `source` from tool input
- **AND** system triggers ingest for that source after stream completion

#### Scenario: text mention does not trigger ingest by default
- **WHEN** assistant output text contains arXiv IDs but no ingest skill event
- **THEN** system does not auto-trigger ingest by default
- **AND** stream completion contract remains unchanged (`finish` + `[DONE]`)
