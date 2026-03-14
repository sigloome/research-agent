## ADDED Requirements

### Requirement: Paper Detail Route MUST Canonicalize Versioned ArXiv IDs

Paper detail route MUST canonicalize versioned arXiv IDs in URL for stable linking.

#### Scenario: Frontend route redirect
- **WHEN** user opens `/paper/2401.12345v1`
- **THEN** frontend redirects to `/paper/2401.12345` using replace-navigation
- **AND** subsequent API calls use canonical ID
