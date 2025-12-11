"""
Simple client example to subscribe to alerts from the Alert Service.
This demonstrates how clients should connect to receive emergency alerts.
"""

import paho.mqtt.client as mqtt
import json
import sys


def on_connect(client, userdata, flags, rc):
    """Handle connection to MQTT broker."""
    if rc == 0:
        print("✓ Connected to MQTT broker")
        
        # Subscribe to broadcast alerts (all clients receive these)
        client.subscribe("alerts/broadcast")
        print("✓ Subscribed to: alerts/broadcast")
        
        # Optionally subscribe to client-specific topic
        # Replace 'client_123' with your actual client ID
        client_id = userdata.get('client_id', 'client_123')
        client.subscribe(f"alerts/client/{client_id}")
        print(f"✓ Subscribed to: alerts/client/{client_id}")
    else:
        print(f"✗ Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Handle incoming alert messages."""
    try:
        alert = json.loads(msg.payload.decode())
        
        print("\n" + "=" * 60)
        print(f"🚨 ALERT RECEIVED on {msg.topic}")
        print("=" * 60)
        print(f"Alert ID:       {alert.get('alert_id')}")
        print(f"Type:           {alert.get('alert_type')}")
        print(f"Severity:       {alert.get('severity')}")
        print(f"Message:        {alert.get('message')}")
        print(f"Timestamp:      {alert.get('timestamp')}")
        print(f"Affected Areas: {alert.get('affected_areas')}")
        print("=" * 60 + "\n")
        
    except json.JSONDecodeError as e:
        print(f"✗ Failed to decode alert: {e}")
    except Exception as e:
        print(f"✗ Error processing alert: {e}")


def main():
    # Configuration
    broker = "localhost"  # Change to your broker address
    port = 1883
    client_id = sys.argv[1] if len(sys.argv) > 1 else "client_123"
    
    # Create MQTT client
    client = mqtt.Client(client_id=f"alert_client_{client_id}")
    client.user_data_set({'client_id': client_id})
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"🔌 Connecting to MQTT broker at {broker}:{port}")
    print(f"👤 Client ID: {client_id}")
    
    try:
        client.connect(broker, port, 60)
        print("📡 Listening for alerts... (Press Ctrl+C to stop)\n")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Disconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
