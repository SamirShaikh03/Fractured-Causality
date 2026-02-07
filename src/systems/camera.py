"""
Camera System - Manages the game camera.

Provides smooth following, shake effects, and bounds clamping.
"""

import pygame
import math
import random
from typing import Tuple, Optional
from dataclasses import dataclass

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


@dataclass
class CameraConfig:
    """Camera configuration."""
    follow_speed: float = 5.0  # How fast camera follows target
    deadzone_x: float = 50.0   # Pixels before camera moves horizontally
    deadzone_y: float = 50.0   # Pixels before camera moves vertically
    lookahead: float = 50.0    # Look ahead in direction of movement


class Camera:
    """
    Game camera with smooth following and effects.
    
    Features:
    - Smooth target following
    - Deadzone (camera doesn't move for small movements)
    - Screen shake
    - Zoom (optional)
    - Bounds clamping
    """
    
    def __init__(self, config: CameraConfig = None):
        """
        Initialize the camera.
        
        Args:
            config: Camera configuration
        """
        self.config = config or CameraConfig()
        
        # Position (top-left of view)
        self.x: float = 0.0
        self.y: float = 0.0
        
        # Target position
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        
        # Viewport size
        self.width: int = SCREEN_WIDTH
        self.height: int = SCREEN_HEIGHT
        
        # World bounds (for clamping)
        self.world_width: int = 0
        self.world_height: int = 0
        
        # Shake effect
        self._shake_intensity: float = 0.0
        self._shake_duration: float = 0.0
        self._shake_timer: float = 0.0
        self._shake_offset_x: float = 0.0
        self._shake_offset_y: float = 0.0
        
        # Zoom (1.0 = normal)
        self.zoom: float = 1.0
        
        # Following target
        self._follow_target = None
        self._last_target_dx: float = 0.0
        self._last_target_dy: float = 0.0
    
    def set_world_bounds(self, width: int, height: int) -> None:
        """
        Set the world bounds for camera clamping.
        
        Args:
            width: World width in pixels
            height: World height in pixels
        """
        self.world_width = width
        self.world_height = height
    
    def follow(self, target) -> None:
        """
        Set the camera to follow a target.
        
        Args:
            target: Entity to follow (must have x, y, width, height)
        """
        self._follow_target = target
    
    def stop_following(self) -> None:
        """Stop following the current target."""
        self._follow_target = None
    
    def center_on(self, x: float, y: float) -> None:
        """
        Immediately center camera on a position.
        
        Args:
            x: X position
            y: Y position
        """
        self.target_x = x - self.width / 2
        self.target_y = y - self.height / 2
        self.x = self.target_x
        self.y = self.target_y
        self._clamp_to_bounds()
    
    def shake(self, intensity: float, duration: float) -> None:
        """
        Start a screen shake effect.
        
        Args:
            intensity: Shake intensity in pixels
            duration: Duration in seconds
        """
        self._shake_intensity = intensity
        self._shake_duration = duration
        self._shake_timer = duration
    
    def update(self, dt: float) -> None:
        """
        Update the camera.
        
        Args:
            dt: Delta time
        """
        # Update target position from followed entity
        if self._follow_target:
            target = self._follow_target
            
            # Center of target
            center_x = target.x + target.width / 2
            center_y = target.y + target.height / 2
            
            # Calculate movement for lookahead
            dx = center_x - (self.target_x + self.width / 2)
            dy = center_y - (self.target_y + self.height / 2)
            
            # Apply deadzone
            target_x = center_x - self.width / 2
            target_y = center_y - self.height / 2
            
            if abs(dx) > self.config.deadzone_x:
                target_x += math.copysign(
                    self.config.lookahead * (abs(dx) / 100), dx
                )
            
            if abs(dy) > self.config.deadzone_y:
                target_y += math.copysign(
                    self.config.lookahead * (abs(dy) / 100), dy
                )
            
            self.target_x = target_x
            self.target_y = target_y
        
        # Smooth follow
        lerp_factor = 1 - math.exp(-self.config.follow_speed * dt)
        self.x += (self.target_x - self.x) * lerp_factor
        self.y += (self.target_y - self.y) * lerp_factor
        
        # Update shake
        if self._shake_timer > 0:
            self._shake_timer -= dt
            
            # Calculate shake offset
            progress = self._shake_timer / self._shake_duration
            intensity = self._shake_intensity * progress
            
            self._shake_offset_x = random.uniform(-intensity, intensity)
            self._shake_offset_y = random.uniform(-intensity, intensity)
        else:
            self._shake_offset_x = 0
            self._shake_offset_y = 0
        
        # Clamp to bounds
        self._clamp_to_bounds()
    
    def _clamp_to_bounds(self) -> None:
        """Clamp camera position to world bounds."""
        if self.world_width > 0:
            max_x = max(0, self.world_width - self.width)
            self.x = max(0, min(self.x, max_x))
            self.target_x = max(0, min(self.target_x, max_x))
        
        if self.world_height > 0:
            max_y = max(0, self.world_height - self.height)
            self.y = max(0, min(self.y, max_y))
            self.target_y = max(0, min(self.target_y, max_y))
    
    def get_offset(self) -> Tuple[int, int]:
        """
        Get the camera offset for rendering.
        
        Returns:
            (offset_x, offset_y) - subtract from world positions
        """
        return (
            int(self.x + self._shake_offset_x),
            int(self.y + self._shake_offset_y)
        )
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: World X position
            world_y: World Y position
            
        Returns:
            (screen_x, screen_y)
        """
        offset = self.get_offset()
        return (
            int((world_x - offset[0]) * self.zoom),
            int((world_y - offset[1]) * self.zoom)
        )
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X position
            screen_y: Screen Y position
            
        Returns:
            (world_x, world_y)
        """
        offset = self.get_offset()
        return (
            screen_x / self.zoom + offset[0],
            screen_y / self.zoom + offset[1]
        )
    
    def is_visible(self, x: float, y: float, 
                   width: float, height: float) -> bool:
        """
        Check if a rectangle is visible in the camera view.
        
        Args:
            x: World X
            y: World Y
            width: Width
            height: Height
            
        Returns:
            True if visible
        """
        offset = self.get_offset()
        
        # Check if rectangle overlaps with camera view
        return (x + width > offset[0] and
                x < offset[0] + self.width and
                y + height > offset[1] and
                y < offset[1] + self.height)
    
    def get_visible_rect(self) -> pygame.Rect:
        """Get the visible area as a Rect."""
        offset = self.get_offset()
        return pygame.Rect(offset[0], offset[1], self.width, self.height)
    
    def get_visible_tiles(self) -> Tuple[int, int, int, int]:
        """
        Get the range of visible tiles.
        
        Returns:
            (left, top, right, bottom) tile indices
        """
        offset = self.get_offset()
        
        left = max(0, int(offset[0] / TILE_SIZE))
        top = max(0, int(offset[1] / TILE_SIZE))
        right = int((offset[0] + self.width) / TILE_SIZE) + 1
        bottom = int((offset[1] + self.height) / TILE_SIZE) + 1
        
        return (left, top, right, bottom)
