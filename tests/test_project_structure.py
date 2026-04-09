from pathlib import Path

def test_kb_directory_exists():
    """Verify kb directory structure"""
    assert Path("src/kb").exists()
    assert Path("src/kb/__init__.py").exists()
    assert Path("src/kb/cli/main.py").exists()
    assert Path("src/kb/mcp/server.py").exists()
    assert Path("pyproject.toml").exists()

def test_skill_directory_exists():
    """Verify skill directory structure"""
    assert Path("skill").exists()
    assert Path("skill/SKILL.md").exists()
