import pytest
from pathlib import Path
from mcp_server.config import Config, ChromaConfig

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
        Config.model_validate(config.model_dump())

def test_config_invalid_chunk_overlap():
    """Test invalid chunk_overlap raises error"""
    config = Config.load_default()
    config.indexing.chunk_overlap = 1000  # >= chunk_size
    with pytest.raises(ValueError):
        Config.model_validate(config.model_dump())

def test_config_save_and_load_file(tmp_path):
    """Test saving and loading configuration from file"""
    config = Config.load_default()
    config.chroma.host = "test-host"
    config.chroma.port = 9000
    config.github.token = "secret-token"

    file_path = tmp_path / "config.json"
    config.save_to_file(file_path)
    assert file_path.exists()

    loaded_config = Config.load_from_file(file_path)
    assert loaded_config.chroma.host == "test-host"
    assert loaded_config.chroma.port == 9000
    assert loaded_config.github.token is None  # Token should be excluded

def test_chroma_config_expand_tilde():
    """Test that tilde is expanded in persist_directory"""
    config = ChromaConfig(persist_directory="~/test/path")
    expanded = config.persist_directory_expanded
    assert str(expanded).startswith("/")  # Should be absolute path
    assert "~" not in str(expanded)