import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from main import AlertService
from models import EmergencyEvent, Alert

class TestAlertService:
    """Test AlertService class."""
    
    def test_service_initialization(self):
        """Test AlertService initialization with environment variables."""
        with patch.dict('os.environ', {
            'SIMULATOR_BROKER': 'test-broker',
            'SIMULATOR_PORT': '1885',
            'MQTT_BROKER': 'client-broker',
            'MQTT_PORT': '1886',
            'SIMULATOR_TOPIC': 'test/topic',
            'CLIENT_TOPIC_PREFIX': 'test/alerts'
        }):
            service = AlertService()
            
            # Verify MQTT handler was initialized with correct values
            assert service.mqtt_handler is not None
            # The handler will use the values from environment
    
    def test_process_emergency_event(self):
        """Test processing emergency event with callback."""
        service = AlertService()
        
        # Mock the MQTT handler
        mock_handler = Mock()
        mock_handler._create_alert_from_event = Mock(return_value=Mock(spec=Alert))
        mock_handler.broadcast_alert = Mock()
        service.mqtt_handler = mock_handler
        
        # Create test event
        event = EmergencyEvent(
            event_id="test-001",
            event_type="FIRE",
            timestamp=datetime.now(),
            severity="HIGH",
            metadata={"description": "Test event"}
        )
        
        # Process the event
        service.process_emergency_event(event)
        
        # Verify handler methods were called
        mock_handler._create_alert_from_event.assert_called_once_with(event)
        mock_handler.broadcast_alert.assert_called_once()
    
    def test_service_start_stop(self):
        """Test starting and stopping the service."""
        service = AlertService()
        
        # Mock the MQTT handler
        mock_handler = Mock()
        mock_handler.start = Mock()
        mock_handler.stop = Mock()
        service.mqtt_handler = mock_handler
        
        # Mock time.sleep to break the loop
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            # Start service (will be interrupted immediately)
            service.start()
            
            # Verify handler was started
            mock_handler.start.assert_called_once()
            
            # Stop service
            service.stop()
            
            # Verify handler was stopped
            mock_handler.stop.assert_called_once()
    
    def test_signal_handler(self):
        """Test signal handler for graceful shutdown."""
        import signal
        import sys
        from main import signal_handler
        
        # Mock sys.exit
        with patch('sys.exit') as mock_exit:
            # Call signal handler
            signal_handler(signal.SIGINT, None)
            
            # Verify sys.exit was called
            mock_exit.assert_called_once_with(0)