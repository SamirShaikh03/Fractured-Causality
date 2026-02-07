"""
Level 02 - The Echo Stone

Introduces ANCHORED objects and their cross-universe behavior.

Theme: A ruined temple where an ancient Causal Stone still persists.
Goal: Use the Causal Stone to solve a cross-universe puzzle.
"""

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
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level02(Level):
    """
    The Echo Stone - Anchored Object Puzzle
    
    Teaches:
    1. Causal Stones exist in the same position across all universes
    2. Moving a stone in one universe moves it everywhere
    3. Using anchored objects to solve cross-universe puzzles
    4. Pressure plates and weight-based mechanics
    
    Layout:
    - Central puzzle area with pressure plates
    - Stone must be positioned to hold plate in one universe
    - While player uses the path opened in another universe
    """
    
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
        
        # Track pressure plate states
        self.plates_pressed = {
            "plate_prime": False,
            "plate_echo": False
        }
    
    def _create_universes(self) -> None:
        """Create the tile maps for Prime and Echo universes."""
        
        # ---------- PRIME UNIVERSE ----------
        prime_tiles = self._create_base_map()
        
        # Prime has a pit in the upper path
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
        
        # ---------- ECHO UNIVERSE ----------
        echo_tiles = self._create_base_map()
        
        # Echo has a pit in the lower path
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
        """Create the base tile map."""
        w, h = self.config.width, self.config.height
        
        # Initialize with floor
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]
        
        # Border walls
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h-1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w-1] = TileType.WALL
        
        # Create temple-like structure
        # Three horizontal paths
        
        # Upper wall section
        for x in range(6, 16):
            tiles[3][x] = TileType.WALL
            tiles[6][x] = TileType.WALL
        
        # Lower wall section  
        for x in range(6, 16):
            tiles[10][x] = TileType.WALL
            tiles[13][x] = TileType.WALL
        
        # Vertical walls creating rooms
        for y in range(3, 14):
            if y not in [8]:  # Leave middle passage
                tiles[y][6] = TileType.WALL
                tiles[y][15] = TileType.WALL
        
        # Pressure plate locations (using HAZARD as visual)
        tiles[8][7] = TileType.HAZARD  # Left plate (Prime)
        tiles[8][14] = TileType.HAZARD  # Right plate (Echo)
        
        # Small treasure rooms
        for y in range(1, 3):
            tiles[y][17] = TileType.FLOOR
            tiles[y][18] = TileType.FLOOR
        
        for y in range(14, 16):
            tiles[y][17] = TileType.FLOOR
            tiles[y][18] = TileType.FLOOR
        
        return tiles
    
    def _place_entities(self) -> None:
        """Place entities in the level."""
        
        # ---------- CAUSAL STONES ----------
        # Two stones for the two pressure plates
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
        
        # ---------- KEYS ----------
        # Key 1: In upper treasure room (requires solving upper path)
        key1 = Key(
            position=(17 * TILE_SIZE, 2 * TILE_SIZE),
            key_id="key_02_a"
        )
        self.add_entity(key1, [UniverseType.PRIME, UniverseType.ECHO])
        
        # Key 2: In lower treasure room
        key2 = Key(
            position=(17 * TILE_SIZE, 14 * TILE_SIZE),
            key_id="key_02_b"
        )
        self.add_entity(key2, [UniverseType.PRIME, UniverseType.ECHO])
        
        # ---------- DOORS ----------
        # Door blocking upper path (opens when plate_prime is pressed)
        door_upper = VariantDoor(
            position=(8 * TILE_SIZE, 4 * TILE_SIZE),
            door_id="door_upper",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_upper, [UniverseType.PRIME, UniverseType.ECHO])
        
        # Door blocking lower path (opens when plate_echo is pressed)
        door_lower = VariantDoor(
            position=(8 * TILE_SIZE, 12 * TILE_SIZE),
            door_id="door_lower",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(door_lower, [UniverseType.PRIME, UniverseType.ECHO])
        
        # ---------- ECHO SWITCHES ----------
        # Switch to activate the main gate
        switch_main = EchoSwitch(
            position=(10 * TILE_SIZE, 8 * TILE_SIZE),
            switch_id="switch_main",
            linked_entity_id="gate_main"
        )
        self.add_entity(switch_main, [UniverseType.PRIME, UniverseType.ECHO])
        
        # ---------- MAIN GATE ----------
        gate_main = VariantDoor(
            position=(17 * TILE_SIZE, 8 * TILE_SIZE),
            door_id="gate_main",
            prime_open=False,
            echo_open=False
        )
        self.add_entity(gate_main, [UniverseType.PRIME, UniverseType.ECHO])
        
        # ---------- EXIT PORTAL ----------
        exit_portal = ExitPortal(
            position=(19 * TILE_SIZE, 8 * TILE_SIZE),
            portal_id="exit_02",
            requires_keys=2
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO])
    
    def _setup_causality(self) -> None:
        """Set up causal relationships."""
        causal_graph = self.multiverse.causal_graph
        
        # Causal Stones are ANCHORED - this is set in their class
        # They propagate position changes across universes automatically
        
        # Switch -> Main Gate
        causal_graph.add_dependency(
            source_id="switch_main",
            target_id="gate_main",
            operator=CausalOperator.ECHO
        )
        
        # Pressure plates use CASCADE - activating one affects both doors
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
        """Update level with pressure plate detection."""
        super().update(dt)
        
        # Check if stones are on pressure plates
        for entity_list in self.entities.values():
            for entity in entity_list:
                if hasattr(entity, 'stone_id'):
                    # Check if stone is on a plate position
                    stone_tile_x = int(entity.x / TILE_SIZE)
                    stone_tile_y = int(entity.y / TILE_SIZE)
                    
                    # Prime plate at (7, 8)
                    if stone_tile_x == 7 and stone_tile_y == 8:
                        if not self.plates_pressed["plate_prime"]:
                            self.plates_pressed["plate_prime"] = True
                            self._activate_plate("plate_prime")
                    
                    # Echo plate at (14, 8)
                    if stone_tile_x == 14 and stone_tile_y == 8:
                        if not self.plates_pressed["plate_echo"]:
                            self.plates_pressed["plate_echo"] = True
                            self._activate_plate("plate_echo")
    
    def _activate_plate(self, plate_id: str) -> None:
        """Activate a pressure plate."""
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": plate_id,
            "change": "pressed"
        })
        
        # Open corresponding door
        for entity_list in self.entities.values():
            for entity in entity_list:
                if plate_id == "plate_prime" and getattr(entity, 'door_id', '') == 'door_upper':
                    entity.open()
                elif plate_id == "plate_echo" and getattr(entity, 'door_id', '') == 'door_lower':
                    entity.open()
    
    def get_tutorial_messages(self) -> List[dict]:
        """Get tutorial messages for this level."""
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
