import asyncio
import os
from aiohttp import web

from kb.config import Config, resolve_config_path
from kb.http.app import create_app


async def _run() -> None:
    config_path = resolve_config_path(os.getenv("KNOWLEDGE_BASE_CONFIG"))
    config = Config.load_from_file(config_path)
    app = await create_app(config)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.service.host, config.service.port)
    await site.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def main() -> None:
    asyncio.run(_run())


if __name__ == '__main__':
    main()
