import logging
from datetime import datetime
import os
from typing import Optional

import anyio
from fastapi import APIRouter, HTTPException, Depends, Body, Query
import pandas as pd

from rkc_controller_api.models import schemas
from rkc_controller_api.core.poller import LOG_FIELDNAMES
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
async def get_history_endpoint(
    lines: Optional[int] = Query(settings.get('max_history_lines', 100), 
                                 description="Max number of lines to return. 0 or negative for all."),
    from_timestamp: Optional[datetime] = Query(None, alias="from", 
                                               description="ISO 8601 format: YYYY-MM-DDTHH:MM:SS[.ffffff][Z or +HH:MM]. " \
                                                "If not provided, all entries are returned. If provided without timezone, local time is assumed."),
    to_timestamp: Optional[datetime] = Query(None, alias="to", 
                                             description="ISO 8601 format: YYYY-MM-DDTHH:MM:SS[.ffffff][Z or +HH:MM]. " \
                                            "If not provided, all entries are returned. If provided without timezone, local time is assumed."),
):
    """
    Retrieves logged data. Can be filtered by a timestamp range and limited by number of lines.
    Timestamp filtering is applied first, then line limiting.
    """
    if not os.path.exists(LOG_FILE_PATH):
        logger.warning("Log file not found: %s", LOG_FILE_PATH)
        raise HTTPException(status_code=404, detail="Log file not found.")

    try:
        df = pd.read_csv(LOG_FILE_PATH)

        # Check for missing headers
        expected_headers = LOG_FIELDNAMES
        if not all(header in df.columns for header in expected_headers):
            logger.error("Log file %s has missing headers. Expected: %s, Got: %s", 
                         LOG_FILE_PATH, expected_headers, df.columns)
            raise HTTPException(status_code=500, detail="Log file format error: Missing expected CSV headers.")

        # Convert timestamp column to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # Filter out rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])

        # Localize naive timestamps from CSV to the server's current local timezone.
        # This assumes timestamps in CSV were logged in the server's local time (as naive)
        # and makes them timezone-aware for correct comparison.
        if not df.empty and pd.api.types.is_datetime64_ns_dtype(df['timestamp']) and df['timestamp'].dt.tz is None:
            try:
                local_tz = datetime.now().astimezone().tzinfo
                df['timestamp'] = df['timestamp'].dt.tz_localize(local_tz, ambiguous='infer', nonexistent='raise')
            except Exception as e:
                logger.error("Failed to localize timestamps in DataFrame: %s", e, exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Error processing timestamp timezones in log data."
                ) from e

        # Make query timestamps timezone-aware if they are naive, assuming local timezone
        effective_from_ts = from_timestamp
        if effective_from_ts and effective_from_ts.tzinfo is None:
            effective_from_ts = effective_from_ts.replace(tzinfo=datetime.now().astimezone().tzinfo)

        effective_to_ts = to_timestamp
        if effective_to_ts and effective_to_ts.tzinfo is None:
            effective_to_ts = effective_to_ts.replace(tzinfo=datetime.now().astimezone().tzinfo)

        # Filter by timestamp range
        if effective_from_ts:
            df = df[df['timestamp'] >= effective_from_ts]
        if effective_to_ts:
            df = df[df['timestamp'] <= effective_to_ts]

        # Convert the DataFrame to a list of HistoryEntry objects
        all_entries = [
            schemas.HistoryEntry(
                timestamp=row['timestamp'],
                current_temperature=row['current_temperature'],
                target_temperature=row['target_temperature'],
                output_value=row['output_value']
            )
            for index, row in df.iterrows()
        ]

    except pd.errors.EmptyDataError as e:
        logger.error("Log file is empty: %s", LOG_FILE_PATH)
        raise HTTPException(status_code=404, detail="Log file is empty.") from e
    except Exception as e:
        logger.error("Error processing log file: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing log file") from e

    # Apply line limit to the filtered (or all) entries
    # If lines is 0 or negative, it means all lines from the filtered set.
    if lines is not None and lines > 0:
        entries_to_return = all_entries[-lines:]
    else: # lines <= 0 or lines is None (though Query gives default)
        entries_to_return = all_entries

    return schemas.HistoryResponse(
        count=len(entries_to_return),
        entries=entries_to_return
    )
