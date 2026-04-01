"""Location 实体"""
from dataclasses import dataclass


@dataclass
class Location:
    """地点实体"""
    id: str
    name: str
    description: str
    location_type: str  # "city", "building", "natural", "other"

    def __post_init__(self):
        """验证实体"""
        if not self.id or not self.id.strip():
            raise ValueError("Location id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Location name cannot be empty")
