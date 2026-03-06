import pytest
from pathlib import Path
from mcp_server.config import Config

def test_config_load_default():
    """Test loading default configuration"""
    config = Config.load_default()
    assert config.chroma.host == "localhost"
    assert config.chroma.port == 8000
    assert config.ollama.model == "nomic-embed-text"

def test_config_validate():
    """Test configuration validation"""
    config = Config.load_default()
    assert config.validate() is True

def test_config_invalid_chunk_size():
    """Test invalid chunk size raises error"""
    config = Config.load_default()
    config.indexing.chunk_size = -1
    with pytest.raises(ValueError):
        config.validate()