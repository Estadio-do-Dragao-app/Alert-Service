from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EmergencyEvent(BaseModel):
    event_id: str
    event_type: str = "emergency"
    severity: str # low, medium, high, critical
    location: str
    timestamp: datetime

class Alert(BaseModel):
    alert_id: str
    message: str
    severity: str
    timestamp: datetime

class ClientAlert(BaseModel):
    type: str = "alert"
    msg: str
    lvl: str
    ts: str
