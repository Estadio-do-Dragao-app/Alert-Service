# Client broker configuration (for publishing alerts to clients)
CLIENT_BROKER = "localhost"
CLIENT_PORT = 1884
CLIENT_TOPIC = "stadium/services/alerts"

# Simulator broker configuration (for receiving events from stadium simulator)
SIMULATOR_BROKER = "localhost"
SIMULATOR_PORT = 1883
SIMULATOR_TOPIC = "stadium/events/alerts"