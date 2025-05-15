import logging
from datetime import datetime
import csv
import os
from typing import List

import anyio
from fastapi import APIRouter, HTTPException, Depends, Body

from rkc_controller_api.models import schemas
from rkc_controller_api.config import settings
from rkc_controller_api.core.rkc_manager import RKCManager, get_rkc_manager

logger = logging.getLogger(__name__)
router = APIRouter()

LOG_FILE_PATH = settings['log_file_path']

@router.post("/set_temperature", response_model=schemas.GeneralResponse)
async def set_temperature_endpoint(
    temp_setting: schemas.TemperatureSetting = Body(...),
    rkc_manager: RKCManager = Depends(get_rkc_manager)
):
    """
    Sets the target temperature (Setpoint Value - SV) on the RKC controller.
    """
    logger.info("Received request to set temperature to: %s", temp_setting.temperature)
    if not rkc_manager.is_connected:
        logger.error("Cannot set temperature: RKC controller not connected.")
        raise HTTPException(status_code=503, detail="RKC controller not connected.")

    success = await anyio.to_thread.run_sync(rkc_manager.set_temperature, temp_setting.temperature)
    if success:
        return schemas.GeneralResponse(success=True, 
                                       message=f"Temperature setpoint updated to {temp_setting.temperature}°C.")
    else:
        logger.error("Failed to set temperature to %s via RKC manager.", temp_setting.temperature)
        raise HTTPException(status_code=500, detail="Failed to set temperature on the controller.")

@router.get("/status", response_model=schemas.ControllerStatus)
async def get_status_endpoint(rkc_manager: RKCManager = Depends(get_rkc_manager)):
    """
    Gets the current status (current_temperature, target_temperature, output_value) 
    from the RKC controller.
    Values are based on the latest successful poll by the background poller.
    """
    # If never connected or lost connection
    if not rkc_manager.is_connected and (rkc_manager.current_temperature is None): 
        logger.warning("Cannot get status: RKC controller not connected or no data available.")
        raise HTTPException(status_code=503, detail="RKC controller not connected or no data available.")

    # Return last known values from the rkc_manager, which are updated by the poller
    return schemas.ControllerStatus(
        timestamp=datetime.now(), # Current time of request
        current_temperature=rkc_manager.current_temperature,
        target_temperature=rkc_manager.target_temperature,
        output_value=rkc_manager.output_value,
        message="Live status from controller." if rkc_manager.is_connected else "Last known status, controller might be disconnected."
    )

@router.get("/history", response_model=schemas.HistoryResponse)
async def get_history_endpoint(lines: int = settings.get('max_history_lines', 100)):
    """
    Retrieves the last N lines of logged data (timestamp, current_temperature, SV, output_value).
    """
    if not os.path.exists(LOG_FILE_PATH):
        logger.warning("Log file not found: %s", LOG_FILE_PATH)
        raise HTTPException(status_code=404, detail="Log file not found.")

    try:
        all_entries: List[schemas.HistoryEntry] = []
        with open(LOG_FILE_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_entries.append(schemas.HistoryEntry(
                    timestamp=row.get('timestamp', ''),
                    current_temperature=row.get('current_temperature'),
                    target_temperature=row.get('target_temperature'),
                    output_value=row.get('output_value')
                ))
        
        # Get the last 'lines' entries
        # If lines is 0 or negative, it means all lines.
        if lines <= 0:
             entries_to_return = all_entries
        else:
            entries_to_return = all_entries[-lines:]
            
        return schemas.HistoryResponse(
            count=len(entries_to_return),
            entries=entries_to_return
        )
    except FileNotFoundError:
        logger.error("Log file not found at path: %s", LOG_FILE_PATH)
        return schemas.HistoryResponse(count=0, entries=[], message="Log file not found.")
    except Exception as e:
        logger.error("Error reading history log: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading history log: {str(e)}") from e

