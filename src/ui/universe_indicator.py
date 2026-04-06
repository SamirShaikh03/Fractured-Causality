   

import pygame
from typing import Tuple

from ..core.settings import (
    SCREEN_WIDTH, COLOR_PRIME, COLOR_ECHO, COLOR_FRACTURE, get_ui_font
)
from ..multiverse.universe import UniverseType


class UniverseIndicator:
       
    
    def __init__(self):
                                                
        pygame.font.init()
        self._font = get_ui_font(24)
        
                       
        self._current_type: UniverseType = UniverseType.PRIME
        self._current_color: Tuple[int, int, int] = COLOR_PRIME

                  
        self._x = SCREEN_WIDTH - 180
        self._y = 20
        self._width = 160
        self._height = 30
    
    def set_universe(self, universe_type: UniverseType) -> None:
           
        self._current_type = universe_type
        
        if universe_type == UniverseType.PRIME:
            self._current_color = COLOR_PRIME
        elif universe_type == UniverseType.ECHO:
            self._current_color = COLOR_ECHO
        else:
            self._current_color = COLOR_FRACTURE
    
    def update(self, dt: float) -> None:
           
        _ = dt
    
    def render(self, surface: pygame.Surface) -> None:
           
        panel = pygame.Rect(self._x, self._y, self._width, self._height)
        pygame.draw.rect(surface, (20, 24, 30), panel)
        pygame.draw.rect(surface, self._current_color, panel, 2)

        label = self._font.render(f"UNIVERSE: {self._current_type.name}", True, self._current_color)
        label_x = self._x + (self._width - label.get_width()) // 2
        label_y = self._y + (self._height - label.get_height()) // 2
        surface.blit(label, (label_x, label_y))
