"""
Key - A collectible item that unlocks doors.
"""

import pygame
from typing import Tuple
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE, COLOR_KEY
from ...multiverse.causal_node import CausalOperator, EntityState
from ...core.events import EventSystem, GameEvent


class Key(Entity):
    """
    Key - An item that unlocks specific doors.
    
    Keys are typically EXCLUSIVE (exist in only one universe),
    creating puzzles where players must find the right universe
    to collect the key.
    
    Keys can be causally linked - a key in Universe A might
    be rusted/broken in Universe B due to different history.
    """
    
    def __init__(self, position: Tuple[float, float],
                 key_id: str = None,
                 door_id: str = None):
        """
        Initialize a Key.
        
        Args:
            position: Position
            key_id: Unique identifier
            door_id: ID of the door this key unlocks
        """
        config = EntityConfig(
            position=position,
            size=(32, 32),
            color=COLOR_KEY,
            persistence=EntityPersistence.EXCLUSIVE,
            solid=False,
            interactive=True,
            entity_id=key_id or f"key_{id(self)}"
        )
        super().__init__(config)
        
        # Key properties
        self.door_id: str = door_id or ""
        self.is_collected: bool = False
        self.is_broken: bool = False  # For variant versions
        
        # Animation
        self._float_offset: float = 0.0
        self._rotation: float = 0.0
        self._sparkle_timer: float = 0.0
        
        # Create causal node
        self.create_causal_node(paradox_weight=3.0)
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the key's appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        
        if self.is_broken:
            # Broken/rusted key
            color = (100, 80, 60)
            pygame.draw.ellipse(self.sprite, color, (w // 4, 2, w // 2, h // 3))
            pygame.draw.rect(self.sprite, color, (w // 2 - 3, h // 3, 6, h // 2))
            # Crack
            pygame.draw.line(self.sprite, (60, 50, 40), 
                           (w // 2, h // 3), (w // 2 + 4, h // 2 + 5), 2)
        else:
            # Shiny golden key
            # Head (circular)
            pygame.draw.ellipse(self.sprite, (200, 170, 50), (w // 4, 2, w // 2, h // 3))
            pygame.draw.ellipse(self.sprite, (255, 220, 100), (w // 4 + 3, 5, w // 2 - 6, h // 3 - 6))
            
            # Hole in head
            pygame.draw.ellipse(self.sprite, (150, 120, 30), (w // 2 - 4, h // 6, 8, 8))
            
            # Shaft
            pygame.draw.rect(self.sprite, (200, 170, 50), (w // 2 - 3, h // 3, 6, h // 2))
            pygame.draw.rect(self.sprite, (255, 220, 100), (w // 2 - 1, h // 3, 2, h // 2))
            
            # Teeth
            pygame.draw.rect(self.sprite, (200, 170, 50), (w // 2 + 3, h * 2 // 3, 6, 4))
            pygame.draw.rect(self.sprite, (200, 170, 50), (w // 2 + 3, h * 5 // 6, 8, 4))
    
    def collect(self, player) -> bool:
        """
        Collect the key.
        
        Args:
            player: The player collecting the key
            
        Returns:
            True if collected
        """
        if self.is_collected or self.is_broken:
            return False
        
        self.is_collected = True
        self.visible = False
        self.exists = False
        
        # Add to player inventory (if they have one)
        if hasattr(player, 'inventory'):
            player.inventory.add(self.entity_id)
        
        # Update causal state
        if self.causal_node:
            self.causal_node.state = EntityState.DESTROYED
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "collected",
            "door_id": self.door_id
        })
        
        return True
    
    def on_interact(self, player) -> bool:
        """Handle player interaction."""
        if self.is_broken:
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "This key is broken and useless.",
                "type": "info"
            })
            return False
        
        return self.collect(player)
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal state changes."""
        if new_state == EntityState.DESTROYED:
            # Key becomes broken in this universe
            self.is_broken = True
            self._create_sprite()
        else:
            super().on_causal_change(new_state, source_id)
    
    def update(self, dt: float) -> None:
        """Update the key."""
        if self.is_collected:
            return
        
        # Floating animation
        self._float_offset = math.sin(pygame.time.get_ticks() / 300) * 4
        
        # Slow rotation
        self._rotation += dt * 30
        
        # Sparkle
        self._sparkle_timer += dt
        
        super().update(dt)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the key with effects."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy + self._float_offset)
        
        # Glow effect (only for intact keys)
        if not self.is_broken:
            glow_surface = pygame.Surface((self.width + 16, self.height + 16), pygame.SRCALPHA)
            glow_alpha = int(80 + 40 * math.sin(pygame.time.get_ticks() / 200))
            pygame.draw.ellipse(glow_surface, (255, 220, 100, glow_alpha),
                              (0, 0, self.width + 16, self.height + 16))
            surface.blit(glow_surface, (render_x - 8, render_y - 8))
        
        # Main sprite
        surface.blit(self.sprite, (render_x, render_y))
        
        # Sparkles
        if not self.is_broken and int(self._sparkle_timer * 5) % 3 == 0:
            sparkle_x = render_x + self.width // 2 + int(math.cos(self._sparkle_timer * 3) * 10)
            sparkle_y = render_y + int(math.sin(self._sparkle_timer * 3) * 10)
            
            pygame.draw.circle(surface, (255, 255, 200), (sparkle_x, sparkle_y), 2)
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "door_id": self.door_id,
            "is_collected": self.is_collected,
            "is_broken": self.is_broken
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Key':
        """Deserialize from save data."""
        key = cls(
            position=tuple(data["position"]),
            key_id=data["entity_id"],
            door_id=data.get("door_id")
        )
        key.is_collected = data.get("is_collected", False)
        key.is_broken = data.get("is_broken", False)
        key.exists = data["exists"]
        if key.is_broken:
            key._create_sprite()
        return key
