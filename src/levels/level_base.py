import pygame
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..core.settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from ..multiverse.universe import Universe, UniverseType
from ..multiverse.multiverse_manager import MultiverseManager
from ..entities.player import Player
from ..core.events import EventSystem, GameEvent


@dataclass
class LevelConfig:
    level_id: str
    name: str
    width: int
    height: int
    starting_universe: UniverseType = UniverseType.PRIME
    starting_position: Tuple[int, int] = (2, 2)

    required_keys: int = 0
    exit_position: Tuple[int, int] = None

    has_prime: bool = True
    has_echo: bool = True
    has_fracture: bool = False


class Level(ABC):
    def __init__(self, config: LevelConfig, multiverse: MultiverseManager):
        self.config = config
        self.multiverse = multiverse

        self.is_complete: bool = False
        self.is_failed: bool = False
        self.keys_collected: int = 0
        self.completion_time: float = 0.0

        self.entities: Dict[UniverseType, List] = {
            UniverseType.PRIME: [],
            UniverseType.ECHO: [],
            UniverseType.FRACTURE: []
        }

        self.player: Optional[Player] = None

        EventSystem.subscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.subscribe(GameEvent.PORTAL_ENTERED, self._on_portal_entered)
        EventSystem.subscribe(GameEvent.PARADOX_ANNIHILATION, self._on_annihilation)
    
    def setup(self, player: Player) -> None:
        self.player = player

        start_x = self.config.starting_position[0] * TILE_SIZE
        start_y = self.config.starting_position[1] * TILE_SIZE
        player.set_position(start_x, start_y)

        self._create_universes()

        self._place_entities()

        self._setup_causality()

        self.multiverse.switch_universe(self.config.starting_universe)

        EventSystem.emit(GameEvent.LEVEL_STARTED, {
            "level_id": self.config.level_id,
            "level_name": self.config.name
        })
    
    @abstractmethod
    def _create_universes(self) -> None:
        pass
    
    @abstractmethod
    def _place_entities(self) -> None:
        pass
    
    @abstractmethod
    def _setup_causality(self) -> None:
        pass
    
    def add_entity(self, entity, universe_types: List[UniverseType] = None) -> None:
        if universe_types is None:
            universe_types = [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE]

        for u_type in universe_types:
            if u_type in self.entities:
                self.entities[u_type].append(entity)

                universe = self.multiverse.get_universe(u_type)
                if universe:
                    universe.entities.append(entity)

        if entity.causal_node:
            self.multiverse.causal_graph.add_node(entity.causal_node)
    
    def get_entities(self, universe_type: UniverseType = None) -> List:
        if universe_type is None:
            universe_type = self.multiverse.active_type

        return self.entities.get(universe_type, [])
    
    def update(self, dt: float) -> None:
        if self.is_complete or self.is_failed:
            return

        self.completion_time += dt

        self._check_win_condition()
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        active_type = self.multiverse.active_type

        for entity in self.entities.get(active_type, []):
            entity.render(surface, camera_offset)
    
    def _check_win_condition(self) -> None:
        pass
    
    def _on_item_collected(self, data: dict) -> None:
        item_type = data.get("item_type", "")

        if item_type == "key":
            self.keys_collected += 1

            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": f"Key collected! ({self.keys_collected}/{self.config.required_keys})",
                "type": "success"
            })
    
    def _on_portal_entered(self, data: dict) -> None:
        if self.keys_collected >= self.config.required_keys:
            self.is_complete = True

            EventSystem.emit(GameEvent.LEVEL_COMPLETE, {
                "level_id": self.config.level_id,
                "time": self.completion_time,
                "keys": self.keys_collected
            })
        else:
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": f"Need {self.config.required_keys - self.keys_collected} more keys!",
                "type": "warning"
            })
    
    def _on_annihilation(self, data: dict) -> None:
        self.is_failed = True

        EventSystem.emit(GameEvent.LEVEL_FAILED, {
            "level_id": self.config.level_id,
            "reason": "paradox_annihilation"
        })
    
    def cleanup(self) -> None:
        EventSystem.unsubscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.unsubscribe(GameEvent.PORTAL_ENTERED, self._on_portal_entered)
        EventSystem.unsubscribe(GameEvent.PARADOX_ANNIHILATION, self._on_annihilation)

        for entity_list in self.entities.values():
            entity_list.clear()
    
    def serialize(self) -> dict:
        return {
            "level_id": self.config.level_id,
            "is_complete": self.is_complete,
            "is_failed": self.is_failed,
            "keys_collected": self.keys_collected,
            "completion_time": self.completion_time,
            "entities": {
                u_type.name: [e.serialize() for e in entities]
                for u_type, entities in self.entities.items()
            }
        }
    
    @property
    def width_pixels(self) -> int:
        return self.config.width * TILE_SIZE
    
    @property
    def height_pixels(self) -> int:
        return self.config.height * TILE_SIZE
