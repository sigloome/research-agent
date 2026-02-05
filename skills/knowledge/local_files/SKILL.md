---
name: local-files
description: Import papers from local PDF files into the library. Supports single file and directory imports.
license: Apache-2.0
metadata:
  type: utility
  python_package: skills.knowledge.local_files
---

# Local Files Skill

Import papers from local PDF files into the library.

## Usage

This skill allows you to:
- Import individual PDF files into the library
- List available PDF files in the local articles folder
- Import all PDFs from a directory at once

## CLI Usage

```bash
# List local files
python -m skills.knowledge.local_files list

# Import single file
python -m skills.knowledge.local_files import /path/to/paper.pdf

# Import all from directory
python -m skills.knowledge.local_files import-dir /path/to/papers
```

## Functions

### import_pdf(file_path, title=None, authors=None)
Import a single PDF file into the library.

### list_local_files(directory=None)
List all PDF files in the local articles directory.

### import_all_from_directory(directory=None)
Import all PDF files from a directory.

## Local Articles Folder
Default location: `local_articles/` in the project root.

## Examples

```python
from skills.local_files import import_pdf, list_local_files

# List available files
files = list_local_files()

# Import a specific PDF
result = import_pdf("/path/to/paper.pdf")

# Import with custom title
result = import_pdf("/path/to/paper.pdf", title="My Paper Title", authors=["Author Name"])
```
