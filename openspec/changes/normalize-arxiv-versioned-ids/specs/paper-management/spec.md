## ADDED Requirements

### Requirement: Versioned ArXiv IDs MUST Resolve To Canonical Paper ID

System MUST resolve versioned modern arXiv IDs (e.g. `2401.12345v1`) to canonical ID (`2401.12345`) when performing paper lookup and ingest.

#### Scenario: API lookup with versioned ID
- **WHEN** client calls `/api/paper/2401.12345v2`
- **THEN** backend resolves to canonical ID `2401.12345`
- **AND** returns the same paper record as `/api/paper/2401.12345`

#### Scenario: paper_ingest with versioned ID
- **WHEN** `paper_ingest("2401.12345v3")` is called
- **THEN** ingest logic uses canonical ID `2401.12345`
- **AND** success/failure envelope references canonical paper ID in stored record
