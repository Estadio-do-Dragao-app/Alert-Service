# Alert Service

A real-time alert service for smart stadiums that receives emergency events from a stadium simulator via MQTT and broadcasts alerts to connected clients.

## 🏗️ Architecture

```
Stadium Simulator → [MQTT] → Alert Service → [MQTT] → Clients
                    (Mosquitto Broker)
```

The service:
1. **Receives** emergency events from a stadium simulator on `stadium/events/emergency`
2. **Processes** events and converts them to alerts
3. **Broadcasts** alerts to all clients on `alerts/broadcast`
4. **Sends** targeted alerts to specific clients on `alerts/client/{client_id}`

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start the service with Mosquitto broker
docker-compose up -d

# View logs
docker-compose logs -f alert-service

# Stop the service
docker-compose down
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Mosquitto broker (in separate terminal)
docker run -p 1883:1883 -p 9001:9001 eclipse-mosquitto:2.0

# Run the service
python main.py
```

## 📡 MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `stadium/events/emergency` | Simulator → Service | Emergency events from stadium |
| `alerts/broadcast` | Service → All Clients | Broadcast alerts to everyone |
| `alerts/client/{client_id}` | Service → Specific Client | Targeted alerts |

## 🧪 Testing

### 1. Start the Alert Service
```bash
python main.py
```

### 2. Run Test Client (in another terminal)
```bash
python example_client.py client_123
```

### 3. Simulate Emergency Events (in another terminal)
```bash
python test_simulator.py
```

You should see:
- Simulator publishing events
- Alert Service processing and broadcasting
- Client receiving alerts

## 📦 Project Structure

```
Alert-Service/
├── models.py              # Pydantic models for events and alerts
├── mqtt_handler.py        # MQTT connection and message handling
├── main.py                # Main service application
├── example_client.py      # Example client subscriber
├── test_simulator.py      # Test event generator
├── docker-compose.yml     # Docker composition
├── Dockerfile             # Service container
├── requirements.txt       # Python dependencies
└── mosquitto/
    └── config/
        └── mosquitto.conf # Mosquitto broker configuration
```

## 🔧 Configuration

Environment variables (see `.env.example`):

```bash
MQTT_BROKER=localhost      # MQTT broker address
MQTT_PORT=1883            # MQTT broker port
SIMULATOR_TOPIC=stadium/events/emergency
CLIENT_TOPIC_PREFIX=alerts/client
```

## 📋 Alert Types

- **FIRE**: Fire-related emergencies
- **SECURITY**: Security incidents
- **MEDICAL**: Medical emergencies
- **EVACUATION**: Evacuation orders

## 🔌 Client Integration

Clients should:
1. Connect to the MQTT broker (default: `localhost:1883`)
2. Subscribe to `alerts/broadcast` for all alerts
3. Subscribe to `alerts/client/{their_id}` for targeted alerts

Example:
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883)
client.subscribe("alerts/broadcast")
client.subscribe("alerts/client/my_client_id")
client.loop_forever()
```

## 📝 Event Format

**Incoming Event** (from simulator):
```json
{
  "event_id": "evt_1234567890",
  "event_type": "FIRE",
  "timestamp": "2025-12-09T10:30:00",
  "location": {"section": "B", "level": 2},
  "severity": "HIGH",
  "details": {
    "description": "Fire detected in section B",
    "disabled_tiles": [101, 102, 103]
  }
}
```

**Outgoing Alert** (to clients):
```json
{
  "alert_id": 1,
  "alert_type": "FIRE",
  "message": "FIRE: Fire detected in section B",
  "timestamp": "2025-12-09T10:30:00",
  "severity": "HIGH",
  "affected_areas": [101, 102, 103]
}
```

## 🛠️ Development

### Adding Custom Logic

Modify `process_emergency_event()` in `main.py`:

```python
def process_emergency_event(self, event: EmergencyEvent):
    # Add your custom processing here
    logger.info(f"Processing: {event.event_type}")
    
    # Create alert
    alert = self.mqtt_handler._create_alert_from_event(event)
    
    # Broadcast or send to specific clients
    self.mqtt_handler.broadcast_alert(alert)
```

## 🐛 Troubleshooting

**Cannot connect to MQTT broker:**
- Check if Mosquitto is running: `docker ps`
- Verify port 1883 is not in use: `netstat -an | findstr 1883`

**Not receiving alerts:**
- Verify subscription topics match
- Check broker logs: `docker logs mosquitto-broker`

## 📄 License

MIT
