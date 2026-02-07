"""
Animation System - Manages sprite animations.

Provides frame-based animation with state machines.
"""

import pygame
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class AnimationFrame:
    """A single frame of animation."""
    surface: pygame.Surface
    duration: float  # Duration in seconds
    offset: Tuple[int, int] = (0, 0)  # Render offset
    event: str = None  # Optional event to trigger


@dataclass
class Animation:
    """An animation sequence."""
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    next_animation: str = None  # Animation to play after (if not looping)
    
    def get_duration(self) -> float:
        """Get total animation duration."""
        return sum(f.duration for f in self.frames)


class AnimationState(Enum):
    """Common animation states."""
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    ATTACK = "attack"
    HURT = "hurt"
    DEATH = "death"
    INTERACT = "interact"
    SPECIAL = "special"


class AnimationPlayer:
    """
    Plays animations for a single entity.
    
    Features:
    - Frame-based animation playback
    - State machine for animation transitions
    - Animation callbacks/events
    - Speed control
    """
    
    def __init__(self):
        """Initialize the animation player."""
        # Registered animations
        self._animations: Dict[str, Animation] = {}
        
        # Current state
        self._current_animation: Optional[Animation] = None
        self._current_frame_index: int = 0
        self._frame_timer: float = 0.0
        self._is_playing: bool = False
        self._is_finished: bool = False
        
        # Speed multiplier
        self.speed: float = 1.0
        
        # Direction (for flipping)
        self.facing_right: bool = True
        
        # Callbacks
        self._on_frame: Optional[Callable[[AnimationFrame], None]] = None
        self._on_animation_end: Optional[Callable[[str], None]] = None
    
    def add_animation(self, animation: Animation) -> None:
        """
        Register an animation.
        
        Args:
            animation: The animation to add
        """
        self._animations[animation.name] = animation
    
    def create_animation(self, name: str, 
                        sprite_sheet: pygame.Surface,
                        frame_count: int,
                        frame_width: int,
                        frame_height: int,
                        frame_duration: float,
                        loop: bool = True,
                        row: int = 0) -> Animation:
        """
        Create an animation from a sprite sheet.
        
        Args:
            name: Animation name
            sprite_sheet: Source sprite sheet
            frame_count: Number of frames
            frame_width: Width of each frame
            frame_height: Height of each frame
            frame_duration: Duration of each frame
            loop: Whether animation loops
            row: Row in sprite sheet (for multi-row sheets)
            
        Returns:
            Created animation
        """
        frames = []
        
        for i in range(frame_count):
            # Extract frame from sprite sheet
            rect = pygame.Rect(
                i * frame_width,
                row * frame_height,
                frame_width,
                frame_height
            )
            
            frame_surface = pygame.Surface(
                (frame_width, frame_height),
                pygame.SRCALPHA
            )
            frame_surface.blit(sprite_sheet, (0, 0), rect)
            
            frames.append(AnimationFrame(
                surface=frame_surface,
                duration=frame_duration
            ))
        
        animation = Animation(name=name, frames=frames, loop=loop)
        self.add_animation(animation)
        
        return animation
    
    def create_simple_animation(self, name: str,
                               surfaces: List[pygame.Surface],
                               frame_duration: float,
                               loop: bool = True) -> Animation:
        """
        Create an animation from a list of surfaces.
        
        Args:
            name: Animation name
            surfaces: List of frame surfaces
            frame_duration: Duration of each frame
            loop: Whether animation loops
            
        Returns:
            Created animation
        """
        frames = [
            AnimationFrame(surface=s, duration=frame_duration)
            for s in surfaces
        ]
        
        animation = Animation(name=name, frames=frames, loop=loop)
        self.add_animation(animation)
        
        return animation
    
    def play(self, name: str, restart: bool = False) -> bool:
        """
        Start playing an animation.
        
        Args:
            name: Animation name
            restart: Whether to restart if already playing
            
        Returns:
            True if animation started
        """
        if name not in self._animations:
            return False
        
        animation = self._animations[name]
        
        # Check if already playing this animation
        if self._current_animation == animation and not restart:
            return True
        
        self._current_animation = animation
        self._current_frame_index = 0
        self._frame_timer = 0.0
        self._is_playing = True
        self._is_finished = False
        
        return True
    
    def stop(self) -> None:
        """Stop the current animation."""
        self._is_playing = False
    
    def resume(self) -> None:
        """Resume the current animation."""
        self._is_playing = True
    
    def update(self, dt: float) -> None:
        """
        Update the animation.
        
        Args:
            dt: Delta time
        """
        if not self._is_playing or not self._current_animation:
            return
        
        if self._is_finished:
            return
        
        # Update timer
        self._frame_timer += dt * self.speed
        
        # Get current frame
        frames = self._current_animation.frames
        if self._current_frame_index >= len(frames):
            return
        
        current_frame = frames[self._current_frame_index]
        
        # Check if frame is complete
        while self._frame_timer >= current_frame.duration:
            self._frame_timer -= current_frame.duration
            
            # Trigger frame event
            if current_frame.event and self._on_frame:
                self._on_frame(current_frame)
            
            # Next frame
            self._current_frame_index += 1
            
            if self._current_frame_index >= len(frames):
                # Animation complete
                if self._current_animation.loop:
                    self._current_frame_index = 0
                else:
                    self._is_finished = True
                    self._current_frame_index = len(frames) - 1
                    
                    # Trigger end callback
                    if self._on_animation_end:
                        self._on_animation_end(self._current_animation.name)
                    
                    # Transition to next animation
                    if self._current_animation.next_animation:
                        self.play(self._current_animation.next_animation)
                    
                    return
            
            current_frame = frames[self._current_frame_index]
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """
        Get the current animation frame surface.
        
        Returns:
            Current frame surface, or None
        """
        if not self._current_animation:
            return None
        
        frames = self._current_animation.frames
        if not frames or self._current_frame_index >= len(frames):
            return None
        
        surface = frames[self._current_frame_index].surface
        
        # Flip if facing left
        if not self.facing_right:
            surface = pygame.transform.flip(surface, True, False)
        
        return surface
    
    def get_current_offset(self) -> Tuple[int, int]:
        """Get the current frame's render offset."""
        if not self._current_animation:
            return (0, 0)
        
        frames = self._current_animation.frames
        if not frames or self._current_frame_index >= len(frames):
            return (0, 0)
        
        return frames[self._current_frame_index].offset
    
    def is_playing(self, name: str = None) -> bool:
        """
        Check if an animation is playing.
        
        Args:
            name: Animation name (None to check any)
            
        Returns:
            True if playing
        """
        if not self._is_playing:
            return False
        
        if name is None:
            return True
        
        return (self._current_animation and 
                self._current_animation.name == name)
    
    def is_finished(self) -> bool:
        """Check if current animation is finished."""
        return self._is_finished
    
    def set_on_frame(self, callback: Callable[[AnimationFrame], None]) -> None:
        """Set the frame event callback."""
        self._on_frame = callback
    
    def set_on_animation_end(self, callback: Callable[[str], None]) -> None:
        """Set the animation end callback."""
        self._on_animation_end = callback


