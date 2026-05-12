import pytest
from unittest.mock import Mock, patch
from main import AlertService
from schemas import EmergencyEvent

@pytest.fixture
def service():
    with patch('main.MQTTAlertHandler') as mock_handler:
        service = AlertService()
        service.mqtt_handler = mock_handler.return_value
        yield service

def test_process_emergency_event(service, sample_emergency_event):
    # Mock the create_alert_from_event and broadcast_alert
    mock_alert = Mock()
    service.mqtt_handler.create_alert_from_event.return_value = mock_alert
    service.mqtt_handler.broadcast_alert = Mock()
    
    service.process_emergency_event(sample_emergency_event)
    
    service.mqtt_handler.create_alert_from_event.assert_called_once_with(sample_emergency_event)
    service.mqtt_handler.broadcast_alert.assert_called_once_with(mock_alert)

def test_start_stop(service):
    service.mqtt_handler.start = Mock()
    service.mqtt_handler.stop = Mock()
    
    # Break the while loop quickly
    with patch('time.sleep', side_effect=KeyboardInterrupt):
        service.start()
    
    service.mqtt_handler.start.assert_called_once()
    service.mqtt_handler.stop.assert_called_once()