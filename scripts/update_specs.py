#!/usr/bin/env python3
"""
Script to automatically update specs documentation when new skills are added.
Run this after adding new skills or modifying existing ones.

Usage:
    python scripts/update_specs.py

This script:
1. Scans all skills in .claude/skills/
2. Updates docs/specs/skills-system.md with current skill list
3. Generates stub spec files for new features
4. Updates AGENTS.md with current skill list
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
SPECS_DIR = PROJECT_ROOT / "docs" / "specs"
AGENT_MD = PROJECT_ROOT / "AGENTS.md"


def get_all_skills() -> list:
    """Get all skills from .claude/skills/."""
    skills = []
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith('_'):
            continue
        
        skill_info = {
            'name': skill_dir.name,
            'has_skill_md': (skill_dir / 'SKILL.md').exists(),
            'has_init': (skill_dir / '__init__.py').exists(),
            'python_files': [],
            'functions': [],
            'description': ''
        }
        
        # Find Python files
        for py_file in skill_dir.glob('*.py'):
            if py_file.name.startswith('_'):
                continue
            skill_info['python_files'].append(py_file.name)
            
            # Extract functions
            content = py_file.read_text()
            functions = re.findall(r'^def (\w+)\(', content, re.MULTILINE)
            skill_info['functions'].extend(functions)
            
            # Extract docstring
            match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
            if match and not skill_info['description']:
                skill_info['description'] = match.group(1).strip().split('\n')[0]
        
        # Get description from SKILL.md if available
        skill_md = skill_dir / 'SKILL.md'
        if skill_md.exists():
            content = skill_md.read_text()
            # Get first paragraph after title
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    # Skip title, get next non-empty line
                    for next_line in lines[i+1:]:
                        if next_line.strip() and not next_line.startswith('#'):
                            skill_info['description'] = next_line.strip()
                            break
                    break
        
        skills.append(skill_info)
    
    return sorted(skills, key=lambda x: x['name'])


def update_skills_spec(skills: list):
    """Update skills-system.md with current skill list."""
    spec_file = SPECS_DIR / "skills-system.md"
    if not spec_file.exists():
        print(f"Skipping {spec_file} - file doesn't exist")
        return
    
    content = spec_file.read_text()
    
    # Generate new skills section
    skills_section = "## Available Skills\n\n"
    for skill in skills:
        skills_section += f"### {skill['name']}\n"
        skills_section += f"- **Purpose**: {skill['description'] or 'No description'}\n"
        if skill['functions']:
            funcs = ', '.join(f"`{f}()`" for f in skill['functions'][:5])
            skills_section += f"- **Functions**: {funcs}\n"
        skills_section += "\n"
    
    # Replace existing skills section
    pattern = r'## Available Skills\n\n.*?(?=\n## [A-Z]|\n## Test Cases|\Z)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, skills_section, content, flags=re.DOTALL)
    else:
        # Append if not found
        content += "\n" + skills_section
    
    spec_file.write_text(content)
    print(f"Updated {spec_file}")


def update_agent_md(skills: list):
    """Update AGENTS.md with current skill list."""
    if not AGENT_MD.exists():
        print(f"Skipping {AGENT_MD} - file doesn't exist")
        return
    
    content = AGENT_MD.read_text()
    
    # Generate skills table
    skills_table = "| Skill | Description | Key Functions |\n"
    skills_table += "|-------|-------------|---------------|\n"
    for skill in skills:
        funcs = ', '.join(skill['functions'][:3]) if skill['functions'] else '-'
        skills_table += f"| {skill['name']} | {skill['description'][:50]}... | {funcs} |\n"
    
    # Try to update existing table (look for skills directory listing)
    # This is a simple approach - could be more sophisticated
    
    print(f"Skills discovered: {len(skills)}")
    for skill in skills:
        print(f"  - {skill['name']}: {len(skill['functions'])} functions")


def generate_missing_skill_mds(skills: list):
    """Generate SKILL.md for skills that don't have one."""
    for skill in skills:
        if skill['has_skill_md']:
            continue
        
        skill_dir = SKILLS_DIR / skill['name']
        skill_md = skill_dir / 'SKILL.md'
        
        # Generate template
        content = f"""# {skill['name'].replace('_', ' ').title()} Skill

{skill['description'] or 'Description needed.'}

## Usage

```python
from skills.{skill['name']} import ...
```

## Functions

"""
        for func in skill['functions']:
            if not func.startswith('_'):
                content += f"### `{func}()`\n\nDescription needed.\n\n"
        
        content += """## Examples

TODO: Add examples.
"""
        
        skill_md.write_text(content)
        print(f"Generated {skill_md}")


def check_test_coverage(skills: list):
    """Check if skills have corresponding tests."""
    tests_dir = PROJECT_ROOT / "tests" / "skills"
    missing_tests = []
    
    for skill in skills:
        test_file = tests_dir / f"test_{skill['name']}.py"
        if not test_file.exists():
            missing_tests.append(skill['name'])
    
    if missing_tests:
        print(f"\nSkills missing tests: {', '.join(missing_tests)}")
        print("Run: pytest tests/skills/ --collect-only to verify")


def main():
    print("=" * 50)
    print("Spec Auto-Update Script")
    print("=" * 50)
    
    # Ensure directories exist
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all skills
    skills = get_all_skills()
    print(f"\nFound {len(skills)} skills")
    
    # Update specs
    update_skills_spec(skills)
    
    # Update AGENTS.md
    update_agent_md(skills)
    
    # Generate missing SKILL.md files
    generate_missing_skill_mds(skills)
    
    # Check test coverage
    check_test_coverage(skills)
    
    print("\n" + "=" * 50)
    print("Done! Review generated files.")
    print("=" * 50)


if __name__ == "__main__":
    main()
