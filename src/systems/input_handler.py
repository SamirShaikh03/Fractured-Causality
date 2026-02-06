"""
Input Handler - Manages all player input.

Handles keyboard input, key bindings, and input buffering.
"""

import pygame
from typing import Dict, Set, Callable, List
from dataclasses import dataclass
from enum import Enum, auto

from ..core.settings import (
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
    KEY_INTERACT, KEY_ATTACK, KEY_SWITCH_UNIVERSE, KEY_CAUSAL_SIGHT,
    KEY_PARADOX_PULSE, KEY_PAUSE
)
from ..core.events import EventSystem, GameEvent


class InputAction(Enum):
    """All possible input actions."""
    # Movement
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    
    # Actions
    INTERACT = auto()
    ATTACK = auto()
    SWITCH_UNIVERSE = auto()
    CAUSAL_SIGHT = auto()
    PARADOX_PULSE = auto()
    
    # UI
    PAUSE = auto()
    CONFIRM = auto()
    CANCEL = auto()
    
    # Debug (optional)
    DEBUG_TOGGLE = auto()


@dataclass
class InputState:
    """Current state of all inputs."""
    # Movement direction
    move_x: float = 0.0
    move_y: float = 0.0
    
    # Button states
    buttons_held: Set[InputAction] = None
    buttons_pressed: Set[InputAction] = None
    buttons_released: Set[InputAction] = None
    
    def __post_init__(self):
        if self.buttons_held is None:
            self.buttons_held = set()
        if self.buttons_pressed is None:
            self.buttons_pressed = set()
        if self.buttons_released is None:
            self.buttons_released = set()


