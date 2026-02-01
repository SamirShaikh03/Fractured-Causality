"""
Universe - A single parallel universe container.

Each universe holds its own entities, tilemap, and local state.
The player can switch between universes, carrying their position.
"""

import pygame
from enum import Enum
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

from ..core.settings import (
    TILE_SIZE, UNIVERSE_COLORS, UNIVERSE_BG_COLORS,
    UNIVERSE_PRIME, UNIVERSE_ECHO, UNIVERSE_FRACTURE
)

if TYPE_CHECKING:
    from ..entities.entity import Entity


class UniverseType(Enum):
    """Types of universes in the game."""
    PRIME = UNIVERSE_PRIME      # The original, stable timeline
    ECHO = UNIVERSE_ECHO        # A divergent timeline
    FRACTURE = UNIVERSE_FRACTURE  # An unstable, "impossible" timeline


class TileType(Enum):
    """Types of tiles in the tilemap."""
    FLOOR = "floor"     # Walkable floor tile
    WALL = "wall"       # Solid, blocking wall
    PIT = "pit"         # Deadly pit (instant death)
    HAZARD = "hazard"   # Damaging hazard area


@dataclass
class TileData:
    """Data for a single tile in the tilemap."""
    solid: bool = False
    tile_type: str = "floor"
    variant: int = 0


