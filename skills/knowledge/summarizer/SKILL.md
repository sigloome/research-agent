---
name: summarizer
description: Summarize text using LLMs. Supports input from CLI, files, or strings.
license: Apache-2.0
metadata:
  type: utility
  python_package: skills.knowledge.summarizer
---

# Summarizer Skill

Description needed.

## Usage

```python
from skills.summarizer import ...
```

### CLI Usage

```bash
# Summarize text from stdin
echo "Long text..." | python -m skills.knowledge.summarizer summarize

# Summarize from file
python -m skills.knowledge.summarizer summarize --file path/to/file.txt --title "My Title"

# Summarize text string
python -m skills.knowledge.summarizer summarize --text "Short text"
```

## Functions

### `generate_summary()`

Description needed.

## Examples

TODO: Add examples.
