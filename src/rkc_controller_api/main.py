import logging
import asyncio
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
import uvicorn # For running the app

from rkc_controller_api.api.routers import router as rkc_api_router
from rkc_controller_api.config import settings
from rkc_controller_api.core import rkc_manager as rkc_manager_module # import the module
from rkc_controller_api.core.poller import polling_task


class RKCControllerServer:
    """
    Encapsulates FastAPI server setup and running logic for the RKC Controller API.

    Example usage:
        server = RKCControllerServer()
        server.start()
    """

    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("rkc_api_app.log"),
            ],
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self._app = FastAPI(
            title="RKC Controller API",
            description="API to interact with RKC FB Series Temperature Controllers and log data.",
            version="0.1.0",
            lifespan=self._lifespan,
        )

        # Include routers
        self._app.include_router(rkc_api_router, prefix="/controller", tags=["RKC Controller"])

        # Root endpoint
        @self._app.get("/", tags=["Root"])
        async def read_root():
            return {"message": "Welcome to the RKC Controller API. See /docs for API details."}

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """
        Lifespan context: 
        Manages application startup and shutdown events.
        - Initializes RKCManager and connects to the controller.
        - Starts/stops the background polling task.
        - Cleans up on shutdown.
        """
        self.logger.info("FastAPI application startup...")

        # Initialize and connect RKCManager
        rkc_manager_module.rkc_handler = rkc_manager_module.RKCManager()
        self.logger.info("Connecting to RKC controller...")
        await anyio.to_thread.run_sync(rkc_manager_module.rkc_handler.connect)

        # Start polling task if connected
        if rkc_manager_module.rkc_handler.is_connected:
            self.logger.info("Connected. Starting polling task.")
            # Start the background polling task
            self._poll_task = asyncio.create_task(
                polling_task(rkc_manager_module.rkc_handler)
            )
        else:
            self.logger.error("Connection failed. Polling task will not start.")
            # The API endpoints will check rkc_manager.is_connected
        yield  # Application runs here

        # Shutdown
        self.logger.info("Application shutdown...")
        if hasattr(self, '_poll_task') and not self._poll_task.done():
            self.logger.info("Cancelling polling task...")
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                self.logger.info("Polling task cancelled.")
            except Exception as e:
                self.logger.error("Error shutting down polling: %s", e, exc_info=True)

        # Disconnect RKC
        if hasattr(rkc_manager_module, 'rkc_handler') and rkc_manager_module.rkc_handler:
            self.logger.info("Disconnecting RKC controller...")
            await anyio.to_thread.run_sync(
                rkc_manager_module.rkc_handler.disconnect
            )
        self.logger.info("Shutdown complete.")

    def start(self, host: str = None, port: int = None, log_level: str = "info"):
        """
        Start the Uvicorn server with the configured FastAPI app.

        :param host: hostname to bind (defaults to settings['host'])
        :param port: port number (defaults to settings['port'])
        :param log_level: Uvicorn log level
        """
        h = host or settings['host']
        p = port or settings['port']
        self.logger.info("Starting Uvicorn server on %s:%s", h, p)
        uvicorn.run(self._app, host=h, port=p, log_level=log_level)


if __name__ == "__main__":
    server = RKCControllerServer()
    server.start()
