---
name: skill-management
description: Manage and modify skills in this project. List, search, read, and update skill implementations.
license: Apache-2.0
metadata:
  short-description: List, search, read, and update skills
  type: management-tool
  python_package: skills.skill_management
---

# Skill Management

This skill provides abilities to manage other skills in the project.

## Capabilities

1. **List skills** - Show all available skills and their descriptions
2. **Search skills** - Find skills by name or description
3. **Read skill** - View the content of a skill file
4. **Update skill code** - Modify skill implementation with hot reload

## CLI Usage

```bash
# List all skills
python -m skills.skill-management list

# Search skills
python -m skills.skill-management search "paper"

# Read skill content
python -m skills.skill-management read skills/learning/__main__.py
```

## Usage

### List All Skills

```bash
cd /Users/bytedance/code/anti-demo
python -c "from tools import list_skills; import json; print(json.dumps(list_skills(), indent=2))"
```

### Search Skills

```bash
cd /Users/bytedance/code/anti-demo
python -c "from tools import search_skills; import json; print(json.dumps(search_skills('paper'), indent=2))"
```

### Read Skill Content

```bash
cd /Users/bytedance/code/anti-demo
python -c "from tools import read_skill; print(read_skill('skills/paper/operations.py'))"
```

### Update Skill Code

```bash
cd /Users/bytedance/code/anti-demo
python -c "from tools import update_skill_code; print(update_skill_code('skills/paper/operations.py', 'NEW_CODE_HERE'))"
```

## Skill Locations

- **SKILL.md files**: `.claude/skills/*/SKILL.md`
- **Python implementations**: `skills/*/`

## Hot Reload

When updating Python skill files, the changes are hot-reloaded automatically without server restart.
