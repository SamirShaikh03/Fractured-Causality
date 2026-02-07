"""
Bridge - A traversable structure that can have causal dependencies.
"""

import pygame
from typing import Tuple
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...multiverse.causal_node import EntityState
from ...core.events import EventSystem, GameEvent


class Bridge(Entity):
    """
    Bridge - A structure for crossing gaps.
    
    Bridges can be:
    - Built from materials (causally linked to sources)
    - Intact or broken
    - Exist in some universes but not others
    
    A bridge might exist in Universe A because a tree was
    cut down to build it. If that tree is never cut, the
    bridge doesn't exist.
    """
    
    def __init__(self, position: Tuple[float, float],
                 bridge_id: str = None,
                 length: int = 3,
                 is_intact: bool = True,
                 material_source_id: str = None):
        """
        Initialize a Bridge.
        
        Args:
            position: Position (left end)
            bridge_id: Unique identifier
            length: Length in tiles
            is_intact: Whether bridge is usable
            material_source_id: ID of the entity this bridge was made from
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE * length, TILE_SIZE // 2),
            color=(120, 90, 60),
            persistence=EntityPersistence.VARIANT,
            solid=False,  # Bridges are walkable, not blocking
            interactive=False,
            entity_id=bridge_id or f"bridge_{id(self)}"
        )
        super().__init__(config)
        
        # Bridge properties
        self.length: int = length
        self.is_intact: bool = is_intact
        self.material_source_id: str = material_source_id or ""
        
        # Visual state
        self._wobble: float = 0.0
        self._collapse_progress: float = 0.0
        self._is_collapsing: bool = False
        
        # Create causal node
        self.create_causal_node(paradox_weight=5.0)
        if self.causal_node:
            self.causal_node.state = EntityState.EXISTS if is_intact else EntityState.DESTROYED
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the bridge's appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        
        if not self.is_intact:
            # Broken bridge - just the ends
            # Left end
            pygame.draw.rect(self.sprite, (100, 70, 45),
                           (0, 0, TILE_SIZE // 2, h))
            # Right end
            pygame.draw.rect(self.sprite, (100, 70, 45),
                           (w - TILE_SIZE // 2, 0, TILE_SIZE // 2, h))
            
            # Broken planks hanging
            pygame.draw.line(self.sprite, (80, 60, 40),
                           (TILE_SIZE // 2, h // 2), (TILE_SIZE, h + 10), 3)
            pygame.draw.line(self.sprite, (80, 60, 40),
                           (w - TILE_SIZE // 2, h // 2), (w - TILE_SIZE, h + 10), 3)
        else:
            # Intact bridge
            # Support beams
            pygame.draw.rect(self.sprite, (80, 60, 40),
                           (0, h - 8, w, 8))
            
            # Planks
            plank_width = TILE_SIZE // 3
            for i in range(int(w / plank_width)):
                x = i * plank_width
                # Alternate colors slightly
                color = (120, 90, 60) if i % 2 == 0 else (110, 80, 55)
                pygame.draw.rect(self.sprite, color,
                               (x, 0, plank_width - 2, h - 8))
                pygame.draw.rect(self.sprite, (90, 70, 50),
                               (x, 0, plank_width - 2, h - 8), 1)
            
            # Rope railings (simple lines)
            pygame.draw.line(self.sprite, (100, 80, 50),
                           (0, 2), (w, 2), 2)
    
    def collapse(self) -> None:
        """Collapse the bridge."""
        if not self.is_intact:
            return
        
        self._is_collapsing = True
        self._collapse_progress = 0.0
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "collapsing"
        })
    
    def _complete_collapse(self) -> None:
        """Complete the collapse."""
        self.is_intact = False
        self._is_collapsing = False
        
        if self.causal_node:
            self.causal_node.state = EntityState.DESTROYED
        
        self._create_sprite()
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "collapsed"
        })
    
    def can_cross(self) -> bool:
        """Check if bridge can be crossed."""
        return self.is_intact and not self._is_collapsing
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal changes."""
        if source_id == self.material_source_id:
            if new_state == EntityState.DESTROYED:
                # Material source destroyed - bridge never built
                if self.is_intact:
                    self.collapse()
            elif new_state == EntityState.EXISTS:
                # Material source exists - bridge can exist
                pass
        
        if new_state == EntityState.DESTROYED:
            if self.is_intact:
                self.collapse()
    
    def update(self, dt: float) -> None:
        """Update the bridge."""
        # Gentle wobble when intact
        if self.is_intact and not self._is_collapsing:
            self._wobble = math.sin(pygame.time.get_ticks() / 800) * 1
        
        # Collapse animation
        if self._is_collapsing:
            self._collapse_progress += dt
            if self._collapse_progress > 1.0:
                self._complete_collapse()
        
        super().update(dt)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the bridge."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy + self._wobble)
        
        if self._is_collapsing:
            # Collapse animation
            progress = self._collapse_progress
            
            # Bridge breaks in the middle
            half_w = self.width // 2
            
            # Left half falls left and down
            left_half = pygame.Surface((half_w, self.height), pygame.SRCALPHA)
            left_half.blit(self.sprite, (0, 0), (0, 0, half_w, self.height))
            
            left_angle = progress * 45
            left_rotated = pygame.transform.rotate(left_half, left_angle)
            left_alpha = int(255 * (1 - progress))
            left_rotated.set_alpha(left_alpha)
            
            left_y = render_y + int(progress * 50)
            surface.blit(left_rotated, (render_x, left_y))
            
            # Right half falls right and down
            right_half = pygame.Surface((half_w, self.height), pygame.SRCALPHA)
            right_half.blit(self.sprite, (0, 0), (half_w, 0, half_w, self.height))
            
            right_angle = -progress * 45
            right_rotated = pygame.transform.rotate(right_half, right_angle)
            right_rotated.set_alpha(left_alpha)
            
            right_x = render_x + half_w + int(progress * 20)
            surface.blit(right_rotated, (right_x, left_y))
        else:
            surface.blit(self.sprite, (render_x, render_y))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "length": self.length,
            "is_intact": self.is_intact,
            "material_source_id": self.material_source_id
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Bridge':
        """Deserialize from save data."""
        bridge = cls(
            position=tuple(data["position"]),
            bridge_id=data["entity_id"],
            length=data.get("length", 3),
            is_intact=data.get("is_intact", True),
            material_source_id=data.get("material_source_id")
        )
        bridge.exists = data["exists"]
        return bridge
