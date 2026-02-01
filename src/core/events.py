"""
Event System - Pub/Sub pattern for decoupled communication.

This system allows game components to communicate without direct references.
Components subscribe to event types and receive notifications when those events occur.
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any
from dataclasses import dataclass


class GameEvent(Enum):
    """Enumeration of all game events."""
    
    # Universe events
    UNIVERSE_SWITCH_REQUESTED = auto()
    UNIVERSE_SWITCHED = auto()
    UNIVERSE_SWITCH_FAILED = auto()
    
    # Causal events
    CAUSAL_CHANGE = auto()
    CAUSAL_PROPAGATION_START = auto()
    CAUSAL_PROPAGATION_COMPLETE = auto()
    CAUSAL_LINK_BROKEN = auto()
    CAUSAL_LINK_CREATED = auto()
    
    # Paradox events
    PARADOX_CHANGED = auto()
    PARADOX_TIER_CHANGED = auto()
    PARADOX_CRITICAL = auto()
    PARADOX_ANNIHILATION = auto()
    
    # Entity events
    ENTITY_CREATED = auto()
    ENTITY_DESTROYED = auto()
    ENTITY_STATE_CHANGED = auto()
    ENTITY_INTERACTED = auto()
    ITEM_COLLECTED = auto()
    KEY_COLLECTED = auto()
    DOOR_OPENED = auto()
    SWITCH_TOGGLED = auto()
    PORTAL_ENTERED = auto()
    TREE_DESTROYED = auto()
    ENEMY_DEFEATED = auto()
    
    # Player events
    PLAYER_MOVED = auto()
    PLAYER_INTERACT = auto()
    PLAYER_ATTACK = auto()
    PLAYER_CAUSAL_SIGHT_TOGGLE = auto()
    CAUSAL_SIGHT_TOGGLED = PLAYER_CAUSAL_SIGHT_TOGGLE  # Alias
    PLAYER_PARADOX_PULSE = auto()
    PLAYER_DIED = auto()
    PLAYER_SPAWNED = auto()
    PLAYER_DAMAGED = auto()
    PLAYER_HEALED = auto()
    
    # Level events
    LEVEL_STARTED = auto()
    LEVEL_COMPLETED = auto()
    LEVEL_COMPLETE = LEVEL_COMPLETED  # Alias for backwards compatibility
    LEVEL_RESET = auto()
    LEVEL_FAILED = auto()
    
    # Game state events
    GAME_PAUSED = auto()
    GAME_RESUMED = auto()
    GAME_OVER = auto()
    GAME_COMPLETE = auto()  # All levels completed
    GAME_SAVED = auto()
    GAME_LOADED = auto()
    
    # UI events
    UI_MESSAGE = auto()
    UI_TUTORIAL = auto()


@dataclass
class EventData:
    """Container for event data."""
    event_type: GameEvent
    data: Dict[str, Any]
    source: Any = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the event data."""
        return self.data.get(key, default)


class EventSystem:
    """
    Global event system using publish/subscribe pattern.
    
    This allows loose coupling between game systems. Instead of direct
    method calls, systems emit events that interested parties receive.
    
    Usage:
        # Subscribe to an event
        EventSystem.subscribe(GameEvent.PARADOX_CHANGED, my_callback)
        
        # Emit an event
        EventSystem.emit(GameEvent.PARADOX_CHANGED, {"level": 50})
        
        # Unsubscribe
        EventSystem.unsubscribe(GameEvent.PARADOX_CHANGED, my_callback)
    """
    
    _subscribers: Dict[GameEvent, List[Callable[[EventData], None]]] = {}
    _event_queue: List[EventData] = []
    _processing: bool = False
    
    @classmethod
    def subscribe(cls, event_type: GameEvent, callback: Callable[[EventData], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event occurs. Receives EventData.
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        
        if callback not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(callback)
    
    @classmethod
    def unsubscribe(cls, event_type: GameEvent, callback: Callable[[EventData], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback to remove
        """
        if event_type in cls._subscribers:
            if callback in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(callback)
    
    @classmethod
    def emit(cls, event_type: GameEvent, data: Dict[str, Any] = None, source: Any = None) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: The type of event to emit
            data: Dictionary of event data
            source: The object that emitted the event
        """
        event_data = EventData(
            event_type=event_type,
            data=data or {},
            source=source
        )
        
        # Queue the event
        cls._event_queue.append(event_data)
        
        # Process if not already processing (prevents recursive issues)
        if not cls._processing:
            cls._process_queue()
    
    @classmethod
    def _process_queue(cls) -> None:
        """Process all queued events."""
        cls._processing = True
        
        while cls._event_queue:
            event_data = cls._event_queue.pop(0)
            
            if event_data.event_type in cls._subscribers:
                for callback in cls._subscribers[event_data.event_type]:
                    try:
                        callback(event_data)
                    except Exception as e:
                        print(f"Error in event callback: {e}")
        
        cls._processing = False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all subscribers and queued events."""
        cls._subscribers.clear()
        cls._event_queue.clear()
        cls._processing = False
    
    @classmethod
    def emit_immediate(cls, event_type: GameEvent, data: Dict[str, Any] = None, source: Any = None) -> None:
        """
        Emit an event immediately without queuing.
        Use sparingly - can cause issues with recursive events.
        
        Args:
            event_type: The type of event to emit
            data: Dictionary of event data
            source: The object that emitted the event
        """
        event_data = EventData(
            event_type=event_type,
            data=data or {},
            source=source
        )
        
        if event_type in cls._subscribers:
            for callback in cls._subscribers[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    print(f"Error in event callback: {e}")
