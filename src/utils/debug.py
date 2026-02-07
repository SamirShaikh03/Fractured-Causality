"""
Debug Utilities - Development and debugging tools.

Provides debug overlays, logging, and development helpers.
"""

import pygame
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import time


@dataclass
class DebugValue:
    """A debug value to display."""
    name: str
    getter: Callable[[], Any]
    format_str: str = "{}"


class DebugOverlay:
    """
    Debug overlay for development.
    
    Shows:
    - FPS counter
    - Custom debug values
    - Entity counts
    - Memory usage (optional)
    - Performance timers
    """
    
    def __init__(self):
        """Initialize the debug overlay."""
        pygame.font.init()
        self._font = pygame.font.Font(None, 20)
        
        # State
        self._visible: bool = False
        self._values: Dict[str, DebugValue] = {}
        
        # Performance tracking
        self._frame_times: List[float] = []
        self._max_frame_samples: int = 60
        self._last_frame_time: float = time.time()
        
        # Performance timers
        self._timers: Dict[str, float] = {}
        self._timer_starts: Dict[str, float] = {}
        
        # Log messages
        self._log_messages: List[str] = []
        self._max_log_messages: int = 10
    
    def toggle(self) -> bool:
        """Toggle visibility."""
        self._visible = not self._visible
        return self._visible
    
    def show(self) -> None:
        """Show the overlay."""
        self._visible = True
    
    def hide(self) -> None:
        """Hide the overlay."""
        self._visible = False
    
    def add_value(self, name: str, getter: Callable[[], Any],
                  format_str: str = "{}") -> None:
        """
        Add a debug value to display.
        
        Args:
            name: Display name
            getter: Function that returns the value
            format_str: Format string for the value
        """
        self._values[name] = DebugValue(name, getter, format_str)
    
    def remove_value(self, name: str) -> None:
        """Remove a debug value."""
        if name in self._values:
            del self._values[name]
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer."""
        self._timer_starts[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> float:
        """
        Stop a performance timer.
        
        Returns:
            Elapsed time in milliseconds
        """
        if name in self._timer_starts:
            elapsed = (time.perf_counter() - self._timer_starts[name]) * 1000
            self._timers[name] = elapsed
            return elapsed
        return 0.0
    
    def log(self, message: str) -> None:
        """Add a log message."""
        timestamp = time.strftime("%H:%M:%S")
        self._log_messages.append(f"[{timestamp}] {message}")
        
        # Trim old messages
        while len(self._log_messages) > self._max_log_messages:
            self._log_messages.pop(0)
    
    def update(self, dt: float) -> None:
        """Update the debug overlay."""
        # Track frame times
        current_time = time.time()
        frame_time = current_time - self._last_frame_time
        self._last_frame_time = current_time
        
        self._frame_times.append(frame_time)
        if len(self._frame_times) > self._max_frame_samples:
            self._frame_times.pop(0)
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the debug overlay.
        
        Args:
            surface: Target surface
        """
        if not self._visible:
            return
        
        x = 10
        y = 10
        line_height = 18
        
        # Background
        bg_width = 250
        bg_height = (len(self._values) + len(self._timers) + 
                    len(self._log_messages) + 5) * line_height + 20
        
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        surface.blit(bg_surface, (x - 5, y - 5))
        
        # Title
        title = self._font.render("DEBUG OVERLAY", True, (255, 255, 0))
        surface.blit(title, (x, y))
        y += line_height + 5
        
        # FPS
        fps = self._calculate_fps()
        fps_color = (0, 255, 0) if fps >= 55 else (255, 255, 0) if fps >= 30 else (255, 0, 0)
        fps_text = self._font.render(f"FPS: {fps:.1f}", True, fps_color)
        surface.blit(fps_text, (x, y))
        y += line_height
        
        # Frame time
        avg_frame_time = sum(self._frame_times) / max(1, len(self._frame_times)) * 1000
        ft_text = self._font.render(f"Frame Time: {avg_frame_time:.2f}ms", True, (200, 200, 200))
        surface.blit(ft_text, (x, y))
        y += line_height
        
        # Separator
        pygame.draw.line(surface, (100, 100, 100), (x, y), (x + bg_width - 10, y))
        y += 5
        
        # Custom values
        for value in self._values.values():
            try:
                val = value.getter()
                text = f"{value.name}: {value.format_str.format(val)}"
            except Exception as e:
                text = f"{value.name}: ERROR"
            
            label = self._font.render(text, True, (200, 200, 200))
            surface.blit(label, (x, y))
            y += line_height
        
        # Performance timers
        if self._timers:
            y += 5
            timer_title = self._font.render("Performance:", True, (255, 200, 100))
            surface.blit(timer_title, (x, y))
            y += line_height
            
            for name, elapsed in self._timers.items():
                color = (0, 255, 0) if elapsed < 5 else (255, 255, 0) if elapsed < 16 else (255, 0, 0)
                text = self._font.render(f"  {name}: {elapsed:.2f}ms", True, color)
                surface.blit(text, (x, y))
                y += line_height
        
        # Log messages
        if self._log_messages:
            y += 5
            log_title = self._font.render("Log:", True, (100, 200, 255))
            surface.blit(log_title, (x, y))
            y += line_height
            
            for msg in self._log_messages[-5:]:  # Show last 5
                text = self._font.render(msg[:40], True, (180, 180, 180))
                surface.blit(text, (x, y))
                y += line_height
    
    def _calculate_fps(self) -> float:
        """Calculate average FPS."""
        if not self._frame_times:
            return 0.0
        
        avg_frame_time = sum(self._frame_times) / len(self._frame_times)
        if avg_frame_time <= 0:
            return 0.0
        
        return 1.0 / avg_frame_time
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self._calculate_fps()
    
    def clear_log(self) -> None:
        """Clear log messages."""
        self._log_messages.clear()
    
    def clear_timers(self) -> None:
        """Clear performance timers."""
        self._timers.clear()
        self._timer_starts.clear()


# Global debug instance for convenience
_debug_instance: DebugOverlay = None


def get_debug() -> DebugOverlay:
    """Get the global debug overlay instance."""
    global _debug_instance
    if _debug_instance is None:
        _debug_instance = DebugOverlay()
    return _debug_instance


def debug_log(message: str) -> None:
    """Log a message to the debug overlay."""
    get_debug().log(message)


def debug_timer_start(name: str) -> None:
    """Start a debug timer."""
    get_debug().start_timer(name)


def debug_timer_stop(name: str) -> float:
    """Stop a debug timer and return elapsed time."""
    return get_debug().stop_timer(name)
