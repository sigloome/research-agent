"""
Skill Management Core Logic.
Provides functions to list, search, read, and update skills.
"""
import re
import sys
import importlib
from pathlib import Path
from typing import Any, Dict, List

# Base paths - PROJECT_ROOT is skills/../
PROJECT_ROOT = Path(__file__).parent.parent.parent

SKILLS_DIR = PROJECT_ROOT / "skills"


def list_skills() -> List[Dict[str, Any]]:
    """
    List all available skills with their descriptions.
    Returns both SKILL.md skills and Python skill modules.
    """
    skills = []
    
    if SKILLS_DIR.exists():
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text()
                    name = skill_dir.name
                    description = ""
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = parts[1]
                            for line in frontmatter.split("\n"):
                                if line.startswith("name:"):
                                    name = line.split(":", 1)[1].strip()
                                elif line.startswith("description:"):
                                    description = line.split(":", 1)[1].strip()
                    skills.append({
                        "type": "skill_md",
                        "name": name,
                        "description": description,
                        "path": str(skill_md.relative_to(PROJECT_ROOT))
                    })
    
    return skills


def search_skills(query: str) -> List[Dict[str, Any]]:
    """Search skills by name or description."""
    query_lower = query.lower()
    all_skills = list_skills()
    return [
        s for s in all_skills
        if query_lower in s["name"].lower() or query_lower in s["description"].lower()
    ]


def read_skill(skill_path: str) -> str:
    """
    Read the content of a skill file.
    Can read both SKILL.md files and Python modules.
    """
    if ".." in skill_path:
        return "Error: Invalid path - cannot use '..' in path."
    
    full_path = PROJECT_ROOT / skill_path
    
    if not full_path.exists():
        alternatives = [
            PROJECT_ROOT / "skills" / skill_path / "SKILL.md",
            PROJECT_ROOT / "skills" / skill_path,
            PROJECT_ROOT / "skills" / f"{skill_path}.py",
        ]
        for alt in alternatives:
            if alt.exists():
                full_path = alt
                break
        else:
            return f"Error: Skill not found at {skill_path}"
    
    try:
        return full_path.read_text()
    except Exception as e:
        return f"Error reading skill: {e}"


def update_skill_code(skill_path: str, code: str) -> str:
    """
    Update the code of a skill file and hot reload it if it's a Python module.
    Use with CAUTION - this modifies live code.
    """
    if ".." in skill_path:
        return "Error: Invalid path - cannot use '..' in path."
    if not skill_path.startswith("skills/"):
        return "Error: Invalid path. Must be within skills/ directory."
        
    try:
        full_path = PROJECT_ROOT / skill_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(code)
        
        if skill_path.endswith(".py"):
            module_name = skill_path.replace("/", ".").replace(".py", "")
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            return f"Successfully updated and hot-reloaded {module_name}."
        else:
            return f"Successfully updated {skill_path}."
             
    except SyntaxError as e:
        return f"Syntax error in code: {e}"
    except Exception as e:
        return f"Error updating skill: {e}"
