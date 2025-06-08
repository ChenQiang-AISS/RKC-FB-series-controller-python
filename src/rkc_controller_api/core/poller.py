import asyncio
import logging
import csv
from datetime import datetime
import os
from typing import Optional
import anyio  # Required for FastAPI's background tasks with sync code

from rkc_controller_api.config import settings
from rkc_controller_api.core.rkc_manager import RKCManager

logger = logging.getLogger(__name__)

LOG_FILE_PATH = settings['log_file_path']
LOG_FIELDNAMES = ['timestamp', 'current_temperature', 'target_temperature', 'output_value']


def initialize_log_file():
    """
    Initializes the log file by creating the necessary directory and writing the header.
    """
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    with open(LOG_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
        writer.writeheader()


def _log_data(timestamp: datetime, current_temperature: Optional[float], 
              target_temperature: Optional[float], output_value: Optional[float]):
    """Appends data to the CSV log file."""
    try:
        with open(LOG_FILE_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
            writer.writerow({
                'timestamp': timestamp.isoformat(),
                'current_temperature': f"{current_temperature:.1f}" if current_temperature is not None else '',
                'target_temperature': f"{target_temperature:.1f}" if target_temperature is not None else '',
                'output_value': f"{output_value:.1f}" if output_value is not None else ''
            })
        logger.debug("Logged data: current_temperature=%s, target_temperature=%s, output_value=%s", 
                     current_temperature, target_temperature, output_value)
    except Exception as e:
        logger.error("Failed to write to log file %s: %s", LOG_FILE_PATH, e, exc_info=True)


async def polling_task(rkc_manager: RKCManager):
    """Periodically polls the RKC controller and logs data."""
    
    loop = asyncio.get_event_loop()
    interval = settings['polling_interval_seconds']
    next_time = loop.time()
    
    logger.info("Polling task started.")
    while True:
        try:
            # Calculate the time until the next poll       
            next_time += interval

            if rkc_manager.is_connected:
                # Run synchronous blocking IO in a separate thread
                current_temperature, target_temperature, output_value = await anyio.to_thread.run_sync(rkc_manager.get_status)

                current_time = datetime.now()
                _log_data(current_time, current_temperature, target_temperature, output_value)
                
            else:
                logger.warning("Polling task: RKC controller not connected. Attempting to reconnect...")
                # Try to reconnect if not connected
                await anyio.to_thread.run_sync(rkc_manager.connect)

            await asyncio.sleep(max(0, next_time - loop.time()))
        except asyncio.CancelledError:
            logger.info("Polling task cancelled.")
            break
        except Exception as e:
            logger.error("Error in polling task: %s", e, exc_info=True)
            # Avoid busy-looping on persistent errors
            await asyncio.sleep(max(0, next_time - loop.time()))

    logger.info("Polling task stopped.")


# Ensure log directory and file exist with headers if new
if not os.path.exists(LOG_FILE_PATH) or os.path.getsize(LOG_FILE_PATH) == 0:
    initialize_log_file()
