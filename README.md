# Alert Service

A real-time alert service for smart stadiums that receives emergency events from the Stadium-Event-Generator via MQTT and broadcasts alerts to connected clients through its own MQTT broker.

## 🏗️ Architecture

```
Stadium-Event-Generator → [MQTT Port 1883] → Alert Service
                                                    ↓
                                           [MQTT Port 1884]
                                                    ↓
                                                Clients
```

The service:
1. **Receives** emergency events from Stadium-Event-Generator broker (port 1883) on `stadium/events/emergency`
2. **Processes** events and converts them to alerts
3. **Broadcasts** alerts to clients via its own broker (port 1884) on `alerts/broadcast`
4. **Sends** targeted alerts to specific clients on `alerts/client/{client_id}`

## 🚀 Quick Start

### Prerequisites
- Stadium-Event-Generator must be running (provides MQTT broker on port 1883)
- Docker and Docker Compose installed

### Option 1: Docker Compose (Recommended)

```bash
# Start the Stadium-Event-Generator first (if not already running)
cd ../Stadium-Event-Generator
docker-compose up -d

# Start Alert-Service with its own Mosquitto broker
cd ../Alert-Service
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

# Ensure Stadium-Event-Generator broker is running on port 1883

# Start Alert-Service's own Mosquitto broker (in separate terminal)
docker run -p 1884:1883 -p 9002:9001 eclipse-mosquitto:2.0

# Run the service
python main.py
```

## 📡 MQTT Brokers & Topics

### Simulator Broker (Port 1883 - Stadium-Event-Generator)
| Topic | Direction | Description |
|-------|-----------|-------------|
| `stadium/events/emergency` | Simulator → Alert Service | Emergency events from stadium |

### Client Broker (Port 1884 - Alert Service)
| Topic | Direction | Description |
|-------|-----------|-------------|
| `alerts/broadcast` | Alert Service → All Clients | Broadcast alerts to everyone |
| `alerts/client/{client_id}` | Alert Service → Specific Client | Targeted alerts |

### WebSocket Ports
- Client connections: `ws://localhost:9002`
- Simulator broker: `ws://localhost:9001`

## 🧪 Testing

### 1. Start the Alert Service
## 🧪 Testing

### 1. Start Stadium-Event-Generator
```bash
cd ../Stadium-Event-Generator
docker-compose up -d
```

### 2. Start Alert Service
```bash
cd ../Alert-Service
docker-compose up -d
```

### 3. Run Test Client (in another terminal)
```bash
# Client connects to Alert-Service broker on port 1884
python example_client.py client_123
```

### 4. Simulate Emergency Events
The Stadium-Event-Generator will publish events automatically. You can also use the test simulator:
```bash
python test_simulator.py
```

You should see:
- Stadium-Event-Generator publishing events on port 1883
- Alert Service receiving from port 1883 and publishing to port 1884
- Client receiving alerts from port 1884

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
