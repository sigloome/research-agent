# Agent Guidelines

This file defines repository-level standards for coding agents.

## Evaluation Standard (Mandatory)

For any change that affects agent behavior, prompting, retrieval, tool usage, or eval code:

1. Follow `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`.
2. Use deterministic-first evaluation design.
3. Keep evals flexible with outcome-based multi-oracle acceptance.
4. Minimize runtime LLM judgment and keep it non-blocking for PR/nightly.

## When Updating Customized Prompt Paths

If a change touches any custom prompt/agent path, update:

1. Path coverage and requirements in `/Users/bytedance/code/anti-demo/docs/specs/agent-evaluation-standard.md`.
2. The corresponding eval tasks and fixtures.
3. Any impacted proposal document in `/Users/bytedance/code/anti-demo/tmp/proposals/`.

