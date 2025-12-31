import asyncio
import logging
import signal
from typing import NoReturn

import uvicorn

from src.api.main import create_app
from src.workers.tick_worker import TickWorker
from src.workers.checker_worker import CheckerWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.tick_worker = TickWorker()
        self.checker_worker = CheckerWorker()
        self.server: uvicorn.Server | None = None
        self.shutdown_event = asyncio.Event()

    async def start_api_server(self) -> None:
        logger.info(f"Starting API server on {self.host}:{self.port}")
        app = create_app()
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True,
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()

    async def start_all(self) -> NoReturn:
        logger.info("Starting ADG Gameserver (API + Workers)...")
        
        tasks = [
            asyncio.create_task(self.start_api_server(), name="api_server"),
            asyncio.create_task(self.tick_worker.start(), name="tick_worker"),
            asyncio.create_task(self.checker_worker.start(), name="checker_worker"),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Services cancelled, shutting down...")

    def stop_all(self) -> None:
        logger.info("Stopping all services...")
        self.tick_worker.stop()
        self.checker_worker.stop()
        if self.server:
            self.server.should_exit = True
        self.shutdown_event.set()


async def main() -> None:
    server = GameServer(host="0.0.0.0", port=8000)
    
    loop = asyncio.get_running_loop()
    
    def signal_handler(sig: int) -> None:
        logger.info(f"Received signal {sig}, initiating shutdown...")
        server.stop_all()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    try:
        await server.start_all()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        server.stop_all()
        logger.info("All services stopped")


if __name__ == "__main__":
    asyncio.run(main())
