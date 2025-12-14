import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from main import AlertService
from mqtt_handler import MQTTAlertHandler
from models import EmergencyEvent, Alert, AlertType

class TestIntegration:
    """Integration tests for the Alert Service."""
    
    @patch('paho.mqtt.client.Client')
    def test_full_flow(self, mock_client_class):
        """Test full flow from event reception to alert broadcast."""
        # Create service
        service = AlertService()
        
        # Mock MQTT handler
        mock_handler = Mock(spec=MQTTAlertHandler)
        mock_handler._create_alert_from_event = Mock()
        mock_handler.broadcast_alert = Mock()
        service.mqtt_handler = mock_handler
        
        # Create test event
        event_data = {
            "event_id": "integration-test",
            "event_type": "MEDICAL",
            "timestamp": datetime.now().isoformat(),
            "severity": "HIGH",
            "metadata": {
                "description": "Medical emergency in section B",
                "disabled_tiles": [401, 402],
                "location": "First Aid Station 2"
            }
        }
        
        # Simulate receiving MQTT message
        event = EmergencyEvent(**event_data)
        service.process_emergency_event(event)
        
        # Verify the flow
        mock_handler._create_alert_from_event.assert_called_once()
        
        # Get the created alert
        alert = mock_handler._create_alert_from_event.return_value
        mock_handler.broadcast_alert.assert_called_once_with(alert)
    
    def test_alert_serialization_deserialization(self):
        """Test that alerts can be serialized to JSON and back."""
        # Create alert
        alert = Alert(
            id=999,
            type=AlertType.EVACUATION,
            disabled_tiles=[501, 502, 503],
            message="Evacuation required",
            timestamp=datetime.now(),
            severity="CRITICAL"
        )
        
        # Simulate what MQTT handler does
        from models import ClientAlert
        client_alert = ClientAlert(
            alert_id=alert.id,
            alert_type=alert.type.value,
            message=alert.message,
            timestamp=alert.timestamp.isoformat(),
            severity=alert.severity,
            affected_areas=alert.disabled_tiles
        )
        
        # Serialize to JSON
        json_str = client_alert.model_dump_json()
        
        # Deserialize back
        data = json.loads(json_str)
        
        # Verify data integrity
        assert data["alert_id"] == 999
        assert data["alert_type"] == "EVACUATION"
        assert data["message"] == "Evacuation required"
        assert data["severity"] == "CRITICAL"
        assert data["affected_areas"] == [501, 502, 503]
    
    @patch('logging.getLogger')
    def test_logging_integration(self, mock_logger):
        """Test logging integration."""
        from mqtt_handler import MQTTAlertHandler
        
        # Setup mock logger
        mock_log = Mock()
        mock_logger.return_value = mock_log
        
        handler = MQTTAlertHandler(
            simulator_broker="localhost",
            simulator_port=1883,
            client_broker="localhost",
            client_port=1884
        )
        
        # Mock the clients
        handler.simulator_client = Mock()
        handler.client_publisher = Mock()
        
        # Test connection logging
        handler._on_simulator_connect(None, None, None, 0)
        assert mock_log.info.called
        assert "Connected to broker" in mock_log.info.call_args[0][0]