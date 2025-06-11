from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TemperatureSetting(BaseModel):
    """Request model for setting temperature."""
    temperature: float

class ControllerStatus(BaseModel):
    """Response model for current controller status."""
    timestamp: datetime
    current_temperature: Optional[float] = None
    target_temperature: Optional[float] = None
    output_value: Optional[float] = None
    message: Optional[str] = None

class HistoryEntry(BaseModel):
    """Model for a single log entry."""
    timestamp: datetime # Store as string from CSV, can be parsed to datetime if needed
    current_temperature: Optional[float] = None
    target_temperature: Optional[float] = None
    output_value: Optional[float] = None

class HistoryResponse(BaseModel):
    """Response model for history."""
    count: int
    entries: List[HistoryEntry]
    message: Optional[str] = None

class GeneralResponse(BaseModel):
    """Generic response model."""
    success: bool
    message: Optional[str] = None
    details: Optional[str] = None

class PollRequest(BaseModel):
    """Request model for polling data from the controller."""
    identifier: str
    memory_area: Optional[str] = ""
    return_with_identifier: Optional[bool] = False

class PollResponse(GeneralResponse):
    """Response model for polling data from the controller."""
    data: Optional[str] = None
    identifier: Optional[str] = None

class SelectRequest(BaseModel):
    """Request model for selecting (sending) data to the controller."""
    identifier: str
    data: str
