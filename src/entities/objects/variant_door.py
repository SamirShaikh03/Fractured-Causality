"""
Variant Door - A door with different states across universes.
"""

import pygame
from typing import Tuple, Optional
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE, COLOR_DOOR_LOCKED, COLOR_DOOR_OPEN
from ...multiverse.causal_node import CausalOperator, EntityState
from ...core.events import EventSystem, GameEvent


class VariantDoor(Entity):
    """
    Variant Door - A door whose state can differ across universes.
    
    Doors can be:
    - Locked (blocks passage, needs key or switch)
    - Unlocked (can be opened)
    - Open (passage allowed)
    - Linked to switches via causal operators
    
    A door might be open in Universe A but locked in Universe B,
    creating puzzles that require visiting multiple universes.
    """
    
    def __init__(self, position: Tuple[float, float],
                 door_id: str = None,
                 initially_open: bool = False,
                 requires_key: bool = False,
                 key_id: str = None,
                 prime_open: bool = None,
                 echo_open: bool = None,
                 fracture_open: bool = None):
        """
        Initialize a Variant Door.
        
        Args:
            position: Position
            door_id: Unique identifier
            initially_open: Whether door starts open (default state)
            requires_key: Whether a key is needed
            key_id: ID of the required key
            prime_open: Door state in Prime universe (overrides initially_open)
            echo_open: Door state in Echo universe (overrides initially_open)
            fracture_open: Door state in Fracture universe (overrides initially_open)
        """
        # Use prime_open as initial state if specified, otherwise initially_open
        is_open = prime_open if prime_open is not None else initially_open
        
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE, TILE_SIZE),
            color=COLOR_DOOR_OPEN if is_open else COLOR_DOOR_LOCKED,
            persistence=EntityPersistence.VARIANT,
            solid=not is_open,
            interactive=True,
            entity_id=door_id or f"door_{id(self)}"
        )
        super().__init__(config)
        
        # Door state
        self.is_open: bool = is_open
        self.is_locked: bool = not is_open
        self.requires_key: bool = requires_key
        self.key_id: str = key_id or ""
        
        # Universe-specific states
        self.prime_open: bool = prime_open if prime_open is not None else initially_open
        self.echo_open: bool = echo_open if echo_open is not None else initially_open
        self.fracture_open: bool = fracture_open if fracture_open is not None else initially_open
        
        # Animation
        self._open_progress: float = 1.0 if initially_open else 0.0
        self._is_animating: bool = False
        
        # Create causal node
        self.create_causal_node(paradox_weight=5.0)
        if self.causal_node:
            self.causal_node.state = EntityState.OPEN if initially_open else EntityState.CLOSED
        
        # Create sprite
        self._update_sprite()
    
    def _update_sprite(self) -> None:
        """Update sprite based on state."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        
        # Door frame
        pygame.draw.rect(self.sprite, (60, 50, 40), (0, 0, w, h), border_radius=4)
        
        # Door panel
        if self.is_open:
            # Open door - just show frame
            pygame.draw.rect(self.sprite, (30, 25, 20), (4, 4, w - 8, h - 8), border_radius=4)
            
            # Open indicator
            pygame.draw.rect(self.sprite, (100, 150, 100), 
                           (w // 2 - 2, 4, 4, h - 8))
        else:
            # Closed door
            door_color = (150, 100, 70) if not self.is_locked else (120, 80, 60)
            pygame.draw.rect(self.sprite, door_color, (4, 4, w - 8, h - 8), border_radius=4)
            
            # Door details
            pygame.draw.line(self.sprite, (100, 70, 50), (w // 2, 4), (w // 2, h - 4), 2)
            
            # Handle/lock
            if self.is_locked:
                # Lock icon
                lock_color = (200, 50, 50) if self.requires_key else (150, 150, 150)
                pygame.draw.rect(self.sprite, lock_color, 
                               (w - 16, h // 2 - 4, 10, 12), border_radius=2)
                pygame.draw.rect(self.sprite, lock_color,
                               (w - 14, h // 2 - 8, 6, 6), border_radius=3)
            else:
                # Handle
                pygame.draw.circle(self.sprite, (200, 180, 100), 
                                 (w - 12, h // 2), 4)
        
        # Frame border
        pygame.draw.rect(self.sprite, (80, 70, 60), (0, 0, w, h), 3, border_radius=4)
    
    def unlock(self, source: str = "key") -> bool:
        """
        Unlock the door.
        
        Args:
            source: What unlocked the door
            
        Returns:
            True if door was unlocked
        """
        if not self.is_locked:
            return False
        
        self.is_locked = False
        self._update_sprite()
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "unlocked",
            "source": source
        })
        
        return True
    
    def lock(self) -> bool:
        """Lock the door."""
        if self.is_locked or self.is_open:
            return False
        
        self.is_locked = True
        self._update_sprite()
        
        return True
    
    def open(self, source: str = "interact") -> bool:
        """
        Open the door.
        
        Args:
            source: What opened the door
            
        Returns:
            True if door was opened
        """
        if self.is_open:
            return False
        
        if self.is_locked:
            # Try to unlock first
            return False
        
        self.is_open = True
        self.solid = False
        self._is_animating = True
        self._update_sprite()
        
        if self.causal_node:
            self.causal_node.state = EntityState.OPEN
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "opened",
            "source": source
        })
        
        return True
    
    def close(self, source: str = "interact") -> bool:
        """Close the door."""
        if not self.is_open:
            return False
        
        self.is_open = False
        self.solid = True
        self._is_animating = True
        self._update_sprite()
        
        if self.causal_node:
            self.causal_node.state = EntityState.CLOSED
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "closed",
            "source": source
        })
        
        return True
    
    def on_interact(self, player) -> bool:
        """Handle player interaction."""
        if self.is_locked:
            # Check if player has the key
            if self.requires_key and hasattr(player, 'inventory'):
                if self.key_id in player.inventory:
                    self.unlock("key")
                    return self.open("player")
            
            # Visual/audio feedback for locked
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "The door is locked.",
                "type": "info"
            })
            return False
        
        # Toggle open/close
        if self.is_open:
            return self.close("player")
        else:
            return self.open("player")
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal state changes."""
        if new_state == EntityState.OPEN:
            self.unlock("causal")
            self.open("causal")
        elif new_state == EntityState.CLOSED:
            self.close("causal")
        elif new_state == EntityState.ACTIVE:
            self.unlock("causal")
            self.open("causal")
        elif new_state == EntityState.INACTIVE:
            self.close("causal")
            self.lock()
        else:
            super().on_causal_change(new_state, source_id)
    
    def update(self, dt: float) -> None:
        """Update the door."""
        # Animation
        if self._is_animating:
            target = 1.0 if self.is_open else 0.0
            diff = target - self._open_progress
            
            if abs(diff) < 0.01:
                self._open_progress = target
                self._is_animating = False
            else:
                self._open_progress += diff * dt * 8
        
        super().update(dt)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the door."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        # Draw door with animation offset
        if self._is_animating:
            # Sliding animation
            offset = int((1 - self._open_progress) * self.width) if not self.is_open else int(self._open_progress * self.width)
            temp_sprite = self.sprite.copy()
            temp_sprite.set_alpha(int(255 * (1 - self._open_progress * 0.3)))
            surface.blit(temp_sprite, (render_x, render_y))
        else:
            surface.blit(self.sprite, (render_x, render_y))
        
        # Lock indicator glow
        if self.is_locked and self.requires_key:
            glow_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
            pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
            glow_alpha = int(50 + 50 * pulse)
            pygame.draw.circle(glow_surface, (200, 50, 50, glow_alpha), (10, 10), 10)
            surface.blit(glow_surface, (render_x + self.width - 20, render_y + self.height // 2 - 10))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "is_open": self.is_open,
            "is_locked": self.is_locked,
            "requires_key": self.requires_key,
            "key_id": self.key_id
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'VariantDoor':
        """Deserialize from save data."""
        door = cls(
            position=tuple(data["position"]),
            door_id=data["entity_id"],
            initially_open=data.get("is_open", False),
            requires_key=data.get("requires_key", False),
            key_id=data.get("key_id")
        )
        door.is_locked = data.get("is_locked", True)
        door.exists = data["exists"]
        door._update_sprite()
        return door
