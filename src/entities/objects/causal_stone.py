"""
Causal Stone - An anchored object that moves identically in all universes.
"""

import pygame
from typing import Tuple, Optional
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...multiverse.causal_node import EntityState
from ...core.events import EventSystem, GameEvent


class CausalStone(Entity):
    """
    Causal Stone - A stone that is anchored across all universes.
    
    When pushed in one universe, it moves in ALL universes simultaneously.
    This creates puzzles where the stone must be positioned to satisfy
    constraints in multiple realities at once.
    
    Causal Stones:
    - Are ANCHORED (same position in all universes)
    - Can be pushed by the player
    - Block movement
    - Can activate switches when positioned on them
    """
    
    def __init__(self, position: Tuple[float, float],
                 stone_id: str = None):
        """
        Initialize a Causal Stone.
        
        Args:
            position: Starting position
            stone_id: Unique identifier
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE - 4, TILE_SIZE - 4),
            color=(150, 150, 170),
            persistence=EntityPersistence.ANCHORED,
            solid=True,
            interactive=True,
            entity_id=stone_id or f"stone_{id(self)}"
        )
        super().__init__(config)
        
        # Push behavior
        self.push_distance: float = TILE_SIZE
        self.is_being_pushed: bool = False
        self._push_progress: float = 0.0
        self._push_direction: Tuple[int, int] = (0, 0)
        self._push_start: Tuple[float, float] = (0, 0)
        self._push_target: Tuple[float, float] = (0, 0)
        
        # Visual
        self._glow: float = 0.0
        
        # Create causal node
        self.create_causal_node(paradox_weight=2.0)
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the stone's appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        
        # Main stone body
        stone_rect = pygame.Rect(2, 2, w - 4, h - 4)
        pygame.draw.rect(self.sprite, (130, 130, 150), stone_rect, border_radius=8)
        
        # Highlight
        highlight = pygame.Rect(4, 4, w // 2 - 4, h // 3)
        pygame.draw.rect(self.sprite, (170, 170, 190), highlight, border_radius=4)
        
        # Shadow
        shadow = pygame.Rect(w // 2, h // 2, w // 2 - 4, h // 3)
        pygame.draw.rect(self.sprite, (100, 100, 120), shadow, border_radius=4)
        
        # Border
        pygame.draw.rect(self.sprite, (80, 80, 100), stone_rect, 2, border_radius=8)
        
        # Causal symbol (indicating it's anchored)
        center = (w // 2, h // 2)
        pygame.draw.circle(self.sprite, (200, 180, 100), center, 8)
        pygame.draw.circle(self.sprite, (255, 220, 150), center, 5)
    
    def can_push(self, direction: Tuple[int, int], tilemap) -> bool:
        """
        Check if the stone can be pushed in a direction.
        
        Args:
            direction: (dx, dy) direction (-1, 0, or 1)
            tilemap: The tilemap to check against
            
        Returns:
            True if push is valid
        """
        if self.is_being_pushed:
            return False
        
        # Calculate target position
        target_x = self.x + direction[0] * self.push_distance
        target_y = self.y + direction[1] * self.push_distance
        
        # Check if target is valid (not solid)
        # Check all corners of the stone at target position
        corners = [
            (target_x + 4, target_y + 4),
            (target_x + self.width - 4, target_y + 4),
            (target_x + 4, target_y + self.height - 4),
            (target_x + self.width - 4, target_y + self.height - 4)
        ]
        
        for cx, cy in corners:
            if tilemap.is_solid_pixel(cx, cy):
                return False
        
        return True
    
    def push(self, direction: Tuple[int, int]) -> bool:
        """
        Start pushing the stone.
        
        Args:
            direction: Direction to push
            
        Returns:
            True if push started
        """
        self.is_being_pushed = True
        self._push_progress = 0.0
        self._push_direction = direction
        self._push_start = self.position
        self._push_target = (
            self.x + direction[0] * self.push_distance,
            self.y + direction[1] * self.push_distance
        )
        self._glow = 1.0
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "push_started",
            "direction": direction
        })
        
        return True
    
    def on_interact(self, player) -> bool:
        """
        Handle interaction (pushing).
        
        Args:
            player: The player entity
            
        Returns:
            True if interaction handled
        """
        if self.is_being_pushed:
            return False
        
        # Determine push direction from player position
        dx = self.center[0] - player.center[0]
        dy = self.center[1] - player.center[1]
        
        # Normalize to push direction
        if abs(dx) > abs(dy):
            direction = (1 if dx > 0 else -1, 0)
        else:
            direction = (0, 1 if dy > 0 else -1)
        
        # Check all universes if this push is valid
        # (Stone is anchored, so must be valid in all)
        # For now, just check current universe's tilemap
        if player.multiverse and player.multiverse.active_universe:
            tilemap = player.multiverse.active_universe.tilemap
            if self.can_push(direction, tilemap):
                return self.push(direction)
        
        return False
    
    def update(self, dt: float) -> None:
        """Update the stone."""
        # Handle push animation
        if self.is_being_pushed:
            self._push_progress += dt * 4  # Push speed
            
            if self._push_progress >= 1.0:
                # Complete push
                self.position = self._push_target
                self.is_being_pushed = False
                self._push_progress = 0.0
                
                EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
                    "entity_id": self.entity_id,
                    "change": "push_completed",
                    "position": self.position
                })
            else:
                # Interpolate position
                t = self._ease_out_cubic(self._push_progress)
                self.position = (
                    self._push_start[0] + (self._push_target[0] - self._push_start[0]) * t,
                    self._push_start[1] + (self._push_target[1] - self._push_start[1]) * t
                )
        
        # Fade glow
        self._glow = max(0, self._glow - dt * 2)
        
        super().update(dt)
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animation."""
        return 1 - pow(1 - t, 3)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the stone with effects."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        # Anchored glow (shows it's connected to other universes)
        if self._glow > 0:
            glow_surface = pygame.Surface(
                (self.width + 20, self.height + 20), pygame.SRCALPHA
            )
            glow_alpha = int(100 * self._glow)
            pygame.draw.rect(
                glow_surface, 
                (200, 180, 100, glow_alpha),
                (0, 0, self.width + 20, self.height + 20),
                border_radius=12
            )
            surface.blit(glow_surface, (render_x - 10, render_y - 10))
        
        # Main sprite
        surface.blit(self.sprite, (render_x, render_y))
        
        # Push indicator when interactive
        if self.interactive and not self.is_being_pushed:
            indicator_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.polygon(
                indicator_surface,
                (255, 255, 255, 150),
                [(8, 0), (16, 8), (8, 16), (0, 8)]
            )
            surface.blit(indicator_surface,
                        (render_x + self.width // 2 - 8, render_y - 20))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "is_being_pushed": self.is_being_pushed
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'CausalStone':
        """Deserialize from save data."""
        stone = cls(
            position=tuple(data["position"]),
            stone_id=data["entity_id"]
        )
        stone.exists = data["exists"]
        return stone
