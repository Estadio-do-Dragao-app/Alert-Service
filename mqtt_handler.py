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
    - Subscribes to emergency events from the stadium simulator (via simulator broker)
    - Publishes alerts to clients (via client broker)
    """
    
    def __init__(self, 
                 simulator_broker: str, simulator_port: int,
                 client_broker: str, client_port: int,
                 simulator_topic: str = "stadium/events/alerts",
                 client_topic_prefix: str = "alerts/client"):
        # Simulator broker connection (for receiving events)
        self.simulator_broker = simulator_broker
        self.simulator_port = simulator_port
        self.simulator_topic = simulator_topic
        
        # Client broker connection (for publishing alerts)
        self.client_broker = client_broker
        self.client_port = client_port
        self.client_topic_prefix = client_topic_prefix
        self.broadcast_topic = "alerts/broadcast"
        
        # Separate MQTT clients for each broker
        self.simulator_client = mqtt.Client(client_id="alert_service_receiver")
        self.simulator_client.on_connect = self._on_simulator_connect
        self.simulator_client.on_message = self._on_message
        self.simulator_client.on_disconnect = self._on_simulator_disconnect
        
        self.client_publisher = mqtt.Client(client_id="alert_service_publisher")
        self.client_publisher.on_connect = self._on_client_connect
        self.client_publisher.on_disconnect = self._on_client_disconnect
        
        self.alert_id_counter = 0
        self.message_callback: Optional[Callable] = None
        
    def set_message_callback(self, callback: Callable[[EmergencyEvent], None]):
        """Set a callback function to process incoming emergency events."""
        self.message_callback = callback
    
    def _on_simulator_connect(self, client, userdata, flags, rc):
        """Handler for MQTT connection event to simulator broker."""
        if rc == 0:
            logger.info(f"✓ Connected to simulator MQTT broker at {self.simulator_broker}:{self.simulator_port}")
            client.subscribe(self.simulator_topic)
            logger.info(f"✓ Subscribed to simulator topic: {self.simulator_topic}")
        else:
            logger.error(f"✗ Simulator connection failed with code {rc}")
    
    def _on_client_connect(self, client, userdata, flags, rc):
        """Handler for MQTT connection event to client broker."""
        if rc == 0:
            logger.info(f"✓ Connected to client MQTT broker at {self.client_broker}:{self.client_port}")
        else:
            logger.error(f"✗ Client broker connection failed with code {rc}")
    
    def _on_simulator_disconnect(self, client, userdata, rc):
        """Handler for MQTT disconnection event from simulator broker."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from simulator broker. Code: {rc}")
    
    def _on_client_disconnect(self, client, userdata, rc):
        """Handler for MQTT disconnection event from client broker."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from client broker. Code: {rc}")
    
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
            "FIRE_ALERT": AlertType.FIRE,  # Simulator uses "fire_alert"
            "SECURITY": AlertType.SECURITY,
            "MEDICAL": AlertType.MEDICAL,
            "EVACUATION": AlertType.EVACUATION
        }
        
        alert_type = alert_type_map.get(event.event_type.upper(), AlertType.SECURITY)
        
        # Get details/metadata from event
        details = event.get_details()
        
        return Alert(
            id=self.alert_id_counter,
            type=alert_type,
            disabled_tiles=details.get("disabled_tiles", []),
            message=f"{event.event_type}: {details.get('description', 'Emergency detected')}",
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
        result = self.client_publisher.publish(self.broadcast_topic, payload, qos=1)
        
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
        result = self.client_publisher.publish(topic, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"📨 Sent alert {alert.id} to client {client_id}")
        else:
            logger.error(f"Failed to send alert to client {client_id}")
    
    def start(self):
        """Start the MQTT clients and connect to both brokers."""
        try:
            # Connect to simulator broker (to receive events)
            self.simulator_client.connect(self.simulator_broker, self.simulator_port, keepalive=60)
            self.simulator_client.loop_start()
            
            # Connect to client broker (to publish alerts)
            self.client_publisher.connect(self.client_broker, self.client_port, keepalive=60)
            self.client_publisher.loop_start()
            
            logger.info(f"🚀 Alert Service MQTT Handler started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT brokers: {e}")
            raise
    
    def stop(self):
        """Stop both MQTT clients."""
        self.simulator_client.loop_stop()
        self.simulator_client.disconnect()
        
        self.client_publisher.loop_stop()
        self.client_publisher.disconnect()
        
        logger.info("Alert Service MQTT Handler stopped")