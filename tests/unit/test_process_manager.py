from pathlib import Path

import pytest

from kb.http import process_manager


def test_service_command_uses_python_module_when_not_frozen(monkeypatch):
    monkeypatch.delenv("KB_HTTP_EXECUTABLE", raising=False)
    monkeypatch.delattr(process_manager.sys, "frozen", raising=False)
    monkeypatch.setattr(process_manager.sys, "executable", "/tmp/python3")

    assert process_manager._service_command() == ["/tmp/python3", "-m", "kb.http"]


def test_service_command_prefers_override_binary(monkeypatch, tmp_path):
    executable = tmp_path / process_manager._binary_name("custom-kb-http")
    executable.write_text("", encoding="utf-8")
    if process_manager.os.name != "nt":
        executable.chmod(0o755)

    monkeypatch.setenv("KB_HTTP_EXECUTABLE", str(executable))
    monkeypatch.delattr(process_manager.sys, "frozen", raising=False)

    assert process_manager._service_command() == [str(executable)]


def test_service_command_uses_companion_binary_when_frozen(monkeypatch, tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    kb_binary = bundle_dir / process_manager._binary_name("kb")
    service_binary = bundle_dir / process_manager._binary_name("kb-http")
    kb_binary.write_text("", encoding="utf-8")
    service_binary.write_text("", encoding="utf-8")
    if process_manager.os.name != "nt":
        kb_binary.chmod(0o755)
        service_binary.chmod(0o755)

    monkeypatch.delenv("KB_HTTP_EXECUTABLE", raising=False)
    monkeypatch.setattr(process_manager.sys, "frozen", True, raising=False)
    monkeypatch.setattr(process_manager.sys, "executable", str(kb_binary))

    assert process_manager._service_command() == [str(service_binary)]


def test_service_command_errors_when_companion_binary_missing(monkeypatch, tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    kb_binary = bundle_dir / process_manager._binary_name("kb")
    kb_binary.write_text("", encoding="utf-8")
    if process_manager.os.name != "nt":
        kb_binary.chmod(0o755)

    monkeypatch.delenv("KB_HTTP_EXECUTABLE", raising=False)
    monkeypatch.setattr(process_manager.sys, "frozen", True, raising=False)
    monkeypatch.setattr(process_manager.sys, "executable", str(kb_binary))

    with pytest.raises(RuntimeError, match="companion service binary"):
        process_manager._service_command()
