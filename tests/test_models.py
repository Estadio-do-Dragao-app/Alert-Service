import pytest
from datetime import datetime
from schemas import EmergencyEvent, Alert, AlertType, ClientAlert

def test_emergency_event_creation():
    event = EmergencyEvent(
        event_id="e1",
        event_type="FIRE",
        severity="high",
        location="A1",
        timestamp=datetime.now(),
        details={"key": "value"}
    )
    assert event.event_id == "e1"
    assert event.get_details() == {"key": "value"}

def test_alert_creation():
    alert = Alert(
        id=1,
        type=AlertType.FIRE,
        disabled_tiles=["T1"],
        message="Test",
        timestamp=datetime.now(),
        severity="critical",
        level="critical"
    )
    assert alert.type == AlertType.FIRE
    assert alert.level == "critical"

def test_client_alert_serialization():
    client_alert = ClientAlert(
        alert_id=1,
        alert_type="FIRE",
        message="Msg",
        timestamp="2025-01-01T00:00:00",
        severity="high",
        affected_areas=["A1"],
        level="high"
    )
    assert client_alert.model_dump_json()