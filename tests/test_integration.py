import pytest
from unittest.mock import Mock, patch
from main import AlertService
from schemas import EmergencyEvent, Alert
from datetime import datetime

@pytest.mark.asyncio
async def test_full_flow():
    with patch('main.MQTTAlertHandler') as MockHandler:
        mock_handler = MockHandler.return_value
        mock_handler._create_alert_from_event.return_value = Mock(spec=Alert)
        mock_handler.broadcast_alert = Mock()
        
        service = AlertService()
        service.mqtt_handler = mock_handler
        
        event = EmergencyEvent(
            event_id="e1",
            event_type="SECURITY",
            severity="medium",
            location="Gate 3",
            timestamp=datetime.now(),
            details={"affected_areas": ["G3"]}
        )
        service.process_emergency_event(event)
        
        mock_handler._create_alert_from_event.assert_called_once()
        mock_handler.broadcast_alert.assert_called_once()