class InputHandler:
    """
    Manages all player input.
    
    Features:
    - Key binding support
    - Input buffering for responsive controls
    - Action-based input (not raw keys)
    - Input state tracking (pressed, held, released)
    """
    
    def __init__(self):
        """Initialize the input handler."""
        # Key bindings: action -> list of keys
        self._bindings: Dict[InputAction, List[int]] = {
            InputAction.MOVE_UP: [KEY_UP, pygame.K_w],
            InputAction.MOVE_DOWN: [KEY_DOWN, pygame.K_s],
            InputAction.MOVE_LEFT: [KEY_LEFT, pygame.K_a],
            InputAction.MOVE_RIGHT: [KEY_RIGHT, pygame.K_d],
            InputAction.INTERACT: [KEY_INTERACT],
            InputAction.ATTACK: [KEY_ATTACK],
            InputAction.SWITCH_UNIVERSE: [KEY_SWITCH_UNIVERSE],
            InputAction.CAUSAL_SIGHT: [KEY_CAUSAL_SIGHT],
            InputAction.PARADOX_PULSE: [KEY_PARADOX_PULSE],
            InputAction.PAUSE: [KEY_PAUSE],
            InputAction.CONFIRM: [pygame.K_RETURN, pygame.K_SPACE],
            InputAction.CANCEL: [pygame.K_ESCAPE],
            InputAction.DEBUG_TOGGLE: [pygame.K_F3],
        }
        
        # Reverse mapping: key -> action
        self._key_to_action: Dict[int, InputAction] = {}
        self._rebuild_key_mapping()
        
        # Current state
        self._current_state = InputState()
        self._previous_state = InputState()
        
        # Input buffering (for responsive controls)
        self._input_buffer: List[InputAction] = []
        self._buffer_duration: float = 0.1  # seconds
        self._buffer_timers: Dict[InputAction, float] = {}
        
        # Enabled state
        self._enabled: bool = True
    
    def _rebuild_key_mapping(self) -> None:
        """Rebuild the key-to-action mapping."""
        self._key_to_action.clear()
        for action, keys in self._bindings.items():
            for key in keys:
                self._key_to_action[key] = action
    
    def bind_key(self, action: InputAction, key: int) -> None:
        """
        Bind a key to an action.
        
        Args:
            action: The action to bind
            key: The pygame key code
        """
        if key not in self._bindings[action]:
            self._bindings[action].append(key)
            self._rebuild_key_mapping()
    
    def unbind_key(self, action: InputAction, key: int) -> None:
        """
        Unbind a key from an action.
        
        Args:
            action: The action to unbind
            key: The pygame key code
        """
        if key in self._bindings[action]:
            self._bindings[action].remove(key)
            self._rebuild_key_mapping()
    
    def update(self, dt: float) -> InputState:
        """
        Update input state.
        
        Args:
            dt: Delta time
            
        Returns:
            Current input state
        """
        if not self._enabled:
            return InputState()
        
        # Save previous state
        self._previous_state = InputState(
            move_x=self._current_state.move_x,
            move_y=self._current_state.move_y,
            buttons_held=set(self._current_state.buttons_held),
            buttons_pressed=set(),
            buttons_released=set()
        )
        
        # Clear one-frame states
        self._current_state.buttons_pressed.clear()
        self._current_state.buttons_released.clear()
        
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Update movement
        self._current_state.move_x = 0.0
        self._current_state.move_y = 0.0
        
        if self._is_action_held(keys, InputAction.MOVE_LEFT):
            self._current_state.move_x -= 1.0
        if self._is_action_held(keys, InputAction.MOVE_RIGHT):
            self._current_state.move_x += 1.0
        if self._is_action_held(keys, InputAction.MOVE_UP):
            self._current_state.move_y -= 1.0
        if self._is_action_held(keys, InputAction.MOVE_DOWN):
            self._current_state.move_y += 1.0
        
        # Normalize diagonal movement
        if self._current_state.move_x != 0 and self._current_state.move_y != 0:
            self._current_state.move_x *= 0.7071  # 1/sqrt(2)
            self._current_state.move_y *= 0.7071
        
        # Update held buttons
        for action in InputAction:
            is_held = self._is_action_held(keys, action)
            was_held = action in self._previous_state.buttons_held
            
            if is_held and not was_held:
                # Just pressed
                self._current_state.buttons_pressed.add(action)
                self._current_state.buttons_held.add(action)
                self._add_to_buffer(action)
                
            elif is_held and was_held:
                # Still held
                self._current_state.buttons_held.add(action)
                
            elif not is_held and was_held:
                # Just released
                self._current_state.buttons_released.add(action)
                self._current_state.buttons_held.discard(action)
        
        # Update input buffer timers
        expired = []
        for action, timer in self._buffer_timers.items():
            self._buffer_timers[action] = timer - dt
            if self._buffer_timers[action] <= 0:
                expired.append(action)
        
        for action in expired:
            del self._buffer_timers[action]
            if action in self._input_buffer:
                self._input_buffer.remove(action)
        
        return self._current_state
    
    def _is_action_held(self, keys, action: InputAction) -> bool:
        """Check if any key for an action is held."""
        for key in self._bindings.get(action, []):
            if keys[key]:
                return True
        return False
    
    def _add_to_buffer(self, action: InputAction) -> None:
        """Add an action to the input buffer."""
        if action not in self._input_buffer:
            self._input_buffer.append(action)
            self._buffer_timers[action] = self._buffer_duration
    
    def consume_buffered(self, action: InputAction) -> bool:
        """
        Consume a buffered action if available.
        
        Args:
            action: The action to consume
            
        Returns:
            True if action was buffered and consumed
        """
        if action in self._input_buffer:
            self._input_buffer.remove(action)
            if action in self._buffer_timers:
                del self._buffer_timers[action]
            return True
        return False
    
    def is_pressed(self, action: InputAction) -> bool:
        """Check if action was just pressed this frame."""
        return action in self._current_state.buttons_pressed
    
    def is_held(self, action: InputAction) -> bool:
        """Check if action is currently held."""
        return action in self._current_state.buttons_held
    
    def is_released(self, action: InputAction) -> bool:
        """Check if action was just released this frame."""
        return action in self._current_state.buttons_released
    
    def get_movement(self) -> tuple:
        """Get movement vector."""
        return (self._current_state.move_x, self._current_state.move_y)
    
    def enable(self) -> None:
        """Enable input processing."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable input processing."""
        self._enabled = False
        self._current_state = InputState()
    
    def is_enabled(self) -> bool:
        """Check if input is enabled."""
        return self._enabled
