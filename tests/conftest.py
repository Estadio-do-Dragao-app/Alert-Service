import pytest
from datetime import datetime
from schemas import EmergencyEvent, Alert, AlertType

@pytest.fixture
def sample_emergency_event():
    return EmergencyEvent(
        event_id="evt_001",
        event_type="FIRE",
        severity="high",
        location="Section B",
        timestamp=datetime.now(),
        details={"affected_areas": ["B12", "B13"], "description": "Fire detected"},
        level="high"
    )

@pytest.fixture
def sample_alert():
    return Alert(
        id=1,
        type=AlertType.FIRE,
        disabled_tiles=["B12", "B13"],
        message="FIRE: Fire detected",
        timestamp=datetime.now(),
        severity="high",
        level="high"
    )