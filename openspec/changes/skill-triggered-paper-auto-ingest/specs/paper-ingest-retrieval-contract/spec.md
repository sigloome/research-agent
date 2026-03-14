## MODIFIED Requirements

### Requirement: Text Mention Fallback MUST Be Explicitly Gated
Text-based ingest fallback SHALL be disabled by default and enabled only via explicit configuration.

#### Scenario: fallback disabled by default
- **WHEN** runtime starts without `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true`
- **THEN** text mention based ingest fallback is disabled

#### Scenario: fallback enabled explicitly
- **WHEN** `ENABLE_PAPER_TEXT_MENTION_FALLBACK=true`
- **THEN** text mention fallback may execute only when no skill-triggered ingest source exists
