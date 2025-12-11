"""
Test simulator to send emergency events to the Alert Service.
This simulates the stadium event generator.
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import random


def publish_emergency_event(client, event_type, severity, details):
    """Publish an emergency event to the simulator topic."""
    
    event = {
        "event_id": f"evt_{int(time.time())}",
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "location": {
            "section": random.choice(["A", "B", "C", "D"]),
            "level": random.randint(1, 3)
        },
        "severity": severity,
        "details": details
    }
    
    topic = "stadium/events/emergency"
    payload = json.dumps(event)
    
    result = client.publish(topic, payload, qos=1)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✓ Published {event_type} event")
        print(f"  Event ID: {event['event_id']}")
        print(f"  Severity: {severity}")
        print(f"  Details: {details.get('description', 'N/A')}\n")
    else:
        print(f"✗ Failed to publish event")


def main():
    broker = "localhost"
    port = 1883
    
    client = mqtt.Client(client_id="stadium_simulator")
    
    print(f"🔌 Connecting to MQTT broker at {broker}:{port}")
    
    try:
        client.connect(broker, port, 60)
        client.loop_start()
        
        print("✓ Connected successfully")
        print("📡 Simulating emergency events...\n")
        
        # Simulate different types of emergencies
        events = [
            {
                "type": "FIRE",
                "severity": "HIGH",
                "details": {
                    "description": "Fire detected in section B",
                    "disabled_tiles": [101, 102, 103, 201, 202]
                }
            },
            {
                "type": "SECURITY",
                "severity": "MEDIUM",
                "details": {
                    "description": "Security incident near gate 4",
                    "disabled_tiles": [405, 406]
                }
            },
            {
                "type": "MEDICAL",
                "severity": "HIGH",
                "details": {
                    "description": "Medical emergency in section C",
                    "disabled_tiles": [301]
                }
            },
            {
                "type": "EVACUATION",
                "severity": "CRITICAL",
                "details": {
                    "description": "Evacuation required - all sections",
                    "disabled_tiles": list(range(100, 500))
                }
            }
        ]
        
        for i, event in enumerate(events, 1):
            print(f"[Event {i}/{len(events)}]")
            publish_emergency_event(
                client,
                event["type"],
                event["severity"],
                event["details"]
            )
            time.sleep(3)  # Wait 3 seconds between events
        
        print("✓ All test events published")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n\n👋 Stopping simulator...")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
