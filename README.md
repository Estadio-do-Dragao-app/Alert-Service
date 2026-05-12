# Alert Service

A real-time alert service designed for smart environments and simulated event sources. It ingests emergency telemetry from an event source via MQTT, transforms the raw data into normalized alerts, and broadcasts them to connected clients.

## 🏗️ Architecture

```
Event Source → [MQTT Port 1883] → Alert Service
                                      ↓
                             [MQTT Port 1884]
                                      ↓
                                  Clients
```

The service operates as a bridge:
1. **Ingests** raw emergency events from the source broker (port 1883) on `alerts/events`.
2. **Normalizes** and transforms events into structured alert models.
3. **Broadcasts** prioritized alerts to all clients via the distribution broker (port 1884) on `alerts/broadcast`.
4. **Dispatches** targeted alerts to specific client identifiers on `alerts/client/{client_id}`.

## 🚀 Quick Start

### Prerequisites
- An MQTT broker must be reachable on port 1883 (for event source ingress).
- Docker and Docker Compose installed for containerized deployment.

### Option 1: Docker Compose (Recommended)

```bash
# Start the Alert Service with its dedicated Mosquitto broker
docker-compose up -d

# Monitor service logs
docker-compose logs -f alert-service
```

### Option 2: Local Development

```bash
# Install environment dependencies
pip install -r requirements.txt

# Start the distribution broker (if not using Docker Compose)
docker run -p 1884:1883 -p 9002:9001 eclipse-mosquitto:2.0

# Launch the service
python main.py
```

## 📡 MQTT Interface

### Source Ingress (Port 1883)
| Topic | Direction | Description |
|-------|-----------|-------------|
| `alerts/events` | Source → Alert Service | Raw emergency telemetry data |

### Client Egress (Port 1884)
| Topic | Direction | Description |
|-------|-----------|-------------|
| `alerts/broadcast` | Alert Service → All Clients | Global alert distribution |
| `alerts/client/{client_id}` | Alert Service → Target Client | Individual notifications |

## 🧪 Testing and Simulation

### Manual Event Simulation
You can trigger alerts manually by publishing a JSON payload to the `alerts/events` topic on the source broker.

**Payload Format:**
```json
{
  "event_id": "manual_001",
  "event_type": "FIRE",
  "severity": "high",
  "location": "Sector B, Level 1",
  "timestamp": "2026-05-11T14:30:00",
  "details": {
    "description": "Manual fire test",
    "affected_areas": ["Zone_1", "Zone_2"]
  },
  "level": "high"
}
```

## 📦 Project Structure

```
Alert-Service/
├── schemas.py             # Pydantic models for events and alerts
├── mqtt_handler.py        # MQTT lifecycle and transformation logic
├── main.py                # Service orchestration and entry point
├── mqtt_configs.py        # Centralized environment configuration
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
└── mosquitto/
    └── config/
        └── mosquitto.conf # Broker persistence and security settings
```

## 🔧 Configuration

The service is configured via environment variables. See `.env.example` for details.

```bash
MQTT_BROKER=localhost      # Distribution broker address
MQTT_PORT=1884            # Distribution broker port
SIMULATOR_TOPIC=alerts/events
CLIENT_TOPIC_PREFIX=alerts/client
```

## 📝 Data Models

### Outgoing Alert (to clients)
```json
{
  "alert_id": 1,
  "alert_type": "FIRE",
  "message": "FIRE: Manual fire test",
  "timestamp": "2026-05-11T14:30:00Z",
  "severity": "high",
  "affected_areas": ["Zone_1", "Zone_2"],
  "level": "high",
  "priority": "HIGH",
  "expiry_time": "2026-05-11T15:30:00Z"
}
```

## 🛠️ Customization

### Extending Transformation Logic
To add custom business rules, modify the `process_emergency_event()` hook in `main.py`:

```python
def process_emergency_event(self, event: EmergencyEvent):
    # Apply custom filtering or enrichment
    logger.info(f"Processing event type: {event.event_type}")
    
    # Generate the normalized alert
    alert = self.mqtt_handler.create_alert_from_event(event)
    
    # Distribute via chosen channel
    self.mqtt_handler.broadcast_alert(alert)
```

## 📄 License
MIT
