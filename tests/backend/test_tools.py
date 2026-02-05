"""
Tests for tools module.
"""

import pytest


class TestListSkills:
    """Test skill listing functionality."""
    
    def test_list_skills_returns_list(self, project_root):
        """Test that list_skills returns a list."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import list_skills
        
        skills = list_skills()
        
        assert isinstance(skills, list)
        assert len(skills) > 0
    
    def test_list_skills_has_required_fields(self, project_root):
        """Test that each skill has required fields."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import list_skills
        
        skills = list_skills()
        
        for skill in skills:
            assert 'name' in skill
            assert 'path' in skill
            assert 'type' in skill


class TestSearchSkills:
    """Test skill search functionality."""
    
    def test_search_skills_returns_list(self, project_root):
        """Test that search_skills returns a list."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import search_skills
        
        results = search_skills("paper")
        
        assert isinstance(results, list)
    
    def test_search_skills_matches_name(self, project_root):
        """Test that search matches skill names."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import search_skills
        
        results = search_skills("weread")
        
        assert len(results) > 0
        assert any('weread' in r['name'].lower() for r in results)


class TestReadSkill:
    """Test skill reading functionality."""
    
    def test_read_skill_returns_content(self, project_root):
        """Test that read_skill returns content."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import read_skill
        
        content = read_skill(".claude/skills/weread/SKILL.md")
        
        assert isinstance(content, str)
        assert len(content) > 0
        assert 'WeRead' in content
    
    def test_read_skill_not_found(self, project_root):
        """Test read_skill with non-existent path."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import read_skill
        
        content = read_skill("nonexistent/skill.md")
        
        assert 'Error' in content or 'not found' in content.lower()
    
    def test_read_skill_blocks_path_traversal(self, project_root):
        """Test that read_skill blocks path traversal."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import read_skill
        
        content = read_skill("../../../etc/passwd")
        
        assert 'Error' in content
        assert 'Invalid' in content


class TestUpdateSkillCode:
    """Test skill update functionality."""
    
    def test_update_skill_code_validates_path(self, project_root):
        """Test that update_skill_code validates paths."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import update_skill_code
        
        # Invalid path outside skills/
        result = update_skill_code("app.py", "# malicious code")
        
        assert 'Error' in result
    
    def test_update_skill_code_blocks_path_traversal(self, project_root):
        """Test that update_skill_code blocks path traversal."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import update_skill_code
        
        result = update_skill_code("skills/../app.py", "# malicious code")
        
        assert 'Error' in result


class TestToolDefinitions:
    """Test tool definitions."""
    
    def test_tools_def_is_list(self, project_root):
        """Test that TOOLS_DEF is a list."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import TOOLS_DEF
        
        assert isinstance(TOOLS_DEF, list)
        assert len(TOOLS_DEF) > 0
    
    def test_tools_have_required_fields(self, project_root):
        """Test that each tool definition has required fields."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import TOOLS_DEF
        
        for tool in TOOLS_DEF:
            assert 'name' in tool
            assert 'description' in tool
            assert 'input_schema' in tool
    
    def test_get_tool_map_returns_dict(self, project_root):
        """Test that get_tool_map returns a dict."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import get_tool_map
        
        tool_map = get_tool_map()
        
        assert isinstance(tool_map, dict)
        assert len(tool_map) > 0
    
    def test_get_tool_function(self, project_root):
        """Test getting tool function by name."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import get_tool_function
        
        fn = get_tool_function("list_skills")
        
        assert callable(fn)
    
    def test_get_tool_function_unknown(self, project_root):
        """Test getting unknown tool function raises error."""
        import sys
        sys.path.insert(0, str(project_root))
        
        from backend.tools import get_tool_function
        
        with pytest.raises(ValueError):
            get_tool_function("nonexistent_tool")
