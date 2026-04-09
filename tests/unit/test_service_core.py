from unittest.mock import AsyncMock

import pytest

from kb.config import Config
from kb.service.core import KBService


@pytest.mark.asyncio
async def test_add_repo_keeps_missing_branch_for_background_resolution():
    service = KBService(Config())
    service._create_source = AsyncMock(return_value={"accepted": True})

    await service.add_repo("https://github-cli.corp.ebay.com/zhiqli/istio-upgrade-automation")
    source = service._create_source.await_args.args[0]
    assert source.id == "github:zhiqli/istio-upgrade-automation"
    assert source.url == "https://github-cli.corp.ebay.com/zhiqli/istio-upgrade-automation"
    assert source.config["branch"] is None


@pytest.mark.asyncio
async def test_add_repo_keeps_explicit_branch():
    service = KBService(Config())
    service._create_source = AsyncMock(return_value={"accepted": True})

    await service.add_repo("owner/repo", branch="release")
    source = service._create_source.await_args.args[0]
    assert source.id == "github:owner/repo"
    assert source.url == "https://github.com/owner/repo"
    assert source.config["branch"] == "release"
