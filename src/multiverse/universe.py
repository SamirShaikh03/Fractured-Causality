   

import pygame
from enum import Enum
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

from ..core.settings import (
    TILE_SIZE, UNIVERSE_COLORS, UNIVERSE_BG_COLORS,
    UNIVERSE_PRIME, UNIVERSE_ECHO, UNIVERSE_FRACTURE
)

if TYPE_CHECKING:
    from ..entities.entity import Entity


class UniverseType(Enum):
                                         
    PRIME = UNIVERSE_PRIME                                     
    ECHO = UNIVERSE_ECHO                              
    FRACTURE = UNIVERSE_FRACTURE                                      


class TileType(Enum):
                                        
    FLOOR = "floor"                          
    WALL = "wall"                             
    PIT = "pit"                                     
    HAZARD = "hazard"                         


@dataclass
class TileData:
                                                
    solid: bool = False
    tile_type: str = "floor"
    variant: int = 0


class TileMap:
       
    
    def __init__(self, width: int, height: int):
           
        self.width = width
        self.height = height
        self._tiles: List[List[TileType]] = []
        self.tiles = [
            [TileType.FLOOR for _ in range(width)]
            for _ in range(height)
        ]

    @property
    def tiles(self) -> List[List[TileType]]:
                                   
        return self._tiles

    @tiles.setter
    def tiles(self, value: List[List[TileType | TileData | str]]) -> None:
                                                             
        normalized: List[List[TileType]] = []

        for row in value[:self.height]:
            normalized_row = [self._coerce_tile_type(cell) for cell in row[:self.width]]
            if len(normalized_row) < self.width:
                normalized_row.extend([TileType.FLOOR] * (self.width - len(normalized_row)))
            normalized.append(normalized_row)

        while len(normalized) < self.height:
            normalized.append([TileType.FLOOR for _ in range(self.width)])

        self._tiles = normalized

    @staticmethod
    def _coerce_tile_type(tile_value: TileType | TileData | str | None) -> TileType:
                                                                   
        if isinstance(tile_value, TileType):
            return tile_value

        if isinstance(tile_value, TileData):
            raw_type = tile_value.tile_type
            if isinstance(raw_type, TileType):
                return raw_type
            if isinstance(raw_type, str):
                try:
                    return TileType(raw_type.lower())
                except ValueError:
                    pass
            return TileType.WALL if tile_value.solid else TileType.FLOOR

        if isinstance(tile_value, str):
            try:
                return TileType(tile_value.lower())
            except ValueError:
                return TileType.WALL

                                                         
        return TileType.WALL
    
    def get_tile(self, x: int, y: int) -> Optional[TileType]:
                                             
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._tiles[y][x]
        return None
    
    def set_tile(self, x: int, y: int, tile_data: TileType | TileData) -> None:
                                             
        if 0 <= x < self.width and 0 <= y < self.height:
            self._tiles[y][x] = self._coerce_tile_type(tile_data)
    
    def is_solid(self, x: int, y: int) -> bool:
                                                         
        tile = self.get_tile(x, y)
        if tile is None:
            return True                          
        return tile in (TileType.WALL, TileType.PIT)
    
    def is_solid_pixel(self, px: int, py: int) -> bool:
                                                           
        grid_x = int(px // TILE_SIZE)
        grid_y = int(py // TILE_SIZE)
        return self.is_solid(grid_x, grid_y)
    
    def get_tile_rect(self, x: int, y: int) -> pygame.Rect:
                                                 
        return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)


class Universe:
       
    
    def __init__(self, universe_type: UniverseType, width: int = 20, height: int = 11):
           
        self.universe_type = universe_type
        self.tilemap = TileMap(width, height)
        self.entities: List['Entity'] = []
        self.entity_map: Dict[str, 'Entity'] = {}
        
                           
        self.color = UNIVERSE_COLORS.get(universe_type.value, (128, 128, 128))
        self.bg_color = UNIVERSE_BG_COLORS.get(universe_type.value, (30, 30, 30))
        
               
        self.is_active = False
        self.time_scale = 1.0                           
        
                                         
        self.stability = 1.0                             
    
    @property
    def width(self) -> int:
                                     
        return self.tilemap.width
    
    @property
    def height(self) -> int:
                                      
        return self.tilemap.height
    
    @property
    def name(self) -> str:
                                                    
        names = {
            UniverseType.PRIME: "Prime",
            UniverseType.ECHO: "Echo",
            UniverseType.FRACTURE: "Fracture"
        }
        return names.get(self.universe_type, "Unknown")
    
    def add_entity(self, entity: 'Entity') -> None:
           
        if entity not in self.entities:
            self.entities.append(entity)
            self.entity_map[entity.entity_id] = entity
            entity.universe = self
    
    def remove_entity(self, entity: 'Entity') -> None:
           
        if entity in self.entities:
            self.entities.remove(entity)
        if entity.entity_id in self.entity_map:
            del self.entity_map[entity.entity_id]
    
    def clear_entities(self) -> None:
           
        self.entities.clear()
        self.entity_map.clear()
    
    def get_entity(self, entity_id: str) -> Optional['Entity']:
           
        return self.entity_map.get(entity_id)
    
    def get_entities_at(self, position: Tuple[float, float], radius: float = 0) -> List['Entity']:
           
        result = []
        px, py = position
        
        for entity in self.entities:
            if not entity.exists:
                continue
                
            ex, ey = entity.position
            distance = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
            
                                                     
            if radius > 0:
                if distance <= radius + max(entity.size[0], entity.size[1]) / 2:
                    result.append(entity)
            else:
                rect = entity.get_rect()
                if rect.collidepoint(px, py):
                    result.append(entity)
        
        return result
    
    def get_entities_of_type(self, entity_type: type) -> List['Entity']:
           
        return [e for e in self.entities if isinstance(e, entity_type) and e.exists]
    
    def update(self, dt: float) -> None:
           
        if not self.is_active:
            return
            
        adjusted_dt = dt * self.time_scale
        
        for entity in self.entities:
            if entity.exists:
                entity.update(adjusted_dt)
    
    def render(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
           
                        
        self._render_tilemap(surface, camera_offset)
        
                                                 
        sorted_entities = sorted(
            [e for e in self.entities if e.exists],
            key=lambda e: e.position[1]
        )
        
        for entity in sorted_entities:
            entity.render(surface, camera_offset)
    
    def _render_tilemap(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
                                 
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
                
                                    
                if rect.right < 0 or rect.left > surface.get_width():
                    continue
                if rect.bottom < 0 or rect.top > surface.get_height():
                    continue
                
                                                    
                if tile == TileType.WALL:
                    color = self._adjust_color((80, 80, 100), 0.8)
                elif tile == TileType.PIT:
                    color = (20, 20, 30)
                else:
                    color = self._adjust_color((50, 50, 60), 0.9)
                
                pygame.draw.rect(surface, color, rect)
                
                                                
                pygame.draw.rect(surface, self._adjust_color((60, 60, 70), 0.5), rect, 1)
    
    def _adjust_color(self, base_color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
                                                    
        r = int(min(255, base_color[0] * factor + self.color[0] * 0.1))
        g = int(min(255, base_color[1] * factor + self.color[1] * 0.1))
        b = int(min(255, base_color[2] * factor + self.color[2] * 0.1))
        return (r, g, b)
    
    def find_valid_position(self, position: Tuple[float, float], size: Tuple[int, int]) -> Tuple[float, float]:
           
        px, py = position
        w, h = size
        
                                            
        if self._is_position_valid(px, py, w, h):
            return position
        
                                                        
        for radius in range(1, 10):
            for angle_step in range(8 * radius):
                import math
                angle = (2 * math.pi * angle_step) / (8 * radius)
                test_x = px + math.cos(angle) * radius * TILE_SIZE
                test_y = py + math.sin(angle) * radius * TILE_SIZE
                
                if self._is_position_valid(test_x, test_y, w, h):
                    return (test_x, test_y)
        
                                   
        return position
    
    def _is_position_valid(self, x: float, y: float, w: int, h: int) -> bool:
                                                                
                                           
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
                                                  
        return {
            "type": self.universe_type.value,
            "stability": self.stability,
            "entities": [e.serialize() for e in self.entities if e.should_save]
        }
    
    @classmethod
    def deserialize(cls, data: dict, width: int, height: int) -> 'Universe':
                                                    
        universe_type = UniverseType(data["type"])
        universe = cls(universe_type, width, height)
        universe.stability = data.get("stability", 1.0)
                                                       
        return universe
