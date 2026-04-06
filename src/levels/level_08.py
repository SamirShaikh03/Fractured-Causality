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
from ..entities.objects.bridge import Bridge
from ..entities.enemies.shade import Shade
from ..entities.enemies.echo_walker import EchoWalker
from ..entities.enemies.paradox_wraith import ParadoxWraith
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level08(Level):
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_08",
            name="The Convergence",
            width=30,
            height=22,
            starting_universe=UniverseType.PRIME,
            starting_position=(15, 20),
            required_keys=3,
            exit_position=(15, 2),
            has_prime=True,
            has_echo=True,
            has_fracture=True
        )
        super().__init__(config, multiverse)
        self.tree_destroyed = False

    def _create_universes(self) -> None:
        for u_type in [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE]:
            tiles = self._create_cathedral_map(u_type)
            universe = Universe(
                universe_type=u_type,
                width=self.config.width,
                height=self.config.height
            )
            universe.tilemap.tiles = tiles
            self.multiverse.add_universe(universe)

    def _create_cathedral_map(self, u_type: UniverseType) -> List[List[TileType]]:
        w, h = self.config.width, self.config.height
        tiles = [[TileType.WALL for _ in range(w)] for _ in range(h)]

        for y in range(1, h - 1):
            for x in range(12, 19):
                tiles[y][x] = TileType.FLOOR

        for y in range(1, 8):
            for x in range(3, 28):
                tiles[y][x] = TileType.FLOOR

        for y in range(9, 16):
            for x in range(1, 12):
                tiles[y][x] = TileType.FLOOR

        for y in range(9, 16):
            for x in range(19, 29):
                tiles[y][x] = TileType.FLOOR

        for y in range(17, h - 1):
            for x in range(10, 21):
                tiles[y][x] = TileType.FLOOR

        for y in range(1, 6):
            tiles[y][9] = TileType.WALL
            tiles[y][21] = TileType.WALL

        for x in range(3, 9):
            tiles[6][x] = TileType.WALL
        for x in range(22, 28):
            tiles[6][x] = TileType.WALL

        for x in range(1, 12):
            if x not in [5, 6]:
                tiles[12][x] = TileType.WALL

        for x in range(19, 29):
            if x not in [23, 24]:
                tiles[12][x] = TileType.WALL

        for y in range(9, 16):
            if y not in [11, 12]:
                tiles[y][12] = TileType.WALL
                tiles[y][18] = TileType.WALL

        if u_type == UniverseType.PRIME:
            for x in range(4, 8):
                tiles[5][x] = TileType.PIT

            for y in range(13, 15):
                for x in range(21, 25):
                    tiles[y][x] = TileType.HAZARD

        elif u_type == UniverseType.ECHO:
            for x in range(19, 29):
                tiles[10][x] = TileType.FLOOR

            for y in range(10, 12):
                for x in range(3, 7):
                    tiles[y][x] = TileType.PIT

        elif u_type == UniverseType.FRACTURE:
            fracture_hazards = [
                (5, 3), (6, 3), (14, 10), (15, 10),
                (25, 4), (26, 4), (8, 14), (22, 14)
            ]
            for fx, fy in fracture_hazards:
                if 0 < fy < h - 1 and 0 < fx < w - 1:
                    tiles[fy][fx] = TileType.HAZARD

        return tiles

    def _place_entities(self) -> None:
        tree = Tree(
            position=(6 * TILE_SIZE, 3 * TILE_SIZE),
            tree_id="cathedral_tree",
            state="living"
        )
        self.add_entity(tree, [UniverseType.PRIME])

        shade1 = Shade(
            position=(15 * TILE_SIZE, 4 * TILE_SIZE),
            shade_id="shade_08_a",
            causal_origin_id="cathedral_tree",
            patrol_points=[
                (13 * TILE_SIZE, 3 * TILE_SIZE),
                (17 * TILE_SIZE, 3 * TILE_SIZE),
                (17 * TILE_SIZE, 5 * TILE_SIZE),
                (13 * TILE_SIZE, 5 * TILE_SIZE)
            ]
        )
        self.add_entity(shade1, [UniverseType.PRIME])

        key1 = Key(
            position=(15 * TILE_SIZE, 3 * TILE_SIZE),
            key_id="key_08_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        stone = CausalStone(
            position=(5 * TILE_SIZE, 10 * TILE_SIZE),
            stone_id="stone_08"
        )
        self.add_entity(stone, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        door_west = VariantDoor(
            position=(5 * TILE_SIZE, 14 * TILE_SIZE),
            door_id="door_08_west",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_west, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        key2 = Key(
            position=(3 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_08_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        walker = EchoWalker(
            position=(24 * TILE_SIZE, 10 * TILE_SIZE),
            echo_delay=1.8
        )
        self.add_entity(walker, [UniverseType.ECHO])

        wraith = ParadoxWraith(
            position=(24 * TILE_SIZE, 14 * TILE_SIZE),
            paradox_threshold=45.0
        )
        self.add_entity(wraith, [UniverseType.FRACTURE])

        key3 = Key(
            position=(25 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_08_c"
        )
        self.add_entity(key3, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        switch_exit = EchoSwitch(
            position=(15 * TILE_SIZE, 11 * TILE_SIZE),
            switch_id="switch_08_exit",
            linked_entity_id="gate_08_exit"
        )
        self.add_entity(switch_exit, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        gate_exit = VariantDoor(
            position=(15 * TILE_SIZE, 3 * TILE_SIZE),
            door_id="gate_08_exit",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate_exit, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

        exit_portal = ExitPortal(
            position=(15 * TILE_SIZE, 2 * TILE_SIZE),
            portal_id="exit_08",
            requires_keys=3
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])

    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph

        causal_graph.add_dependency(
            source_id="cathedral_tree",
            target_id="shade_08_a",
            operator=CausalOperator.EXISTENCE
        )

        causal_graph.add_dependency(
            source_id="stone_08",
            target_id="door_08_west",
            operator=CausalOperator.CONDITIONAL
        )

        causal_graph.add_dependency(
            source_id="switch_08_exit",
            target_id="gate_08_exit",
            operator=CausalOperator.ECHO
        )

    def update(self, dt: float) -> None:
        super().update(dt)

        if not self.tree_destroyed:
            for entity in self.entities.get(UniverseType.PRIME, []):
                if hasattr(entity, 'tree_id') and entity.tree_id == 'cathedral_tree':
                    if getattr(entity, 'tree_state', 'living') == 'stump':
                        self._on_tree_destroyed()

        for entity_list in self.entities.values():
            for entity in entity_list:
                if hasattr(entity, 'stone_id') and entity.stone_id == 'stone_08':
                    tile_x = int(entity.x / TILE_SIZE)
                    tile_y = int(entity.y / TILE_SIZE)
                    if tile_x == 8 and tile_y == 14:
                        for elist in self.entities.values():
                            for e in elist:
                                if getattr(e, 'door_id', '') == 'door_08_west':
                                    e.open()

    def _on_tree_destroyed(self) -> None:
        self.tree_destroyed = True
        EventSystem.emit(GameEvent.UI_MESSAGE, {
            "message": "The cathedral tree falls... the shade dissipates!",
            "type": "causal"
        })
        for entity in self.entities.get(UniverseType.PRIME, []):
            if hasattr(entity, 'shade_id'):
                entity.on_causal_change(EntityState.DESTROYED, "cathedral_tree")

    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "The Cathedral of Convergence. Everything you've learned matters here.",
                "position": (15, 20)
            }
        ]
