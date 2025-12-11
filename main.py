import os
import time
import signal
import sys
from mqtt_handler import MQTTAlertHandler
from models import EmergencyEvent, Alert
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertService:
    """Main Alert Service application."""
    
    def __init__(self):
        # Get configuration from environment or use defaults
        broker = os.getenv('MQTT_BROKER', 'localhost')
        port = int(os.getenv('MQTT_PORT', 1883))
        simulator_topic = os.getenv('SIMULATOR_TOPIC', 'stadium/events/emergency')
        client_topic_prefix = os.getenv('CLIENT_TOPIC_PREFIX', 'alerts/client')
        
        # Initialize MQTT handler
        self.mqtt_handler = MQTTAlertHandler(
            broker=broker,
            port=port,
            simulator_topic=simulator_topic,
            client_topic_prefix=client_topic_prefix
        )
        
        # Set custom message handler if needed
        self.mqtt_handler.set_message_callback(self.process_emergency_event)
        
        self.running = False
        
    def process_emergency_event(self, event: EmergencyEvent):
        """
        Custom logic to process emergency events from the simulator.
        You can add business logic here (e.g., filtering, validation, enrichment).
        """
        logger.info(f"Processing emergency event: {event.event_type}")
        
        # Create alert from event
        alert = self.mqtt_handler._create_alert_from_event(event)
        
        # Broadcast to all clients
        self.mqtt_handler.broadcast_alert(alert)
        
        # You can also send to specific clients if needed:
        # self.mqtt_handler.send_alert_to_client("client_123", alert)
        
    def start(self):
        """Start the Alert Service."""
        logger.info("=" * 50)
        logger.info("🚨 Starting Alert Service 🚨")
        logger.info("=" * 50)
        
        try:
            self.mqtt_handler.start()
            self.running = True
            
            logger.info("Alert Service is running. Press Ctrl+C to stop.")
            
            # Keep the service running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nShutting down gracefully...")
        except Exception as e:
            logger.error(f"Error in Alert Service: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Alert Service."""
        logger.info("Stopping Alert Service...")
        self.running = False
        self.mqtt_handler.stop()
        logger.info("Alert Service stopped.")
        

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("\nReceived shutdown signal")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the service
    service = AlertService()
    service.start()
