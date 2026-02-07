"""
Effects Manager - Manages visual effects.

Handles screen effects like transitions, flashes, and shakes.
"""

import pygame
from typing import Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class TransitionType(Enum):
    """Types of screen transitions."""
    FADE = auto()
    WIPE_LEFT = auto()
    WIPE_RIGHT = auto()
    CIRCLE = auto()
    PIXELATE = auto()


@dataclass
class ScreenFlash:
    """A screen flash effect."""
    color: Tuple[int, int, int]
    duration: float
    timer: float
    alpha: int = 255


@dataclass
class ScreenTransition:
    """A screen transition effect."""
    type: TransitionType
    duration: float
    timer: float
    is_out: bool  # True = transitioning out, False = transitioning in
    callback: Optional[Callable] = None


class EffectsManager:
    """
    Manages screen-wide visual effects.
    
    Features:
    - Screen flashes
    - Transitions (fade, wipe, etc.)
    - Color grading
    - Post-processing effects
    """
    
    def __init__(self):
        """Initialize the effects manager."""
        # Active effects
        self._flashes: list = []
        self._transition: Optional[ScreenTransition] = None
        
        # Persistent effects
        self._vignette_intensity: float = 0.0
        self._color_grade: Optional[Tuple[int, int, int]] = None
        self._saturation: float = 1.0
        
        # Effect surfaces
        self._flash_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self._transition_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self._vignette_surface = self._create_vignette()
    
    def _create_vignette(self) -> pygame.Surface:
        """Create a vignette overlay surface."""
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        max_radius = max(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Draw radial gradient
        for r in range(max_radius, 0, -5):
            alpha = int(150 * (1 - r / max_radius) ** 2)
            pygame.draw.circle(
                surface,
                (0, 0, 0, alpha),
                center,
                r,
                5
            )
        
        return surface
    
    def flash(self, color: Tuple[int, int, int],
              duration: float = 0.2,
              alpha: int = 255) -> None:
        """
        Create a screen flash effect.
        
        Args:
            color: Flash color
            duration: Flash duration
            alpha: Maximum alpha
        """
        flash = ScreenFlash(
            color=color,
            duration=duration,
            timer=duration,
            alpha=alpha
        )
        self._flashes.append(flash)
    
    def transition_out(self, transition_type: TransitionType,
                      duration: float = 0.5,
                      callback: Callable = None) -> None:
        """
        Start a transition out effect.
        
        Args:
            transition_type: Type of transition
            duration: Duration in seconds
            callback: Called when transition is complete
        """
        self._transition = ScreenTransition(
            type=transition_type,
            duration=duration,
            timer=0.0,
            is_out=True,
            callback=callback
        )
    
    def transition_in(self, transition_type: TransitionType,
                     duration: float = 0.5) -> None:
        """
        Start a transition in effect.
        
        Args:
            transition_type: Type of transition
            duration: Duration in seconds
        """
        self._transition = ScreenTransition(
            type=transition_type,
            duration=duration,
            timer=duration,
            is_out=False
        )
    
    def set_vignette(self, intensity: float) -> None:
        """Set vignette intensity (0-1)."""
        self._vignette_intensity = max(0, min(1, intensity))
    
    def set_color_grade(self, color: Optional[Tuple[int, int, int]]) -> None:
        """Set color grading overlay."""
        self._color_grade = color
    
    def update(self, dt: float) -> None:
        """
        Update all effects.
        
        Args:
            dt: Delta time
        """
        # Update flashes
        for flash in self._flashes[:]:
            flash.timer -= dt
            if flash.timer <= 0:
                self._flashes.remove(flash)
        
        # Update transition
        if self._transition:
            if self._transition.is_out:
                self._transition.timer += dt
                if self._transition.timer >= self._transition.duration:
                    if self._transition.callback:
                        self._transition.callback()
                    self._transition = None
            else:
                self._transition.timer -= dt
                if self._transition.timer <= 0:
                    self._transition = None
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render all effects to a surface.
        
        Args:
            surface: Target surface
        """
        # Render flashes
        for flash in self._flashes:
            progress = flash.timer / flash.duration
            alpha = int(flash.alpha * progress)
            
            self._flash_surface.fill((*flash.color, alpha))
            surface.blit(self._flash_surface, (0, 0))
        
        # Render transition
        if self._transition:
            self._render_transition(surface)
        
        # Render vignette
        if self._vignette_intensity > 0:
            vignette = self._vignette_surface.copy()
            vignette.set_alpha(int(255 * self._vignette_intensity))
            surface.blit(vignette, (0, 0))
        
        # Render color grade
        if self._color_grade:
            grade_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            grade_surface.fill((*self._color_grade, 30))
            surface.blit(grade_surface, (0, 0))
    
    def _render_transition(self, surface: pygame.Surface) -> None:
        """Render the current transition."""
        if not self._transition:
            return
        
        progress = self._transition.timer / self._transition.duration
        
        self._transition_surface.fill((0, 0, 0, 0))
        
        if self._transition.type == TransitionType.FADE:
            alpha = int(255 * progress)
            self._transition_surface.fill((0, 0, 0, alpha))
        
        elif self._transition.type == TransitionType.WIPE_LEFT:
            width = int(SCREEN_WIDTH * progress)
            pygame.draw.rect(
                self._transition_surface,
                (0, 0, 0, 255),
                (0, 0, width, SCREEN_HEIGHT)
            )
        
        elif self._transition.type == TransitionType.WIPE_RIGHT:
            width = int(SCREEN_WIDTH * progress)
            pygame.draw.rect(
                self._transition_surface,
                (0, 0, 0, 255),
                (SCREEN_WIDTH - width, 0, width, SCREEN_HEIGHT)
            )
        
        elif self._transition.type == TransitionType.CIRCLE:
            max_radius = max(SCREEN_WIDTH, SCREEN_HEIGHT)
            radius = int(max_radius * (1 - progress))
            
            # Fill black, then cut circle
            self._transition_surface.fill((0, 0, 0, 255))
            pygame.draw.circle(
                self._transition_surface,
                (0, 0, 0, 0),
                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                radius
            )
        
        surface.blit(self._transition_surface, (0, 0))
    
    def is_transitioning(self) -> bool:
        """Check if a transition is active."""
        return self._transition is not None
    
    def clear_effects(self) -> None:
        """Clear all temporary effects."""
        self._flashes.clear()
        self._transition = None
