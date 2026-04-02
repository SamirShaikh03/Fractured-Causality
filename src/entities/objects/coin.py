"""Coin - A collectible for scoring."""

import pygame
from typing import Tuple

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...core.events import EventSystem, GameEvent


class Coin(Entity):
    """
    A coin collectible that grants points when touched by the player.
    """
    
    def __init__(self, position: Tuple[float, float], coin_id: str = None):
        config = EntityConfig(
            position=position,
            size=(16, 16),
            color=(255, 200, 50),
            persistence=EntityPersistence.EXCLUSIVE,
            solid=False,
            interactive=True
        )
        super().__init__(config)
        
        if coin_id:
            self.entity_id = coin_id
        
        self.coin_value = 10
        self._rotation = 0.0
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.circle(self.sprite, (255, 200, 50), (8, 8), 8)
        pygame.draw.circle(self.sprite, (255, 255, 100), (8, 8), 6)
        pygame.draw.circle(self.sprite, (200, 150, 20), (8, 8), 4)
    
    def update(self, dt: float) -> None:
        self._rotation += dt * 180
        if self._rotation > 360:
            self._rotation -= 360
        super().update(dt)
    
    def interact(self, interactor) -> bool:
        if hasattr(interactor, 'entity_id') and interactor.entity_id == 'player':
            EventSystem.emit(GameEvent.ITEM_COLLECTED, {
                "item_type": "coin",
                "value": self.coin_value,
                "entity_id": self.entity_id
            })
            self.destroy()
            return True
        return False

    def collect(self, interactor) -> bool:
        return self.interact(interactor)
    
    def render(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        surface.blit(self.sprite, (render_x, render_y))
