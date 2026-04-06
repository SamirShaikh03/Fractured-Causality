   

import pygame

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from .design_system import UI_CONTAINER, UI_PALETTE, UI_SPACING


def get_ui_scale(surface: pygame.Surface) -> float:
                                                           
    return min(
        surface.get_width() / SCREEN_WIDTH,
        surface.get_height() / SCREEN_HEIGHT,
    )


def sx(value: int, scale: float) -> int:
                                                                        
    if value <= 0:
        return 0
    return max(1, int(round(value * scale)))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               bg_color=None, border_color=None,
               border_width: int = None, radius: int = None,
               alpha: int = 235) -> None:
                                                                 
    bg = bg_color or UI_PALETTE.panel
    border = border_color or UI_PALETTE.border
    width = UI_CONTAINER.border if border_width is None else border_width
    corner = UI_CONTAINER.radius if radius is None else radius

    panel = pygame.Surface((rect.width, rect.height))
    panel.set_alpha(alpha)
    panel.fill(bg)
    pygame.draw.rect(panel, border, (0, 0, rect.width, rect.height), width, border_radius=corner)
    surface.blit(panel, rect.topleft)


def draw_stat_box(surface: pygame.Surface, rect: pygame.Rect,
                  label: str, value: str,
                  label_font, value_font,
                  accent_color=None,
                  text_color=None) -> None:
                                                                  
    accent = accent_color or UI_PALETTE.border
    text = text_color or UI_PALETTE.text_primary

    draw_panel(surface, rect, bg_color=UI_PALETTE.panel, border_color=accent)

    label_surf = label_font.render(label, True, UI_PALETTE.text_secondary)
    value_surf = value_font.render(value, True, text)

    lx = rect.x + UI_CONTAINER.pad_x
    ly = rect.y + (rect.height - label_surf.get_height()) // 2
    vx = rect.right - value_surf.get_width() - UI_CONTAINER.pad_x
    vy = rect.y + (rect.height - value_surf.get_height()) // 2

    surface.blit(label_surf, (lx, ly))
    surface.blit(value_surf, (vx, vy))


def draw_center_label_box(surface: pygame.Surface, rect: pygame.Rect,
                          text: str, font,
                          border_color=None, text_color=None) -> None:
                                                              
    border = border_color or UI_PALETTE.border
    fg = text_color or UI_PALETTE.text_primary

    draw_panel(surface, rect, bg_color=UI_PALETTE.panel_soft, border_color=border)
    text_surf = font.render(text, True, fg)
    tx = rect.x + (rect.width - text_surf.get_width()) // 2
    ty = rect.y + (rect.height - text_surf.get_height()) // 2
    surface.blit(text_surf, (tx, ty))


def draw_bottom_bar(surface: pygame.Surface, text: str, font) -> None:
                                                   
    scale = get_ui_scale(surface)
    margin = sx(UI_SPACING.large, scale)
    height = sx(22, scale)

    rect = pygame.Rect(
        margin,
        surface.get_height() - margin - height,
        surface.get_width() - margin * 2,
        height,
    )
    draw_panel(surface, rect, bg_color=UI_PALETTE.panel_soft, border_color=UI_PALETTE.border, alpha=220)

    text_surf = font.render(text, True, UI_PALETTE.text_secondary)
    tx = rect.x + (rect.width - text_surf.get_width()) // 2
    ty = rect.y + (rect.height - text_surf.get_height()) // 2
    surface.blit(text_surf, (tx, ty))


def hud_layout(surface: pygame.Surface) -> dict:
       
    scale = get_ui_scale(surface)
    margin = sx(UI_SPACING.large, scale)
    gap = sx(UI_SPACING.medium, scale)
    bar_h = sx(UI_CONTAINER.height, scale)

    stat_w = sx(240, scale)
    center_min_w = sx(280, scale)
    center_gap = 10

    paradox = pygame.Rect(margin, margin, stat_w, bar_h)
    keys = pygame.Rect(margin, paradox.bottom + gap, stat_w, bar_h)
    health = pygame.Rect(surface.get_width() - margin - stat_w, margin, stat_w, bar_h)

    center_left = paradox.right + center_gap
    center_right = health.left - center_gap
    center_w = max(center_min_w, center_right - center_left)
    center = pygame.Rect(center_left, margin, center_w, bar_h)

    return {
        "paradox": paradox,
        "keys": keys,
        "center": center,
        "health": health,
    }
