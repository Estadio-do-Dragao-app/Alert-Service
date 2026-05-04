from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any, Dict
from enum import Enum

class AlertType(str, Enum):
    FIRE = "FIRE"
    SECURITY = "SECURITY"
    MEDICAL = "MEDICAL"
    EVACUATION = "EVACUATION"

class EmergencyEvent(BaseModel):
    event_id: str
    event_type: str = "emergency"
    severity: str  # low, medium, high, critical
    location: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    level: Optional[str] = None

    def get_details(self) -> Dict[str, Any]:
        return self.details or {}

class Alert(BaseModel):
    id: int
    type: AlertType
    disabled_tiles: List[str]
    message: str
    timestamp: datetime
    severity: str
    level: str  # low, medium, high, critical

class ClientAlert(BaseModel):
    alert_id: int
    alert_type: str
    message: str
    timestamp: str
    severity: str
    affected_areas: List[str]
    level: str
    priority: str = "CRITICAL"
    expiry_time: Optional[str] = None