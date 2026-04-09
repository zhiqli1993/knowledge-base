import pytest
from pathlib import Path
from kb.config import Config, ChromaConfig, DEFAULT_CONFIG_PATH, resolve_config_path

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


def test_service_config_defaults():
    """Test service config defaults."""
    config = Config.load_default()
    assert config.service.host == "127.0.0.1"
    assert config.service.port == 8864
    assert config.service.effective_base_url == "http://127.0.0.1:8864"


def test_resolve_config_path_prefers_override(tmp_path):
    """Test config path override wins."""
    override = tmp_path / "custom.json"
    assert resolve_config_path(str(override)) == override


def test_resolve_config_path_defaults_to_kb_path():
    """Test default config path uses ~/.kb/config.json."""
    assert resolve_config_path() == DEFAULT_CONFIG_PATH
