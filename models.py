from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


# Basic Models
class Boundary(BaseModel):
    x_bound: tuple[float, float]
    y_bound: tuple[float, float]


class Pos(BaseModel):
    x: int
    y: int


# Entity Models
class EntityType(Enum):
    NODE = "NODE"
    GATE = "GATE"


class Entity(BaseModel):
    id: int
    type: EntityType
    pos: Pos


class Node(Entity):
    pass


# Tile Model
class Tile(BaseModel):
    id: int
    level: int
    grid_pos: Pos
    boundary: Boundary
    walkable: bool
    entities: list[Entity] = Field(default_factory=list)


# Alert Models
class AlertType(Enum):
    FIRE = "FIRE"
    SECURITY = "SECURITY"
    MEDICAL = "MEDICAL"
    EVACUATION = "EVACUATION"


class EmergencyEvent(BaseModel):
    """Incoming event from stadium simulator"""
    event_id: str
    event_type: str
    timestamp: datetime
    location_id: Optional[str] = None
    location: Optional[dict] = None
    severity: str
    metadata: Optional[dict] = None  # Simulator uses 'metadata', keep 'details' for backwards compatibility
    details: Optional[dict] = None
    
    def get_details(self) -> dict:
        """Get details/metadata regardless of which field is used"""
        return self.metadata or self.details or {}


class Alert(BaseModel):
    """Alert to be sent to clients"""
    id: int
    type: AlertType
    disabled_tiles: list[int] = Field(default_factory=list)  # Just tile IDs for efficiency
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: str = "HIGH"
    

class ClientAlert(BaseModel):
    """Simplified alert format for client consumption"""
    alert_id: int
    alert_type: str
    message: str
    timestamp: str
    severity: str
    affected_areas: list[int] = Field(default_factory=list)