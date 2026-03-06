import os
from pathlib import Path

def test_mcp_server_directory_exists():
    """Verify mcp-server directory structure"""
    assert Path("mcp-server").exists()
    assert Path("mcp-server/__init__.py").exists()
    assert Path("mcp-server/requirements.txt").exists()

def test_skill_directory_exists():
    """Verify skill directory structure"""
    assert Path("skill").exists()
    assert Path("skill/SKILL.md").exists()