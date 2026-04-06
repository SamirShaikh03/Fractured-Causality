import pygame
from typing import List

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator
from ..entities.player import Player
from ..entities.objects.causal_stone import CausalStone
from ..entities.objects.echo_switch import EchoSwitch
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.enemies.echo_walker import EchoWalker
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level02(Level):
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_02",
            name="The Echo Stone",
            width=22,
            height=17,
            starting_universe=UniverseType.PRIME,
            starting_position=(2, 8),
            required_keys=2,
            exit_position=(19, 8),
            has_prime=True,
            has_echo=True,
            has_fracture=False
        )
        super().__init__(config, multiverse)
        
        self.plates_pressed = {
            "plate_prime": False,
            "plate_echo": False
        }
    
    def _create_universes(self) -> None:

        prime_tiles = self._create_base_map()
        for x in range(9, 13):
            prime_tiles[4][x] = TileType.PIT
            prime_tiles[5][x] = TileType.PIT
        
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)

        echo_tiles = self._create_base_map()

        for x in range(9, 13):
            echo_tiles[11][x] = TileType.PIT
            echo_tiles[12][x] = TileType.PIT
        
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)
    
    def _create_base_map(self) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]
        
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h-1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w-1] = TileType.WALL
        for x in range(6, 16):
            tiles[3][x] = TileType.WALL
            tiles[6][x] = TileType.WALL
        for x in range(6, 16):
            tiles[10][x] = TileType.WALL
            tiles[13][x] = TileType.WALL
        for y in range(3, 14):
            if y not in [8]:
                tiles[y][6] = TileType.WALL
                tiles[y][15] = TileType.WALL
        
        tiles[8][7] = TileType.HAZARD 
        tiles[8][14] = TileType.HAZARD 
        for y in range(1, 3):
            tiles[y][17] = TileType.FLOOR
            tiles[y][18] = TileType.FLOOR
        
        for y in range(14, 16):
            tiles[y][17] = TileType.FLOOR
            tiles[y][18] = TileType.FLOOR
        
        return tiles
    
    def _place_entities(self) -> None:
        stone1 = CausalStone(
            position=(4 * TILE_SIZE, 8 * TILE_SIZE),
            stone_id="stone_01"
        )
        self.add_entity(stone1, [UniverseType.PRIME, UniverseType.ECHO])
        
        stone2 = CausalStone(
            position=(5 * TILE_SIZE, 8 * TILE_SIZE),
            stone_id="stone_02"
        )
        self.add_entity(stone2, [UniverseType.PRIME, UniverseType.ECHO])
        
        key1 = Key(
            position=(17 * TILE_SIZE, 2 * TILE_SIZE),
            key_id="key_02_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO])
        key2 = Key(
            position=(17 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_02_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO])
        
        door_upper = VariantDoor(
            position=(8 * TILE_SIZE, 4 * TILE_SIZE),
            door_id="door_upper",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_upper, [UniverseType.PRIME, UniverseType.ECHO])
        door_lower = VariantDoor(
            position=(8 * TILE_SIZE, 12 * TILE_SIZE),
            door_id="door_lower",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_lower, [UniverseType.PRIME, UniverseType.ECHO])
        
        switch_main = EchoSwitch(
            position=(10 * TILE_SIZE, 8 * TILE_SIZE),
            switch_id="switch_main",
            linked_entity_id="gate_main"
        )
        self.add_entity(switch_main, [UniverseType.PRIME, UniverseType.ECHO])

        gate_main = VariantDoor(
            position=(17 * TILE_SIZE, 8 * TILE_SIZE),
            door_id="gate_main",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate_main, [UniverseType.PRIME, UniverseType.ECHO])

        walker_intro = EchoWalker(
            position=(12 * TILE_SIZE, 8 * TILE_SIZE),
            echo_delay=1.6,
            home_universe=UniverseType.ECHO,
        )
        self.add_entity(walker_intro, [UniverseType.ECHO])
        exit_portal = ExitPortal(
            position=(19 * TILE_SIZE, 8 * TILE_SIZE),
            portal_id="exit_02",
            requires_keys=2
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO])
    
    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        causal_graph.add_dependency(
            source_id="switch_main",
            target_id="gate_main",
            operator=CausalOperator.ECHO
        )
        
        causal_graph.add_dependency(
            source_id="stone_01",
            target_id="door_upper",
            operator=CausalOperator.CONDITIONAL
        )
        
        causal_graph.add_dependency(
            source_id="stone_02",
            target_id="door_lower",
            operator=CausalOperator.CONDITIONAL
        )
    
    def update(self, dt: float) -> None:
        super().update(dt)
        
        for entity_list in self.entities.values():
            for entity in entity_list:
                if hasattr(entity, 'stone_id'):
                    stone_tile_x = int(entity.x / TILE_SIZE)
                    stone_tile_y = int(entity.y / TILE_SIZE)
                    
                    if stone_tile_x == 7 and stone_tile_y == 8:
                        if not self.plates_pressed["plate_prime"]:
                            self.plates_pressed["plate_prime"] = True
                            self._activate_plate("plate_prime")
                    
                    if stone_tile_x == 14 and stone_tile_y == 8:
                        if not self.plates_pressed["plate_echo"]:
                            self.plates_pressed["plate_echo"] = True
                            self._activate_plate("plate_echo")
    
    def _activate_plate(self, plate_id: str) -> None:
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": plate_id,
            "change": "pressed"
        })
        
        for entity_list in self.entities.values():
            for entity in entity_list:
                if plate_id == "plate_prime" and getattr(entity, 'door_id', '') == 'door_upper':
                    entity.open()
                elif plate_id == "plate_echo" and getattr(entity, 'door_id', '') == 'door_lower':
                    entity.open()
    
    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The Echo Stone... an artifact that exists across all realities.",
                "position": (2, 8)
            },
            {
                "trigger": "near_stone",
                "message": "Push the stone with [E]. It will move in ALL universes!",
                "position": (4, 8)
            },
            {
                "trigger": "see_plate",
                "message": "Pressure plates require weight. Place a stone to activate.",
                "position": (7, 8)
            }
        ]
