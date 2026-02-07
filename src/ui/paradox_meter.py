"""
Paradox Meter - Visual display of the current paradox level.

Shows the player how close they are to reality collapse.
"""

import pygame
import math
from typing import Tuple

from ..core.settings import (
    PARADOX_STABLE, PARADOX_UNSTABLE, PARADOX_CRITICAL, PARADOX_COLLAPSE
)


class ParadoxMeter:
    """
    Animated paradox level display.
    
    Features:
    - Color-coded warning levels
    - Pulsing at critical levels
    - Particle effects at high paradox
    """
    
    def __init__(self, x: int = 20, y: int = 20, 
                 width: int = 200, height: int = 30):
        """
        Initialize the paradox meter.
        
        Args:
            x: X position
            y: Y position
            width: Meter width
            height: Meter height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # State
        self._level: float = 0.0
        self._target_level: float = 0.0
        
        # Animation
        self._pulse: float = 0.0
        self._shake: float = 0.0
        
        # Particles
        self._particles: list = []
        
        # Fonts
        pygame.font.init()
        self._font = pygame.font.Font(None, 22)
    
    def set_level(self, level: float) -> None:
        """
        Set the paradox level.
        
        Args:
            level: Paradox level (0-100)
        """
        self._target_level = max(0.0, min(100.0, level))
        
        # Spawn particles at high levels
        if level > PARADOX_UNSTABLE:
            self._spawn_particles(int((level - PARADOX_UNSTABLE) / 20))
    
    def _spawn_particles(self, count: int) -> None:
        """Spawn paradox particles."""
        import random
        
        for _ in range(count):
            particle = {
                'x': self.x + random.uniform(0, self.width),
                'y': self.y + self.height / 2,
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-50, -20),
                'life': random.uniform(0.5, 1.0),
                'size': random.uniform(2, 5)
            }
            self._particles.append(particle)
    
    def update(self, dt: float) -> None:
        """
        Update animations.
        
        Args:
            dt: Delta time
        """
        # Smooth level change
        diff = self._target_level - self._level
        self._level += diff * dt * 5.0
        
        # Update pulse based on level
        if self._level > PARADOX_CRITICAL:
            self._pulse += dt * 8.0  # Fast pulse
            self._shake = math.sin(self._pulse * 10) * 3
        elif self._level > PARADOX_UNSTABLE:
            self._pulse += dt * 4.0  # Medium pulse
            self._shake = math.sin(self._pulse * 5) * 1
        else:
            self._pulse = 0.0
            self._shake = 0.0
        
        # Update particles
        for particle in self._particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 100 * dt  # Gravity
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self._particles.remove(particle)
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the paradox meter.
        
        Args:
            surface: Target surface
        """
        x = int(self.x + self._shake)
        y = self.y
        
        # Background
        bg_rect = pygame.Rect(x - 2, y - 2, self.width + 4, self.height + 4)
        pygame.draw.rect(surface, (20, 20, 30), bg_rect, border_radius=6)
        
        # Determine color based on level
        color = self._get_level_color()
        
        # Fill
        fill_width = int(self.width * (self._level / 100))
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.height)
            
            # Add pulsing glow at high levels
            if self._level > PARADOX_UNSTABLE:
                pulse_factor = abs(math.sin(self._pulse)) * 0.3
                glow_color = tuple(
                    min(255, int(c * (1 + pulse_factor))) 
                    for c in color
                )
            else:
                glow_color = color
            
            pygame.draw.rect(surface, glow_color, fill_rect, border_radius=4)
        
        # Border (changes color at high paradox)
        border_color = (100, 100, 120)
        if self._level > PARADOX_CRITICAL:
            pulse_val = abs(math.sin(self._pulse))
            border_color = (
                int(100 + 155 * pulse_val),
                int(50 * (1 - pulse_val)),
                int(50 * (1 - pulse_val))
            )
        
        pygame.draw.rect(surface, border_color, bg_rect, 2, border_radius=6)
        
        # Render particles
        for particle in self._particles:
            alpha = int(255 * (particle['life']))
            size = int(particle['size'] * particle['life'])
            
            if size > 0:
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf, 
                    (*color, alpha),
                    (size, size), size
                )
                surface.blit(particle_surf, 
                           (int(particle['x'] - size), int(particle['y'] - size)))
        
        # Label
        label = self._font.render("PARADOX", True, (180, 180, 180))
        surface.blit(label, (x + 5, y + self.height // 2 - label.get_height() // 2))
        
        # Level text
        level_text = f"{int(self._level)}%"
        level = self._font.render(level_text, True, (255, 255, 255))
        surface.blit(level, (x + self.width - level.get_width() - 5,
                            y + self.height // 2 - level.get_height() // 2))
        
        # Status text
        status = self._get_status_text()
        if status:
            status_surface = self._font.render(status, True, color)
            surface.blit(status_surface, (x, y + self.height + 5))
    
    def _get_level_color(self) -> Tuple[int, int, int]:
        """Get color based on paradox level."""
        if self._level < PARADOX_STABLE:
            return (80, 200, 80)  # Green - Stable
        elif self._level < PARADOX_UNSTABLE:
            # Lerp green to yellow
            t = (self._level - PARADOX_STABLE) / (PARADOX_UNSTABLE - PARADOX_STABLE)
            return (
                int(80 + (200 - 80) * t),
                200,
                int(80 * (1 - t))
            )
        elif self._level < PARADOX_CRITICAL:
            # Lerp yellow to orange
            t = (self._level - PARADOX_UNSTABLE) / (PARADOX_CRITICAL - PARADOX_UNSTABLE)
            return (
                200,
                int(200 - 60 * t),
                int(40 * t)
            )
        elif self._level < PARADOX_COLLAPSE:
            # Lerp orange to red
            t = (self._level - PARADOX_CRITICAL) / (PARADOX_COLLAPSE - PARADOX_CRITICAL)
            return (
                int(200 + 55 * t),
                int(140 - 100 * t),
                40
            )
        else:
            # Pulsing red
            return (255, 40, 40)
    
    def _get_status_text(self) -> str:
        """Get status text based on level."""
        if self._level < PARADOX_STABLE:
            return "STABLE"
        elif self._level < PARADOX_UNSTABLE:
            return "UNSTABLE"
        elif self._level < PARADOX_CRITICAL:
            return "CRITICAL"
        elif self._level < PARADOX_COLLAPSE:
            return "COLLAPSE IMMINENT"
        else:
            return "ANNIHILATION"
