
import os
import re
import sys
import yaml
from pathlib import Path

# Configuration
SKILLS_DIR = Path("skills")
REQUIRED_FIELDS = ["name", "description", "license"]

def validate_name_format(name):
    """
    Validates name against:
    - 1-64 chars
    - lowercase alphanumeric and hyphens
    - no start/end hyphen
    - no consecutive hyphens
    """
    if not (1 <= len(name) <= 64):
        return "Name length must be between 1 and 64 characters"
    if not re.match(r"^[a-z0-9-]+$", name):
        return "Name must contain only lowercase alphanumeric characters and hyphens"
    if name.startswith("-") or name.endswith("-"):
        return "Name must not start or end with a hyphen"
    if "--" in name:
        return "Name must not contain consecutive hyphens"
    return None

def validate_directory_match(dir_name, skill_name):
    """
    Validates that directory name matches skill name, allowing for snake_case <-> kebab-case conversion.
    """
    normalized_dir = dir_name.replace("_", "-")
    if normalized_dir != skill_name:
        return f"Directory name '{dir_name}' (normalized: '{normalized_dir}') does not match skill name '{skill_name}'"
    return None

def validate_skill(skill_path):
    errors = []
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        return [f"Missing SKILL.md in {skill_path}"]

    try:
        with open(skill_md, "r") as f:
            content = f.read()
            
        # Extract frontmatter
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return ["Missing or invalid YAML frontmatter in SKILL.md"]
            
        fm_text = match.group(1)
        try:
            frontmatter = yaml.safe_load(fm_text)
        except yaml.YAMLError as e:
            return [f"Invalid YAML in frontmatter: {e}"]
            
        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in frontmatter:
                errors.append(f"Missing required field: '{field}'")
                
        # Validate name
        if "name" in frontmatter:
            name_error = validate_name_format(frontmatter["name"])
            if name_error:
                errors.append(f"Invalid name '{frontmatter['name']}': {name_error}")
            
            # Directory match check
            dir_match_error = validate_directory_match(skill_path.name, frontmatter["name"])
            if dir_match_error:
                errors.append(dir_match_error)

        # Validate description length
        if "description" in frontmatter:
            desc = frontmatter["description"]
            if not (1 <= len(desc) <= 1024):
                 errors.append(f"Description length ({len(desc)}) must be between 1 and 1024 characters")

    except Exception as e:
        errors.append(f"Unexpected error validating {skill_path}: {e}")
        
    return errors

def main():
    print(f"Validating skills in {SKILLS_DIR.absolute()}...")
    
    all_valid = True
    
    # Walk specifically through skills directory
    # We need to handle nested skills (e.g. library/db)
    # Strategy: find all SKILL.md files and validate their parent directory
    
    skill_roots = set()
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            skill_roots.add(Path(root))
            
    if not skill_roots:
        print("No skills found!")
        sys.exit(1)
        
    for skill_path in sorted(skill_roots):
        rel_path = skill_path.relative_to(SKILLS_DIR)
        errors = validate_skill(skill_path)
        
        if errors:
            all_valid = False
            print(f"❌ {rel_path}:")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"✅ {rel_path}")
            
    if all_valid:
        print("\nAll skills passed validation!")
        sys.exit(0)
    else:
        print("\nValidation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
