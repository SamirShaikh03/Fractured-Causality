import pygame
from typing import List, Tuple

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator
from ..entities.player import Player
from ..entities.objects.echo_switch import EchoSwitch
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.objects.coin import Coin
from ..entities.enemies.shade import Shade
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level01(Level):
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_01",
            name="First Fracture",
            width=20,
            height=15,
            starting_universe=UniverseType.PRIME,
            starting_position=(2, 7),
            required_keys=1,
            exit_position=(17, 7),
            has_prime=True,
            has_echo=True,
            has_fracture=False
        )
        super().__init__(config, multiverse)
    
    def _create_universes(self) -> None:
        prime_tiles = self._create_base_map()
        for x in range(8, 12):
            prime_tiles[3][x] = TileType.WALL
        
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)
        
        echo_tiles = self._create_base_map()
        for x in range(8, 12):
            echo_tiles[11][x] = TileType.WALL
        
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)
    
    def _create_base_map(self) -> List[List[TileType]]:
        """Create the base tile map shared by both universes."""
        w, h = self.config.width, self.config.height
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h-1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w-1] = TileType.WALL
        for y in range(5, 10):
            for x in range(5, 15):
                if y in [6, 7, 8]:
                    pass
                else:
                    tiles[y][x] = TileType.WALL

        for x in range(1, w-1):
            if tiles[2][x] != TileType.WALL:
                tiles[2][x] = TileType.FLOOR
            if tiles[4][x] != TileType.WALL:
                tiles[4][x] = TileType.FLOOR

        for x in range(1, w-1):
            if tiles[10][x] != TileType.WALL:
                tiles[10][x] = TileType.FLOOR
            if tiles[12][x] != TileType.WALL:
                tiles[12][x] = TileType.FLOOR

        for y in range(1, h-1):
            tiles[y][1] = TileType.FLOOR
            tiles[y][w-2] = TileType.FLOOR

        for y in range(1, 4):
            tiles[y][w-3] = TileType.FLOOR
            tiles[y][w-4] = TileType.FLOOR
        
        return tiles
    
    def _place_entities(self) -> None:
        
        key = Key(
            position=(16 * TILE_SIZE, 2 * TILE_SIZE),
            key_id="key_01"
        )
        self.add_entity(key, [UniverseType.PRIME, UniverseType.ECHO])
        
        coin1 = Coin(position=(6 * TILE_SIZE, 3 * TILE_SIZE))
        self.add_entity(coin1, [UniverseType.PRIME, UniverseType.ECHO])
        
        coin2 = Coin(position=(12 * TILE_SIZE, 3 * TILE_SIZE))
        self.add_entity(coin2, [UniverseType.PRIME, UniverseType.ECHO])
        
        coin3 = Coin(position=(6 * TILE_SIZE, 11 * TILE_SIZE))
        self.add_entity(coin3, [UniverseType.PRIME, UniverseType.ECHO])
        
        coin4 = Coin(position=(12 * TILE_SIZE, 11 * TILE_SIZE))
        self.add_entity(coin4, [UniverseType.PRIME, UniverseType.ECHO])

        shade_intro = Shade(
            position=(15 * TILE_SIZE, 3 * TILE_SIZE),
            shade_id="shade_intro_01",
            patrol_points=[
                (14 * TILE_SIZE, 3 * TILE_SIZE),
                (16 * TILE_SIZE, 3 * TILE_SIZE),
                (16 * TILE_SIZE, 4 * TILE_SIZE),
                (14 * TILE_SIZE, 4 * TILE_SIZE),
            ]
        )
        self.add_entity(shade_intro, [UniverseType.PRIME])
        exit_portal = ExitPortal(
            position=(17 * TILE_SIZE, 7 * TILE_SIZE),
            portal_id="exit_01",
            requires_keys=1
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO])

        switch = EchoSwitch(
            position=(10 * TILE_SIZE, 7 * TILE_SIZE),
            switch_id="switch_01",
            linked_entity_id="door_01"
        )
        self.add_entity(switch, [UniverseType.PRIME, UniverseType.ECHO])
        door = VariantDoor(
            position=(14 * TILE_SIZE, 7 * TILE_SIZE),
            door_id="door_01",
            requires_key=True,
            key_id="key_01",
            prime_open=False, 
            echo_open=True     
        )
        self.add_entity(door, [UniverseType.PRIME, UniverseType.ECHO])
    
    def _setup_causality(self) -> None:
        causal_graph = self.multiverse.causal_graph
        
        causal_graph.add_dependency(
            source_id="switch_01",
            target_id="door_01",
            operator=CausalOperator.ECHO
        )
    
    def _check_win_condition(self) -> None:
        pass
    
    def get_tutorial_messages(self) -> List[dict]:
        return [
            {
                "trigger": "start",
                "message": "Welcome to the Archive. Reality has fractured here.",
                "position": (2, 7)
            },
            {
                "trigger": "first_switch",
                "message": "Press [SPACE] to switch universes. Each universe is different.",
                "position": (5, 7)
            },
            {
                "trigger": "near_key",
                "message": "Collect the key to unlock the portal.",
                "position": (14, 2)
            },
            {
                "trigger": "near_exit",
                "message": "The portal leads to the next fracture...",
                "position": (17, 7)
            }
        ]
