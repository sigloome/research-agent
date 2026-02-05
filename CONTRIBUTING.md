# Contributing to Velvet Research

Welcome to the team! We build with **"Vibe"** and **Precision**.

## Development Philosophy

We use a mix of **Documentation-Driven Development (DocDD)** and **Specification-Driven Development (SDD)**.

### 1. The Vibe (DocDD) -> "Write it to feel it"
Before you write code, you must write the documentation. This gives the AI context and helps us clear up ambiguity.

*   **For New Features**: Write a short section in this `CONTRIBUTING.md` or a specific design doc explaining the feature *as if it already exists*.
*   **For Functions**: Write the Docstring first.
    ```python
    def complex_logic(data):
        """
        Takes raw data, cleans out the noise (nulls, empty strings),
        and returns a structured list of valid items.
        """
        # Then let the AI write the code.
    ```
*   **For UI**: Update the `README.md` or a feature spec to describe the User Journey.

### 2. The Guardrails (SDD) -> "Type it to keep it"
We use strict types and schemas to keep the "vibe" from breaking the build.

*   **Backend**: Use Pydantic models for everything. Define the `class Model(BaseModel):` BEFORE the logic.
*   **Frontend**: Define `interface Ops {...}` BEFORE the React component.

### 3. The Proof (TDD) -> "Test it to trust it"
Tests are the safety net that lets us move fast without breaking things.
*   **Write Tests First**: If you can't test it, you don't understand it.
*   **Verification**: Run tests locally to ensure your logic holds up under pressure.

### 4. Review-Driven Development
You are the **Lead Reviewer**, even if the AI writes the code.
*   **Read the Diffs**: Don't just blindly apply.
*   **Linting is Law**: We use `ruff` (Python) and `eslint`/`prettier` (Frontend).

## Setup

### Linting
We enforce strict linting. Run this before every commit:

```bash
./scripts/lint.sh
```

### Backend
- **Linter**: `ruff`
- **Formatter**: `ruff format`

### Frontend
- **Linter**: `eslint`
- **Formatter**: `prettier`

## Pull Requests
1. Update Docs (DocDD).
2. Update Types (SDD).
3. Implement Logic.
4. Verify with `./scripts/lint.sh`.
