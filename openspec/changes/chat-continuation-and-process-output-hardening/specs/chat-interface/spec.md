## MODIFIED Requirements

### Requirement: Response Streaming
The system SHALL keep user-facing answer text separate from process/progress state in the stream contract and rendering hierarchy.

#### Scenario: Final answer text excludes process narration
- **WHEN** the assistant emits a completed answer
- **THEN** the user-facing final text excludes hidden reasoning tags and obvious process-control tags
- **THEN** structured process state remains available through non-text stream parts

### Requirement: Tool Execution Display
The interface SHALL render process/tool progress as a secondary UI layer and SHALL weaken it after turn completion by default.

#### Scenario: Completed process timeline is weak by default
- **WHEN** a turn has completed and tool/progress items exist
- **THEN** the process section is collapsed or visually minimized by default
- **THEN** the final answer remains the primary visible content
