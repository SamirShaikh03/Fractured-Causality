import pygame
from typing import Tuple, Optional, List
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...multiverse.causal_node import CausalNode, CausalOperator, EntityState
from ...core.events import EventSystem, GameEvent
from ...utils.sprite_loader import load_entity_sprite


class Shade(Entity):
    def __init__(self, position: Tuple[float, float],
                 origin_id: str = None,
                 patrol_path: List[Tuple[float, float]] = None,
                 shade_id: str = None,
                 causal_origin_id: str = None,
                 patrol_points: List[Tuple[float, float]] = None):
        scaled_size = max(1, int(round((TILE_SIZE - 8) * 1.3225)))
        config = EntityConfig(
            position=position,
            size=(scaled_size, scaled_size),
            color=(80, 40, 100),
            persistence=EntityPersistence.EXCLUSIVE,
            solid=True,
            interactive=False
        )
        super().__init__(config)
        actual_origin = causal_origin_id or origin_id or ""
        actual_patrol = patrol_points or patrol_path or [position]
        
        if shade_id:
            self.entity_id = shade_id
        self.is_enemy = True
        self.health: int = 50
        self.max_health: int = 50
        self.damage: int = 10
        
        self.origin_id: str = actual_origin
        self.origin_exists: bool = True

        self.patrol_path: List[Tuple[float, float]] = actual_patrol
        self.current_patrol_index: int = 0
        self.patrol_speed: float = 50.0 
        self.patrol_wait_time: float = 1.0
        self._patrol_wait_timer: float = 0.0
        self._is_waiting: bool = False

        self._opacity: float = 1.0
        self._flicker_timer: float = 0.0
        self._is_fading: bool = False

        self.create_causal_node(paradox_weight=10.0)

        self._create_shade_sprite()
    
    def _create_shade_sprite(self) -> None:
        loaded = load_entity_sprite("enemy_shade.png", self.size)
        if loaded is not None:
            self.sprite = loaded
            return

        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        center = (w // 2, h // 2)
        
        for i in range(3):
            radius = w // 2 - i * 4
            alpha = 150 - i * 40
            color = (80 - i * 20, 40 - i * 10, 100 - i * 20, alpha)
            pygame.draw.circle(self.sprite, color, center, radius)
        
        eye_y = h // 3
        pygame.draw.circle(self.sprite, (200, 50, 50), (w // 3, eye_y), 4)
        pygame.draw.circle(self.sprite, (200, 50, 50), (2 * w // 3, eye_y), 4)
        pygame.draw.circle(self.sprite, (255, 100, 100), (w // 3, eye_y), 2)
        pygame.draw.circle(self.sprite, (255, 100, 100), (2 * w // 3, eye_y), 2)
    
    def set_origin(self, origin_id: str, causal_graph) -> None:
        self.origin_id = origin_id
        if self.causal_node:
            causal_graph.add_dependency(
                origin_id,
                self.causal_node.node_id,
                CausalOperator.EXISTENCE
            )
    
    def update(self, dt: float) -> None:

        if not self.exists:
            return
        
        self._flicker_timer += dt
        if not self.origin_exists:
            self._is_fading = True
            self._opacity = max(0, self._opacity - dt * 2)
            if self._opacity <= 0:
                self.destroy()
                return
        else:
            self._opacity = 0.8 + 0.2 * math.sin(self._flicker_timer * 3)
        
        self._update_patrol(dt)
        
        super().update(dt)
    
    def _update_patrol(self, dt: float) -> None:
        if len(self.patrol_path) < 2:
            return
        
        if self._is_waiting:
            self._patrol_wait_timer -= dt
            if self._patrol_wait_timer <= 0:
                self._is_waiting = False
                self.current_patrol_index = (
                    (self.current_patrol_index + 1) % len(self.patrol_path)
                )
            return
        
        target = self.patrol_path[self.current_patrol_index]
        dx = target[0] - self.x
        dy = target[1] - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 5:
            self._is_waiting = True
            self._patrol_wait_timer = self.patrol_wait_time
        else:
            speed = self.patrol_speed * dt
            if speed > distance:
                speed = distance
            
            self.position = (
                self.x + (dx / distance) * speed,
                self.y + (dy / distance) * speed
            )
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        if source_id == self.origin_id:
            if new_state == EntityState.DESTROYED:
                self.origin_exists = False
                self._is_fading = True
                
                EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
                    "entity_id": self.entity_id,
                    "change": "origin_destroyed",
                    "origin_id": self.origin_id
                })
        
        if new_state == EntityState.DESTROYED and source_id != self.origin_id:
            super().on_causal_change(new_state, source_id)
    
    def take_damage(self, amount: int) -> bool:
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self._is_fading = True
            EventSystem.emit(GameEvent.ENEMY_DEFEATED, {
                "entity_id": self.entity_id,
                "enemy_type": "shade"
            })
            self.destroy()
            return True
        return False
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        if self._opacity < 1.0:
            temp_sprite = self.sprite.copy()
            temp_sprite.set_alpha(int(255 * self._opacity))
            surface.blit(temp_sprite, (render_x, render_y))
        else:
            surface.blit(self.sprite, (render_x, render_y))
        
        if self._is_fading:
            for i in range(3):
                particle_y = render_y - int(self._flicker_timer * 20) % 30 - i * 10
                particle_x = render_x + self.width // 2 + int(math.sin(self._flicker_timer * 5 + i) * 10)
                particle_alpha = int((1 - (self._flicker_timer * 20 % 30) / 30) * 100)
                
                particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (80, 40, 100, particle_alpha), (3, 3), 3)
                surface.blit(particle_surface, (particle_x, particle_y))
    
    def serialize(self) -> dict:
        data = super().serialize()
        data.update({
            "origin_id": self.origin_id,
            "patrol_path": self.patrol_path,
            "current_patrol_index": self.current_patrol_index,
            "origin_exists": self.origin_exists
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Shade':
        shade = cls(
            position=tuple(data["position"]),
            origin_id=data.get("origin_id"),
            patrol_path=data.get("patrol_path", [])
        )
        shade.current_patrol_index = data.get("current_patrol_index", 0)
        shade.origin_exists = data.get("origin_exists", True)
        shade.exists = data["exists"]
        return shade
