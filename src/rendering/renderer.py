"""
Renderer - Main rendering system for the game.

Handles all drawing operations with proper layering.
"""

import pygame
from typing import List, Tuple, Optional

from ..core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    COLOR_PRIME, COLOR_ECHO, COLOR_FRACTURE
)
from ..multiverse.universe import Universe, UniverseType, TileType
from ..systems.camera import Camera


class Renderer:
    """
    Main rendering system.
    
    Handles:
    - Tile map rendering
    - Entity rendering (with proper z-ordering)
    - UI rendering
    - Effects and overlays
    - Debug rendering
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the renderer.
        
        Args:
            screen: Main display surface
        """
        self.screen = screen
        
        # Rendering layers
        self._background_layer = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self._entity_layer = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self._effect_layer = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self._ui_layer = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        
        # Tile colors
        self._tile_colors = {
            TileType.FLOOR: (60, 60, 70),
            TileType.WALL: (40, 40, 50),
            TileType.PIT: (20, 20, 30),
            TileType.HAZARD: (80, 40, 40),
        }
        
        # Universe tints
        self._universe_tints = {
            UniverseType.PRIME: (50, 100, 200, 30),
            UniverseType.ECHO: (50, 200, 100, 30),
            UniverseType.FRACTURE: (200, 50, 50, 30),
        }
        
        # Debug mode
        self.debug_mode: bool = False
        
        # Font for debug
        pygame.font.init()
        self._debug_font = pygame.font.Font(None, 20)
    
    def clear(self) -> None:
        """Clear all layers."""
        self.screen.fill((0, 0, 0))
        self._background_layer.fill((0, 0, 0, 0))
        self._entity_layer.fill((0, 0, 0, 0))
        self._effect_layer.fill((0, 0, 0, 0))
        self._ui_layer.fill((0, 0, 0, 0))
    
    def render_universe(self, universe: Universe, 
                       camera: Camera) -> None:
        """
        Render a universe's tile map.
        
        Args:
            universe: Universe to render
            camera: Camera for view offset
        """
        if not universe or not universe.tilemap:
            return
        
        offset = camera.get_offset()
        
        # Get visible tiles
        left, top, right, bottom = camera.get_visible_tiles()
        
        # Clamp to universe bounds
        right = min(right, universe.width)
        bottom = min(bottom, universe.height)
        
        # Render tiles
        for y in range(max(0, top), bottom):
            for x in range(max(0, left), right):
                tile_type = universe.tilemap.get_tile(x, y)
                
                # Get base color
                color = self._tile_colors.get(tile_type, (50, 50, 50))
                
                # Apply universe tint
                tint = self._get_universe_color(universe.universe_type)
                color = self._blend_colors(color, tint[:3], 0.1)
                
                # Calculate screen position
                screen_x = x * TILE_SIZE - offset[0]
                screen_y = y * TILE_SIZE - offset[1]
                
                # Draw tile
                tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self._background_layer, color, tile_rect)
                
                # Draw tile border for visual clarity
                border_color = tuple(max(0, c - 15) for c in color)
                pygame.draw.rect(self._background_layer, border_color, tile_rect, 1)
                
                # Special tile effects
                if tile_type == TileType.PIT:
                    self._draw_pit_effect(screen_x, screen_y)
                elif tile_type == TileType.HAZARD:
                    self._draw_hazard_effect(screen_x, screen_y)
    
    def _draw_pit_effect(self, x: int, y: int) -> None:
        """Draw a pit tile effect."""
        # Darker center
        inner_rect = pygame.Rect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(self._background_layer, (10, 10, 15), inner_rect)
        
        # Gradient edges
        for i in range(4):
            edge_color = (10 + i * 5, 10 + i * 5, 15 + i * 3, 100)
            pygame.draw.rect(
                self._background_layer,
                edge_color[:3],
                pygame.Rect(x + i, y + i, TILE_SIZE - i * 2, TILE_SIZE - i * 2),
                1
            )
    
    def _draw_hazard_effect(self, x: int, y: int) -> None:
        """Draw a hazard tile effect."""
        import math
        # Pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        
        color = (int(100 * pulse), int(40 * pulse), int(40 * pulse))
        pygame.draw.rect(
            self._background_layer,
            color,
            pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
        )
        
        # Warning pattern
        pattern_color = (int(150 * pulse), int(80 * pulse), 40)
        for i in range(0, TILE_SIZE, 16):
            pygame.draw.line(
                self._background_layer,
                pattern_color,
                (x + i, y),
                (x, y + i),
                2
            )
    
    def render_entities(self, entities: List, camera: Camera) -> None:
        """
        Render entities with proper z-ordering.
        
        Args:
            entities: List of entities to render
            camera: Camera for view offset
        """
        offset = camera.get_offset()
        
        # Sort by y position for pseudo-3D layering
        sorted_entities = sorted(entities, key=lambda e: e.y)
        
        for entity in sorted_entities:
            if not entity.visible or not entity.exists:
                continue
            
            # Check if in view
            if not camera.is_visible(entity.x, entity.y, 
                                    entity.width, entity.height):
                continue
            
            # Render entity
            entity.render(self._entity_layer, offset)
            
            # Debug rendering
            if self.debug_mode:
                self._draw_entity_debug(entity, offset)
    
    def _draw_entity_debug(self, entity, offset: Tuple[int, int]) -> None:
        """Draw debug info for an entity."""
        x = int(entity.x - offset[0])
        y = int(entity.y - offset[1])
        
        # Bounding box
        rect = pygame.Rect(x, y, entity.width, entity.height)
        color = (0, 255, 0) if entity.solid else (0, 255, 255)
        pygame.draw.rect(self._entity_layer, color, rect, 1)
        
        # Entity ID
        label = self._debug_font.render(
            getattr(entity, 'entity_id', 'unknown')[:15],
            True, (255, 255, 0)
        )
        self._entity_layer.blit(label, (x, y - 15))
    
    def render_player(self, player, camera: Camera) -> None:
        """
        Render the player (always on top of entities).
        
        Args:
            player: Player entity
            camera: Camera for view offset
        """
        offset = camera.get_offset()
        player.render(self._entity_layer, offset)
        
        if self.debug_mode:
            self._draw_entity_debug(player, offset)
    
    def apply_universe_overlay(self, universe_type: UniverseType) -> None:
        """
        Apply a color overlay for the current universe.
        
        Args:
            universe_type: Current universe type
        """
        tint = self._universe_tints.get(universe_type)
        if tint:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(tint)
            self._effect_layer.blit(overlay, (0, 0))
    
    def _get_universe_color(self, universe_type: UniverseType) -> Tuple[int, int, int, int]:
        """Get the color for a universe type."""
        return self._universe_tints.get(universe_type, (100, 100, 100, 30))
    
    def _blend_colors(self, color1: Tuple[int, int, int],
                     color2: Tuple[int, int, int],
                     factor: float) -> Tuple[int, int, int]:
        """Blend two colors."""
        return tuple(
            int(c1 * (1 - factor) + c2 * factor)
            for c1, c2 in zip(color1, color2)
        )
    
    def composite(self) -> None:
        """Composite all layers to the screen."""
        self.screen.blit(self._background_layer, (0, 0))
        self.screen.blit(self._entity_layer, (0, 0))
        self.screen.blit(self._effect_layer, (0, 0))
        self.screen.blit(self._ui_layer, (0, 0))
    
    def get_ui_layer(self) -> pygame.Surface:
        """Get the UI layer for UI components to draw on."""
        return self._ui_layer
    
    def get_effect_layer(self) -> pygame.Surface:
        """Get the effect layer for effects to draw on."""
        return self._effect_layer
    
    def toggle_debug(self) -> bool:
        """Toggle debug rendering."""
        self.debug_mode = not self.debug_mode
        return self.debug_mode
    
    def draw_debug_info(self, info: dict) -> None:
        """
        Draw debug information.
        
        Args:
            info: Dictionary of debug values
        """
        if not self.debug_mode:
            return
        
        y = 100
        for key, value in info.items():
            text = f"{key}: {value}"
            label = self._debug_font.render(text, True, (255, 255, 0))
            self._ui_layer.blit(label, (SCREEN_WIDTH - 200, y))
            y += 18
