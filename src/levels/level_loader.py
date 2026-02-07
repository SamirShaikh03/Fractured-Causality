"""
Level Loader - Loads and manages game levels.

Handles level transitions, saves, and progress.
"""

from typing import Dict, Optional, Type, List

from .level_base import Level, LevelConfig
from ..multiverse.multiverse_manager import MultiverseManager
from ..entities.player import Player
from ..core.events import EventSystem, GameEvent


class LevelLoader:
    """
    Manages level loading and transitions.
    
    Features:
    - Registry of available levels
    - Level loading and unloading
    - Progress tracking
    - Save/load integration
    """
    
    def __init__(self, multiverse: MultiverseManager):
        """
        Initialize the level loader.
        
        Args:
            multiverse: The multiverse manager
        """
        self.multiverse = multiverse
        
        # Level registry (populated by register_level)
        self._level_classes: Dict[str, Type[Level]] = {}
        self._level_order: List[str] = []
        
        # Current state
        self.current_level: Optional[Level] = None
        self.current_level_id: str = ""
        
        # Progress
        self.completed_levels: List[str] = []
        self.best_times: Dict[str, float] = {}
        
        # Subscribe to events
        EventSystem.subscribe(GameEvent.LEVEL_COMPLETE, self._on_level_complete)
    
    def register_level(self, level_id: str, level_class: Type[Level]) -> None:
        """
        Register a level class.
        
        Args:
            level_id: Unique level identifier
            level_class: The Level subclass
        """
        self._level_classes[level_id] = level_class
        if level_id not in self._level_order:
            self._level_order.append(level_id)
    
    def load_level(self, level_id: str, player: Player) -> Optional[Level]:
        """
        Load a level.
        
        Args:
            level_id: Level to load
            player: The player entity
            
        Returns:
            The loaded level, or None if not found
        """
        # Unload current level
        if self.current_level:
            self.current_level.cleanup()
            self.current_level = None
        
        # Check if level exists
        if level_id not in self._level_classes:
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": f"Level '{level_id}' not found!",
                "type": "error"
            })
            return None
        
        # Reset multiverse
        self.multiverse.reset()
        
        # Create level instance
        level_class = self._level_classes[level_id]
        self.current_level = level_class(self.multiverse)
        self.current_level_id = level_id
        
        # Set up level
        self.current_level.setup(player)
        
        EventSystem.emit(GameEvent.UI_MESSAGE, {
            "message": f"Loading: {self.current_level.config.name}",
            "type": "info"
        })
        
        return self.current_level
    
    def reload_current_level(self, player: Player) -> Optional[Level]:
        """
        Reload the current level (for retry).
        
        Args:
            player: The player entity
            
        Returns:
            The reloaded level
        """
        if self.current_level_id:
            return self.load_level(self.current_level_id, player)
        return None
    
    def load_next_level(self, player: Player) -> Optional[Level]:
        """
        Load the next level in order.
        
        Args:
            player: The player entity
            
        Returns:
            The next level, or None if no more levels
        """
        if not self.current_level_id:
            # Load first level
            if self._level_order:
                return self.load_level(self._level_order[0], player)
            return None
        
        # Find current index
        try:
            current_index = self._level_order.index(self.current_level_id)
            next_index = current_index + 1
            
            if next_index < len(self._level_order):
                return self.load_level(self._level_order[next_index], player)
            else:
                # All levels complete!
                EventSystem.emit(GameEvent.GAME_COMPLETE, {
                    "completed_levels": len(self.completed_levels)
                })
                return None
                
        except ValueError:
            return None
    
    def get_level_count(self) -> int:
        """Get total number of levels."""
        return len(self._level_order)
    
    def get_completed_count(self) -> int:
        """Get number of completed levels."""
        return len(self.completed_levels)
    
    def is_level_unlocked(self, level_id: str) -> bool:
        """
        Check if a level is unlocked.
        
        Levels are unlocked if:
        - It's the first level
        - The previous level has been completed
        """
        if level_id not in self._level_order:
            return False
        
        index = self._level_order.index(level_id)
        
        if index == 0:
            return True
        
        previous_level = self._level_order[index - 1]
        return previous_level in self.completed_levels
    
    def _on_level_complete(self, data: dict) -> None:
        """Handle level completion."""
        level_id = data.get("level_id", "")
        time = data.get("time", 0.0)
        
        if level_id and level_id not in self.completed_levels:
            self.completed_levels.append(level_id)
        
        # Track best time
        if level_id:
            if level_id not in self.best_times or time < self.best_times[level_id]:
                self.best_times[level_id] = time
    
    def serialize(self) -> dict:
        """Serialize progress."""
        return {
            "current_level": self.current_level_id,
            "completed_levels": self.completed_levels,
            "best_times": self.best_times
        }
    
    def deserialize(self, data: dict) -> None:
        """Load saved progress."""
        self.current_level_id = data.get("current_level", "")
        self.completed_levels = data.get("completed_levels", [])
        self.best_times = data.get("best_times", {})
