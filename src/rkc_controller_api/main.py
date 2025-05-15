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

# --- Logging Configuration ---
# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(), # Log to console
        # add a FileHandler here for application logs
        logging.FileHandler("rkc_api_app.log")
    ]
)
logger = logging.getLogger(__name__)


# --- Lifespan Management for RKC Connection and Poller ---
polling_bg_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    - Initializes RKCManager and connects to the controller.
    - Starts the background polling task.
    - Cleans up on shutdown.
    """
    global polling_bg_task
    logger.info("FastAPI application startup...")

    # Initialize and connect RKCManager
    # Assign to the module-level variable rkc_handler
    rkc_manager_module.rkc_handler = rkc_manager_module.RKCManager()
    logger.info("Attempting to connect RKC controller via RKCManager...")
    # The connect method is synchronous, run it in a thread to avoid blocking event loop
    await anyio.to_thread.run_sync(rkc_manager_module.rkc_handler.connect)

    if rkc_manager_module.rkc_handler.is_connected:
        logger.info("RKC Manager connected. Starting polling task.")
        # Start the background polling task
        polling_bg_task = asyncio.create_task(polling_task(rkc_manager_module.rkc_handler))
    else:
        logger.error("RKC Manager failed to connect. Polling task will not start. API might be limited.")
        # The API endpoints will check rkc_manager.is_connected

    yield  # Application runs here

    logger.info("FastAPI application shutdown...")
    if polling_bg_task and not polling_bg_task.done():
        logger.info("Cancelling polling task...")
        polling_bg_task.cancel()
        try:
            await polling_bg_task
        except asyncio.CancelledError:
            logger.info("Polling task successfully cancelled.")
        except Exception as e:
            logger.error("Error during polling task shutdown: %s", e, exc_info=True)

    if rkc_manager_module.rkc_handler:
        logger.info("Disconnecting RKC controller via RKCManager...")
        # The disconnect method is synchronous
        await anyio.to_thread.run_sync(rkc_manager_module.rkc_handler.disconnect)
    logger.info("Shutdown complete.")

# --- FastAPI Application Instance ---
app = FastAPI(
    title="RKC Controller API",
    description="API to interact with RKC FB Series Temperature Controllers and log data.",
    version="0.1.0",
    lifespan=lifespan # Register lifespan context manager
)

# Include API routers
app.include_router(rkc_api_router, prefix="/controller", tags=["RKC Controller"])

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for the API. Returns a welcome message.
    """
    return {"message": "Welcome to the RKC Controller API. See /docs for API details."}

# --- Main entry point for running the server ---
if __name__ == "__main__":
    # This allows running the app directly using `python src/rkc_controller_api/main.py`
    # For production, prefer `uvicorn rkc_controller_api.main:app --reload`
    logger.info("Starting Uvicorn server on %s:%s", settings['host'], settings['port'])
    uvicorn.run(app, host=settings['host'], port=settings['port'], log_level="info")

