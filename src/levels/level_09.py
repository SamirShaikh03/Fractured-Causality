"""
Level 09 - The Final Rift

The ultimate challenge - everything at stake.

Theme: The boundary between realities is collapsing.
Goal: Seal the rift by collecting all fragments across universes.
"""

import pygame
from typing import List

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator, EntityState
from ..entities.objects.echo_switch import EchoSwitch
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.objects.tree import Tree
from ..entities.objects.causal_stone import CausalStone
from ..entities.enemies.shade import Shade
from ..entities.enemies.echo_walker import EchoWalker
from ..entities.enemies.paradox_wraith import ParadoxWraith
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level09(Level):
    """
    The Final Rift - Ultimate Challenge

    Combines ALL mechanics:
    1. Complex three-universe maze
    2. Multiple enemy types across realities
    3. Causal chains with inverse effects
    4. Stone puzzles and tree dependencies
    5. High paradox pressure throughout

    Layout:
    - Spiraling path toward center
    - Outer ring: hazardous terrain
    - Middle ring: enemy gauntlet
    - Inner ring: puzzle chambers
    - Center: the Rift (exit)
    """

    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_09",
            name="The Final Rift",
            width=32,
            height=24,
            starting_universe=UniverseType.PRIME,
            starting_position=(1, 22),
            required_keys=4,
            exit_position=(16, 12),
            has_prime=True,
            has_echo=True,
            has_fracture=True
        )
        super().__init__(config, multiverse)
        self.rift_tree_destroyed = False

    def _create_universes(self) -> None:
        for u_type in [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE]:
            tiles = self._create_rift_map(u_type)
            universe = Universe(
                universe_type=u_type,
                width=self.config.width,
                height=self.config.height
            )
            universe.tilemap.tiles = tiles
            self.multiverse.add_universe(universe)

    def _create_rift_map(self, u_type: UniverseType) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.WALL for _ in range(w)] for _ in range(h)]

        # Border
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h - 1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w - 1] = TileType.WALL

        # Outer ring - perimeter path
        for x in range(1, w - 1):
            tiles[1][x] = TileType.FLOOR
            tiles[2][x] = TileType.FLOOR
            tiles[h - 2][x] = TileType.FLOOR
            tiles[h - 3][x] = TileType.FLOOR
        for y in range(1, h - 1):
            tiles[y][1] = TileType.FLOOR
            tiles[y][2] = TileType.FLOOR
            tiles[y][w - 2] = TileType.FLOOR
            tiles[y][w - 3] = TileType.FLOOR

        # Middle ring
        for x in range(5, w - 5):
            tiles[5][x] = TileType.FLOOR
            tiles[6][x] = TileType.FLOOR
            tiles[h - 6][x] = TileType.FLOOR
            tiles[h - 7][x] = TileType.FLOOR
        for y in range(5, h - 5):
            tiles[y][5] = TileType.FLOOR
            tiles[y][6] = TileType.FLOOR
            tiles[y][w - 6] = TileType.FLOOR
            tiles[y][w - 7] = TileType.FLOOR

        # Inner ring / center area
        for y in range(9, h - 9):
            for x in range(9, w - 9):
                tiles[y][x] = TileType.FLOOR

        # Connections between rings (corridors)
        # Bottom connector (outer to middle)
        for y in range(h - 6, h - 2):
            tiles[y][8] = TileType.FLOOR
            tiles[y][9] = TileType.FLOOR

        # Left connector (outer to middle)
        for x in range(2, 6):
            tiles[10][x] = TileType.FLOOR
            tiles[11][x] = TileType.FLOOR

        # Top connector (outer to middle)
        for y in range(2, 6):
            tiles[y][16] = TileType.FLOOR
            tiles[y][17] = TileType.FLOOR

        # Right connector (outer to middle)
        for x in range(w - 6, w - 2):
            tiles[12][x] = TileType.FLOOR
            tiles[13][x] = TileType.FLOOR

        # Middle to inner connectors
        # Left
        for x in range(6, 10):
            tiles[12][x] = TileType.FLOOR

        # Top
        for y in range(6, 10):
            tiles[y][15] = TileType.FLOOR

        # Right
        for x in range(w - 10, w - 6):
            tiles[12][x] = TileType.FLOOR

        # Bottom
        for y in range(h - 10, h - 6):
            tiles[y][16] = TileType.FLOOR

        # Inner rooms dividers
        for y in range(9, 15):
            if y != 12:
                tiles[y][14] = TileType.WALL
                tiles[y][18] = TileType.WALL

        # Universe-specific terrain
        if u_type == UniverseType.PRIME:
            # Outer ring top has pits
            for x in range(10, 22):
                tiles[1][x] = TileType.PIT
            # Middle ring right has hazards
            for y in range(7, 11):
                tiles[y][w - 6] = TileType.HAZARD

        elif u_type == UniverseType.ECHO:
            # Outer ring bottom has pits
            for x in range(10, 22):
                tiles[h - 2][x] = TileType.PIT
            # Middle ring left has hazards
            for y in range(12, 17):
                tiles[y][5] = TileType.HAZARD

        elif u_type == UniverseType.FRACTURE:
            # Scattered pits in middle ring
            pit_spots = [
                (8, 6), (12, 5), (20, 6), (24, 5),
                (8, h - 7), (12, h - 6), (20, h - 7), (24, h - 6)
            ]
            for px, py in pit_spots:
                if 0 < py < h - 1 and 0 < px < w - 1:
                    tiles[py][px] = TileType.PIT
            # Hazards surrounding inner chamber
            for x in range(10, 22):
                tiles[9][x] = TileType.HAZARD
                tiles[h - 10][x] = TileType.HAZARD

        return tiles

    def _place_entities(self) -> None:
        # --- KEY 1: Outer ring, top-right corner ---
        key1 = Key(
            position=(29 * TILE_SIZE, 2 * TILE_SIZE),
            key_id="key_09_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        # --- KEY 2: Middle ring, guarded by shade ---
        key2 = Key(
            position=(6 * TILE_SIZE, 6 * TILE_SIZE),
            key_id="key_09_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        # Rift Tree in inner chamber left
        rift_tree = Tree(
            position=(11 * TILE_SIZE, 11 * TILE_SIZE),
            tree_id="rift_tree",
            state="living"
        )
        self.add_entity(rift_tree, [UniverseType.PRIME])

        # Shade dependent on rift tree, guarding key 2
        shade = Shade(
            position=(7 * TILE_SIZE, 6 * TILE_SIZE),
            shade_id="shade_09",
            causal_origin_id="rift_tree",
            patrol_points=[
                (6 * TILE_SIZE, 5 * TILE_SIZE),
                (8 * TILE_SIZE, 5 * TILE_SIZE),
                (8 * TILE_SIZE, 7 * TILE_SIZE),
                (6 * TILE_SIZE, 7 * TILE_SIZE)
            ]
        )
        self.add_entity(shade, [UniverseType.PRIME])

        # --- KEY 3: Inner chamber right, behind door ---
        key3 = Key(
            position=(20 * TILE_SIZE, 11 * TILE_SIZE),
            key_id="key_09_c"
        )
        self.add_entity(key3, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        # --- KEY 4: Fracture-only, in center of inner ring ---
        key4 = Key(
            position=(16 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_09_d"
        )
        self.add_entity(key4, [UniverseType.FRACTURE])

        # Enemies across the map
        walker1 = EchoWalker(
            position=(20 * TILE_SIZE, 2 * TILE_SIZE),
            echo_delay=1.5
        )
        self.add_entity(walker1, [UniverseType.ECHO])

        wraith1 = ParadoxWraith(
            position=(16 * TILE_SIZE, 10 * TILE_SIZE),
            paradox_threshold=35.0
        )
        self.add_entity(wraith1, [UniverseType.FRACTURE])

        shade2 = Shade(
            position=(25 * TILE_SIZE, 12 * TILE_SIZE),
            shade_id="shade_09_b",
            patrol_points=[
                (25 * TILE_SIZE, 11 * TILE_SIZE),
                (27 * TILE_SIZE, 11 * TILE_SIZE),
                (27 * TILE_SIZE, 13 * TILE_SIZE),
                (25 * TILE_SIZE, 13 * TILE_SIZE)
            ]
        )
        self.add_entity(shade2, [UniverseType.PRIME])

        # Switches and doors
        switch_inner = EchoSwitch(
            position=(12 * TILE_SIZE, 12 * TILE_SIZE),
            switch_id="switch_09_inner",
            linked_entity_id="door_09_inner"
        )
        self.add_entity(switch_inner, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        door_inner = VariantDoor(
            position=(18 * TILE_SIZE, 12 * TILE_SIZE),
            door_id="door_09_inner",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_inner, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        # Causal stone for puzzle
        stone = CausalStone(
            position=(10 * TILE_SIZE, 12 * TILE_SIZE),
            stone_id="stone_09"
        )
        self.add_entity(stone, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        # Exit - The Rift
        exit_portal = ExitPortal(
            position=(16 * TILE_SIZE, 12 * TILE_SIZE),
            portal_id="exit_09",
            requires_keys=4
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph

        # Tree -> Shade
        causal_graph.add_dependency(
            source_id="rift_tree",
            target_id="shade_09",
            operator=CausalOperator.EXISTENCE
        )

        # Switch -> Inner door
        causal_graph.add_dependency(
            source_id="switch_09_inner",
            target_id="door_09_inner",
            operator=CausalOperator.ECHO
        )

    def update(self, dt: float) -> None:
        super().update(dt)

        if not self.rift_tree_destroyed:
            for entity in self.entities.get(UniverseType.PRIME, []):
                if hasattr(entity, 'tree_id') and entity.tree_id == 'rift_tree':
                    if getattr(entity, 'tree_state', 'living') == 'stump':
                        self._on_tree_destroyed()

    def _on_tree_destroyed(self) -> None:
        self.rift_tree_destroyed = True
        EventSystem.emit(GameEvent.UI_MESSAGE, {
            "message": "The Rift Tree crumbles... the shade fades from existence!",
            "type": "causal"
        })
        for entity in self.entities.get(UniverseType.PRIME, []):
            if hasattr(entity, 'shade_id') and entity.shade_id == 'shade_09':
                entity.on_causal_change(EntityState.DESTROYED, "rift_tree")

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The Final Rift tears at reality itself. Seal it before all is lost.",
                "position": (1, 22)
            },
            {
                "trigger": "near_rift",
                "message": "Four fragments are needed to seal the Rift. Find them across all realities.",
                "position": (16, 13)
            }
        ]
