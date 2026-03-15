import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from mqtt_handler import MQTTAlertHandler
from models import EmergencyEvent, Alert, AlertType

class TestMQTTAlertHandler:
    """Test MQTTAlertHandler class."""
    
    def test_handler_initialization(self, sample_mqtt_config):
        """Test MQTTAlertHandler initialization."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        assert handler.simulator_broker == "localhost"
        assert handler.simulator_port == 1883
        assert handler.client_broker == "localhost"
        assert handler.client_port == 1884
        assert handler.simulator_topic == "stadium/events/alerts"
        assert handler.client_topic_prefix == "alerts/client"
        assert handler.alert_id_counter == 0
        assert handler.message_callback is None
    
    def test_set_message_callback(self, sample_mqtt_config):
        """Test setting message callback."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        # Create a mock callback
        mock_callback = Mock()
        handler.set_message_callback(mock_callback)
        
        assert handler.message_callback == mock_callback
    
    def test_create_alert_from_event(self, sample_mqtt_config):
        """Test converting EmergencyEvent to Alert."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        event = EmergencyEvent(
            event_id="fire-001",
            event_type="FIRE",
            timestamp=datetime.now(),
            severity="CRITICAL",
            metadata={
                "description": "Major fire",
                "disabled_tiles": [201, 202, 203]
            }
        )
        
        alert = handler._create_alert_from_event(event)
        
        assert alert.id == 1  # First alert, ID should be 1
        assert alert.type == AlertType.FIRE
        assert alert.disabled_tiles == [201, 202, 203]
        assert "Major fire" in alert.message
        assert alert.severity == "CRITICAL"
        assert alert.timestamp == event.timestamp
        
        # Test counter increments
        alert2 = handler._create_alert_from_event(event)
        assert alert2.id == 2
    
    def test_create_alert_from_different_event_types(self, sample_mqtt_config):
        """Test alert creation for different event types."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        event_types = [
            ("FIRE", AlertType.FIRE),
            ("SECURITY", AlertType.SECURITY),
            ("MEDICAL", AlertType.MEDICAL),
            ("EVACUATION", AlertType.EVACUATION),
            ("UNKNOWN_TYPE", AlertType.SECURITY),  # Default to SECURITY
        ]
        
        for event_type, expected_alert_type in event_types:
            event = EmergencyEvent(
                event_id=f"{event_type.lower()}-001",
                event_type=event_type,
                timestamp=datetime.now(),
                severity="MEDIUM",
                metadata={"description": f"{event_type} event"}
            )
            
            alert = handler._create_alert_from_event(event)
            assert alert.type == expected_alert_type
    
    @patch('paho.mqtt.client.Client')
    def test_broadcast_alert(self, mock_client_class, sample_mqtt_config):
        """Test broadcasting alert to all clients."""
        # Setup
        handler = MQTTAlertHandler(**sample_mqtt_config)
        handler.client_publisher = Mock()
        handler.client_publisher.publish = Mock(return_value=Mock(rc=0))
        
        # Create test alert
        alert = Alert(
            id=1,
            type=AlertType.FIRE,
            disabled_tiles=[101, 102],
            message="Test fire alert",
            timestamp=datetime.now(),
            severity="HIGH"
        )
        
        # Call method
        handler.broadcast_alert(alert)
        
        # Verify
        assert handler.client_publisher.publish.called
        call_args = handler.client_publisher.publish.call_args
        assert call_args[0][0] == "alerts/broadcast"
        
        # Verify payload is valid JSON
        payload = call_args[0][1]
        payload_dict = json.loads(payload)
        assert payload_dict["alert_id"] == 1
        assert payload_dict["alert_type"] == "FIRE"
        assert payload_dict["message"] == "Test fire alert"
        assert payload_dict["severity"] == "HIGH"
    
    @patch('paho.mqtt.client.Client')
    def test_send_alert_to_client(self, mock_client_class, sample_mqtt_config):
        """Test sending alert to specific client."""
        # Setup
        handler = MQTTAlertHandler(**sample_mqtt_config)
        handler.client_publisher = Mock()
        handler.client_publisher.publish = Mock(return_value=Mock(rc=0))
        
        # Create test alert
        alert = Alert(
            id=2,
            type=AlertType.MEDICAL,
            disabled_tiles=[301],
            message="Medical emergency",
            timestamp=datetime.now(),
            severity="HIGH"
        )
        
        # Call method
        handler.send_alert_to_client("client_123", alert)
        
        # Verify
        assert handler.client_publisher.publish.called
        call_args = handler.client_publisher.publish.call_args
        assert call_args[0][0] == "alerts/client/client_123"
        
        # Verify payload
        payload = call_args[0][1]
        payload_dict = json.loads(payload)
        assert payload_dict["alert_id"] == 2
        assert payload_dict["alert_type"] == "MEDICAL"
    
    def test_on_message_with_callback(self, sample_mqtt_config):
        """Test processing incoming MQTT message with callback."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        # Setup mock callback
        mock_callback = Mock()
        handler.set_message_callback(mock_callback)
        
        # Create mock message
        mock_msg = Mock()
        test_payload = {
            "event_id": "test-001",
            "event_type": "FIRE",
            "timestamp": datetime.now().isoformat(),
            "severity": "HIGH",
            "metadata": {"description": "Test fire"}
        }
        mock_msg.payload = json.dumps(test_payload).encode()
        
        # Call message handler
        handler._on_message(None, None, mock_msg)
        
        # Verify callback was called
        assert mock_callback.called
        event_arg = mock_callback.call_args[0][0]
        assert isinstance(event_arg, EmergencyEvent)
        assert event_arg.event_id == "test-001"
    
    def test_on_message_without_callback(self, sample_mqtt_config):
        """Test processing incoming MQTT message without callback."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        # Mock the broadcast_alert method
        handler.broadcast_alert = Mock()
        
        # Create mock message
        mock_msg = Mock()
        test_payload = {
            "event_id": "test-002",
            "event_type": "SECURITY",
            "timestamp": datetime.now().isoformat(),
            "severity": "MEDIUM",
            "metadata": {"description": "Security alert"}
        }
        mock_msg.payload = json.dumps(test_payload).encode()
        
        # Call message handler
        handler._on_message(None, None, mock_msg)
        
        # Verify broadcast_alert was called
        assert handler.broadcast_alert.called
    
    def test_on_message_invalid_json(self, sample_mqtt_config, caplog):
        """Test handling invalid JSON in message."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        # Create mock message with invalid JSON
        mock_msg = Mock()
        mock_msg.payload = b"invalid json"
        
        # Call message handler
        handler._on_message(None, None, mock_msg)
        
        # Should log error but not crash
        assert "Failed to decode JSON" in caplog.text
    
    @patch('paho.mqtt.client.Client')
    def test_start_and_stop(self, mock_client_class, sample_mqtt_config):
        """Test starting and stopping the MQTT handler."""
        handler = MQTTAlertHandler(**sample_mqtt_config)
        
        # Mock the MQTT clients
        mock_simulator_client = Mock()
        mock_client_publisher = Mock()
        handler.simulator_client = mock_simulator_client
        handler.client_publisher = mock_client_publisher
        
        # Test start
        handler.start()
        
        assert mock_simulator_client.connect.called
        assert mock_simulator_client.loop_start.called
        assert mock_client_publisher.connect.called
        assert mock_client_publisher.loop_start.called
        
        # Test stop
        handler.stop()
        
        assert mock_simulator_client.loop_stop.called
        assert mock_simulator_client.disconnect.called
        assert mock_client_publisher.loop_stop.called
        assert mock_client_publisher.disconnect.called