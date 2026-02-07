"""
Universe Indicator - Visual indicator for the current universe.

Shows which universe the player is currently in with color and icon.
"""

import pygame
import math
from typing import Tuple

from ..core.settings import (
    SCREEN_WIDTH, COLOR_PRIME, COLOR_ECHO, COLOR_FRACTURE
)
from ..multiverse.universe import UniverseType


class UniverseIndicator:
    """
    Displays the current universe with visual flair.
    
    Features:
    - Animated universe icon
    - Color-coded display
    - Transition effects on switch
    """
    
    def __init__(self):
        """Initialize the universe indicator."""
        pygame.font.init()
        self._font = pygame.font.Font(None, 24)
        
        # Current state
        self._current_type: UniverseType = UniverseType.PRIME
        self._current_color: Tuple[int, int, int] = COLOR_PRIME
        
        # Animation
        self._rotation: float = 0.0
        self._scale: float = 1.0
        self._flash: float = 0.0
        
        # Position
        self._x = SCREEN_WIDTH - 100
        self._y = 20
        self._size = 60
    
    def set_universe(self, universe_type: UniverseType) -> None:
        """
        Set the current universe.
        
        Args:
            universe_type: The universe type
        """
        if universe_type != self._current_type:
            self._flash = 1.0
            self._scale = 1.3
        
        self._current_type = universe_type
        
        if universe_type == UniverseType.PRIME:
            self._current_color = COLOR_PRIME
        elif universe_type == UniverseType.ECHO:
            self._current_color = COLOR_ECHO
        else:
            self._current_color = COLOR_FRACTURE
    
    def update(self, dt: float) -> None:
        """
        Update animations.
        
        Args:
            dt: Delta time
        """
        # Rotate based on universe
        if self._current_type == UniverseType.PRIME:
            self._rotation += dt * 0.5  # Slow, stable
        elif self._current_type == UniverseType.ECHO:
            self._rotation += dt * 1.0  # Medium
        else:
            self._rotation += dt * 2.0  # Fast, chaotic
        
        # Decay flash
        if self._flash > 0:
            self._flash -= dt * 2.0
        
        # Decay scale
        if self._scale > 1.0:
            self._scale -= dt * 2.0
            if self._scale < 1.0:
                self._scale = 1.0
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the universe indicator.
        
        Args:
            surface: Target surface
        """
        size = int(self._size * self._scale)
        
        # Create indicator surface
        indicator = pygame.Surface((size, size), pygame.SRCALPHA)
        
        center = size // 2
        
        # Draw universe symbol based on type
        if self._current_type == UniverseType.PRIME:
            self._draw_prime_symbol(indicator, center, size)
        elif self._current_type == UniverseType.ECHO:
            self._draw_echo_symbol(indicator, center, size)
        else:
            self._draw_fracture_symbol(indicator, center, size)
        
        # Flash overlay
        if self._flash > 0:
            flash_alpha = int(150 * self._flash)
            flash_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            flash_surface.fill((*self._current_color, flash_alpha))
            indicator.blit(flash_surface, (0, 0))
        
        # Draw to screen
        pos_x = self._x - size // 2
        pos_y = self._y
        surface.blit(indicator, (pos_x, pos_y))
        
        # Label
        label = self._font.render(self._current_type.name, True, self._current_color)
        label_x = self._x - label.get_width() // 2
        surface.blit(label, (label_x, self._y + size + 5))
    
    def _draw_prime_symbol(self, surface: pygame.Surface, 
                           center: int, size: int) -> None:
        """Draw the Prime universe symbol (stable circle)."""
        color = self._current_color
        
        # Outer ring
        pygame.draw.circle(surface, color, (center, center), size // 2 - 4, 3)
        
        # Inner circle
        pygame.draw.circle(surface, color, (center, center), size // 4)
        
        # Stability lines
        for i in range(4):
            angle = self._rotation + i * (math.pi / 2)
            x1 = center + int(math.cos(angle) * (size // 4 + 5))
            y1 = center + int(math.sin(angle) * (size // 4 + 5))
            x2 = center + int(math.cos(angle) * (size // 2 - 6))
            y2 = center + int(math.sin(angle) * (size // 2 - 6))
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
    
    def _draw_echo_symbol(self, surface: pygame.Surface,
                          center: int, size: int) -> None:
        """Draw the Echo universe symbol (rippling circles)."""
        color = self._current_color
        
        # Multiple rings
        for i in range(3):
            radius = size // 4 + i * 8
            offset = math.sin(self._rotation + i * 0.5) * 2
            pygame.draw.circle(surface, color, 
                             (center + int(offset), center), 
                             radius, 2)
        
        # Center dot
        pygame.draw.circle(surface, color, (center, center), 4)
    
    def _draw_fracture_symbol(self, surface: pygame.Surface,
                              center: int, size: int) -> None:
        """Draw the Fracture universe symbol (broken/chaotic)."""
        color = self._current_color
        
        # Broken circle segments
        for i in range(6):
            angle = self._rotation * 2 + i * (math.pi / 3)
            # Random-ish offset for chaos
            chaos_offset = math.sin(self._rotation * 3 + i) * 3
            
            start_angle = angle - 0.3
            end_angle = angle + 0.3
            
            radius = size // 2 - 6 + int(chaos_offset)
            
            # Draw arc approximation with lines
            prev_x = center + int(math.cos(start_angle) * radius)
            prev_y = center + int(math.sin(start_angle) * radius)
            
            for j in range(5):
                t = (j + 1) / 5
                curr_angle = start_angle + t * (end_angle - start_angle)
                curr_x = center + int(math.cos(curr_angle) * radius)
                curr_y = center + int(math.sin(curr_angle) * radius)
                pygame.draw.line(surface, color, 
                               (prev_x, prev_y), (curr_x, curr_y), 2)
                prev_x, prev_y = curr_x, curr_y
        
        # Cracks through center
        for i in range(3):
            angle = self._rotation + i * (2 * math.pi / 3)
            x1 = center
            y1 = center
            x2 = center + int(math.cos(angle) * (size // 3))
            y2 = center + int(math.sin(angle) * (size // 3))
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
