import pytest
from datetime import datetime
from models import (
    EmergencyEvent, Alert, ClientAlert, AlertType,
    Boundary, Pos, Entity, EntityType, Node, Tile
)

class TestModels:
    """Test Pydantic models."""
    
    def test_emergency_event_creation(self):
        """Test EmergencyEvent creation with all fields."""
        event = EmergencyEvent(
            event_id="fire-001",
            event_type="FIRE",
            timestamp=datetime.now(),
            severity="HIGH",
            metadata={"description": "Fire detected", "location": "Gate 1"}
        )
        
        assert event.event_id == "fire-001"
        assert event.event_type == "FIRE"
        assert event.severity == "HIGH"
        assert "Fire detected" in event.get_details()["description"]
    
    def test_emergency_event_without_metadata(self):
        """Test EmergencyEvent with details instead of metadata."""
        event = EmergencyEvent(
            event_id="security-001",
            event_type="SECURITY",
            timestamp=datetime.now(),
            severity="MEDIUM",
            details={"description": "Security breach"}
        )
        
        assert event.event_id == "security-001"
        assert event.event_type == "SECURITY"
        assert event.severity == "MEDIUM"
        assert "Security breach" in event.get_details()["description"]
    
    def test_alert_creation(self):
        """Test Alert creation."""
        alert = Alert(
            id=1,
            type=AlertType.FIRE,
            disabled_tiles=[101, 102, 103],
            message="Fire detected in sector A",
            timestamp=datetime.now(),
            severity="HIGH"
        )
        
        assert alert.id == 1
        assert alert.type == AlertType.FIRE
        assert alert.disabled_tiles == [101, 102, 103]
        assert "Fire detected" in alert.message
        assert alert.severity == "HIGH"
    
    def test_client_alert_creation(self):
        """Test ClientAlert creation."""
        timestamp = datetime.now().isoformat()
        client_alert = ClientAlert(
            alert_id=1,
            alert_type="FIRE",
            message="Fire alert",
            timestamp=timestamp,
            severity="HIGH",
            affected_areas=[101, 102]
        )
        
        assert client_alert.alert_id == 1
        assert client_alert.alert_type == "FIRE"
        assert client_alert.message == "Fire alert"
        assert client_alert.timestamp == timestamp
        assert client_alert.severity == "HIGH"
        assert client_alert.affected_areas == [101, 102]
    
    def test_entity_models(self):
        """Test Entity, Node, and other basic models."""
        # Test Pos
        pos = Pos(x=100, y=200)
        assert pos.x == 100
        assert pos.y == 200
        
        # Test Boundary
        boundary = Boundary(x_bound=(0, 100), y_bound=(0, 200))
        assert boundary.x_bound == (0, 100)
        assert boundary.y_bound == (0, 200)
        
        # Test Entity
        entity = Entity(
            id=1,
            type=EntityType.NODE,
            pos=Pos(x=50, y=50)
        )
        assert entity.id == 1
        assert entity.type == EntityType.NODE
        assert entity.pos.x == 50
        
        # Test Node (inherits from Entity)
        node = Node(
            id=1,
            type=EntityType.NODE,
            pos=Pos(x=100, y=100)
        )
        assert isinstance(node, Entity)
        assert node.type == EntityType.NODE
    
    def test_tile_model(self):
        """Test Tile model."""
        tile = Tile(
            id=1,
            level=0,
            grid_pos=Pos(x=10, y=10),
            boundary=Boundary(x_bound=(0, 5), y_bound=(0, 5)),
            walkable=True,
            entities=[]
        )
        
        assert tile.id == 1
        assert tile.level == 0
        assert tile.grid_pos.x == 10
        assert tile.walkable is True
        assert tile.entities == []
    
    def test_alert_type_enum(self):
        """Test AlertType enum values."""
        assert AlertType.FIRE.value == "FIRE"
        assert AlertType.SECURITY.value == "SECURITY"
        assert AlertType.MEDICAL.value == "MEDICAL"
        assert AlertType.EVACUATION.value == "EVACUATION"
        
        # Test string conversion
        assert str(AlertType.FIRE) == "AlertType.FIRE"