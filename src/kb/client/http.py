from typing import Any, Dict, Optional
from urllib.parse import quote

import aiohttp

from kb.config import Config, resolve_config_path


class KBHttpClient:
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config.load_from_file(resolve_config_path())
        self.config = config
        self.base_url = self.config.service.effective_base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=self.config.service.timeout_seconds)

    async def _request(self, method: str, path: str, *, params=None, json=None) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.request(method, f"{self.base_url}{path}", params=params, json=json) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    raise RuntimeError(data.get('error', f'HTTP {response.status}'))
                return data

    async def health(self) -> Dict[str, Any]:
        return await self._request('GET', '/healthz')

    async def status(self) -> Dict[str, Any]:
        return await self._request('GET', '/v1/status')

    async def list_sources(self, source_type: Optional[str] = None) -> Dict[str, Any]:
        params = {'type': source_type} if source_type else None
        return await self._request('GET', '/v1/sources', params=params)

    async def get_source(self, source_id: str) -> Dict[str, Any]:
        return await self._request('GET', f"/v1/sources/{quote(source_id, safe='')}")

    async def progress(self, source_id: str) -> Dict[str, Any]:
        return await self._request('GET', f"/v1/sources/{quote(source_id, safe='')}/progress")

    async def add_url(self, url: str) -> Dict[str, Any]:
        return await self._request('POST', '/v1/sources/url', json={'url': url})

    async def add_site(self, base_url: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
        payload = {'base_url': base_url}
        if max_pages is not None:
            payload['max_pages'] = max_pages
        return await self._request('POST', '/v1/sources/site', json=payload)

    async def add_repo(self, repo_url: str, branch: Optional[str] = None, include=None, exclude=None) -> Dict[str, Any]:
        return await self._request('POST', '/v1/sources/repo', json={
            'repo_url': repo_url,
            'branch': branch,
            'include': include or [],
            'exclude': exclude or [],
        })

    async def add_local(self, path: str, include=None, exclude=None) -> Dict[str, Any]:
        return await self._request('POST', '/v1/sources/local', json={
            'path': path,
            'include': include or [],
            'exclude': exclude or [],
        })

    async def search(self, query: str, n_results: int = 5, source_filter: Optional[str] = None) -> Dict[str, Any]:
        params = {'q': query, 'n_results': str(n_results)}
        if source_filter:
            params['source_filter'] = source_filter
        return await self._request('GET', '/v1/search', params=params)

    async def delete(self, source_id: str) -> Dict[str, Any]:
        return await self._request('DELETE', f"/v1/sources/{quote(source_id, safe='')}")

    async def reindex(self, source_id: Optional[str] = None) -> Dict[str, Any]:
        path = '/v1/sources/reindex' if source_id is None else f"/v1/sources/{quote(source_id, safe='')}/reindex"
        return await self._request('POST', path)

    async def update(self, source_id: Optional[str] = None) -> Dict[str, Any]:
        path = '/v1/sources/update' if source_id is None else f"/v1/sources/{quote(source_id, safe='')}/update"
        return await self._request('POST', path)
