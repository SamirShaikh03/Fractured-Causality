"""Shared sprite loading helpers with fallback support."""

import os
from typing import Optional, Tuple

import pygame

from ..core.settings import ASSETS_DIR


def load_entity_sprite(filename: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
    """Load and scale an entity sprite from assets/images/sprites.

    Returns None when the file does not exist or cannot be loaded.
    """
    sprite_dir = os.path.join(ASSETS_DIR, "images", "sprites")
    sprite_path = os.path.join(sprite_dir, filename)

    if not os.path.exists(sprite_path):
        return None

    try:
        sprite = pygame.image.load(sprite_path)
        sprite = sprite.convert_alpha()
        return pygame.transform.scale(sprite, size)
    except (OSError, ValueError, RuntimeError, TypeError):
        return None
