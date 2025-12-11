import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from typing import Callable, Optional
from models import EmergencyEvent, Alert, ClientAlert, AlertType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTAlertHandler:
    """
    Handles MQTT communication for the Alert Service.
    - Subscribes to emergency events from the stadium simulator
    - Publishes alerts to clients
    """
    
    def __init__(self, broker: str, port: int, 
                 simulator_topic: str = "stadium/events/emergency",
                 client_topic_prefix: str = "alerts/client"):
        self.broker = broker
        self.port = port
        self.simulator_topic = simulator_topic
        self.client_topic_prefix = client_topic_prefix
        self.broadcast_topic = "alerts/broadcast"
        
        self.client = mqtt.Client(client_id="alert_service")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.alert_id_counter = 0
        self.message_callback: Optional[Callable] = None
        
    def set_message_callback(self, callback: Callable[[EmergencyEvent], None]):
        """Set a callback function to process incoming emergency events."""
        self.message_callback = callback
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handler for MQTT connection event."""
        if rc == 0:
            logger.info(f"✓ Connected to MQTT broker at {self.broker}:{self.port}")
            client.subscribe(self.simulator_topic)
            logger.info(f"✓ Subscribed to topic: {self.simulator_topic}")
        else:
            logger.error(f"✗ Connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handler for MQTT disconnection event."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages with emergency data."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"📨 Received emergency event: {payload.get('event_type', 'UNKNOWN')}")
            
            # Parse incoming event
            event = EmergencyEvent(**payload)
            
            # Call custom callback if set
            if self.message_callback:
                self.message_callback(event)
            else:
                # Default behavior: convert and broadcast
                alert = self._create_alert_from_event(event)
                self.broadcast_alert(alert)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _create_alert_from_event(self, event: EmergencyEvent) -> Alert:
        """Convert an emergency event to an alert."""
        self.alert_id_counter += 1
        
        # Map event type to alert type
        alert_type_map = {
            "FIRE": AlertType.FIRE,
            "SECURITY": AlertType.SECURITY,
            "MEDICAL": AlertType.MEDICAL,
            "EVACUATION": AlertType.EVACUATION
        }
        
        alert_type = alert_type_map.get(event.event_type.upper(), AlertType.SECURITY)
        
        return Alert(
            id=self.alert_id_counter,
            type=alert_type,
            disabled_tiles=event.details.get("disabled_tiles", []) if event.details else [],
            message=f"{event.event_type}: {event.details.get('description', 'Emergency detected')}",
            timestamp=event.timestamp,
            severity=event.severity
        )
    
    def broadcast_alert(self, alert: Alert):
        """Send alert to all clients via broadcast topic."""
        client_alert = ClientAlert(
            alert_id=alert.id,
            alert_type=alert.type.value,
            message=alert.message,
            timestamp=alert.timestamp.isoformat(),
            severity=alert.severity,
            affected_areas=alert.disabled_tiles
        )
        
        payload = client_alert.model_dump_json()
        result = self.client.publish(self.broadcast_topic, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📢 Broadcast alert {alert.id} to all clients")
        else:
            logger.error(f"Failed to publish alert {alert.id}")
    
    def send_alert_to_client(self, client_id: str, alert: Alert):
        """Send alert to a specific client."""
        client_alert = ClientAlert(
            alert_id=alert.id,
            alert_type=alert.type.value,
            message=alert.message,
            timestamp=alert.timestamp.isoformat(),
            severity=alert.severity,
            affected_areas=alert.disabled_tiles
        )
        
        topic = f"{self.client_topic_prefix}/{client_id}"
        payload = client_alert.model_dump_json()
        result = self.client.publish(topic, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📨 Sent alert {alert.id} to client {client_id}")
        else:
            logger.error(f"Failed to send alert to client {client_id}")
    
    def start(self):
        """Start the MQTT client and connect to the broker."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"🚀 Alert Service MQTT Handler started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT client."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Alert Service MQTT Handler stopped")