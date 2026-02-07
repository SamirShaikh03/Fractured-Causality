"""
Exit Portal - The level exit that must be reached in all universes.
"""

import pygame
from typing import Tuple
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE, COLOR_PORTAL
from ...core.events import EventSystem, GameEvent


class ExitPortal(Entity):
    """
    Exit Portal - The goal of each level.
    
    The exit portal exists in all universes (ANCHORED).
    The player must reach it to complete the level.
    
    Visual effects indicate the portal's stability and
    readiness for use.
    """
    
    def __init__(self, position: Tuple[float, float],
                 portal_id: str = None,
                 requires_keys: int = 0):
        """
        Initialize an Exit Portal.
        
        Args:
            position: Position
            portal_id: Unique identifier
            requires_keys: Number of keys required to use portal
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE + 16, TILE_SIZE + 16),
            color=COLOR_PORTAL,
            persistence=EntityPersistence.ANCHORED,
            solid=False,
            interactive=True,
            entity_id=portal_id or "exit_portal"
        )
        super().__init__(config)
        
        # Portal state
        self.is_active: bool = True
        self.player_nearby: bool = False
        self.stability: float = 1.0  # Affected by paradox
        self.requires_keys: int = requires_keys
        self.keys_collected: int = 0
        
        # Animation
        self._rotation: float = 0.0
        self._pulse: float = 0.0
        self._particle_timer: float = 0.0
        
        # Particles
        self._particles: list = []
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the portal's appearance."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        center = (w // 2, h // 2)
        
        # Outer ring
        pygame.draw.circle(self.sprite, (100, 50, 150), center, w // 2 - 2, 4)
        
        # Inner swirl (simplified - actual effect is animated)
        for i in range(3):
            radius = w // 2 - 8 - i * 6
            alpha = 180 - i * 40
            pygame.draw.circle(self.sprite, (150, 100, 200, alpha), center, radius, 2)
        
        # Center glow
        pygame.draw.circle(self.sprite, (200, 150, 255), center, w // 6)
    
    def on_interact(self, player) -> bool:
        """
        Handle player interaction (entering the portal).
        
        Args:
            player: The player entity
            
        Returns:
            True if player entered portal
        """
        if not self.is_active:
            return False
        
        EventSystem.emit(GameEvent.LEVEL_COMPLETED, {
            "portal_id": self.entity_id,
            "stability": self.stability
        })
        
        return True
    
    def check_player_overlap(self, player) -> bool:
        """
        Check if player is overlapping the portal.
        
        Args:
            player: Player entity
            
        Returns:
            True if overlapping
        """
        if not self.is_active:
            return False
        
        # Use center distance
        portal_center = self.center
        player_center = player.center
        
        dx = portal_center[0] - player_center[0]
        dy = portal_center[1] - player_center[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        threshold = self.width // 3
        
        if distance < threshold:
            if not self.player_nearby:
                self.player_nearby = True
                # Auto-trigger level complete
                return self.on_interact(player)
        else:
            self.player_nearby = False
        
        return False
    
    def set_stability(self, stability: float) -> None:
        """
        Set portal stability (affected by paradox).
        
        Args:
            stability: Stability value (0-1)
        """
        self.stability = max(0.1, min(1.0, stability))
    
    def update(self, dt: float) -> None:
        """Update the portal."""
        # Animation
        self._rotation += dt * 60 * self.stability
        self._pulse = (self._pulse + dt * 3) % (2 * math.pi)
        
        # Spawn particles
        self._particle_timer += dt
        if self._particle_timer > 0.1:
            self._particle_timer = 0
            self._spawn_particle()
        
        # Update particles
        for particle in self._particles[:]:
            particle["life"] -= dt
            particle["y"] -= particle["speed"] * dt
            particle["alpha"] = particle["life"] * 255
            
            if particle["life"] <= 0:
                self._particles.remove(particle)
        
        super().update(dt)
    
    def _spawn_particle(self) -> None:
        """Spawn a particle effect."""
        import random
        
        angle = random.random() * 2 * math.pi
        distance = random.random() * self.width // 2
        
        particle = {
            "x": self.x + self.width // 2 + math.cos(angle) * distance,
            "y": self.y + self.height // 2 + math.sin(angle) * distance,
            "speed": 30 + random.random() * 20,
            "life": 0.5 + random.random() * 0.5,
            "size": 2 + random.randint(0, 2),
            "alpha": 255
        }
        self._particles.append(particle)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the portal with effects."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        center_x = render_x + self.width // 2
        center_y = render_y + self.height // 2
        
        # Outer glow
        glow_radius = int(self.width // 2 + math.sin(self._pulse) * 5)
        glow_alpha = int(80 + 40 * math.sin(self._pulse))
        
        glow_surface = pygame.Surface(
            (glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA
        )
        
        # Stability affects color
        if self.stability > 0.7:
            glow_color = (150, 100, 255, glow_alpha)
        elif self.stability > 0.4:
            glow_color = (200, 100, 200, glow_alpha)
        else:
            glow_color = (255, 100, 100, glow_alpha)
        
        pygame.draw.circle(
            glow_surface, glow_color,
            (glow_radius + 10, glow_radius + 10), glow_radius
        )
        surface.blit(glow_surface,
                    (center_x - glow_radius - 10, center_y - glow_radius - 10))
        
        # Rotating rings
        for i in range(3):
            ring_radius = self.width // 2 - 4 - i * 8
            ring_surface = pygame.Surface(
                (ring_radius * 2 + 4, ring_radius * 2 + 4), pygame.SRCALPHA
            )
            
            # Draw arc
            ring_color = (150 + i * 30, 100, 200 + i * 20)
            start_angle = self._rotation / 60 + i * (2 * math.pi / 3)
            end_angle = start_angle + math.pi
            
            pygame.draw.arc(
                ring_surface, ring_color,
                (2, 2, ring_radius * 2, ring_radius * 2),
                start_angle, end_angle, 3
            )
            
            surface.blit(ring_surface,
                        (center_x - ring_radius - 2, center_y - ring_radius - 2))
        
        # Center portal (the void)
        pygame.draw.circle(surface, (30, 20, 50), (center_x, center_y), self.width // 5)
        
        core_pulse = int(self.width // 8 + math.sin(self._pulse * 2) * 3)
        pygame.draw.circle(surface, (100, 80, 150), (center_x, center_y), core_pulse)
        
        # Particles
        for particle in self._particles:
            px = int(particle["x"] - ox)
            py = int(particle["y"] - oy)
            
            particle_surface = pygame.Surface(
                (particle["size"] * 2, particle["size"] * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                particle_surface, 
                (200, 150, 255, int(particle["alpha"])),
                (particle["size"], particle["size"]), 
                particle["size"]
            )
            surface.blit(particle_surface, (px - particle["size"], py - particle["size"]))
        
        # Inactive overlay
        if not self.is_active:
            overlay = pygame.Surface(self.size, pygame.SRCALPHA)
            overlay.fill((50, 50, 50, 180))
            surface.blit(overlay, (render_x, render_y))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "is_active": self.is_active,
            "stability": self.stability
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'ExitPortal':
        """Deserialize from save data."""
        portal = cls(
            position=tuple(data["position"]),
            portal_id=data["entity_id"]
        )
        portal.is_active = data.get("is_active", True)
        portal.stability = data.get("stability", 1.0)
        return portal
