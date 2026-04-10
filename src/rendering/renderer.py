   

import pygame
from typing import List, Tuple

from ..core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    get_ui_font
)
from ..multiverse.universe import Universe, UniverseType, TileType
from ..systems.camera import Camera


class Renderer:
       
    
    def __init__(self, screen: pygame.Surface):
           
        self.screen = screen
        
                          
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
        
                                      
        self._tile_colors = {
            TileType.FLOOR: (55, 58, 68),
            TileType.WALL: (35, 37, 48),
            TileType.PIT: (15, 15, 22),
            TileType.HAZARD: (75, 35, 35),
        }
        
                            
        self._wall_highlight = (50, 52, 65)
        self._wall_shadow = (25, 26, 35)
        self._floor_accent = (48, 50, 60)
        
                        
        self._universe_tints = {
            UniverseType.PRIME: (50, 100, 200, 30),
            UniverseType.ECHO: (50, 200, 100, 30),
            UniverseType.FRACTURE: (200, 50, 50, 30),
        }

                                                                    
                                                               
        self._overlay_cache: dict[UniverseType, pygame.Surface] = {}
        
                    
        self.debug_mode: bool = False
        
                        
        pygame.font.init()
        self._debug_font = get_ui_font(20)
    
    def clear(self) -> None:
                               
        self.screen.fill((0, 0, 0))
        self._background_layer.fill((0, 0, 0, 0))
        self._entity_layer.fill((0, 0, 0, 0))
        self._effect_layer.fill((0, 0, 0, 0))
        self._ui_layer.fill((0, 0, 0, 0))
    
    def render_universe(self, universe: Universe, 
                       camera: Camera) -> None:
           
        if not universe or not universe.tilemap:
            return
        
        offset = camera.get_offset()
        
                           
        left, top, right, bottom = camera.get_visible_tiles()
        
                                  
        right = min(right, universe.width)
        bottom = min(bottom, universe.height)
        
                      
        for y in range(max(0, top), bottom):
            for x in range(max(0, left), right):
                tile_type = universe.tilemap.get_tile(x, y)
                
                                
                color = self._tile_colors.get(tile_type, (50, 50, 50))
                
                                     
                tint = self._get_universe_color(universe.universe_type)
                color = self._blend_colors(color, tint[:3], 0.1)
                
                                           
                screen_x = x * TILE_SIZE - offset[0]
                screen_y = y * TILE_SIZE - offset[1]
                
                           
                tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self._background_layer, color, tile_rect)
                
                                                   
                if tile_type == TileType.FLOOR:
                    border_color = tuple(max(0, c - 10) for c in color)
                    pygame.draw.rect(self._background_layer, border_color, tile_rect, 1)
                                                            
                    accent = tuple(min(255, c + 8) for c in color)
                    pygame.draw.line(self._background_layer, accent,
                                   (screen_x + 1, screen_y + 1),
                                   (screen_x + 4, screen_y + 1), 1)
                elif tile_type == TileType.WALL:
                                                                          
                    pygame.draw.line(self._background_layer, self._wall_highlight,
                                   (screen_x, screen_y),
                                   (screen_x + TILE_SIZE - 1, screen_y), 1)
                    pygame.draw.line(self._background_layer, self._wall_highlight,
                                   (screen_x, screen_y),
                                   (screen_x, screen_y + TILE_SIZE - 1), 1)
                    pygame.draw.line(self._background_layer, self._wall_shadow,
                                   (screen_x + TILE_SIZE - 1, screen_y + 1),
                                   (screen_x + TILE_SIZE - 1, screen_y + TILE_SIZE - 1), 1)
                    pygame.draw.line(self._background_layer, self._wall_shadow,
                                   (screen_x + 1, screen_y + TILE_SIZE - 1),
                                   (screen_x + TILE_SIZE - 1, screen_y + TILE_SIZE - 1), 1)
                else:
                    border_color = tuple(max(0, c - 15) for c in color)
                    pygame.draw.rect(self._background_layer, border_color, tile_rect, 1)
                
                                      
                if tile_type == TileType.PIT:
                    self._draw_pit_effect(screen_x, screen_y)
                elif tile_type == TileType.HAZARD:
                    self._draw_hazard_effect(screen_x, screen_y)
    
    def _draw_pit_effect(self, x: int, y: int) -> None:
                                     
                       
        inner_rect = pygame.Rect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(self._background_layer, (10, 10, 15), inner_rect)
        
                        
        for i in range(4):
            edge_color = (10 + i * 5, 10 + i * 5, 15 + i * 3, 100)
            pygame.draw.rect(
                self._background_layer,
                edge_color[:3],
                pygame.Rect(x + i, y + i, TILE_SIZE - i * 2, TILE_SIZE - i * 2),
                1
            )
    
    def _draw_hazard_effect(self, x: int, y: int) -> None:
                                        
        import math
                        
        pulse = abs(math.sin(pygame.time.get_ticks() / 500)) * 0.3 + 0.7
        
        color = (int(100 * pulse), int(40 * pulse), int(40 * pulse))
        pygame.draw.rect(
            self._background_layer,
            color,
            pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
        )
        
                         
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
           
        offset = camera.get_offset()
        from ..entities.ghost_entity import GhostEntity
        
                                                   
        sorted_entities = sorted(entities, key=lambda e: e.y)
        
        for entity in sorted_entities:
            if not entity.visible or not entity.exists:
                continue

            if isinstance(entity, GhostEntity):
                continue
            
                              
            if not camera.is_visible(entity.x, entity.y, 
                                    entity.width, entity.height):
                continue
            
                           
            entity.render(self._entity_layer, offset)
            
                             
            if self.debug_mode:
                self._draw_entity_debug(entity, offset)
    
    def _draw_entity_debug(self, entity, offset: Tuple[int, int]) -> None:
                                            
        x = int(entity.x - offset[0])
        y = int(entity.y - offset[1])
        
        rect = pygame.Rect(x, y, entity.width, entity.height)
        color = (0, 255, 0) if entity.solid else (0, 255, 255)
        pygame.draw.rect(self._entity_layer, color, rect, 1)
        
        label = self._debug_font.render(
            getattr(entity, 'entity_id', 'unknown')[:15],
            True, (255, 255, 0)
        )
        self._entity_layer.blit(label, (x, y - 15))
    
    def render_player(self, player, camera: Camera) -> None:
           
        offset = camera.get_offset()
        player.render(self._entity_layer, offset)
        
        if self.debug_mode:
            self._draw_entity_debug(player, offset)
    
    def apply_universe_overlay(self, universe_type: UniverseType) -> None:
           
        tint = self._universe_tints.get(universe_type)
        if tint:
            overlay = self._overlay_cache.get(universe_type)
            if overlay is None:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill(tint)
                self._overlay_cache[universe_type] = overlay
            self._effect_layer.blit(overlay, (0, 0))
    
    def _get_universe_color(self, universe_type: UniverseType) -> Tuple[int, int, int, int]:
                                                
        return self._universe_tints.get(universe_type, (100, 100, 100, 30))
    
    def _blend_colors(self, color1: Tuple[int, int, int],
                     color2: Tuple[int, int, int],
                     factor: float) -> Tuple[int, int, int]:
                               
        return tuple(
            int(c1 * (1 - factor) + c2 * factor)
            for c1, c2 in zip(color1, color2)
        )
    
    def composite(self) -> None:
                                                 
        self.screen.blit(self._background_layer, (0, 0))
        self.screen.blit(self._entity_layer, (0, 0))
        self.screen.blit(self._effect_layer, (0, 0))
        self.screen.blit(self._ui_layer, (0, 0))
    
    def get_ui_layer(self) -> pygame.Surface:
                                                            
        return self._ui_layer
    
    def get_effect_layer(self) -> pygame.Surface:
                                                          
        return self._effect_layer
    
    def toggle_debug(self) -> bool:
                                     
        self.debug_mode = not self.debug_mode
        return self.debug_mode
    
    def draw_debug_info(self, info: dict) -> None:
           
        if not self.debug_mode:
            return
        
        y = 100
        for key, value in info.items():
            text = f"{key}: {value}"
            label = self._debug_font.render(text, True, (255, 255, 0))
            self._ui_layer.blit(label, (SCREEN_WIDTH - 200, y))
            y += 18
