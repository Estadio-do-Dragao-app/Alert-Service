import pytest
from unittest.mock import Mock, patch, call
from mqtt_handler import MQTTAlertHandler
from schemas import EmergencyEvent, Alert, ClientAlert, AlertType
from datetime import datetime, timedelta
import json

@pytest.fixture
def handler():
    handler = MQTTAlertHandler(
        simulator_broker="localhost",
        simulator_port=1883,
        client_broker="localhost",
        client_port=1884,
        simulator_topic="test/topic",
        client_topic_prefix="alerts/client"
    )
    # Prevent actual MQTT connections
    handler.simulator_client.connect = Mock()
    handler.simulator_client.loop_start = Mock()
    handler.client_publisher.connect = Mock()
    handler.client_publisher.loop_start = Mock()
    return handler

def test_create_alert_from_event(handler, sample_emergency_event):
    alert = handler.create_alert_from_event(sample_emergency_event)
    assert alert.type == AlertType.FIRE
    assert alert.disabled_tiles == ["B12", "B13"]
    assert alert.message == "FIRE: Fire detected"
    assert alert.severity == "high"
    assert alert.level == sample_emergency_event.severity

def test_broadcast_alert(handler, sample_alert):
    handler.client_publisher.publish = Mock(return_value=Mock(rc=0))
    handler.broadcast_alert(sample_alert)
    handler.client_publisher.publish.assert_called_once()
    args, _ = handler.client_publisher.publish.call_args
    assert args[0] == "alerts/broadcast"
    assert "alert_id" in args[1]

def test_on_message_callback(handler, sample_emergency_event):
    callback = Mock()
    handler.set_message_callback(callback)
    import json
    payload = sample_emergency_event.model_dump_json().encode()
    msg = Mock(payload=payload)
    handler._on_message(None, None, msg)
    callback.assert_called_once()
    called_event = callback.call_args[0][0]
    assert called_event.event_id == sample_emergency_event.event_id


# ===== New Tests for Priority, Expiry Time, and ACK Validation =====

def test_priority_mapping_from_severity(handler):
    """Test that priority is correctly mapped from severity levels."""
    assert handler._get_priority_from_severity("critical") == "CRITICAL"
    assert handler._get_priority_from_severity("high") == "HIGH"
    assert handler._get_priority_from_severity("medium") == "MEDIUM"
    assert handler._get_priority_from_severity("low") == "LOW"
    # Test case insensitivity
    assert handler._get_priority_from_severity("CRITICAL") == "CRITICAL"
    assert handler._get_priority_from_severity("High") == "HIGH"
    # Test default for unknown/None
    assert handler._get_priority_from_severity(None) == "MEDIUM"
    assert handler._get_priority_from_severity("unknown") == "MEDIUM"


def test_broadcast_alert_priority_and_expiry(handler, sample_alert):
    """Test that broadcast alert uses severity-based priority and alert.timestamp for expiry."""
    handler.client_publisher.publish = Mock(return_value=Mock(rc=0))
    
    # Test with high severity alert
    sample_alert.severity = "high"
    handler.broadcast_alert(sample_alert)
    
    handler.client_publisher.publish.assert_called_once()
    args, kwargs = handler.client_publisher.publish.call_args
    payload_str = args[1]
    
    # Parse the JSON payload
    import json
    payload = json.loads(payload_str)
    
    # Verify priority is HIGH, not CRITICAL
    assert payload["priority"] == "HIGH", "Priority should be HIGH for high severity alert"
    
    # Verify expiry_time is based on alert.timestamp + 1 hour
    alert_timestamp = sample_alert.timestamp
    expected_expiry = (alert_timestamp + timedelta(hours=1)).isoformat()
    assert payload["expiry_time"] == expected_expiry, "expiry_time should be alert.timestamp + 1 hour"


def test_send_alert_to_client_priority_and_expiry(handler, sample_alert):
    """Test that send_alert_to_client uses severity-based priority and alert.timestamp for expiry."""
    from datetime import timedelta
    handler.client_publisher.publish = Mock(return_value=Mock(rc=0))
    
    sample_alert.severity = "medium"
    handler.send_alert_to_client("client_123", sample_alert)
    
    handler.client_publisher.publish.assert_called_once()
    args, kwargs = handler.client_publisher.publish.call_args
    payload_str = args[1]
    
    import json
    payload = json.loads(payload_str)
    
    assert payload["priority"] == "MEDIUM", "Priority should be MEDIUM for medium severity alert"
    expected_expiry = (sample_alert.timestamp + timedelta(hours=1)).isoformat()
    assert payload["expiry_time"] == expected_expiry, "expiry_time should be alert.timestamp + 1 hour"


def test_on_client_message_ack_validation_missing_alert_id(handler):
    """Test that ACK without alert_id is properly rejected with warning."""
    msg = Mock()
    msg.topic = "alerts/ack/client_123"
    msg.payload = json.dumps({"status": "received"}).encode()  # Missing alert_id
    
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_client_message(None, None, msg)
        # Verify warning was logged for missing alert_id
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "missing alert_id" in call_args


