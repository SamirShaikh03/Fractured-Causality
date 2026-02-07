"""
Echo Walker - An enemy that exists across multiple universes simultaneously.

Echo Walkers mirror the player's movements with a delay, potentially
blocking paths in other universes.
"""

import pygame
from typing import Tuple, List, Optional
from collections import deque
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...multiverse.causal_node import EntityState
from ...multiverse.universe import UniverseType
from ...core.events import EventSystem, GameEvent


class EchoWalker(Entity):
    """
    Echo Walker - A being that exists in multiple universes at once.
    
    Echo Walkers copy the player's movements with a time delay.
    When the player moves in Universe A, the Echo Walker in Universe B
    will mirror that movement a few seconds later.
    
    This creates a puzzle element where players must think ahead:
    "If I move here now, where will the Echo Walker be when I switch?"
    
    Echo Walkers:
    - Exist in all universes (ANCHORED)
    - Mirror player movement with delay
    - Block paths in other universes
    - Can be "confused" by paradox (erratic behavior)
    - Defeated by creating a paradox in their existence pattern
    """
    
    def __init__(self, position: Tuple[float, float],
                 echo_delay: float = 2.0,
                 home_universe: UniverseType = UniverseType.ECHO):
        """
        Initialize an Echo Walker.
        
        Args:
            position: Starting position
            echo_delay: Seconds of delay before copying player movement
            home_universe: The universe this walker is most "real" in
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE - 12, TILE_SIZE - 12),
            color=(100, 180, 200),
            persistence=EntityPersistence.ANCHORED,
            solid=True,
            interactive=False
        )
        super().__init__(config)
        
        # Echo behavior
        self.echo_delay: float = echo_delay
        self.home_universe: UniverseType = home_universe
        
        # Mark as enemy for combat system
        self.is_enemy = True
        self.health: int = 40
        self.max_health: int = 40
        self.damage: int = 15  # Damage dealt to player on contact
        
        # Movement history buffer (stores (position, timestamp))
        self._movement_buffer: deque = deque(maxlen=300)  # ~5 seconds at 60fps
        self._current_time: float = 0.0
        
        # Target position (where we're moving toward)
        self._target_position: Optional[Tuple[float, float]] = None
        self.move_speed: float = 100.0
        
        # Visual state
        self._echo_phase: float = 0.0
        self._confusion: float = 0.0  # Increases with paradox
        
        # Track player reference
        self._player_last_pos: Optional[Tuple[float, float]] = None
        
        # Create causal node
        self.create_causal_node(paradox_weight=5.0)
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the Echo Walker's appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        center = (w // 2, h // 2)
        
        # Ethereal body with concentric rings
        for i in range(4):
            radius = w // 2 - i * 3
            alpha = 180 - i * 40
            color = (100 + i * 20, 180 + i * 15, 200 + i * 10, alpha)
            pygame.draw.circle(self.sprite, color, center, radius)
        
        # Inner glow
        pygame.draw.circle(self.sprite, (200, 255, 255, 200), center, w // 6)
        
        # Eye-like patterns
        pygame.draw.circle(self.sprite, (50, 100, 150), 
                          (w // 3, h // 3), 3)
        pygame.draw.circle(self.sprite, (50, 100, 150), 
                          (2 * w // 3, h // 3), 3)
    
    def record_player_position(self, player_pos: Tuple[float, float]) -> None:
        """
        Record the player's position for delayed echoing.
        
        Called each frame by the game.
        
        Args:
            player_pos: Current player position
        """
        # Only record if position changed significantly
        if self._player_last_pos is None:
            self._player_last_pos = player_pos
            self._movement_buffer.append((player_pos, self._current_time))
            return
        
        dx = player_pos[0] - self._player_last_pos[0]
        dy = player_pos[1] - self._player_last_pos[1]
        
        if abs(dx) > 5 or abs(dy) > 5:
            self._movement_buffer.append((player_pos, self._current_time))
            self._player_last_pos = player_pos
    
    def update(self, dt: float) -> None:
        """Update the Echo Walker."""
        if not self.exists:
            return
        
        self._current_time += dt
        self._echo_phase += dt * 2
        
        # Find position from echo_delay seconds ago
        self._update_echo_target()
        
        # Move toward target
        if self._target_position:
            self._move_toward_target(dt)
        
        # Confusion effect (from paradox)
        if self._confusion > 0:
            self._confusion = max(0, self._confusion - dt * 0.5)
            # Random jitter when confused
            if self._confusion > 0.5:
                jitter = math.sin(self._current_time * 20) * self._confusion * 3
                self.position = (self.x + jitter, self.y)
        
        super().update(dt)
    
    def _update_echo_target(self) -> None:
        """Find the target position from the movement buffer."""
        target_time = self._current_time - self.echo_delay
        
        # Find the position recorded closest to target_time
        best_pos = None
        best_diff = float('inf')
        
        for pos, timestamp in self._movement_buffer:
            diff = abs(timestamp - target_time)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos
        
        if best_pos:
            self._target_position = best_pos
    
    def _move_toward_target(self, dt: float) -> None:
        """Move toward the target position."""
        if not self._target_position:
            return
        
        tx, ty = self._target_position
        dx = tx - self.x
        dy = ty - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 3:
            return  # Close enough
        
        # Calculate speed (confused echo walkers move erratically)
        speed = self.move_speed * dt
        if self._confusion > 0:
            speed *= (1 - self._confusion * 0.5)
        
        if speed > distance:
            speed = distance
        
        self.position = (
            self.x + (dx / distance) * speed,
            self.y + (dy / distance) * speed
        )
    
    def apply_confusion(self, amount: float) -> None:
        """
        Apply confusion from paradox effects.
        
        Args:
            amount: Confusion amount (0-1)
        """
        self._confusion = min(1.0, self._confusion + amount)
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal changes."""
        if new_state == EntityState.DESTROYED:
            self.destroy()
    
    def take_damage(self, amount: int) -> bool:
        """
        Take damage from an attack.
        
        Args:
            amount: Amount of damage to take
            
        Returns:
            True if the enemy was defeated
        """
        self.health -= amount
        self._confusion = min(1.0, self._confusion + 0.3)  # Become confused when hit
        if self.health <= 0:
            self.health = 0
            EventSystem.emit(GameEvent.ENEMY_DEFEATED, {
                "entity_id": self.entity_id,
                "enemy_type": "echo_walker"
            })
            self.destroy()
            return True
        return False
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the Echo Walker with effects."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        # Pulsing glow effect
        glow_radius = int(self.width // 2 + math.sin(self._echo_phase) * 5)
        glow_alpha = int(100 + math.sin(self._echo_phase) * 50)
        
        glow_surface = pygame.Surface(
            (glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA
        )
        pygame.draw.circle(
            glow_surface, 
            (100, 200, 255, glow_alpha),
            (glow_radius + 10, glow_radius + 10),
            glow_radius + 5
        )
        surface.blit(glow_surface, 
                    (render_x + self.width // 2 - glow_radius - 10,
                     render_y + self.height // 2 - glow_radius - 10))
        
        # Echo trail (show previous positions)
        if self._target_position:
            trail_alpha = 80
            trail_surface = pygame.Surface(self.size, pygame.SRCALPHA)
            pygame.draw.circle(
                trail_surface,
                (100, 180, 200, trail_alpha),
                (self.width // 2, self.height // 2),
                self.width // 3
            )
            
            # Draw at target position (faded)
            tx = int(self._target_position[0] - ox)
            ty = int(self._target_position[1] - oy)
            surface.blit(trail_surface, (tx, ty))
        
        # Main sprite with confusion shake
        shake_x = int(math.sin(self._current_time * 30) * self._confusion * 5)
        shake_y = int(math.cos(self._current_time * 30) * self._confusion * 5)
        surface.blit(self.sprite, (render_x + shake_x, render_y + shake_y))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "echo_delay": self.echo_delay,
            "home_universe": self.home_universe.value
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'EchoWalker':
        """Deserialize from save data."""
        walker = cls(
            position=tuple(data["position"]),
            echo_delay=data.get("echo_delay", 2.0),
            home_universe=UniverseType(data.get("home_universe", "echo"))
        )
        walker.exists = data["exists"]
        return walker
