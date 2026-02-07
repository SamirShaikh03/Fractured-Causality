"""
Level 03 - Shade of the Tree

Introduces enemies and causal existence dependencies.

Theme: A dark forest clearing where Shades protect an ancient tree.
Goal: Discover that destroying the tree destroys the Shades that depend on it.
"""

import pygame
from typing import List

from .level_base import Level, LevelConfig
from ..multiverse.universe import Universe, UniverseType, TileType
from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.causal_node import CausalOperator, EntityState
from ..entities.player import Player
from ..entities.objects.tree import Tree
from ..entities.objects.bridge import Bridge
from ..entities.objects.variant_door import VariantDoor
from ..entities.objects.exit_portal import ExitPortal
from ..entities.objects.key import Key
from ..entities.enemies.shade import Shade
from ..core.settings import TILE_SIZE
from ..core.events import EventSystem, GameEvent


class Level03(Level):
    """
    Shade of the Tree - Causal Enemy Puzzle
    
    Teaches:
    1. Enemies can have causal origins
    2. Destroying a causal origin destroys dependents
    3. Actions in one universe affect entities in others
    4. The EXISTENCE causal operator
    
    Layout:
    - Forest clearing with a central ancient tree
    - Shades patrol, blocking access to the key
    - Player must find a way to destroy the tree
    - Tree exists in Prime but is dead in Echo
    """
    
    def __init__(self, multiverse: MultiverseManager):
        config = LevelConfig(
            level_id="level_03",
            name="Shade of the Tree",
            width=25,
            height=19,
            starting_universe=UniverseType.PRIME,
            starting_position=(2, 9),
            required_keys=1,
            exit_position=(22, 9),
            has_prime=True,
            has_echo=True,
            has_fracture=True  # Introduce Fracture universe
        )
        super().__init__(config, multiverse)
        
        self.tree_destroyed = False
    
    def _create_universes(self) -> None:
        """Create the tile maps for all three universes."""
        
        # ---------- PRIME UNIVERSE ----------
        # Dense forest with living tree, Shades active
        prime_tiles = self._create_forest_map(living_tree=True)
        
        prime = Universe(
            universe_type=UniverseType.PRIME,
            width=self.config.width,
            height=self.config.height
        )
        prime.tilemap.tiles = prime_tiles
        self.multiverse.add_universe(prime)
        
        # ---------- ECHO UNIVERSE ----------
        # Withered forest, tree is dead, different paths available
        echo_tiles = self._create_forest_map(living_tree=False)
        
        # Echo has bridge that doesn't exist in Prime (tree wasn't cut)
        # Already handled in base map
        
        echo = Universe(
            universe_type=UniverseType.ECHO,
            width=self.config.width,
            height=self.config.height
        )
        echo.tilemap.tiles = echo_tiles
        self.multiverse.add_universe(echo)
        
        # ---------- FRACTURE UNIVERSE ----------
        # Unstable, partially collapsed forest
        fracture_tiles = self._create_fractured_map()
        
        fracture = Universe(
            universe_type=UniverseType.FRACTURE,
            width=self.config.width,
            height=self.config.height
        )
        fracture.tilemap.tiles = fracture_tiles
        self.multiverse.add_universe(fracture)
    
    def _create_forest_map(self, living_tree: bool) -> List[List[TileType]]:
        """Create a forest tile map."""
        w, h = self.config.width, self.config.height
        
        # Initialize with floor (grass)
        tiles = [[TileType.FLOOR for _ in range(w)] for _ in range(h)]
        
        # Border walls (dense trees)
        for x in range(w):
            tiles[0][x] = TileType.WALL
            tiles[h-1][x] = TileType.WALL
        for y in range(h):
            tiles[y][0] = TileType.WALL
            tiles[y][w-1] = TileType.WALL
        
        # Forest grove pattern - scattered "tree walls"
        tree_positions = [
            (4, 3), (5, 3), (4, 4),
            (8, 2), (9, 2), (8, 3),
            (4, 14), (5, 14), (4, 15),
            (8, 15), (9, 15), (8, 16),
            (15, 3), (16, 3), (15, 4),
            (15, 14), (16, 14), (15, 15),
        ]
        for tx, ty in tree_positions:
            if ty < h and tx < w:
                tiles[ty][tx] = TileType.WALL
        
        # Central clearing for the Ancient Tree
        # The tree itself is an entity, but we leave the clearing open
        for y in range(7, 12):
            for x in range(10, 15):
                tiles[y][x] = TileType.FLOOR
        
        # Paths
        # Main horizontal path
        for x in range(1, w-1):
            tiles[9][x] = TileType.FLOOR
            if tiles[8][x] == TileType.WALL:
                pass
            else:
                tiles[8][x] = TileType.FLOOR
            if tiles[10][x] == TileType.WALL:
                pass
            else:
                tiles[10][x] = TileType.FLOOR
        
        # Pit/water surrounding the tree area (moat)
        if living_tree:
            # Living tree has protective moat
            for x in range(9, 16):
                tiles[6][x] = TileType.PIT
                tiles[12][x] = TileType.PIT
            tiles[7][9] = TileType.PIT
            tiles[11][9] = TileType.PIT
        else:
            # Dead tree - moat dried up
            pass
        
        # Key alcove (guarded by Shades in Prime)
        for y in range(4, 7):
            tiles[y][19] = TileType.FLOOR
            tiles[y][20] = TileType.FLOOR
            tiles[y][21] = TileType.FLOOR
        
        return tiles
    
    def _create_fractured_map(self) -> List[List[TileType]]:
        """Create the unstable Fracture universe map."""
        w, h = self.config.width, self.config.height
        
        # Start with base forest
        tiles = self._create_forest_map(living_tree=False)
        
        # Add reality tears (pits/hazards)
        fracture_zones = [
            (6, 4), (7, 4), (6, 5),
            (17, 7), (18, 7), (17, 8), (18, 8),
            (6, 12), (7, 12), (6, 13),
            (11, 5), (12, 5),
            (11, 13), (12, 13)
        ]
        for fx, fy in fracture_zones:
            if fy < h and fx < w:
                tiles[fy][fx] = TileType.HAZARD
        
        # Some walls collapsed
        collapse_positions = [
            (4, 3), (15, 3), (4, 14), (15, 14)
        ]
        for cx, cy in collapse_positions:
            if cy < h and cx < w:
                tiles[cy][cx] = TileType.FLOOR
        
        return tiles
    
    def _place_entities(self) -> None:
        """Place entities in the level."""
        
        # ---------- THE ANCIENT TREE ----------
        # Living in Prime, dead in Echo
        tree_prime = Tree(
            position=(12 * TILE_SIZE, 9 * TILE_SIZE),
            tree_id="ancient_tree",
            state="living"
        )
        self.add_entity(tree_prime, [UniverseType.PRIME])
        
        tree_echo = Tree(
            position=(12 * TILE_SIZE, 9 * TILE_SIZE),
            tree_id="ancient_tree_echo",
            state="dead"
        )
        self.add_entity(tree_echo, [UniverseType.ECHO])
        
        tree_fracture = Tree(
            position=(12 * TILE_SIZE, 9 * TILE_SIZE),
            tree_id="ancient_tree_fracture",
            state="stump"
        )
        self.add_entity(tree_fracture, [UniverseType.FRACTURE])
        
        # ---------- SHADES ----------
        # Guardians of the tree - only exist in Prime while tree lives
        shade1 = Shade(
            position=(18 * TILE_SIZE, 5 * TILE_SIZE),
            shade_id="shade_01",
            causal_origin_id="ancient_tree",
            patrol_points=[
                (18 * TILE_SIZE, 5 * TILE_SIZE),
                (19 * TILE_SIZE, 5 * TILE_SIZE),
                (19 * TILE_SIZE, 7 * TILE_SIZE),
                (18 * TILE_SIZE, 7 * TILE_SIZE)
            ]
        )
        self.add_entity(shade1, [UniverseType.PRIME])
        
        shade2 = Shade(
            position=(18 * TILE_SIZE, 11 * TILE_SIZE),
            shade_id="shade_02",
            causal_origin_id="ancient_tree",
            patrol_points=[
                (18 * TILE_SIZE, 11 * TILE_SIZE),
                (19 * TILE_SIZE, 11 * TILE_SIZE),
                (19 * TILE_SIZE, 13 * TILE_SIZE),
                (18 * TILE_SIZE, 13 * TILE_SIZE)
            ]
        )
        self.add_entity(shade2, [UniverseType.PRIME])
        
        # ---------- KEY ----------
        # Located in the guarded alcove
        key = Key(
            position=(20 * TILE_SIZE, 5 * TILE_SIZE),
            key_id="key_03"
        )
        self.add_entity(key, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])
        
        # ---------- BRIDGE ----------
        # Only exists in Echo (tree was cut down to build it long ago)
        bridge = Bridge(
            position=(9 * TILE_SIZE, 6 * TILE_SIZE),
            bridge_id="bridge_01",
            length=6,
            is_intact=True,
            material_source_id="ancient_tree"
        )
        self.add_entity(bridge, [UniverseType.ECHO])
        
        # ---------- DOORS ----------
        # Gate to the exit area
        gate = VariantDoor(
            position=(20 * TILE_SIZE, 9 * TILE_SIZE),
            door_id="exit_gate",
            prime_open=False,  # Closed while Shades exist
            echo_open=True     # Open in Echo (no Shades)
        )
        self.add_entity(gate, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])
        
        # ---------- EXIT PORTAL ----------
        exit_portal = ExitPortal(
            position=(22 * TILE_SIZE, 9 * TILE_SIZE),
            portal_id="exit_03",
            requires_keys=1
        )
        self.add_entity(exit_portal, [UniverseType.PRIME, UniverseType.ECHO, UniverseType.FRACTURE])
    
    def _setup_causality(self) -> None:
        """Set up causal relationships."""
        causal_graph = self.multiverse.causal_graph
        
        # Shades depend on the Tree for existence
        causal_graph.add_dependency(
            source_id="ancient_tree",
            target_id="shade_01",
            operator=CausalOperator.EXISTENCE
        )
        
        causal_graph.add_dependency(
            source_id="ancient_tree",
            target_id="shade_02",
            operator=CausalOperator.EXISTENCE
        )
        
        # Tree destruction affects the exit gate
        causal_graph.add_dependency(
            source_id="ancient_tree",
            target_id="exit_gate",
            operator=CausalOperator.INVERSE
        )
        
        # Bridge exists because tree was cut (paradox in Prime)
        causal_graph.add_dependency(
            source_id="ancient_tree",
            target_id="bridge_01",
            operator=CausalOperator.INVERSE
        )
    
    def update(self, dt: float) -> None:
        """Update level with tree destruction check."""
        super().update(dt)
        
        # Check if tree was destroyed in Prime
        if not self.tree_destroyed:
            for entity in self.entities.get(UniverseType.PRIME, []):
                if hasattr(entity, 'tree_id') and entity.tree_id == 'ancient_tree':
                    if entity.tree_state == 'stump':
                        self._on_tree_destroyed()
    
    def _on_tree_destroyed(self) -> None:
        """Handle tree destruction - cascade effects."""
        self.tree_destroyed = True
        
        EventSystem.emit(GameEvent.UI_MESSAGE, {
            "message": "The Ancient Tree falls... its guardians fade to nothing!",
            "type": "causal"
        })
        
        # Destroy all Shades
        for entity in self.entities.get(UniverseType.PRIME, []):
            if hasattr(entity, 'shade_id'):
                entity.on_causal_change(EntityState.DESTROYED, "ancient_tree")
        
        # Open the gate
        for entity_list in self.entities.values():
            for entity in entity_list:
                if getattr(entity, 'door_id', '') == 'exit_gate':
                    entity.open()
    
    def get_tutorial_messages(self) -> List[dict]:
        """Get tutorial messages for this level."""
        return [
            {
                "trigger": "start",
                "message": "A dark presence guards this grove. The Shades...",
                "position": (2, 9)
            },
            {
                "trigger": "see_shade",
                "message": "Shades cannot be harmed directly. Find their source.",
                "position": (17, 5)
            },
            {
                "trigger": "near_tree",
                "message": "This ancient tree... the Shades seem connected to it.",
                "position": (12, 9)
            },
            {
                "trigger": "first_fracture",
                "message": "The Fracture universe is unstable. Be careful!",
                "position": (2, 9)
            }
        ]
