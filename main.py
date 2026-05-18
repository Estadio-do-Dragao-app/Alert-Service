import time
import signal
import sys
from mqtt_handler import MQTTAlertHandler
from schemas import EmergencyEvent
from mqtt_configs import (
    SIMULATOR_BROKER, SIMULATOR_PORT, SIMULATOR_TOPIC,
    CLIENT_BROKER, CLIENT_PORT, CLIENT_TOPIC_PREFIX
)
import logging

# Initialize structured logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertService:
    """
    Orchestrates the Alert Service lifecycle.
    Responsible for initializing MQTT communication and coordinating
    the conversion of raw emergency events into actionable client alerts.
    """
    
    def __init__(self):
        # Initialize the underlying MQTT handler with centralized environment configuration
        self.mqtt_handler = MQTTAlertHandler(
            simulator_broker=SIMULATOR_BROKER,
            simulator_port=SIMULATOR_PORT,
            client_broker=CLIENT_BROKER,
            client_port=CLIENT_PORT,
            simulator_topic=SIMULATOR_TOPIC,
            client_topic_prefix=CLIENT_TOPIC_PREFIX
        )
        
        # Bind the local event processor to the MQTT handler's message reception logic
        self.mqtt_handler.set_message_callback(self.process_emergency_event)
        
        # Operational state flag for the service loop
        self.running = False
        
    def process_emergency_event(self, event: EmergencyEvent):
        """
        Ingests raw emergency events from the source and broadcasts them to clients.
        This serves as the primary hook for additional business logic like 
        event filtering, validation, or metadata enrichment.
        """
        logger.info(f"Processing emergency event: {event.event_type}")
        
        # Transform the normalized event into a specific Alert entity
        alert = self.mqtt_handler.create_alert_from_event(event)
        
        # Distribute the alert via global broadcast
        self.mqtt_handler.broadcast_alert(alert)
        
        # Support for targeted client delivery is available but disabled by default:
        # self.mqtt_handler.send_alert_to_client("client_123", alert)
        
    def start(self):
        """
        Entry point for the service. Established broker connections and 
        enters the primary execution loop.
        """
        logger.info("=" * 50)
        logger.info("Starting Alert Service")
        logger.info("=" * 50)
        
        try:
            self.mqtt_handler.start()
            self.running = True
            
            logger.info("Alert Service is operational. Press Ctrl+C for graceful shutdown.")
            
            # Maintain service residency until interrupted
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user. Initiating shutdown procedure...")
        except Exception as e:
            logger.exception("Critical error in Alert Service runtime")
        finally:
            self.stop()
    
    def stop(self):
        """
        Terminates operational state and cleans up MQTT connections.
        """
        logger.info("Stopping Alert Service...")
        self.running = False
        self.mqtt_handler.stop()
        logger.info("Alert Service terminated successfully.")
        

def signal_handler(sig, frame):
    """Bridge for system signals to ensure clean resource release."""
    logger.info("\nReceived system termination signal")
    sys.exit(0)


if __name__ == "__main__":
    # Configure OS-level signal handling for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Instantiate and launch the service controller
    service = AlertService()
    service.start()
