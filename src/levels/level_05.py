"""
Level 05 - Bridge of Echoes

Multiple bridges and echo switches create a chain puzzle.

Theme: A vast chasm with fragmented bridges across universes.
Goal: Activate switches in the right order to form a path.
"""

import pygame
from typing import List

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator
from ..entities.objects.echo_switch import EchoSwitch
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.bridge import Bridge
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.objects.causal_stone import CausalStone
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level05(Level):
    """
    Bridge of Echoes - Chain Puzzle

    Teaches:
    1. Sequential switch activation across universes
    2. Bridges appearing/disappearing between realities
    3. Causal stones used as puzzle weights
    4. Managing paradox through careful switching

    Layout:
    - Series of islands separated by chasms
    - Bridges exist in different universes
    - Must chain-activate switches to create a full path
    """

    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_05",
            name="Bridge of Echoes",
            width=26,
            height=16,
            starting_universe=UniverseType.PRIME,
            starting_position=(1, 8),
            required_keys=1,
            exit_position=(24, 8),
            has_prime=True,
            has_echo=True,
            has_fracture=False
        )
        super().__init__(config, multiverse)

    def _create_universes(self) -> None:
        prime_tiles = self._create_island_map(is_prime=True)
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)

        echo_tiles = self._create_island_map(is_prime=False)
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)

    def _create_island_map(self, is_prime: bool) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        # Start with pit (the chasm)
        tiles = [[TileType.PIT for _ in range(w)] for _ in range(h)]

        # Border walls
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        # Island 1 - Start (left)
        for y in range(4, 12):
            for x in range(1, 6):
                tiles[y][x] = TileType.FLOOR

        # Island 2 - Middle-left
        for y in range(3, 11):
            for x in range(8, 12):
                tiles[y][x] = TileType.FLOOR

        # Island 3 - Center
        for y in range(5, 13):
            for x in range(14, 18):
                tiles[y][x] = TileType.FLOOR

        # Island 4 - Middle-right
        for y in range(2, 10):
            for x in range(20, 23):
                tiles[y][x] = TileType.FLOOR

        # Island 5 - End (right)
        for y in range(5, 12):
            for x in range(24, 25):
                tiles[y][x] = TileType.FLOOR

        # Bridges - different per universe
        if is_prime:
            # Prime: bridge from island 1 to island 2 (top path)
            for x in range(6, 8):
                tiles[5][x] = TileType.FLOOR
                tiles[6][x] = TileType.FLOOR
            # Prime: bridge from island 3 to island 4 (bottom)
            for x in range(18, 20):
                tiles[8][x] = TileType.FLOOR
                tiles[9][x] = TileType.FLOOR
        else:
            # Echo: bridge from island 2 to island 3 (middle)
            for x in range(12, 14):
                tiles[7][x] = TileType.FLOOR
                tiles[8][x] = TileType.FLOOR
            # Echo: bridge from island 4 to island 5
            for x in range(23, 24):
                tiles[7][x] = TileType.FLOOR
                tiles[8][x] = TileType.FLOOR

        return tiles

    def _place_entities(self) -> None:
        # Key on island 3
        key = Key(
            position=(15 * TILE_SIZE, 7 * TILE_SIZE),
            key_id="key_05"
        )
        self.add_entity(key, [UniverseType.PRIME, UniverseType.ECHO])

        # Causal stone on island 1 for pressure puzzle
        stone = CausalStone(
            position=(3 * TILE_SIZE, 8 * TILE_SIZE),
            stone_id="stone_05"
        )
        self.add_entity(stone, [UniverseType.PRIME, UniverseType.ECHO])

        # Switch on island 2 - opens gate on island 4
        switch1 = EchoSwitch(
            position=(10 * TILE_SIZE, 6 * TILE_SIZE),
            switch_id="switch_05_a",
            linked_entity_id="gate_05"
        )
        self.add_entity(switch1, [UniverseType.PRIME, UniverseType.ECHO])

        # Gate on island 4 approach
        gate = VariantDoor(
            position=(20 * TILE_SIZE, 5 * TILE_SIZE),
            door_id="gate_05",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate, [UniverseType.PRIME, UniverseType.ECHO])

        # Exit portal
        exit_portal = ExitPortal(
            position=(24 * TILE_SIZE, 8 * TILE_SIZE),
            portal_id="exit_05",
            requires_keys=1
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        causal_graph.add_dependency(
            source_id="switch_05_a",
            target_id="gate_05",
            operator=CausalOperator.ECHO
        )

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "Islands float in the void. Bridges exist... in some realities.",
                "position": (1, 8)
            },
            {
                "trigger": "near_chasm",
                "message": "The chasm is impassable. Switch universes to find a bridge.",
                "position": (5, 6)
            }
        ]
