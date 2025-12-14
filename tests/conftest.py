import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

@pytest.fixture
def sample_emergency_event():
    """Sample emergency event for testing."""
    return {
        "event_id": "fire-001",
        "event_type": "FIRE",
        "timestamp": datetime.now().isoformat(),
        "severity": "HIGH",
        "metadata": {
            "description": "Fire detected in section A",
            "location": "Gate 1",
            "disabled_tiles": [101, 102, 103]
        }
    }

@pytest.fixture
def sample_mqtt_config():
    """MQTT configuration for testing."""
    return {
        "simulator_broker": "localhost",
        "simulator_port": 1883,
        "client_broker": "localhost", 
        "client_port": 1884,
        "simulator_topic": "stadium/events/alerts",
        "client_topic_prefix": "alerts/client"
    }

@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client."""
    client = Mock()
    client.connect = Mock()
    client.loop_start = Mock()
    client.loop_stop = Mock()
    client.disconnect = Mock()
    client.publish = Mock(return_value=Mock(rc=0))
    client.subscribe = Mock()
    return client

@pytest.fixture
def mock_emergency_event():
    """Mock emergency event object."""
    from models import EmergencyEvent
    return EmergencyEvent(
        event_id="test-001",
        event_type="FIRE",
        timestamp=datetime.now(),
        severity="HIGH",
        metadata={"description": "Test fire", "disabled_tiles": [1, 2, 3]}
    )