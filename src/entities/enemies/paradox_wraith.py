"""
Paradox Wraith - An entity that only exists when paradox is high.

The Paradox Wraith is attracted to causal instability. It hunts
the player when paradox levels are elevated, but disappears when
reality stabilizes.
"""

import pygame
from typing import Tuple, Optional
import math
import random

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE, PARADOX_CRITICAL_THRESHOLD
from ...multiverse.causal_node import EntityState
from ...core.events import EventSystem, GameEvent


class ParadoxWraith(Entity):
    """
    Paradox Wraith - A creature born from broken causality.
    
    These entities only manifest when paradox exceeds a threshold.
    They hunt the player, and touching one forces a brief
    "ejection" from the current universe.
    
    Paradox Wraiths:
    - Only exist when paradox > 50%
    - Hunt the player actively
    - Phase through walls (reality doesn't bind them)
    - Touching ejects player from universe briefly
    - Disappear when paradox drops
    - Multiple can spawn at high paradox
    """
    
    def __init__(self, position: Tuple[float, float],
                 paradox_threshold: float = 50.0):
        """
        Initialize a Paradox Wraith.
        
        Args:
            position: Starting position
            paradox_threshold: Minimum paradox level to exist
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE, TILE_SIZE),
            color=(255, 50, 50),
            persistence=EntityPersistence.EXCLUSIVE,
            solid=False,  # Passes through walls
            interactive=False
        )
        super().__init__(config)
        
        # Paradox binding
        self.paradox_threshold: float = paradox_threshold
        self.current_paradox: float = 0.0
        self.is_manifested: bool = False
        
        # Mark as enemy for combat system
        self.is_enemy = True
        self.health: int = 75
        self.max_health: int = 75
        self.damage: int = 20  # Damage dealt to player on contact
        
        # Hunting behavior
        self.hunt_speed: float = 80.0
        self.detection_range: float = 300.0
        self._player_position: Optional[Tuple[float, float]] = None
        
        # Visual state
        self._phase: float = 0.0
        self._flicker_intensity: float = 0.0
        self._manifest_progress: float = 0.0
        
        # Spawn protection (can't touch player immediately)
        self._spawn_immunity: float = 0.0
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the Wraith's terrifying appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        center = (w // 2, h // 2)
        
        # Distorted, flame-like body
        for i in range(5):
            points = []
            num_points = 8
            for j in range(num_points):
                angle = (2 * math.pi * j) / num_points
                radius = w // 2 - i * 3 + random.randint(-3, 3)
                px = center[0] + math.cos(angle) * radius
                py = center[1] + math.sin(angle) * radius
                points.append((px, py))
            
            alpha = 200 - i * 35
            color = (255 - i * 30, 50 + i * 10, 50 + i * 20, alpha)
            if len(points) >= 3:
                pygame.draw.polygon(self.sprite, color, points)
        
        # Void eye
        pygame.draw.circle(self.sprite, (0, 0, 0), center, w // 5)
        pygame.draw.circle(self.sprite, (255, 100, 100), center, w // 8)
    
    def set_paradox_level(self, level: float) -> None:
        """
        Update the current paradox level.
        
        Called by the game when paradox changes.
        
        Args:
            level: Current paradox level (0-100)
        """
        self.current_paradox = level
        
        was_manifested = self.is_manifested
        self.is_manifested = level >= self.paradox_threshold
        
        if self.is_manifested and not was_manifested:
            # Just manifested
            self._manifest_progress = 0.0
            self._spawn_immunity = 1.0  # 1 second immunity
            self.exists = True
            self.visible = True
            
            EventSystem.emit(GameEvent.ENTITY_CREATED, {
                "entity_id": self.entity_id,
                "type": "paradox_wraith",
                "reason": "high_paradox"
            })
        
        elif not self.is_manifested and was_manifested:
            # Just de-manifested
            self._manifest_progress = 1.0  # Will fade out
            
            EventSystem.emit(GameEvent.ENTITY_DESTROYED, {
                "entity_id": self.entity_id,
                "type": "paradox_wraith",
                "reason": "paradox_reduced"
            })
    
    def set_player_position(self, pos: Tuple[float, float]) -> None:
        """Set the player's position for hunting."""
        self._player_position = pos
    
    def update(self, dt: float) -> None:
        """Update the Paradox Wraith."""
        self._phase += dt * 3
        
        # Update spawn immunity
        if self._spawn_immunity > 0:
            self._spawn_immunity = max(0, self._spawn_immunity - dt)
        
        # Manifestation animation
        if self.is_manifested and self._manifest_progress < 1.0:
            self._manifest_progress = min(1.0, self._manifest_progress + dt * 2)
            self.visible = True
            self.exists = self._manifest_progress > 0.3
        elif not self.is_manifested and self._manifest_progress > 0:
            self._manifest_progress = max(0, self._manifest_progress - dt * 2)
            if self._manifest_progress <= 0:
                self.exists = False
                self.visible = False
        
        if not self.is_manifested or not self.exists:
            return
        
        # Hunt player
        if self._player_position:
            self._hunt_player(dt)
        
        # Random flicker
        self._flicker_intensity = 0.5 + 0.5 * math.sin(self._phase * 5)
        
        super().update(dt)
    
    def _hunt_player(self, dt: float) -> None:
        """Move toward the player."""
        if not self._player_position:
            return
        
        px, py = self._player_position
        dx = px - self.x
        dy = py - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > self.detection_range:
            return  # Too far, wander instead
        
        if distance < 5:
            return  # On top of palyer
        
        # Move toward player with erratic motion
        speed = self.hunt_speed * dt
        
        # Add some erratic movement (paradox creatures are unstable)
        erratic_x = math.sin(self._phase * 7) * 20 * dt
        erratic_y = math.cos(self._phase * 7) * 20 * dt
        
        self.position = (
            self.x + (dx / distance) * speed + erratic_x,
            self.y + (dy / distance) * speed + erratic_y
        )
    
    def check_player_collision(self, player_rect: pygame.Rect) -> bool:
        """
        Check if wraith is touching the player.
        
        Args:
            player_rect: Player's bounding rectangle
            
        Returns:
            True if collision (and should eject player)
        """
        if not self.exists or not self.is_manifested:
            return False
        
        if self._spawn_immunity > 0:
            return False
        
        if self._manifest_progress < 0.8:
            return False  # Not fully manifested
        
        return self.get_rect().colliderect(player_rect)
    
    def take_damage(self, amount: int) -> bool:
        """
        Take damage from an attack.
        
        Args:
            amount: Amount of damage to take
            
        Returns:
            True if the enemy was defeated
        """
        self.health -= amount
        # Wraith flickers violently when hit
        self._flicker_intensity = 1.0
        if self.health <= 0:
            self.health = 0
            EventSystem.emit(GameEvent.ENEMY_DEFEATED, {
                "entity_id": self.entity_id,
                "enemy_type": "paradox_wraith"
            })
            self.destroy()
            return True
        return False
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the Paradox Wraith with distortion effects."""
        if not self.visible:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        # Manifestation effect
        if self._manifest_progress < 1.0:
            # Particles coalescing
            for i in range(8):
                angle = (2 * math.pi * i) / 8 + self._phase
                dist = (1 - self._manifest_progress) * 50
                px = render_x + self.width // 2 + math.cos(angle) * dist
                py = render_y + self.height // 2 + math.sin(angle) * dist
                
                particle_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
                alpha = int(self._manifest_progress * 200)
                pygame.draw.circle(particle_surface, (255, 50, 50, alpha), (4, 4), 4)
                surface.blit(particle_surface, (int(px) - 4, int(py) - 4))
        
        # Distortion aura
        aura_radius = int(self.width // 2 + math.sin(self._phase) * 10)
        aura_alpha = int(80 * self._flicker_intensity * self._manifest_progress)
        
        aura_surface = pygame.Surface(
            (aura_radius * 2 + 20, aura_radius * 2 + 20), pygame.SRCALPHA
        )
        pygame.draw.circle(
            aura_surface,
            (255, 50, 50, aura_alpha),
            (aura_radius + 10, aura_radius + 10),
            aura_radius + 5
        )
        surface.blit(aura_surface,
                    (render_x + self.width // 2 - aura_radius - 10,
                     render_y + self.height // 2 - aura_radius - 10))
        
        # Main sprite with flicker
        if self._manifest_progress > 0.3:
            temp_sprite = self.sprite.copy()
            temp_sprite.set_alpha(int(255 * self._manifest_progress * self._flicker_intensity))
            
            # Slight position jitter
            jitter_x = int(math.sin(self._phase * 10) * 2)
            jitter_y = int(math.cos(self._phase * 10) * 2)
            surface.blit(temp_sprite, (render_x + jitter_x, render_y + jitter_y))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "paradox_threshold": self.paradox_threshold,
            "is_manifested": self.is_manifested
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'ParadoxWraith':
        """Deserialize from save data."""
        wraith = cls(
            position=tuple(data["position"]),
            paradox_threshold=data.get("paradox_threshold", 50.0)
        )
        wraith.is_manifested = data.get("is_manifested", False)
        wraith.exists = data["exists"]
        return wraith
