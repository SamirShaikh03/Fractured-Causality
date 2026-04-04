"""Global UI design tokens and helpers.

Single source of truth for typography, spacing, container styling,
and palette used across menu, HUD, and in-game overlays.
"""

from dataclasses import dataclass
from typing import Dict

from ..core.settings import get_ui_font


@dataclass(frozen=True)
class TypographyScale:
    title: int = 24
    primary: int = 18
    secondary: int = 14
    hint: int = 12


@dataclass(frozen=True)
class SpacingScale:
    small: int = 4
    medium: int = 8
    large: int = 16
    section: int = 32


@dataclass(frozen=True)
class ContainerStyle:
    height: int = 32
    pad_x: int = 8
    pad_y: int = 6
    border: int = 2
    radius: int = 4


@dataclass(frozen=True)
class Palette:
    bg: tuple = (18, 20, 24)
    panel: tuple = (30, 36, 48)
    panel_soft: tuple = (24, 28, 38)
    border: tuple = (140, 160, 210)
    text_primary: tuple = (245, 248, 255)
    text_secondary: tuple = (165, 180, 205)
    warning: tuple = (220, 140, 95)
    success: tuple = (105, 175, 120)
    info: tuple = (120, 170, 230)
    error: tuple = (215, 95, 95)


UI_TYPOGRAPHY = TypographyScale()
UI_SPACING = SpacingScale()
UI_CONTAINER = ContainerStyle()
UI_PALETTE = Palette()


def get_ui_fonts(scale: float = 1.0) -> Dict[str, object]:
    """Build a font set for the current UI scale."""
    safe_scale = max(0.75, min(2.0, scale))
    return {
        "title": get_ui_font(max(10, int(UI_TYPOGRAPHY.title * safe_scale))),
        "primary": get_ui_font(max(10, int(UI_TYPOGRAPHY.primary * safe_scale))),
        "secondary": get_ui_font(max(10, int(UI_TYPOGRAPHY.secondary * safe_scale))),
        "hint": get_ui_font(max(10, int(UI_TYPOGRAPHY.hint * safe_scale))),
    }