class TileMap:
    """
    Grid-based tilemap for a universe.
    
    Handles the static geometry of a level within a single universe.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the tilemap.
        
        Args:
            width: Width in tiles
            height: Height in tiles
        """
        self.width = width
        self.height = height
        self.tiles: List[List[TileData]] = [
            [TileData() for _ in range(width)]
            for _ in range(height)
        ]
    
    def get_tile(self, x: int, y: int) -> Optional[TileData]:
        """Get tile data at grid position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def set_tile(self, x: int, y: int, tile_data: TileData) -> None:
        """Set tile data at grid position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_data
    
    def is_solid(self, x: int, y: int) -> bool:
        """Check if a tile is solid (blocks movement)."""
        tile = self.get_tile(x, y)
        if tile is None:
            return True  # Out of bounds is solid
        return tile.solid
    
    def is_solid_pixel(self, px: int, py: int) -> bool:
        """Check if a pixel position is in a solid tile."""
        grid_x = int(px // TILE_SIZE)
        grid_y = int(py // TILE_SIZE)
        return self.is_solid(grid_x, grid_y)
    
    def get_tile_rect(self, x: int, y: int) -> pygame.Rect:
        """Get the pixel rectangle for a tile."""
        return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)


class Universe:
    """
    A single parallel universe.
    
    Each universe contains:
    - A tilemap defining the level geometry
    - A list of entities (objects, enemies, etc.)
    - Universe-specific state and properties
    
    The player exists across all universes but is only
    visible/active in one at a time.
    """
    
    def __init__(self, universe_type: UniverseType, width: int = 20, height: int = 11):
        """
        Initialize a universe.
        
        Args:
            universe_type: The type of this universe
            width: Width in tiles
            height: Height in tiles
        """
        self.universe_type = universe_type
        self.tilemap = TileMap(width, height)
        self.entities: List['Entity'] = []
        self.entity_map: Dict[str, 'Entity'] = {}
        
        # Visual properties
        self.color = UNIVERSE_COLORS.get(universe_type.value, (128, 128, 128))
        self.bg_color = UNIVERSE_BG_COLORS.get(universe_type.value, (30, 30, 30))
        
        # State
        self.is_active = False
        self.time_scale = 1.0  # For slow-motion effects
        
        # Stability (affected by paradox)
        self.stability = 1.0  # 0.0 = completely unstable
    
    @property
    def width(self) -> int:
        """Get the width in tiles."""
        return self.tilemap.width
    
    @property
    def height(self) -> int:
        """Get the height in tiles."""
        return self.tilemap.height
    
    @property
    def name(self) -> str:
        """Get the display name of this universe."""
        names = {
            UniverseType.PRIME: "Prime",
            UniverseType.ECHO: "Echo",
            UniverseType.FRACTURE: "Fracture"
        }
        return names.get(self.universe_type, "Unknown")
    
    def add_entity(self, entity: 'Entity') -> None:
        """
        Add an entity to this universe.
        
        Args:
            entity: The entity to add
        """
        if entity not in self.entities:
            self.entities.append(entity)
            self.entity_map[entity.entity_id] = entity
            entity.universe = self
    
    def remove_entity(self, entity: 'Entity') -> None:
        """
        Remove an entity from this universe.
        
        Args:
            entity: The entity to remove
        """
        if entity in self.entities:
            self.entities.remove(entity)
        if entity.entity_id in self.entity_map:
            del self.entity_map[entity.entity_id]
    
    def clear_entities(self) -> None:
        """
        Remove all entities from this universe.
        
        Called when loading a new level.
        """
        self.entities.clear()
        self.entity_map.clear()
    
    def get_entity(self, entity_id: str) -> Optional['Entity']:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to find
            
        Returns:
            The entity, or None if not found
        """
        return self.entity_map.get(entity_id)
    
    def get_entities_at(self, position: Tuple[float, float], radius: float = 0) -> List['Entity']:
        """
        Get all entities at or near a position.
        
        Args:
            position: The (x, y) position to check
            radius: Optional radius for proximity check
            
        Returns:
            List of entities at/near the position
        """
        result = []
        px, py = position
        
        for entity in self.entities:
            if not entity.exists:
                continue
                
            ex, ey = entity.position
            distance = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
            
            # Check if within entity bounds or radius
            if radius > 0:
                if distance <= radius + max(entity.size[0], entity.size[1]) / 2:
                    result.append(entity)
            else:
                rect = entity.get_rect()
                if rect.collidepoint(px, py):
                    result.append(entity)
        
        return result
    
    def get_entities_of_type(self, entity_type: type) -> List['Entity']:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: The class type to filter by
            
        Returns:
            List of matching entities
        """
        return [e for e in self.entities if isinstance(e, entity_type) and e.exists]
    
    def update(self, dt: float) -> None:
        """
        Update all entities in this universe.
        
        Args:
            dt: Delta time in seconds
        """
        if not self.is_active:
            return
            
        adjusted_dt = dt * self.time_scale
        
        for entity in self.entities:
            if entity.exists:
                entity.update(adjusted_dt)
    
    def render(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Render the universe.
        
        Args:
            surface: Surface to render to
            camera_offset: Camera offset (x, y)
        """
        ox, oy = camera_offset
        
        # Render tilemap
        self._render_tilemap(surface, camera_offset)
        
        # Render entities (sorted by y for depth)
        sorted_entities = sorted(
            [e for e in self.entities if e.exists],
            key=lambda e: e.position[1]
        )
        
        for entity in sorted_entities:
            entity.render(surface, camera_offset)
    
    def _render_tilemap(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Render the tilemap."""
        ox, oy = camera_offset
        
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.width):
                tile = self.tilemap.get_tile(x, y)
                rect = pygame.Rect(
                    x * TILE_SIZE - ox,
                    y * TILE_SIZE - oy,
                    TILE_SIZE,
                    TILE_SIZE
                )
                
                # Skip if off screen
                if rect.right < 0 or rect.left > surface.get_width():
                    continue
                if rect.bottom < 0 or rect.top > surface.get_height():
                    continue
                
                # Determine color based on tile type
                if tile.tile_type == "wall":
                    color = self._adjust_color((80, 80, 100), 0.8)
                elif tile.tile_type == "pit":
                    color = (20, 20, 30)
                else:
                    color = self._adjust_color((50, 50, 60), 0.9)
                
                pygame.draw.rect(surface, color, rect)
                
                # Draw grid lines for visibility
                pygame.draw.rect(surface, self._adjust_color((60, 60, 70), 0.5), rect, 1)
    
    def _adjust_color(self, base_color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Adjust a color based on universe tint."""
        r = int(min(255, base_color[0] * factor + self.color[0] * 0.1))
        g = int(min(255, base_color[1] * factor + self.color[1] * 0.1))
        b = int(min(255, base_color[2] * factor + self.color[2] * 0.1))
        return (r, g, b)
    
    def find_valid_position(self, position: Tuple[float, float], size: Tuple[int, int]) -> Tuple[float, float]:
        """
        Find the nearest valid position for an entity.
        
        Used when switching universes if the target position is blocked.
        
        Args:
            position: Desired position
            size: Entity size
            
        Returns:
            Valid position (may be same as input)
        """
        px, py = position
        w, h = size
        
        # Check if current position is valid
        if self._is_position_valid(px, py, w, h):
            return position
        
        # Search in expanding circles for valid position
        for radius in range(1, 10):
            for angle_step in range(8 * radius):
                import math
                angle = (2 * math.pi * angle_step) / (8 * radius)
                test_x = px + math.cos(angle) * radius * TILE_SIZE
                test_y = py + math.sin(angle) * radius * TILE_SIZE
                
                if self._is_position_valid(test_x, test_y, w, h):
                    return (test_x, test_y)
        
        # Fallback: return original
        return position
    
    def _is_position_valid(self, x: float, y: float, w: int, h: int) -> bool:
        """Check if a position is valid (not in solid tiles)."""
        # Check corners of the bounding box
        corners = [
            (x, y),
            (x + w - 1, y),
            (x, y + h - 1),
            (x + w - 1, y + h - 1)
        ]
        
        for cx, cy in corners:
            if self.tilemap.is_solid_pixel(cx, cy):
                return False
        
        return True
    
    def serialize(self) -> dict:
        """Serialize universe state for saving."""
        return {
            "type": self.universe_type.value,
            "stability": self.stability,
            "entities": [e.serialize() for e in self.entities if e.should_save]
        }
    
    @classmethod
    def deserialize(cls, data: dict, width: int, height: int) -> 'Universe':
        """Deserialize a universe from save data."""
        universe_type = UniverseType(data["type"])
        universe = cls(universe_type, width, height)
        universe.stability = data.get("stability", 1.0)
        # Entities are loaded separately by LevelLoader
        return universe
