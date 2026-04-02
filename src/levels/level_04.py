"""
Level 04 - The Temporal Maze

A labyrinth that changes layout between universes.

Theme: A shifting maze where walls move between realities.
Goal: Navigate through by switching universes to find paths.
"""

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
from ..entities.enemies.shade import Shade
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level04(Level):
    """
    The Temporal Maze - Universe-Shifting Labyrinth

    Teaches:
    1. Complex multi-path navigation using universe switching
    2. Dead ends in one universe are paths in another
    3. Multiple keys spread across universes
    4. Enemies that patrol different paths per universe

    Layout:
    - Dense maze with different wall configurations per universe
    - 2 keys hidden in opposite corners
    - Shades guarding key locations
    """

    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_04",
            name="The Temporal Maze",
            width=24,
            height=18,
            starting_universe=UniverseType.PRIME,
            starting_position=(1, 1),
            required_keys=2,
            exit_position=(22, 16),
            has_prime=True,
            has_echo=True,
            has_fracture=False
        )
        super().__init__(config, multiverse)

    def _create_universes(self) -> None:
        prime_tiles = self._create_maze_prime()
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)

        echo_tiles = self._create_maze_echo()
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)

    def _create_maze_prime(self) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]

        # Border
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        # Maze walls - Prime has horizontal emphasis
        # Row 2 wall segments
        for x in range(2, 8):
            tiles[2][x] = TileType.WALL
        for x in range(10, 16):
            tiles[2][x] = TileType.WALL
        for x in range(18, 22):
            tiles[2][x] = TileType.WALL

        # Row 4
        for x in range(4, 7):
            tiles[4][x] = TileType.WALL
        for x in range(9, 14):
            tiles[4][x] = TileType.WALL
        for x in range(16, 20):
            tiles[4][x] = TileType.WALL

        # Row 6
        for x in range(1, 5):
            tiles[6][x] = TileType.WALL
        for x in range(7, 11):
            tiles[6][x] = TileType.WALL
        for x in range(13, 18):
            tiles[6][x] = TileType.WALL
        for x in range(20, 23):
            tiles[6][x] = TileType.WALL

        # Row 8 - central corridor blocked
        for x in range(3, 6):
            tiles[8][x] = TileType.WALL
        for x in range(8, 12):
            tiles[8][x] = TileType.WALL
        for x in range(14, 17):
            tiles[8][x] = TileType.WALL
        for x in range(19, 22):
            tiles[8][x] = TileType.WALL

        # Row 10
        for x in range(1, 4):
            tiles[10][x] = TileType.WALL
        for x in range(6, 10):
            tiles[10][x] = TileType.WALL
        for x in range(12, 16):
            tiles[10][x] = TileType.WALL
        for x in range(18, 21):
            tiles[10][x] = TileType.WALL

        # Row 12
        for x in range(3, 8):
            tiles[12][x] = TileType.WALL
        for x in range(10, 14):
            tiles[12][x] = TileType.WALL
        for x in range(16, 20):
            tiles[12][x] = TileType.WALL

        # Row 14
        for x in range(1, 6):
            tiles[14][x] = TileType.WALL
        for x in range(8, 12):
            tiles[14][x] = TileType.WALL
        for x in range(14, 18):
            tiles[14][x] = TileType.WALL
        for x in range(20, 23):
            tiles[14][x] = TileType.WALL

        # Row 16
        for x in range(2, 5):
            tiles[16][x] = TileType.WALL
        for x in range(7, 11):
            tiles[16][x] = TileType.WALL
        for x in range(13, 17):
            tiles[16][x] = TileType.WALL

        # Vertical connectors
        for y in range(2, 6):
            tiles[y][8] = TileType.WALL
        for y in range(4, 8):
            tiles[y][15] = TileType.WALL
        for y in range(10, 14):
            tiles[y][5] = TileType.WALL
        for y in range(12, 16):
            tiles[y][19] = TileType.WALL

        return tiles

    def _create_maze_echo(self) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]

        # Border
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        # Echo has vertical emphasis - different maze pattern
        # Vertical wall columns
        for y in range(1, 6):
            tiles[y][3] = TileType.WALL
        for y in range(3, 9):
            tiles[y][6] = TileType.WALL
        for y in range(1, 5):
            tiles[y][10] = TileType.WALL
        for y in range(2, 8):
            tiles[y][13] = TileType.WALL
        for y in range(1, 6):
            tiles[y][17] = TileType.WALL
        for y in range(3, 7):
            tiles[y][20] = TileType.WALL

        # Middle section
        for y in range(7, 12):
            tiles[y][4] = TileType.WALL
        for y in range(8, 13):
            tiles[y][8] = TileType.WALL
        for y in range(7, 11):
            tiles[y][11] = TileType.WALL
        for y in range(9, 14):
            tiles[y][15] = TileType.WALL
        for y in range(7, 12):
            tiles[y][18] = TileType.WALL
        for y in range(8, 11):
            tiles[y][21] = TileType.WALL

        # Lower section
        for y in range(12, 17):
            tiles[y][2] = TileType.WALL
        for y in range(13, 17):
            tiles[y][6] = TileType.WALL
        for y in range(11, 16):
            tiles[y][10] = TileType.WALL
        for y in range(13, 17):
            tiles[y][13] = TileType.WALL
        for y in range(12, 16):
            tiles[y][17] = TileType.WALL
        for y in range(14, 17):
            tiles[y][20] = TileType.WALL

        # Horizontal connectors
        for x in range(3, 7):
            tiles[9][x] = TileType.WALL
        for x in range(11, 16):
            tiles[5][x] = TileType.WALL
        for x in range(15, 19):
            tiles[13][x] = TileType.WALL

        return tiles

    def _place_entities(self) -> None:
        # Key 1 - top right area
        key1 = Key(
            position=(21 * TILE_SIZE, 1 * TILE_SIZE),
            key_id="key_04_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO])

        # Key 2 - bottom left area
        key2 = Key(
            position=(2 * TILE_SIZE, 16 * TILE_SIZE),
            key_id="key_04_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO])

        # Shade guarding key 1 area
        shade1 = Shade(
            position=(20 * TILE_SIZE, 3 * TILE_SIZE),
            shade_id="shade_04_a",
            patrol_points=[
                (20 * TILE_SIZE, 2 * TILE_SIZE),
                (22 * TILE_SIZE, 2 * TILE_SIZE),
                (22 * TILE_SIZE, 5 * TILE_SIZE),
                (20 * TILE_SIZE, 5 * TILE_SIZE)
            ]
        )
        self.add_entity(shade1, [UniverseType.PRIME])

        # Shade guarding key 2 area
        shade2 = Shade(
            position=(3 * TILE_SIZE, 15 * TILE_SIZE),
            shade_id="shade_04_b",
            patrol_points=[
                (1 * TILE_SIZE, 15 * TILE_SIZE),
                (4 * TILE_SIZE, 15 * TILE_SIZE),
                (4 * TILE_SIZE, 16 * TILE_SIZE),
                (1 * TILE_SIZE, 16 * TILE_SIZE)
            ]
        )
        self.add_entity(shade2, [UniverseType.ECHO])

        # Switch to open the exit gate
        switch = EchoSwitch(
            position=(12 * TILE_SIZE, 9 * TILE_SIZE),
            switch_id="switch_04",
            linked_entity_id="gate_04"
        )
        self.add_entity(switch, [UniverseType.PRIME, UniverseType.ECHO])

        # Gate before exit
        gate = VariantDoor(
            position=(21 * TILE_SIZE, 16 * TILE_SIZE),
            door_id="gate_04",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate, [UniverseType.PRIME, UniverseType.ECHO])

        # Exit portal
        exit_portal = ExitPortal(
            position=(22 * TILE_SIZE, 16 * TILE_SIZE),
            portal_id="exit_04",
            requires_keys=2
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        causal_graph.add_dependency(
            source_id="switch_04",
            target_id="gate_04",
            operator=CausalOperator.ECHO
        )

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The maze shifts between realities. Both paths lead somewhere.",
                "position": (1, 1)
            },
            {
                "trigger": "stuck",
                "message": "A wall here... but in another universe, maybe not.",
                "position": (8, 4)
            }
        ]
