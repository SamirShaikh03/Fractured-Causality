from enum import Enum, auto
from typing import Optional, Callable, Dict, Any
import pygame


class GameState(Enum):
    """Possible game states."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_SELECT = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()
    CREDITS = auto()


class StateManager:
    """
    Manages game state transitions and state-specific logic.
    
    The state manager maintains a stack of states, allowing for
    overlays (like pause menu over gameplay).
    
    Usage:
        manager = StateManager()
        manager.push_state(GameState.MENU)
        manager.push_state(GameState.PLAYING)
        manager.pop_state()  # Returns to MENU
    """
    
    def __init__(self):
        """Initialize the state manager."""
        self._state_stack: list[GameState] = []
        self._state_data: Dict[str, Any] = {}
        self._transition_callbacks: Dict[GameState, Callable] = {}
        self._enter_callbacks: Dict[GameState, Callable] = {}
        self._exit_callbacks: Dict[GameState, Callable] = {}
    
    @property
    def current_state(self) -> Optional[GameState]:
        """Get the current (top) state."""
        return self._state_stack[-1] if self._state_stack else None
    
    @property
    def previous_state(self) -> Optional[GameState]:
        """Get the previous state (one below current)."""
        return self._state_stack[-2] if len(self._state_stack) > 1 else None
    
    def push_state(self, state: GameState, data: Dict[str, Any] = None) -> None:
        """
        Push a new state onto the stack.
        
        Args:
            state: The state to push
            data: Optional data to pass to the state
        """
        # Call exit on current state
        if self.current_state and self.current_state in self._exit_callbacks:
            self._exit_callbacks[self.current_state]()
        
        # Push new state
        self._state_stack.append(state)
        self._state_data = data or {}
        
        # Call enter on new state
        if state in self._enter_callbacks:
            self._enter_callbacks[state](self._state_data)
    
    def pop_state(self) -> Optional[GameState]:
        """
        Pop the current state from the stack.
        
        Returns:
            The popped state, or None if stack was empty
        """
        if not self._state_stack:
            return None
        
        # Call exit on current state
        if self.current_state in self._exit_callbacks:
            self._exit_callbacks[self.current_state]()
        
        popped = self._state_stack.pop()
        
        # Call enter on new current state (if any)
        if self.current_state and self.current_state in self._enter_callbacks:
            self._enter_callbacks[self.current_state](self._state_data)
        
        return popped
    
    def change_state(self, state: GameState, data: Dict[str, Any] = None) -> None:
        """
        Replace the current state with a new one.
        
        Args:
            state: The new state
            data: Optional data to pass to the state
        """
        self.pop_state()
        self.push_state(state, data)
    
    def clear_states(self) -> None:
        """Clear all states from the stack."""
        while self._state_stack:
            self.pop_state()
    
    def set_state(self, state: GameState, data: Dict[str, Any] = None) -> None:
        """
        Clear all states and set a single state.
        
        Args:
            state: The state to set
            data: Optional data to pass to the state
        """
        self.clear_states()
        self.push_state(state, data)
    
    def on_enter(self, state: GameState, callback: Callable) -> None:
        """
        Register a callback for when a state is entered.
        
        Args:
            state: The state to register for
            callback: Function to call when entering this state
        """
        self._enter_callbacks[state] = callback
    
    def on_exit(self, state: GameState, callback: Callable) -> None:
        """
        Register a callback for when a state is exited.
        
        Args:
            state: The state to register for
            callback: Function to call when exiting this state
        """
        self._exit_callbacks[state] = callback
    
    def is_state(self, state: GameState) -> bool:
        """Check if the current state matches the given state."""
        return self.current_state == state
    
    def is_any_state(self, *states: GameState) -> bool:
        """Check if the current state matches any of the given states."""
        return self.current_state in states
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """Get data associated with the current state transition."""
        return self._state_data.get(key, default)
