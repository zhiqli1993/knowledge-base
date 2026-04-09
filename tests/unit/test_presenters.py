from kb.presenters import format_error, format_logs, format_search, format_sources, format_usage


def test_format_sources_empty_uses_box():
    output = format_sources({"sources": []})
    assert "┌─ KB " in output
    assert "No sources found." in output


def test_format_search_empty_uses_box():
    output = format_search({"results": []})
    assert "┌─ KB " in output
    assert "No results found." in output


def test_format_logs_uses_log_box():
    output = format_logs("line one\nline two")
    assert "KB Logs" in output
    assert "line one" in output
    assert "line two" in output


def test_format_usage_mentions_https_repo_url():
    output = format_usage()
    assert "kb add-repo <owner/repo|https-url> [branch]" in output


def test_format_error_uses_error_box():
    output = format_error("boom")
    assert "KB Error" in output
    assert "boom" in output
