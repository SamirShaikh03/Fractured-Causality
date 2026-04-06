import pygame
from enum import Enum
from typing import Tuple, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
import uuid

from ..core.settings import TILE_SIZE, COLOR_WHITE
from ..multiverse.causal_node import CausalNode, EntityState

if TYPE_CHECKING:
    from ..multiverse.universe import Universe


class EntityPersistence(Enum):
    
    ANCHORED = "anchored"
    
    VARIANT = "variant"
    
    EXCLUSIVE = "exclusive"


@dataclass
class EntityConfig:
    position: Tuple[float, float] = (0, 0)
    size: Tuple[int, int] = (TILE_SIZE, TILE_SIZE)
    color: Tuple[int, int, int] = COLOR_WHITE
    persistence: EntityPersistence = EntityPersistence.VARIANT
    solid: bool = True
    interactive: bool = False
    entity_id: str = None


class Entity:
    def __init__(self, config: EntityConfig = None, **kwargs):
        config = config or EntityConfig()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.entity_id: str = config.entity_id or str(uuid.uuid4())[:8]
        self.position: Tuple[float, float] = config.position
        self.size: Tuple[int, int] = config.size
        self.color: Tuple[int, int, int] = config.color
        self.persistence: EntityPersistence = config.persistence
        self.universe: Optional['Universe'] = None

        self.solid: bool = config.solid
        self.velocity: Tuple[float, float] = (0, 0)

        self.exists: bool = True
        self.active: bool = True
        self.visible: bool = True
        self.interactive: bool = config.interactive
        self.is_enemy: bool = False
        
        self.causal_node: Optional[CausalNode] = None

        self.sprite: Optional[pygame.Surface] = None
        self.animation_frame: int = 0
        self.animation_timer: float = 0

        self.should_save: bool = True
        self.marked_for_removal: bool = False

        self._create_default_sprite()
    
    def _create_default_sprite(self) -> None:
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(self.sprite, self.color, 
                        (0, 0, self.size[0], self.size[1]))
        pygame.draw.rect(self.sprite, (255, 255, 255), 
                        (0, 0, self.size[0], self.size[1]), 2)
    
    @property
    def x(self) -> float:
        return self.position[0]
    
    @x.setter
    def x(self, value: float) -> None:
        self.position = (value, self.position[1])
    
    @property
    def y(self) -> float:
        return self.position[1]
    
    @y.setter
    def y(self, value: float) -> None:
        self.position = (self.position[0], value)
    
    @property
    def width(self) -> int:
        return self.size[0]
    
    @property
    def height(self) -> int:
        return self.size[1]
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def set_position(self, x: float, y: float) -> None:
        self.position = (x, y)
    
    def move(self, dx: float, dy: float) -> None:
        self.position = (self.x + dx, self.y + dy)
    
    def distance_to(self, other: 'Entity') -> float:
        dx = other.center[0] - self.center[0]
        dy = other.center[1] - self.center[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def distance_to_point(self, point: Tuple[float, float]) -> float:
        dx = point[0] - self.center[0]
        dy = point[1] - self.center[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def collides_with(self, other: 'Entity') -> bool:
        if not self.exists or not other.exists:
            return False
        return self.get_rect().colliderect(other.get_rect())
    
    def contains_point(self, point: Tuple[float, float]) -> bool:
        return self.get_rect().collidepoint(point)
    
    def update(self, dt: float) -> None:
        if not self.active:
            return
        
        if self.velocity != (0, 0):
            self.move(self.velocity[0] * dt, self.velocity[1] * dt)
        self.animation_timer += dt
    
    def render(self, surface: pygame.Surface, 
               camera_offset: Tuple[int, int] = (0, 0)) -> None:

        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)

        if (render_x + self.width < 0 or render_x > surface.get_width() or
            render_y + self.height < 0 or render_y > surface.get_height()):
            return
        
        if self.sprite:
            surface.blit(self.sprite, (render_x, render_y))
        else:
            pygame.draw.rect(surface, self.color,
                           (render_x, render_y, self.width, self.height))
    
    def render_debug(self, surface: pygame.Surface,
                    camera_offset: Tuple[int, int] = (0, 0)) -> None:
        ox, oy = camera_offset
        rect = pygame.Rect(int(self.x - ox), int(self.y - oy),
                          self.width, self.height)

        color = (0, 255, 0) if not self.solid else (255, 0, 0)
        pygame.draw.rect(surface, color, rect, 1)

        cx = int(self.center[0] - ox)
        cy = int(self.center[1] - oy)
        pygame.draw.circle(surface, (255, 255, 0), (cx, cy), 3)
    
    def on_interact(self, player: 'Entity') -> bool:
        return False
    
    def on_collision(self, other: 'Entity') -> None:
        pass
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        if new_state == EntityState.DESTROYED:
            self.destroy()
        elif new_state == EntityState.ACTIVE:
            self.active = True
        elif new_state == EntityState.INACTIVE:
            self.active = False
    
    def destroy(self) -> None:
        self.exists = False
        self.active = False
        self.visible = False
        self.marked_for_removal = True
        
        if self.causal_node:
            self.causal_node.exists = False
            self.causal_node.state = EntityState.DESTROYED
    
    def revive(self) -> None:
        self.exists = True
        self.active = True
        self.visible = True
        self.marked_for_removal = False
        
        if self.causal_node:
            self.causal_node.exists = True
            self.causal_node.state = EntityState.EXISTS
    
    def create_causal_node(self, paradox_weight: float = 1.0) -> CausalNode:
        self.causal_node = CausalNode(self.entity_id, self)
        self.causal_node.paradox_weight = paradox_weight
        return self.causal_node
    
    def serialize(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "type": self.__class__.__name__,
            "position": self.position,
            "size": self.size,
            "exists": self.exists,
            "active": self.active,
            "persistence": self.persistence.value,
            "causal_node": self.causal_node.serialize() if self.causal_node else None
        }
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Entity':
        config = EntityConfig(
            entity_id=data["entity_id"],
            position=tuple(data["position"]),
            size=tuple(data["size"]),
            persistence=EntityPersistence(data["persistence"])
        )
        entity = cls(config)
        entity.exists = data["exists"]
        entity.active = data["active"]
        return entity
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.entity_id}, pos={self.position})"
