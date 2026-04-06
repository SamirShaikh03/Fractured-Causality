from typing import Dict, Optional, Type, List

from .level_base import Level, LevelConfig
from ..multiverse.multiverse_manager import MultiverseManager
from ..entities.player import Player
from ..core.events import EventSystem, GameEvent


class LevelLoader:
    def __init__(self, multiverse: MultiverseManager):
        self.multiverse = multiverse

        self._level_classes: Dict[str, Type[Level]] = {}
        self._level_order: List[str] = []

        self.current_level: Optional[Level] = None
        self.current_level_id: str = ""

        self.completed_levels: List[str] = []
        self.best_times: Dict[str, float] = {}

        EventSystem.subscribe(GameEvent.LEVEL_COMPLETE, self._on_level_complete)
    
    def register_level(self, level_id: str, level_class: Type[Level]) -> None:
        self._level_classes[level_id] = level_class
        if level_id not in self._level_order:
            self._level_order.append(level_id)
    
    def load_level(self, level_id: str, player: Player) -> Optional[Level]:
        if self.current_level:
            self.current_level.cleanup()
            self.current_level = None

        if level_id not in self._level_classes:
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": f"Level '{level_id}' not found!",
                "type": "error"
            })
            return None

        self.multiverse.reset()

        level_class = self._level_classes[level_id]
        self.current_level = level_class(self.multiverse)
        self.current_level_id = level_id

        self.current_level.setup(player)

        EventSystem.emit(GameEvent.UI_MESSAGE, {
            "message": f"Loading: {self.current_level.config.name}",
            "type": "info"
        })

        return self.current_level
    
    def reload_current_level(self, player: Player) -> Optional[Level]:
        if self.current_level_id:
            return self.load_level(self.current_level_id, player)
        return None
    
    def load_next_level(self, player: Player) -> Optional[Level]:
        if not self.current_level_id:
            if self._level_order:
                return self.load_level(self._level_order[0], player)
            return None

        try:
            current_index = self._level_order.index(self.current_level_id)
            next_index = current_index + 1

            if next_index < len(self._level_order):
                return self.load_level(self._level_order[next_index], player)
            else:
                EventSystem.emit(GameEvent.GAME_COMPLETE, {
                    "completed_levels": len(self.completed_levels)
                })
                return None

        except ValueError:
            return None
    
    def get_level_count(self) -> int:
        return len(self._level_order)
    
    def get_completed_count(self) -> int:
        return len(self.completed_levels)
    
    def is_level_unlocked(self, level_id: str) -> bool:
        if level_id not in self._level_order:
            return False

        index = self._level_order.index(level_id)

        if index == 0:
            return True

        previous_level = self._level_order[index - 1]
        return previous_level in self.completed_levels
    
    def _on_level_complete(self, data: dict) -> None:
        level_id = data.get("level_id", "")
        time = data.get("time", 0.0)

        if level_id and level_id not in self.completed_levels:
            self.completed_levels.append(level_id)

        if level_id:
            if level_id not in self.best_times or time < self.best_times[level_id]:
                self.best_times[level_id] = time
    
    def serialize(self) -> dict:
        return {
            "current_level": self.current_level_id,
            "completed_levels": self.completed_levels,
            "best_times": self.best_times
        }
    
    def deserialize(self, data: dict) -> None:
        self.current_level_id = data.get("current_level", "")
        self.completed_levels = data.get("completed_levels", [])
        self.best_times = data.get("best_times", {})
