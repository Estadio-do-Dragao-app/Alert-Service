import os

# --- Broker Connection Settings ---
# Configuration for the environment source (where emergency events originate)
SIMULATOR_BROKER = os.getenv('SIMULATOR_BROKER', 'localhost')
SIMULATOR_PORT = int(os.getenv('SIMULATOR_PORT', 1883))
SIMULATOR_TOPIC = os.getenv('SIMULATOR_TOPIC', 'alerts/events')

# Configuration for the client-facing broker (where processed alerts are published)
CLIENT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
CLIENT_PORT = int(os.getenv('MQTT_PORT', 1884))
CLIENT_TOPIC_PREFIX = os.getenv('CLIENT_TOPIC_PREFIX', 'alerts/client')

# --- Protocol & Policy Settings ---
# MQTT communication parameters and message retention policies
BROADCAST_TOPIC = os.getenv('BROADCAST_TOPIC', 'alerts/broadcast')
ACK_TOPIC = os.getenv('ACK_TOPIC', 'alerts/ack/#')
# Extract prefix from ACK_TOPIC (removes wildcard suffix for topic matching)
ACK_TOPIC_PREFIX = ACK_TOPIC.rstrip('/#') + '/'
DEFAULT_QOS = int(os.getenv('DEFAULT_QOS', 2))
DEFAULT_EXPIRY_HOURS = int(os.getenv('DEFAULT_EXPIRY_HOURS', 1))

# --- TLS / Authentication ---
MQTT_USER = os.getenv('MQTT_USER', 'services')
MQTT_PASS = os.getenv('MQTT_PASS', 'dragao_mqtt_2026')
MQTT_CA_CERT = os.getenv('MQTT_CA_CERT', '')  # e.g. /certs/ca.crt