---
description: Standard workflow for implementing features using OpenSpec
---

# OpenSpec Feature Implementation

This workflow guides you through the Spec-Driven Development (SDD) process using OpenSpec. Ideally, you should follow this for every non-trivial change.

## 1. Start a New Change

Begin by creating a new change workspace. This isolates the context and sets up the directory structure.

- **Command**: `/opsx-new <feature-name>`
- **Example**: `/opsx-new add-dark-mode`
- **Output**: Creates `openspec/changes/<feature-name>/`

## 2. Planning Phase (Iterative)

In this phase, you generate and refine the planning artifacts. You can do this step-by-step or fast-forward.

### Option A: Fast-Forward (Recommended)
Generate the proposal, specs, design, and tasks in one go.
- **Command**: `/opsx-ff`
- **Action**: Review the generated files in `openspec/changes/<feature-name>/`.
  - `proposal.md`: Why and high-level what.
  - `specs/`: Requirements and scenarios (Delta Specs).
  - `design.md`: Technical implementation details.
  - `tasks.md`: Implementation checklist.

### Option B: Step-by-Step
If the feature is complex, perform each step manually:
1.  **Proposal**: `/opsx-continue` (creates proposal) -> Review with user.
2.  **Specs**: `/opsx-continue` (creates delta specs) -> Review with user.
3.  **Design**: `/opsx-continue` (creates design) -> Review with user.
4.  **Tasks**: `/opsx-continue` (creates tasks) -> Review with user.

## 3. Implementation Phase

Once `tasks.md` is generated and you (and the user) are happy with the plan, proceed to implementation.

- **Command**: `/opsx-apply`
- **Action**: This will read `tasks.md` and execute the steps one by one.
- **Note**: Resume this command if it doesn't finish in one turn.

## 4. Verification

After implementation, verify the changes against the original specs.

- **Command**: `/opsx-verify`
- **Action**: Runs verification steps and ensures all requirements are met.

## 5. Completion & Archiving

When the feature is complete and verified, archive the change. This merges the Delta Specs into the Main Specs.

- **Command**: `/opsx-archive`
- **Action**: Moves change to `openspec/changes/archive/` and updates `openspec/specs/`.
