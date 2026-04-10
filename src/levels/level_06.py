import pygame
from typing import List

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator
from ..entities.objects.echo_switch import EchoSwitch
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.enemies.echo_walker import EchoWalker
from ..entities.enemies.paradox_wraith import ParadoxWraith
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level06(Level):
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_06",
            name="Paradox Chamber",
            width=22,
            height=18,
            starting_universe=UniverseType.PRIME,
            starting_position=(1, 9),
            required_keys=3,
            exit_position=(20, 9),
            has_prime=True,
            has_echo=True,
            has_fracture=True
        )
        super().__init__(config, multiverse)

    def _create_universes(self) -> None:
        prime_tiles = self._create_lab_map("prime")
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)

        echo_tiles = self._create_lab_map("echo")
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)

        fracture_tiles = self._create_lab_map("fracture")
        fracture = Universe(
            universe_type=UniverseType.FRACTURE,
            width=self.config.width,
            height=self.config.height
        )
        fracture.tilemap.tiles = fracture_tiles
        self.multiverse.add_universe(fracture)

    def _create_lab_map(self, variant: str) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        for y in range(1, h - 1):
            if y not in [4, 5, 9, 12, 13]: 
                tiles[y][7] = TileType.WALL
            if y not in [4, 5, 9, 12, 13]:
                tiles[y][14] = TileType.WALL
        for x in range(1, w - 1):
            if x not in [3, 4, 10, 11, 17, 18]:
                tiles[6][x] = TileType.WALL
            if x not in [3, 4, 10, 11, 17, 18]:
                tiles[12][x] = TileType.WALL
        if variant == "prime":
            for y in range(13, 16):
                for x in range(2, 5):
                    tiles[y][x] = TileType.HAZARD
            for y in range(2, 5):
                for x in range(16, 19):
                    tiles[y][x] = TileType.PIT

        elif variant == "echo":
            for y in range(2, 5):
                for x in range(2, 5):
                    tiles[y][x] = TileType.HAZARD
            for y in range(13, 16):
                for x in range(16, 19):
                    tiles[y][x] = TileType.PIT

        elif variant == "fracture":
            for y in range(8, 11):
                for x in range(9, 13):
                    tiles[y][x] = TileType.HAZARD
            for x in range(2, 6):
                tiles[3][x] = TileType.PIT
            for x in range(16, 20):
                tiles[14][x] = TileType.PIT

        return tiles

    def _place_entities(self) -> None:

        key1 = Key(
            position=(3 * TILE_SIZE, 3 * TILE_SIZE),
            key_id="key_06_a"
        )
        self.add_entity(key1, [UniverseType.PRIME])
        key2 = Key(
            position=(18 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_06_b"
        )
        self.add_entity(key2, [UniverseType.ECHO])

        key3 = Key(
            position=(17 * TILE_SIZE, 9 * TILE_SIZE),
            key_id="key_06_c"
        )
        self.add_entity(key3, [UniverseType.FRACTURE])

        walker = EchoWalker(
            position=(10 * TILE_SIZE, 9 * TILE_SIZE),
            echo_delay=1.5
        )
        self.add_entity(walker, [UniverseType.PRIME, UniverseType.ECHO])

        prime_wraith = ParadoxWraith(
            position=(16 * TILE_SIZE, 9 * TILE_SIZE),
            paradox_threshold=0.0
        )
        self.add_entity(prime_wraith, [UniverseType.PRIME])

        fracture_wraith = ParadoxWraith(
            position=(16 * TILE_SIZE, 9 * TILE_SIZE),
            paradox_threshold=0.0
        )
        self.add_entity(fracture_wraith, [UniverseType.FRACTURE])

        switch1 = EchoSwitch(
            position=(4 * TILE_SIZE, 9 * TILE_SIZE),
            switch_id="switch_06",
            linked_entity_id="gate_06"
        )
        self.add_entity(switch1, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        gate = VariantDoor(
            position=(19 * TILE_SIZE, 9 * TILE_SIZE),
            door_id="gate_06",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        exit_portal = ExitPortal(
            position=(20 * TILE_SIZE, 9 * TILE_SIZE),
            portal_id="exit_06",
            requires_keys=3
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        causal_graph.add_dependency(
            source_id="switch_06",
            target_id="gate_06",
            operator=CausalOperator.ECHO
        )

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The research facility... three realities overlap here.",
                "position": (1, 9)
            },
            {
                "trigger": "see_hazard",
                "message": "Hazards shift between universes. Switch to find safe ground.",
                "position": (3, 3)
            },
            {
                "trigger": "near_fracture_key",
                "message": "Some things only exist in the Fracture. Be careful in there.",
                "position": (17, 9)
            },
            {
                "trigger": "near_wraith",
                "message": "Paradox Wraith detected. It now appears in both Prime and Fracture sectors.",
                "position": (16, 9)
            }
        ]
