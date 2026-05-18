import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional
from schemas import EmergencyEvent, Alert, ClientAlert, AlertType
from mqtt_configs import (
    DEFAULT_QOS, BROADCAST_TOPIC, ACK_TOPIC, ACK_TOPIC_PREFIX, DEFAULT_EXPIRY_HOURS
)

logger = logging.getLogger(__name__)


class MQTTAlertHandler:
    """
    Manages MQTT-based bidirectional communication for the Alert Service.
    - Ingests telemetry/events from an external event source via a dedicated broker.
    - Dispatches transformed alerts to end-user clients through a separate publishing broker.
    """
    
    def __init__(self, 
                 simulator_broker: str, simulator_port: int,
                 client_broker: str, client_port: int,
                 simulator_topic: str = "alerts/events",
                 client_topic_prefix: str = "alerts/client"):
        # Connection parameters for the source of emergency events
        self.simulator_broker = simulator_broker
        self.simulator_port = simulator_port
        self.simulator_topic = simulator_topic
        
        # Connection parameters for the client notification distribution system
        self.client_broker = client_broker
        self.client_port = client_port
        self.client_topic_prefix = client_topic_prefix
        self.broadcast_topic = BROADCAST_TOPIC
        
        # Isolated MQTT clients to manage distinct broker lifecycles independently
        self.simulator_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="alert_service_receiver")
        self.simulator_client.on_connect = self._on_simulator_connect
        self.simulator_client.on_message = self._on_message
        self.simulator_client.on_disconnect = self._on_simulator_disconnect

        self.client_publisher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="alert_service_publisher")
        self.client_publisher.on_connect = self._on_client_connect
        self.client_publisher.on_disconnect = self._on_client_disconnect
        self.client_publisher.on_message = self._on_client_message
        
        # Internal state for alert indexing and external event processing
        self.alert_id_counter = 0
        self.message_callback: Optional[Callable] = None
        
    def set_message_callback(self, callback: Callable[[EmergencyEvent], None]):
        """Registers a callback for processing newly ingested events."""
        self.message_callback = callback
    
    def _on_simulator_connect(self, client, userdata, flags, rc):
        """Lifecycle hook: triggered on connection to the event source broker."""
        if rc == 0:
            logger.info(f"[SOURCE] Successfully connected to broker at {self.simulator_broker}:{self.simulator_port}")
            client.subscribe(self.simulator_topic)
            logger.info(f"[SOURCE] Subscribed to event ingress topic: {self.simulator_topic}")
        else:
            logger.error(f"[SOURCE] Connection failure. Return code: {rc}")
    
    def _on_client_connect(self, client, userdata, flags, rc):
        """Lifecycle hook: triggered on connection to the client distribution broker."""
        if rc == 0:
            logger.info(f"[CLIENT] Successfully connected to broker at {self.client_broker}:{self.client_port}")
            client.subscribe(ACK_TOPIC, qos=DEFAULT_QOS)
            logger.info(f"[CLIENT] Subscribed to acknowledgment monitoring topic: {ACK_TOPIC}")
        else:
            logger.error(f"[CLIENT] Connection failure. Return code: {rc}")

    def _on_client_message(self, client, userdata, msg):
        """Asynchronous handler for incoming client acknowledgments (ACKs)."""
        try:
            if msg.topic.startswith(ACK_TOPIC_PREFIX):
                client_id = msg.topic.split("/")[-1]
                payload = json.loads(msg.payload.decode())
                if not isinstance(payload, dict):
                    logger.warning(f"[ACK] Malformed ACK payload from client {client_id}: expected JSON object")
                    return
                alert_id = payload.get("alert_id")
                if alert_id is None:
                    logger.warning(f"[ACK] Malformed ACK from client {client_id}: missing alert_id field")
                    return
                logger.info(f"[ACK] Acknowledgment confirmed for alert {alert_id} from client {client_id}")
        except Exception as e:
            logger.error(f"[ACK] Logic error during acknowledgment processing: {e}")
    
    def _on_simulator_disconnect(self, client, userdata, rc):
        """Lifecycle hook: triggered on disconnection from the event source broker."""
        if rc != 0:
            logger.warning(f"[SOURCE] Unexpected disconnection detected. Connection return code: {rc}")
    
    def _on_client_disconnect(self, client, userdata, rc):
        """Lifecycle hook: triggered on disconnection from the client distribution broker."""
        if rc != 0:
            logger.warning(f"[CLIENT] Unexpected disconnection detected. Connection return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Core ingress handler: parses raw MQTT payloads into normalized event models."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"[SOURCE] Ingested emergency event: {payload.get('event_type', 'UNKNOWN')}")
            
            # Map raw dictionary to Pydantic model for validation and type safety
            event = EmergencyEvent(**payload)
            
            if self.message_callback:
                self.message_callback(event)
            else:
                # Fallback to automated transformation and broadcast if no callback is registered
                alert = self.create_alert_from_event(event)
                self.broadcast_alert(alert)
                
        except json.JSONDecodeError as e:
            logger.error(f"[INGRESS] Failed to decode JSON payload: {e}")
        except Exception as e:
            logger.error(f"[INGRESS] Transformation error during message processing: {e}")
    
    def create_alert_from_event(self, event: EmergencyEvent) -> Alert:
        """Transforms a normalized emergency event into an actionable Alert object."""
        self.alert_id_counter += 1
        
        # Static mapping for standard event types to alert classifications
        alert_type_map = {
            "FIRE": AlertType.FIRE,
            "FIRE_ALERT": AlertType.FIRE,  # Legacy support for specific source formats
            "SECURITY": AlertType.SECURITY,
            "MEDICAL": AlertType.MEDICAL,
            "EVACUATION": AlertType.EVACUATION
        }
        
        alert_type = alert_type_map.get(event.event_type.upper(), AlertType.SECURITY)
        details = event.get_details()
        
        # Normalize area identifiers from source-specific fields
        areas = details.get("affected_areas", details.get("disabled_tiles", []))
        
        return Alert(
            id=self.alert_id_counter,
            type=alert_type,
            disabled_tiles=areas,
            message=f"{event.event_type}: {details.get('description', 'Emergency detected')}",
            timestamp=event.timestamp,
            severity=event.severity,
            level=event.level or event.severity or "medium"
        )
    
    def _get_priority_from_severity(self, severity: str) -> str:
        """Maps qualitative severity strings to quantitative MQTT priority levels."""
        severity_lower = severity.lower() if severity else "medium"
        priority_map = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW"
        }
        return priority_map.get(severity_lower, "MEDIUM")
    
    def _prepare_client_alert(self, alert: Alert) -> ClientAlert:
        """Centralized factory for constructing formatted ClientAlert payloads."""
        priority = self._get_priority_from_severity(alert.severity)
        expiry_time = (alert.timestamp + timedelta(hours=DEFAULT_EXPIRY_HOURS)).isoformat()
        
        return ClientAlert(
            alert_id=alert.id,
            alert_type=alert.type.value,
            message=alert.message,
            timestamp=alert.timestamp.isoformat(),
            severity=alert.severity,
            affected_areas=alert.disabled_tiles,
            level=alert.level,
            priority=priority,
            expiry_time=expiry_time
        )
    
    def broadcast_alert(self, alert: Alert):
        """Encapsulates global distribution of an alert via the broadcast topic."""
        client_alert = self._prepare_client_alert(alert)
        payload = client_alert.model_dump_json()
        result = self.client_publisher.publish(self.broadcast_topic, payload, qos=DEFAULT_QOS)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"[EGRESS] Broadcasted alert {alert.id} to topic {self.broadcast_topic} (Priority: {client_alert.priority})")
        else:
            logger.error(f"[EGRESS] Failed to publish broadcast for alert {alert.id}")
    
    def send_alert_to_client(self, client_id: str, alert: Alert):
        """Directs an alert to a specific client-bound topic."""
        client_alert = self._prepare_client_alert(alert)
        topic = f"{self.client_topic_prefix}/{client_id}"
        payload = client_alert.model_dump_json()
        result = self.client_publisher.publish(topic, payload, qos=DEFAULT_QOS)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"[EGRESS] Dispatched alert {alert.id} to client topic {topic} (Priority: {client_alert.priority})")
        else:
            logger.error(f"[EGRESS] Failed to dispatch alert to client {client_id}")
    
    def start(self):
        """Initiates async MQTT client loops and establishes broker connections."""
        try:
            # Source broker connection lifecycle
            self.simulator_client.connect(self.simulator_broker, self.simulator_port, keepalive=60)
            self.simulator_client.loop_start()
            
            # Distribution broker connection lifecycle
            self.client_publisher.connect(self.client_broker, self.client_port, keepalive=60)
            self.client_publisher.loop_start()
            
            logger.info("MQTT Handler operational: Ingress and Egress loops established")
        except Exception as e:
            logger.error(f"Critical initialization failure for MQTT clients: {e}")
            raise
    
    def stop(self):
        """Ensures graceful termination of MQTT client loops and connections."""
        self.simulator_client.loop_stop()
        self.simulator_client.disconnect()
        
        self.client_publisher.loop_stop()
        self.client_publisher.disconnect()
        
        logger.info("MQTT Handler operational loops terminated")