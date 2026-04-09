from aiohttp import web
from typing import Any, Dict

from kb.config import Config
from kb.service.core import KBService


async def _json_error(message: str, status: int) -> web.Response:
    return web.json_response({"error": message}, status=status)


def _exc_message(exc: Exception) -> str:
    if isinstance(exc, KeyError) and exc.args:
        return str(exc.args[0])
    return str(exc)


async def create_app(config: Config) -> web.Application:
    service = KBService(config)
    await service.initialize()
    app = web.Application()
    app["service"] = service

    async def healthz(request: web.Request) -> web.Response:
        return web.json_response(await service.health())

    async def status(request: web.Request) -> web.Response:
        return web.json_response(await service.status())

    async def list_sources(request: web.Request) -> web.Response:
        return web.json_response(await service.list_sources(request.query.get("type")))

    async def get_source(request: web.Request) -> web.Response:
        try:
            return web.json_response(await service.get_source(request.match_info["source_id"]))
        except KeyError as exc:
            return await _json_error(_exc_message(exc), 404)

    async def get_progress(request: web.Request) -> web.Response:
        try:
            return web.json_response(await service.get_progress(request.match_info["source_id"]))
        except KeyError as exc:
            return await _json_error(_exc_message(exc), 404)

    async def add_url(request: web.Request) -> web.Response:
        payload = await request.json()
        try:
            return web.json_response(await service.add_url(payload["url"]), status=202)
        except (KeyError, ValueError) as exc:
            return await _json_error(_exc_message(exc), 400)

    async def add_site(request: web.Request) -> web.Response:
        payload = await request.json()
        try:
            return web.json_response(await service.add_site(payload["base_url"], payload.get("max_pages")), status=202)
        except (KeyError, ValueError) as exc:
            return await _json_error(_exc_message(exc), 400)

    async def add_repo(request: web.Request) -> web.Response:
        payload = await request.json()
        try:
            return web.json_response(
                await service.add_repo(
                    payload["repo_url"],
                    payload.get("branch"),
                    payload.get("include"),
                    payload.get("exclude"),
                ),
                status=202,
            )
        except (KeyError, ValueError, RuntimeError) as exc:
            return await _json_error(_exc_message(exc), 400)

    async def add_local(request: web.Request) -> web.Response:
        payload = await request.json()
        try:
            return web.json_response(
                await service.add_local(payload["path"], payload.get("include"), payload.get("exclude")),
                status=202,
            )
        except FileNotFoundError as exc:
            return await _json_error(_exc_message(exc), 404)
        except PermissionError as exc:
            return await _json_error(_exc_message(exc), 422)
        except (KeyError, ValueError) as exc:
            return await _json_error(_exc_message(exc), 400)

    async def search(request: web.Request) -> web.Response:
        query = request.query.get("q")
        if not query:
            return await _json_error("Missing q query parameter", 400)
        n_results = int(request.query.get("n_results", 5))
        source_filter = request.query.get("source_filter")
        return web.json_response(await service.search(query, n_results, source_filter))

    async def delete_source(request: web.Request) -> web.Response:
        try:
            return web.json_response(await service.delete_source(request.match_info["source_id"]))
        except KeyError as exc:
            return await _json_error(_exc_message(exc), 404)

    async def reindex_source(request: web.Request) -> web.Response:
        try:
            return web.json_response(await service.reindex_source(request.match_info["source_id"]), status=202)
        except KeyError as exc:
            return await _json_error(_exc_message(exc), 404)

    async def update_source(request: web.Request) -> web.Response:
        try:
            return web.json_response(await service.update_source(request.match_info["source_id"]), status=202)
        except KeyError as exc:
            return await _json_error(_exc_message(exc), 404)

    async def reindex_all(request: web.Request) -> web.Response:
        return web.json_response(await service.reindex_all(), status=202)

    async def update_all(request: web.Request) -> web.Response:
        return web.json_response(await service.update_all(), status=202)

    app.router.add_get('/healthz', healthz)
    app.router.add_get('/v1/status', status)
    app.router.add_get('/v1/sources', list_sources)
    app.router.add_post('/v1/sources/url', add_url)
    app.router.add_post('/v1/sources/site', add_site)
    app.router.add_post('/v1/sources/repo', add_repo)
    app.router.add_post('/v1/sources/local', add_local)
    app.router.add_get('/v1/search', search)
    app.router.add_post('/v1/sources/reindex', reindex_all)
    app.router.add_post('/v1/sources/update', update_all)
    app.router.add_get(r'/v1/sources/{source_id:.+}/progress', get_progress)
    app.router.add_post(r'/v1/sources/{source_id:.+}/reindex', reindex_source)
    app.router.add_post(r'/v1/sources/{source_id:.+}/update', update_source)
    app.router.add_delete(r'/v1/sources/{source_id:.+}', delete_source)
    app.router.add_get(r'/v1/sources/{source_id:.+}', get_source)
    return app