class AnimationSystem:
    """
    System for managing multiple animation players.
    
    Provides centralized animation management and
    shared animation resources.
    """
    
    def __init__(self):
        """Initialize the animation system."""
        # Shared animation templates
        self._templates: Dict[str, Animation] = {}
        
        # Active players
        self._players: List[AnimationPlayer] = []
    
    def create_player(self) -> AnimationPlayer:
        """
        Create a new animation player.
        
        Returns:
            New animation player
        """
        player = AnimationPlayer()
        self._players.append(player)
        return player
    
    def remove_player(self, player: AnimationPlayer) -> None:
        """Remove an animation player."""
        if player in self._players:
            self._players.remove(player)
    
    def register_template(self, animation: Animation) -> None:
        """
        Register a shared animation template.
        
        Args:
            animation: Animation template
        """
        self._templates[animation.name] = animation
    
    def get_template(self, name: str) -> Optional[Animation]:
        """Get a registered template."""
        return self._templates.get(name)
    
    def update(self, dt: float) -> None:
        """
        Update all animation players.
        
        Args:
            dt: Delta time
        """
        for player in self._players:
            player.update(dt)
    
    def create_color_flash_frames(self, base_surface: pygame.Surface,
                                  flash_color: Tuple[int, int, int],
                                  frame_count: int = 4) -> List[pygame.Surface]:
        """
        Create flash animation frames (for damage effects).
        
        Args:
            base_surface: Base sprite surface
            flash_color: Color to flash
            frame_count: Number of frames
            
        Returns:
            List of flash frames
        """
        frames = []
        
        for i in range(frame_count):
            # Alternate between base and flash
            if i % 2 == 0:
                frames.append(base_surface.copy())
            else:
                # Create tinted version
                flash_surface = base_surface.copy()
                flash_surface.fill(flash_color, special_flags=pygame.BLEND_ADD)
                frames.append(flash_surface)
        
        return frames
