"""
HUD - Heads-Up Display for in-game information.

Displays paradox level, keys, universe indicator, and messages.
Features a cyberpunk/neon aesthetic.
"""

import pygame
from typing import List, Tuple
from dataclasses import dataclass
import time

from ..core.settings import (
    COLOR_PRIME,
    PARADOX_STABLE, PARADOX_UNSTABLE, PARADOX_CRITICAL,
    PLAYER_MAX_HEALTH
)
from ..core.events import EventSystem, GameEvent
from .design_system import UI_PALETTE, get_ui_fonts
from .components import draw_stat_box, draw_center_label_box, draw_bottom_bar, hud_layout, get_ui_scale


# Basic HUD colors
HUD_CYAN = (95, 180, 220)
HUD_GOLD = (190, 165, 95)
HUD_BG_DARK = (20, 24, 30)
HUD_TEXT_BRIGHT = (255, 255, 255)
HUD_TEXT_DIM = (165, 170, 180)


@dataclass
class Message:
    """A UI message to display."""
    text: str
    type: str  # "info", "warning", "success", "causal", "error"
    timestamp: float
    duration: float = 3.0
    alpha: float = 255.0


class HUD:
    """
    Heads-Up Display showing game information.
    
    Displays:
    - Paradox meter
    - Keys collected
    - Current universe indicator
    - Tutorial/status messages
    - Causal sight indicator
    """
    
    def __init__(self):
        """Initialize the HUD."""
        # Font initialization
        pygame.font.init()
        self._ui_scale: float = 1.0
        self._fonts = get_ui_fonts(self._ui_scale)
        self._font_large = self._fonts["title"]
        self._font_medium = self._fonts["primary"]
        self._font_small = self._fonts["secondary"]
        self._font_tiny = self._fonts["hint"]
        
        # State
        self._paradox_level: float = 0.0
        self._keys_collected: int = 0
        self._keys_required: int = 0
        self._current_universe: str = "PRIME"
        self._current_level_name: str = ""
        self._universe_color: Tuple[int, int, int] = COLOR_PRIME
        self._causal_sight_active: bool = False
        
        # Health state
        self._player_health: int = PLAYER_MAX_HEALTH
        self._player_max_health: int = PLAYER_MAX_HEALTH
        self._health_flash: float = 0.0
        
        # Messages
        self._messages: List[Message] = []
        self._max_messages: int = 5
        
        # Animation
        self._paradox_pulse: float = 0.0
        self._universe_flash: float = 0.0
        
        # Subscribe to events
        EventSystem.subscribe(GameEvent.PARADOX_CHANGED, self._on_paradox_changed)
        EventSystem.subscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.subscribe(GameEvent.UNIVERSE_SWITCHED, self._on_universe_switched)
        EventSystem.subscribe(GameEvent.CAUSAL_SIGHT_TOGGLED, self._on_causal_sight)
        EventSystem.subscribe(GameEvent.UI_MESSAGE, self._on_message)
        EventSystem.subscribe(GameEvent.PLAYER_DAMAGED, self._on_player_damaged)
        EventSystem.subscribe(GameEvent.PLAYER_HEALED, self._on_player_healed)
        EventSystem.subscribe(GameEvent.LEVEL_STARTED, self._on_level_started)
    
    def update(self, dt: float) -> None:
        """
        Update HUD animations and messages.
        
        Args:
            dt: Delta time
        """
        # Update paradox pulse
        if self._paradox_level > PARADOX_CRITICAL:
            self._paradox_pulse += dt * 5.0
        elif self._paradox_level > PARADOX_UNSTABLE:
            self._paradox_pulse += dt * 2.0
        else:
            self._paradox_pulse = 0.0
        
        # Update universe flash
        if self._universe_flash > 0:
            self._universe_flash -= dt * 3.0
        
        # Update health flash
        if self._health_flash > 0:
            self._health_flash -= dt * 4.0
        
        # Update messages
        current_time = time.time()
        for message in self._messages[:]:
            age = current_time - message.timestamp
            
            if age > message.duration:
                self._messages.remove(message)
            elif age > message.duration - 0.5:
                # Fade out
                message.alpha = 255 * (message.duration - age) / 0.5
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the HUD.
        
        Args:
            surface: Target surface
        """
        self._refresh_fonts_for_surface(surface)
        layout = hud_layout(surface)

        self._render_paradox_meter(surface, layout["paradox"])
        self._render_key_counter(surface, layout["keys"])
        self._render_universe_indicator(surface, layout["center"])
        self._render_health_bar(surface, layout["health"])
        self._render_causal_sight_indicator(surface, layout["center"])
        self._render_messages(surface)
        self._render_controls_reminder(surface)

    def _refresh_fonts_for_surface(self, surface: pygame.Surface) -> None:
        """Rebuild fonts when UI scale changes for resolution responsiveness."""
        scale = get_ui_scale(surface)
        if abs(scale - self._ui_scale) < 0.02:
            return

        self._ui_scale = scale
        self._fonts = get_ui_fonts(scale)
        self._font_large = self._fonts["title"]
        self._font_medium = self._fonts["primary"]
        self._font_small = self._fonts["secondary"]
        self._font_tiny = self._fonts["hint"]
    
    def _render_paradox_meter(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a basic paradox meter."""
        fill_width = int((rect.width - 4) * (self._paradox_level / 100))

        if self._paradox_level < PARADOX_STABLE:
            color = UI_PALETTE.info
        elif self._paradox_level < PARADOX_UNSTABLE:
            color = UI_PALETTE.warning
        elif self._paradox_level < PARADOX_CRITICAL:
            color = (200, 125, 70)
        else:
            color = UI_PALETTE.error

        draw_stat_box(
            surface,
            rect,
            "PARADOX",
            f"{int(self._paradox_level)}%",
            self._font_small,
            self._font_medium,
            accent_color=color,
            text_color=UI_PALETTE.text_primary,
        )

        if fill_width > 0:
            fill_rect = pygame.Rect(rect.x + 2, rect.bottom - 7, fill_width, 5)
            pygame.draw.rect(surface, color, fill_rect)
    
    def _render_health_bar(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render the player health bar."""
        health_pct = self._player_health / self._player_max_health if self._player_max_health > 0 else 0
        fill_width = int((rect.width - 4) * health_pct)

        if health_pct > 0.6:
            color = UI_PALETTE.success
        elif health_pct > 0.3:
            color = UI_PALETTE.warning
        else:
            color = UI_PALETTE.error

        if self._health_flash > 0:
            flash_intensity = self._health_flash
            color = (
                min(255, int(color[0] + (255 - color[0]) * flash_intensity)),
                int(color[1] * (1 - flash_intensity * 0.5)),
                int(color[2] * (1 - flash_intensity * 0.5))
            )

        draw_stat_box(
            surface,
            rect,
            "HEALTH",
            f"{self._player_health}/{self._player_max_health}",
            self._font_small,
            self._font_medium,
            accent_color=color,
            text_color=UI_PALETTE.text_primary,
        )

        if fill_width > 0:
            fill_rect = pygame.Rect(rect.x + 2, rect.bottom - 7, fill_width, 5)
            pygame.draw.rect(surface, color, fill_rect)
    
    def _render_key_counter(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a basic key counter."""
        draw_stat_box(
            surface,
            rect,
            "KEYS",
            f"{self._keys_collected}/{self._keys_required}",
            self._font_small,
            self._font_medium,
            accent_color=UI_PALETTE.warning,
            text_color=UI_PALETTE.text_primary,
        )
    
    def _render_universe_indicator(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a basic universe indicator."""
        header = self._current_level_name or "UNKNOWN LEVEL"
        text = f"{header} | {self._current_universe}"
        draw_center_label_box(
            surface,
            rect,
            text,
            self._font_small,
            border_color=self._universe_color,
            text_color=self._universe_color,
        )
    
    def _render_causal_sight_indicator(self, surface: pygame.Surface, center_rect: pygame.Rect) -> None:
        """Render causal sight status text."""
        if not self._causal_sight_active:
            return

        label = self._font_small.render("CAUSAL SIGHT ON", True, UI_PALETTE.info)
        width = label.get_width() + 16
        height = 24
        x = center_rect.centerx - width // 2
        y = center_rect.bottom + 6

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, UI_PALETTE.panel_soft, rect)
        pygame.draw.rect(surface, UI_PALETTE.info, rect, 1)
        surface.blit(label, (x + 8, y + (height - label.get_height()) // 2))
    
    def _render_messages(self, surface: pygame.Surface) -> None:
        """Render status messages as plain text with simple boxes."""
        x = surface.get_width() // 2
        y = surface.get_height() - 100
        
        type_colors = {
            "info": UI_PALETTE.text_primary,
            "warning": UI_PALETTE.warning,
            "success": UI_PALETTE.success,
            "causal": UI_PALETTE.info,
            "error": UI_PALETTE.error,
        }
        type_accents = {
            "info": UI_PALETTE.border,
            "warning": UI_PALETTE.warning,
            "success": UI_PALETTE.success,
            "causal": UI_PALETTE.info,
            "error": UI_PALETTE.error,
        }
        
        for i, message in enumerate(self._messages):
            color = type_colors.get(message.type, (200, 200, 200))
            
            text = self._font_medium.render(message.text, True, color)
            text.set_alpha(int(message.alpha))
            
            text_x = x - text.get_width() // 2
            text_y = y - i * 32
            
            bg_w = text.get_width() + 16
            bg_h = text.get_height() + 6
            bg_surface = pygame.Surface((bg_w, bg_h))
            bg_surface.set_alpha(int(message.alpha * 0.7))
            bg_surface.fill(UI_PALETTE.panel_soft)
            border = type_accents.get(message.type, (120, 120, 120))
            pygame.draw.rect(bg_surface, border, (0, 0, bg_w, bg_h), 1)
            surface.blit(bg_surface, (text_x - 8, text_y - 3))
            
            surface.blit(text, (text_x, text_y))
    
    def show_message(self, text: str, msg_type: str = "info",
                    duration: float = 3.0) -> None:
        """
        Show a message on the HUD.
        
        Args:
            text: Message text
            msg_type: Message type
            duration: Display duration
        """
        message = Message(
            text=text,
            type=msg_type,
            timestamp=time.time(),
            duration=duration
        )
        
        self._messages.insert(0, message)
        
        # Limit message count
        while len(self._messages) > self._max_messages:
            self._messages.pop()
    
    def set_keys(self, collected: int, required: int) -> None:
        """Set the key counter."""
        self._keys_collected = collected
        self._keys_required = required
    
    def set_player_health(self, health: int, max_health: int) -> None:
        """Set player health values directly."""
        self._player_health = health
        self._player_max_health = max_health
    
    # Event handlers
    def _on_paradox_changed(self, data: dict) -> None:
        self._paradox_level = data.get("level", 0.0)
    
    def _on_item_collected(self, data: dict) -> None:
        if data.get("item_type") == "key":
            self._keys_collected += 1
    
    def _on_universe_switched(self, data: dict) -> None:
        self._current_universe = data.get("universe", "PRIME")
        self._universe_color = data.get("color", COLOR_PRIME)
        self._universe_flash = 1.0

    def _on_level_started(self, data: dict) -> None:
        self._current_level_name = data.get("level_name", "")
    
    def _on_causal_sight(self, data: dict) -> None:
        self._causal_sight_active = data.get("active", False)
    
    def _on_player_damaged(self, data: dict) -> None:
        self._player_health = data.get("health", self._player_health)
        self._health_flash = 1.0
    
    def _on_player_healed(self, data: dict) -> None:
        self._player_health = data.get("health", self._player_health)
    
    def _on_message(self, data: dict) -> None:
        self.show_message(
            data.get("message", ""),
            data.get("type", "info"),
            data.get("duration", 3.0)
        )
    
    def cleanup(self) -> None:
        """Clean up event subscriptions."""
        EventSystem.unsubscribe(GameEvent.PARADOX_CHANGED, self._on_paradox_changed)
        EventSystem.unsubscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.unsubscribe(GameEvent.UNIVERSE_SWITCHED, self._on_universe_switched)
        EventSystem.unsubscribe(GameEvent.CAUSAL_SIGHT_TOGGLED, self._on_causal_sight)
        EventSystem.unsubscribe(GameEvent.UI_MESSAGE, self._on_message)
        EventSystem.unsubscribe(GameEvent.PLAYER_DAMAGED, self._on_player_damaged)
        EventSystem.unsubscribe(GameEvent.PLAYER_HEALED, self._on_player_healed)
        EventSystem.unsubscribe(GameEvent.LEVEL_STARTED, self._on_level_started)
    
    def _render_controls_reminder(self, surface: pygame.Surface) -> None:
        """Render a plain controls reminder."""
        hint = "WASD Move | Space Switch | E Interact | F Attack | Tab Sight | Esc Pause"
        draw_bottom_bar(surface, hint, self._font_tiny)
