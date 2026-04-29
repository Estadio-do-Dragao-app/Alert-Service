import pytest
from unittest.mock import Mock, patch, call
from mqtt_handler import MQTTAlertHandler
from schemas import EmergencyEvent, Alert, ClientAlert, AlertType
from datetime import datetime

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
    alert = handler._create_alert_from_event(sample_emergency_event)
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