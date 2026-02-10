# Feature Specifications

This directory contains specifications for all features in Velvet Research.

## Spec-Driven Development

All new features should follow this workflow:

1. **Write Spec First**: Create a spec file before implementation
2. **Write Tests**: Create tests based on the spec
3. **Implement**: Build the feature to pass the tests
4. **Verify**: Ensure implementation matches spec
5. **Update Docs**: Update AGENTS.md and relevant docs

## Spec Format

Each spec file should include:

```markdown
# Feature Name

## Overview
Brief description of the feature.

## Requirements
- Functional requirements
- Non-functional requirements

## API Specification
Endpoints, parameters, responses.

## Data Model
Database schema changes if any.

## User Interface
UI components and interactions.

## Test Cases
Key test scenarios.

## Dependencies
Other features or services required.
```

## Current Specs

| Spec | Status | Description |
|------|--------|-------------|
| [core-features.md](./core-features.md) | Active | Core system features |
| [skills-system.md](./skills-system.md) | Active | Skills framework |
| [paper-management.md](./paper-management.md) | Active | Paper search and storage |
| [book-management.md](./book-management.md) | Active | Book download and management |
| [chat-interface.md](./chat-interface.md) | Active | Chat UI and streaming |
| [user-preferences.md](./user-preferences.md) | Active | Preference learning |
| [agent-evaluation-standard.md](./agent-evaluation-standard.md) | Active | Deterministic-first, flexible-oracle agent eval policy |

## Adding New Features

When adding a new capability:

1. Create `docs/specs/new-feature.md`
2. Add entry to this README
3. Create tests in `tests/`
4. Implement the feature
5. Update AGENTS.md