def test_on_client_message_ack_validation_non_dict_payload(handler):
    """Test that non-dict payloads are properly rejected."""
    msg = Mock()
    msg.topic = "alerts/ack/client_123"
    msg.payload = json.dumps(["array", "not", "object"]).encode()  # Array instead of dict
    
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_client_message(None, None, msg)
        # Verify warning was logged for non-dict payload
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "expected JSON object" in call_args


def test_on_client_message_ack_valid(handler):
    """Test that valid ACK with alert_id is properly logged."""
    msg = Mock()
    msg.topic = "alerts/ack/client_456"
    msg.payload = json.dumps({"alert_id": 42}).encode()

    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_client_message(None, None, msg)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "42" in call_args
        assert "client_456" in call_args


def test_on_simulator_connect_success(handler):
    """Test simulator on_connect with rc=0 subscribes to topic."""
    client = Mock()
    handler._on_simulator_connect(client, None, {}, 0)
    client.subscribe.assert_called_once_with(handler.simulator_topic)


def test_on_simulator_connect_failure(handler):
    """Test simulator on_connect with rc!=0 logs error."""
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_simulator_connect(Mock(), None, {}, 1)
        mock_logger.error.assert_called_once()


def test_on_client_connect_success(handler):
    """Test client on_connect with rc=0 subscribes to ACK topic."""
    client = Mock()
    handler._on_client_connect(client, None, {}, 0)
    client.subscribe.assert_called_once()


def test_on_client_connect_failure(handler):
    """Test client on_connect with rc!=0 logs error."""
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_client_connect(Mock(), None, {}, 5)
        mock_logger.error.assert_called_once()


def test_on_simulator_disconnect_unexpected(handler):
    """Test simulator on_disconnect with non-zero rc logs warning."""
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_simulator_disconnect(None, None, 1)
        mock_logger.warning.assert_called_once()


def test_on_simulator_disconnect_clean(handler):
    """Test simulator on_disconnect with rc=0 does not log warning."""
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_simulator_disconnect(None, None, 0)
        mock_logger.warning.assert_not_called()


def test_on_client_disconnect_unexpected(handler):
    """Test client on_disconnect with non-zero rc logs warning."""
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_client_disconnect(None, None, 1)
        mock_logger.warning.assert_called_once()


def test_on_message_no_callback_broadcasts(handler, sample_emergency_event):
    """Test _on_message falls back to create_alert+broadcast when no callback set."""
    handler.message_callback = None
    handler.client_publisher.publish = Mock(return_value=Mock(rc=0))

    payload = sample_emergency_event.model_dump_json().encode()
    msg = Mock(payload=payload)
    handler._on_message(None, None, msg)

    handler.client_publisher.publish.assert_called_once()


def test_on_message_invalid_json(handler):
    """Test _on_message logs error on malformed JSON."""
    msg = Mock(payload=b"not json {")
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_message(None, None, msg)
        mock_logger.error.assert_called()


def test_on_message_exception(handler):
    """Test _on_message logs error on unexpected exception."""
    msg = Mock(payload=b'{"event_id": "x"}')
    with patch('mqtt_handler.logger') as mock_logger:
        handler._on_message(None, None, msg)
        mock_logger.error.assert_called()


def test_broadcast_alert_publish_failure(handler, sample_alert):
    """Test broadcast_alert logs error when publish fails."""
    handler.client_publisher.publish = Mock(return_value=Mock(rc=1))
    with patch('mqtt_handler.logger') as mock_logger:
        handler.broadcast_alert(sample_alert)
        mock_logger.error.assert_called_once()


def test_send_alert_to_client_publish_failure(handler, sample_alert):
    """Test send_alert_to_client logs error when publish fails."""
    handler.client_publisher.publish = Mock(return_value=Mock(rc=1))
    with patch('mqtt_handler.logger') as mock_logger:
        handler.send_alert_to_client("client_1", sample_alert)
        mock_logger.error.assert_called_once()


def test_start_exception(handler):
    """Test start() logs error and re-raises on connection failure."""
    handler.simulator_client.connect = Mock(side_effect=Exception("timeout"))
    with pytest.raises(Exception, match="timeout"):
        handler.start()


def test_stop(handler):
    """Test stop() calls loop_stop and disconnect on both clients."""
    handler.simulator_client.loop_stop = Mock()
    handler.simulator_client.disconnect = Mock()
    handler.client_publisher.loop_stop = Mock()
    handler.client_publisher.disconnect = Mock()

    handler.stop()

    handler.simulator_client.loop_stop.assert_called_once()
    handler.simulator_client.disconnect.assert_called_once()
    handler.client_publisher.loop_stop.assert_called_once()
    handler.client_publisher.disconnect.assert_called_once()