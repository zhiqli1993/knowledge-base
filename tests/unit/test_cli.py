from unittest.mock import patch

import pytest

from kb.cli import main as cli_main


@pytest.mark.asyncio
async def test_async_main_formats_runtime_errors(capsys, monkeypatch):
    class DummyCLI:
        async def status(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(cli_main.sys, "argv", ["kb", "status"])

    with patch.object(cli_main, "KnowledgeBaseCLI", return_value=DummyCLI()):
        exit_code = await cli_main.async_main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "KB Error" in captured.out
    assert "boom" in captured.out


@pytest.mark.asyncio
async def test_async_main_formats_logs_validation_error(capsys, monkeypatch):
    monkeypatch.setattr(cli_main.sys, "argv", ["kb", "logs", "0"])

    exit_code = await cli_main.async_main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "KB Error" in captured.out
    assert "greater than 0" in captured.out


@pytest.mark.asyncio
async def test_async_main_formats_logs_type_error(capsys, monkeypatch):
    monkeypatch.setattr(cli_main.sys, "argv", ["kb", "logs", "abc"])

    exit_code = await cli_main.async_main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "KB Error" in captured.out
    assert "must be an integer" in captured.out


@pytest.mark.asyncio
async def test_async_main_formats_logs_output(capsys, monkeypatch):
    monkeypatch.setattr(cli_main.sys, "argv", ["kb", "logs", "2"])

    with patch.object(cli_main, "read_logs", return_value="line one\nline two"):
        exit_code = await cli_main.async_main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "KB Logs" in captured.out
    assert "line one" in captured.out
