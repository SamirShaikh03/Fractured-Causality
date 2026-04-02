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
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_PRIME,
    PARADOX_STABLE, PARADOX_UNSTABLE, PARADOX_CRITICAL,
    PLAYER_MAX_HEALTH,
    get_ui_font
)
from ..core.events import EventSystem, GameEvent


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
        self._font_large = get_ui_font(36)
        self._font_medium = get_ui_font(28)
        self._font_small = get_ui_font(22)
        self._font_tiny = get_ui_font(16)
        
        # State
        self._paradox_level: float = 0.0
        self._keys_collected: int = 0
        self._keys_required: int = 0
        self._current_universe: str = "PRIME"
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
        self._render_health_bar(surface)
        self._render_paradox_meter(surface)
        self._render_key_counter(surface)
        self._render_universe_indicator(surface)
        self._render_causal_sight_indicator(surface)
        self._render_messages(surface)
        self._render_controls_reminder(surface)
    
    def _render_paradox_meter(self, surface: pygame.Surface) -> None:
        """Render a basic paradox meter."""
        x, y = 20, 20
        width, height = 220, 28

        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HUD_BG_DARK, bg_rect)

        fill_width = int((width - 4) * (self._paradox_level / 100))

        if self._paradox_level < PARADOX_STABLE:
            color = HUD_CYAN
        elif self._paradox_level < PARADOX_UNSTABLE:
            color = HUD_GOLD
        elif self._paradox_level < PARADOX_CRITICAL:
            color = (200, 125, 70)
        else:
            color = (200, 75, 75)

        if fill_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
            pygame.draw.rect(surface, color, fill_rect)

        border_color = color if self._paradox_level > 0 else HUD_CYAN
        pygame.draw.rect(surface, border_color, bg_rect, 2)

        label = self._font_small.render("PARADOX", True, HUD_TEXT_DIM)
        surface.blit(label, (x + 6, y + 6))

        pct_text = f"{int(self._paradox_level)}%"
        pct = self._font_medium.render(pct_text, True, HUD_TEXT_BRIGHT)
        surface.blit(pct, (x + width - pct.get_width() - 8, y + 4))
    
    def _render_health_bar(self, surface: pygame.Surface) -> None:
        """Render the player health bar."""
        x = SCREEN_WIDTH - 240
        y = 20
        width, height = 220, 28

        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HUD_BG_DARK, bg_rect)

        health_pct = self._player_health / self._player_max_health if self._player_max_health > 0 else 0
        fill_width = int((width - 4) * health_pct)

        if health_pct > 0.6:
            color = (75, 180, 100)
        elif health_pct > 0.3:
            color = HUD_GOLD
        else:
            color = (190, 80, 80)

        if self._health_flash > 0:
            flash_intensity = self._health_flash
            color = (
                min(255, int(color[0] + (255 - color[0]) * flash_intensity)),
                int(color[1] * (1 - flash_intensity * 0.5)),
                int(color[2] * (1 - flash_intensity * 0.5))
            )

        if fill_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
            pygame.draw.rect(surface, color, fill_rect)

        border_color = color if health_pct > 0 else (100, 100, 100)
        pygame.draw.rect(surface, border_color, bg_rect, 2)

        label = self._font_small.render("HEALTH", True, HUD_TEXT_DIM)
        surface.blit(label, (x + 6, y + 6))

        hp_text = f"{self._player_health}/{self._player_max_health}"
        hp = self._font_medium.render(hp_text, True, HUD_TEXT_BRIGHT)
        surface.blit(hp, (x + width - hp.get_width() - 8, y + 4))
    
    def _render_key_counter(self, surface: pygame.Surface) -> None:
        """Render a basic key counter."""
        x, y = 20, 58

        panel_rect = pygame.Rect(x - 4, y - 2, 170, 28)
        pygame.draw.rect(surface, HUD_BG_DARK, panel_rect)
        pygame.draw.rect(surface, HUD_GOLD, panel_rect, 1)

        text = self._font_medium.render(
            f"KEYS {self._keys_collected}/{self._keys_required}",
            True,
            HUD_TEXT_BRIGHT,
        )
        surface.blit(text, (x + 6, y))
    
    def _render_universe_indicator(self, surface: pygame.Surface) -> None:
        """Render a basic universe indicator."""
        width, height = 170, 30
        x = (SCREEN_WIDTH - width) // 2
        y = 18

        bg_color = tuple(int(c * 0.2) for c in self._universe_color)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, bg_color, bg_rect)
        pygame.draw.rect(surface, self._universe_color, bg_rect, 2)

        label = self._font_medium.render(f"UNIVERSE: {self._current_universe}", True, self._universe_color)
        label_x = x + (width - label.get_width()) // 2
        label_y = y + (height - label.get_height()) // 2
        surface.blit(label, (label_x, label_y))
    
    def _render_causal_sight_indicator(self, surface: pygame.Surface) -> None:
        """Render causal sight status text."""
        if not self._causal_sight_active:
            return

        label = self._font_small.render("CAUSAL SIGHT ON", True, (180, 190, 220))
        width = label.get_width() + 16
        height = 24
        x = (SCREEN_WIDTH - width) // 2
        y = 56

        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HUD_BG_DARK, rect)
        pygame.draw.rect(surface, (120, 130, 165), rect, 1)
        surface.blit(label, (x + 8, y + (height - label.get_height()) // 2))
    
    def _render_messages(self, surface: pygame.Surface) -> None:
        """Render status messages as plain text with simple boxes."""
        x = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 100
        
        type_colors = {
            "info": (200, 200, 200),
            "warning": (255, 200, 80),
            "success": (80, 255, 120),
            "causal": (160, 170, 255),
            "error": (255, 90, 90),
        }
        type_accents = {
            "info": (120, 140, 160),
            "warning": (180, 140, 40),
            "success": (50, 180, 80),
            "causal": (110, 110, 200),
            "error": (180, 50, 50),
        }
        
        for i, message in enumerate(self._messages):
            color = type_colors.get(message.type, (200, 200, 200))
            
            text = self._font_medium.render(message.text, True, color)
            text.set_alpha(int(message.alpha))
            
            text_x = x - text.get_width() // 2
            text_y = y - i * 32
            
            bg_w = text.get_width() + 16
            bg_h = text.get_height() + 6
            bg_surface = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (16, 18, 24, int(message.alpha * 0.65)), (0, 0, bg_w, bg_h))
            border = type_accents.get(message.type, (120, 120, 120))
            pygame.draw.rect(bg_surface, (*border, int(message.alpha * 0.45)), (0, 0, bg_w, bg_h), 1)
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
    
    def _render_controls_reminder(self, surface: pygame.Surface) -> None:
        """Render a plain controls reminder."""
        hint = "WASD Move | Space Switch | E Interact | F Attack | Tab Sight | Esc Pause"
        text = self._font_tiny.render(hint, True, HUD_TEXT_DIM)
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT - 26
        surface.blit(text, (x, y))
