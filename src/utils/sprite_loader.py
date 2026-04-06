import os
from typing import Dict, Optional, Tuple

import pygame

from ..core.settings import ASSETS_DIR


_sprite_cache: Dict[Tuple[str, Tuple[int, int]], Optional[pygame.Surface]] = {}


def load_entity_sprite(filename: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
       
    cache_key = (filename, size)
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]

    sprite_dir = os.path.join(ASSETS_DIR, "images", "sprites")
    sprite_path = os.path.join(sprite_dir, filename)

    if not os.path.exists(sprite_path):
        _sprite_cache[cache_key] = None
        return None

    try:
        sprite = pygame.image.load(sprite_path)
        sprite = sprite.convert_alpha()
        scaled = pygame.transform.scale(sprite, size)
        _sprite_cache[cache_key] = scaled
        return scaled
    except (OSError, ValueError, RuntimeError, TypeError):
        _sprite_cache[cache_key] = None
        return None


def clear_sprite_cache() -> None:
                                                                             
    _sprite_cache.clear()
