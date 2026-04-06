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
from ..entities.objects.causal_stone import CausalStone
from ..entities.enemies.shade import Shade
from ..entities.enemies.paradox_wraith import ParadoxWraith
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level07(Level):
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_07",
            name="The Causal Loop",
            width=28,
            height=16,
            starting_universe=UniverseType.PRIME,
            starting_position=(1, 8),
            required_keys=2,
            exit_position=(26, 8),
            has_prime=True,
            has_echo=True,
            has_fracture=True
        )
        super().__init__(config, multiverse)

    def _create_universes(self) -> None:
        for u_type in [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE]:
            tiles = self._create_clockwork_map(u_type)
            universe = Universe(
                universe_type=u_type,
                width=self.config.width,
                height=self.config.height
            )
            universe.tilemap.tiles = tiles
            self.multiverse.add_universe(universe)

    def _create_clockwork_map(self, u_type: UniverseType) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]

        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        for y in range(1, h - 1):
            if y not in [7, 8]:
                tiles[y][5] = TileType.WALL
                tiles[y][10] = TileType.WALL
                tiles[y][16] = TileType.WALL
                tiles[y][22] = TileType.WALL

        for x in range(1, w - 1):
            if x % 6 not in [2, 3]:
                tiles[5][x] = TileType.WALL
                tiles[11][x] = TileType.WALL

        for x_start, x_end in [(1, 5), (6, 10), (11, 16), (17, 22), (23, 27)]:
            for x in range(x_start, min(x_end, w - 1)):
                tiles[5][x] = TileType.WALL
                tiles[11][x] = TileType.WALL

        for x in range(1, w - 1):
            tiles[7][x] = TileType.FLOOR
            tiles[8][x] = TileType.FLOOR

        for room_start in [1, 6, 11, 17, 23]:
            room_end = min(room_start + 4, w - 1)
            for y in range(1, 5):
                for x in range(room_start, room_end):
                    tiles[y][x] = TileType.FLOOR
            for y in range(12, h - 1):
                for x in range(room_start, room_end):
                    tiles[y][x] = TileType.FLOOR
        if u_type == UniverseType.PRIME:
            for y in range(2, 4):
                for x in range(12, 15):
                    tiles[y][x] = TileType.PIT
        elif u_type == UniverseType.ECHO:
            for y in range(13, 15):
                for x in range(7, 9):
                    tiles[y][x] = TileType.HAZARD
        elif u_type == UniverseType.FRACTURE:
            hazard_spots = [(3, 2), (8, 13), (13, 3), (19, 13), (24, 3)]
            for hx, hy in hazard_spots:
                if 0 < hy < h - 1 and 0 < hx < w - 1:
                    tiles[hy][hx] = TileType.HAZARD

        return tiles

    def _place_entities(self) -> None:

        switch_a = EchoSwitch(
            position=(3 * TILE_SIZE, 3 * TILE_SIZE),
            switch_id="switch_07_a",
            linked_entity_id="door_07_a"
        )
        self.add_entity(switch_a, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        door_a = VariantDoor(
            position=(10 * TILE_SIZE, 7 * TILE_SIZE),
            door_id="door_07_a",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_a, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        switch_b = EchoSwitch(
            position=(13 * TILE_SIZE, 8 * TILE_SIZE),
            switch_id="switch_07_b",
            linked_entity_id="door_07_b"
        )
        self.add_entity(switch_b, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        door_b = VariantDoor(
            position=(22 * TILE_SIZE, 7 * TILE_SIZE),
            door_id="door_07_b",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_b, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])
        key1 = Key(
            position=(8 * TILE_SIZE, 3 * TILE_SIZE),
            key_id="key_07_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        key2 = Key(
            position=(19 * TILE_SIZE, 13 * TILE_SIZE),
            key_id="key_07_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        wraith_a = ParadoxWraith(
            position=(19 * TILE_SIZE, 8 * TILE_SIZE),
            paradox_threshold=35.0
        )
        self.add_entity(wraith_a, [UniverseType.FRACTURE])

        wraith_b = ParadoxWraith(
            position=(24 * TILE_SIZE, 8 * TILE_SIZE),
            paradox_threshold=45.0
        )
        self.add_entity(wraith_b, [UniverseType.FRACTURE])

        shade_a = Shade(
            position=(7 * TILE_SIZE, 8 * TILE_SIZE),
            shade_id="shade_07_a",
            patrol_points=[
                (6 * TILE_SIZE, 7 * TILE_SIZE),
                (9 * TILE_SIZE, 7 * TILE_SIZE),
                (9 * TILE_SIZE, 9 * TILE_SIZE),
                (6 * TILE_SIZE, 9 * TILE_SIZE),
            ]
        )
        self.add_entity(shade_a, [UniverseType.PRIME])

        shade_b = Shade(
            position=(13 * TILE_SIZE, 8 * TILE_SIZE),
            shade_id="shade_07_b",
            patrol_points=[
                (11 * TILE_SIZE, 7 * TILE_SIZE),
                (15 * TILE_SIZE, 7 * TILE_SIZE),
                (15 * TILE_SIZE, 9 * TILE_SIZE),
                (11 * TILE_SIZE, 9 * TILE_SIZE),
            ]
        )
        self.add_entity(shade_b, [UniverseType.ECHO])

        shade_c = Shade(
            position=(20 * TILE_SIZE, 8 * TILE_SIZE),
            shade_id="shade_07_c",
            patrol_points=[
                (18 * TILE_SIZE, 7 * TILE_SIZE),
                (25 * TILE_SIZE, 7 * TILE_SIZE),
                (25 * TILE_SIZE, 9 * TILE_SIZE),
                (18 * TILE_SIZE, 9 * TILE_SIZE),
            ]
        )
        self.add_entity(shade_c, [UniverseType.PRIME, UniverseType.FRACTURE])

        exit_portal = ExitPortal(
            position=(26 * TILE_SIZE, 8 * TILE_SIZE),
            portal_id="exit_07",
            requires_keys=2
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        causal_graph.add_dependency(
            source_id="switch_07_a",
            target_id="door_07_a",
            operator=CausalOperator.ECHO
        )
        causal_graph.add_dependency(
            source_id="switch_07_b",
            target_id="door_07_b",
            operator=CausalOperator.CASCADE
        )

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The clockwork turns... each action echoes forward.",
                "position": (1, 8)
            },
            {
                "trigger": "near_wraith",
                "message": "Paradox Wraith! It feeds on instability. Avoid or attack!",
                "position": (19, 8)
            }
        ]
