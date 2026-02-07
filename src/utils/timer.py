"""
Timer Utilities - Time-based utilities for gameplay.

Handles timers, cooldowns, and delayed actions.
"""

from typing import Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class Timer:
    """
    A simple countdown timer.
    
    Features:
    - Countdown to zero
    - Optional callback on complete
    - Loop option for repeating timers
    """
    duration: float
    callback: Optional[Callable] = None
    loop: bool = False
    autostart: bool = True
    
    # Internal state
    _time_remaining: float = field(default=0.0, init=False)
    _is_running: bool = field(default=False, init=False)
    _is_complete: bool = field(default=False, init=False)
    
    def __post_init__(self):
        self._time_remaining = self.duration
        if self.autostart:
            self.start()
    
    def start(self) -> None:
        """Start the timer."""
        self._is_running = True
        self._is_complete = False
        self._time_remaining = self.duration
    
    def stop(self) -> None:
        """Stop the timer."""
        self._is_running = False
    
    def pause(self) -> None:
        """Pause the timer."""
        self._is_running = False
    
    def resume(self) -> None:
        """Resume the timer."""
        if not self._is_complete:
            self._is_running = True
    
    def reset(self) -> None:
        """Reset the timer to initial state."""
        self._time_remaining = self.duration
        self._is_complete = False
        self._is_running = False
    
    def update(self, dt: float) -> bool:
        """
        Update the timer.
        
        Args:
            dt: Delta time
            
        Returns:
            True if timer just completed
        """
        if not self._is_running or self._is_complete:
            return False
        
        self._time_remaining -= dt
        
        if self._time_remaining <= 0:
            self._is_complete = True
            self._is_running = False
            
            if self.callback:
                self.callback()
            
            if self.loop:
                self._time_remaining = self.duration + self._time_remaining
                self._is_complete = False
                self._is_running = True
            
            return True
        
        return False
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_complete(self) -> bool:
        return self._is_complete
    
    @property
    def time_remaining(self) -> float:
        return max(0, self._time_remaining)
    
    @property
    def progress(self) -> float:
        """Get timer progress (0.0 to 1.0)."""
        if self.duration <= 0:
            return 1.0
        return 1.0 - (self._time_remaining / self.duration)


class Cooldown(Timer):
    """
    A cooldown timer that can be checked for availability.
    
    Usage:
        cooldown = Cooldown(1.0)  # 1 second cooldown
        if cooldown.is_ready():
            do_action()
            cooldown.trigger()
    """
    
    def __init__(self, duration: float):
        super().__init__(duration=duration, autostart=False)
        self._is_complete = True  # Start ready
    
    def is_ready(self) -> bool:
        """Check if cooldown is ready."""
        return self._is_complete or not self._is_running
    
    def trigger(self) -> bool:
        """
        Trigger the cooldown if ready.
        
        Returns:
            True if triggered, False if still on cooldown
        """
        if self.is_ready():
            self.start()
            self._is_complete = False
            return True
        return False


class TimerManager:
    """
    Manages multiple timers.
    
    Features:
    - Centralized timer updates
    - Named timer access
    - Auto-cleanup of completed non-looping timers
    """
    
    def __init__(self):
        self._timers: dict = {}
        self._anonymous_timers: List[Timer] = []
    
    def add(self, name: str, timer: Timer) -> Timer:
        """
        Add a named timer.
        
        Args:
            name: Timer name
            timer: Timer instance
            
        Returns:
            The added timer
        """
        self._timers[name] = timer
        return timer
    
    def create(self, name: str, duration: float,
               callback: Callable = None,
               loop: bool = False) -> Timer:
        """
        Create and add a new timer.
        
        Args:
            name: Timer name
            duration: Timer duration
            callback: Completion callback
            loop: Whether to loop
            
        Returns:
            The created timer
        """
        timer = Timer(
            duration=duration,
            callback=callback,
            loop=loop
        )
        return self.add(name, timer)
    
    def create_anonymous(self, duration: float,
                        callback: Callable = None) -> Timer:
        """
        Create an anonymous (auto-cleaned) timer.
        
        Args:
            duration: Timer duration
            callback: Completion callback
            
        Returns:
            The created timer
        """
        timer = Timer(
            duration=duration,
            callback=callback,
            loop=False
        )
        self._anonymous_timers.append(timer)
        return timer
    
    def get(self, name: str) -> Optional[Timer]:
        """Get a timer by name."""
        return self._timers.get(name)
    
    def remove(self, name: str) -> None:
        """Remove a timer by name."""
        if name in self._timers:
            del self._timers[name]
    
    def update(self, dt: float) -> None:
        """
        Update all timers.
        
        Args:
            dt: Delta time
        """
        # Update named timers
        for timer in self._timers.values():
            timer.update(dt)
        
        # Update anonymous timers and clean up completed
        for timer in self._anonymous_timers[:]:
            timer.update(dt)
            if timer.is_complete and not timer.loop:
                self._anonymous_timers.remove(timer)
    
    def clear(self) -> None:
        """Clear all timers."""
        self._timers.clear()
        self._anonymous_timers.clear()


def delay(duration: float, callback: Callable) -> Timer:
    """
    Simple delayed callback.
    
    Args:
        duration: Delay in seconds
        callback: Function to call
        
    Returns:
        Timer instance (must be updated manually or added to manager)
    """
    return Timer(duration=duration, callback=callback)
