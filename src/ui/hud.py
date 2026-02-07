"""
HUD - Heads-Up Display for in-game information.

Displays paradox level, keys, universe indicator, and messages.
Features a cyberpunk/neon aesthetic.
"""

import pygame
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import time

from ..core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, 
    COLOR_PRIME, COLOR_ECHO, COLOR_FRACTURE,
    PARADOX_STABLE, PARADOX_UNSTABLE, PARADOX_CRITICAL,
    PLAYER_MAX_HEALTH
)
from ..core.events import EventSystem, GameEvent


# Cyberpunk theme colors
HUD_NEON_CYAN = (0, 255, 255)
HUD_NEON_MAGENTA = (255, 0, 128)
HUD_NEON_GOLD = (255, 215, 0)
HUD_BG_DARK = (16, 16, 32)
HUD_TEXT_BRIGHT = (255, 255, 255)
HUD_TEXT_DIM = (140, 140, 160)


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
        self._font_large = pygame.font.Font(None, 36)
        self._font_medium = pygame.font.Font(None, 28)
        self._font_small = pygame.font.Font(None, 22)
        
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
        """Render the paradox meter with cyberpunk styling."""
        x, y = 20, 20
        width, height = 220, 28
        
        # Outer glow/border
        glow_rect = pygame.Rect(x - 3, y - 3, width + 6, height + 6)
        pygame.draw.rect(surface, (30, 30, 50), glow_rect, border_radius=6)
        
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HUD_BG_DARK, bg_rect, border_radius=4)
        
        # Fill based on paradox level
        fill_width = int((width - 4) * (self._paradox_level / 100))
        
        # Color gradient based on level
        if self._paradox_level < PARADOX_STABLE:
            color = HUD_NEON_CYAN  # Cyan - stable
        elif self._paradox_level < PARADOX_UNSTABLE:
            color = HUD_NEON_GOLD  # Gold - unstable
        elif self._paradox_level < PARADOX_CRITICAL:
            color = (255, 128, 0)  # Orange - critical
        else:
            # Pulsing magenta/red for collapse
            pulse = abs(math.sin(self._paradox_pulse))
            color = (200 + int(55 * pulse), int(50 * (1 - pulse)), int(80 * (1 - pulse)))
        
        if fill_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
            pygame.draw.rect(surface, color, fill_rect, border_radius=2)
            
            # Scanline effect
            for i in range(0, fill_width, 4):
                pygame.draw.line(surface, (*color[:3], 100), 
                               (x + 2 + i, y + 2), (x + 2 + i, y + height - 3))
        
        # Neon border
        border_color = color if self._paradox_level > 0 else HUD_NEON_CYAN
        pygame.draw.rect(surface, border_color, bg_rect, 2, border_radius=4)
        
        # Label with glow
        label = self._font_small.render("PARADOX", True, HUD_TEXT_DIM)
        surface.blit(label, (x + 6, y + 6))
        
        # Percentage with neon effect
        pct_text = f"{int(self._paradox_level)}%"
        pct = self._font_medium.render(pct_text, True, HUD_TEXT_BRIGHT)
        surface.blit(pct, (x + width - pct.get_width() - 8, y + 4))
    
    def _render_health_bar(self, surface: pygame.Surface) -> None:
        """Render the player health bar."""
        # Position on the right side of screen
        x = SCREEN_WIDTH - 240
        y = 20
        width, height = 220, 28
        
        # Outer glow/border
        glow_rect = pygame.Rect(x - 3, y - 3, width + 6, height + 6)
        pygame.draw.rect(surface, (30, 30, 50), glow_rect, border_radius=6)
        
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HUD_BG_DARK, bg_rect, border_radius=4)
        
        # Calculate fill width
        health_pct = self._player_health / self._player_max_health if self._player_max_health > 0 else 0
        fill_width = int((width - 4) * health_pct)
        
        # Color based on health level
        if health_pct > 0.6:
            color = (50, 220, 100)  # Green - healthy
        elif health_pct > 0.3:
            color = HUD_NEON_GOLD  # Gold - caution
        else:
            color = (220, 50, 50)  # Red - danger
        
        # Flash red when damaged
        if self._health_flash > 0:
            flash_intensity = self._health_flash
            color = (
                min(255, int(color[0] + (255 - color[0]) * flash_intensity)),
                int(color[1] * (1 - flash_intensity * 0.5)),
                int(color[2] * (1 - flash_intensity * 0.5))
            )
        
        if fill_width > 0:
            fill_rect = pygame.Rect(x + 2, y + 2, fill_width, height - 4)
            pygame.draw.rect(surface, color, fill_rect, border_radius=2)
            
            # Scanline effect
            for i in range(0, fill_width, 4):
                pygame.draw.line(surface, (*color[:3], 100), 
                               (x + 2 + i, y + 2), (x + 2 + i, y + height - 3))
        
        # Neon border
        border_color = color if health_pct > 0 else (100, 100, 100)
        pygame.draw.rect(surface, border_color, bg_rect, 2, border_radius=4)
        
        # Label
        label = self._font_small.render("HEALTH", True, HUD_TEXT_DIM)
        surface.blit(label, (x + 6, y + 6))
        
        # Health value
        hp_text = f"{self._player_health}/{self._player_max_health}"
        hp = self._font_medium.render(hp_text, True, HUD_TEXT_BRIGHT)
        surface.blit(hp, (x + width - hp.get_width() - 8, y + 4))
    
    def _render_key_counter(self, surface: pygame.Surface) -> None:
        """Render the key counter with neon styling."""
        x, y = 20, 58
        
        # Background panel
        panel_rect = pygame.Rect(x - 4, y - 4, 100, 32)
        pygame.draw.rect(surface, HUD_BG_DARK, panel_rect, border_radius=4)
        pygame.draw.rect(surface, HUD_NEON_GOLD, panel_rect, 1, border_radius=4)
        
        # Key icon (diamond shape)
        icon_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(icon_surface, HUD_NEON_GOLD, [
            (10, 0), (20, 10), (10, 20), (0, 10)
        ])
        pygame.draw.circle(icon_surface, (40, 40, 40), (10, 10), 4)
        pygame.draw.circle(icon_surface, HUD_NEON_GOLD, (10, 10), 2)
        
        surface.blit(icon_surface, (x, y))
        
        # Count with glow
        count_text = f"{self._keys_collected}/{self._keys_required}"
        count = self._font_medium.render(count_text, True, HUD_TEXT_BRIGHT)
        surface.blit(count, (x + 26, y + 1))
    
    def _render_universe_indicator(self, surface: pygame.Surface) -> None:
        """Render the current universe indicator with cyberpunk styling."""
        x = SCREEN_WIDTH - 160
        y = 20
        width, height = 140, 40
        
        # Background with universe color tint
        bg_color = tuple(int(c * 0.2) for c in self._universe_color)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=6)
        
        # Inner darker area
        inner_rect = pygame.Rect(x + 2, y + 2, width - 4, height - 4)
        pygame.draw.rect(surface, HUD_BG_DARK, inner_rect, border_radius=4)
        
        # Flash on switch
        if self._universe_flash > 0:
            flash_alpha = int(150 * self._universe_flash)
            flash_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            flash_surface.fill((*self._universe_color, flash_alpha))
            surface.blit(flash_surface, (x, y))
        
        # Neon border with glow
        pygame.draw.rect(surface, self._universe_color, bg_rect, 2, border_radius=6)
        
        # Universe symbol (geometric shape)
        symbol_x = x + 12
        symbol_y = y + height // 2
        if self._current_universe == "PRIME":
            # Circle for Prime
            pygame.draw.circle(surface, self._universe_color, (symbol_x, symbol_y), 8, 2)
        elif self._current_universe == "ECHO":
            # Double circle for Echo
            pygame.draw.circle(surface, self._universe_color, (symbol_x - 4, symbol_y), 6, 2)
            pygame.draw.circle(surface, self._universe_color, (symbol_x + 4, symbol_y), 6, 2)
        else:
            # Triangle for Fracture
            points = [(symbol_x, symbol_y - 8), (symbol_x - 7, symbol_y + 5), (symbol_x + 7, symbol_y + 5)]
            pygame.draw.polygon(surface, self._universe_color, points, 2)
        
        # Label
        label = self._font_medium.render(self._current_universe, True, self._universe_color)
        label_x = x + 30
        label_y = y + (height - label.get_height()) // 2
        surface.blit(label, (label_x, label_y))
    
    def _render_causal_sight_indicator(self, surface: pygame.Surface) -> None:
        """Render the causal sight indicator."""
        if not self._causal_sight_active:
            return
        
        x = SCREEN_WIDTH - 150
        y = 62
        
        # Eye icon
        icon_surface = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(icon_surface, (180, 180, 255), (0, 4, 24, 16))
        pygame.draw.circle(icon_surface, (80, 80, 200), (12, 12), 6)
        pygame.draw.circle(icon_surface, (40, 40, 100), (12, 12), 3)
        
        surface.blit(icon_surface, (x, y))
        
        # Label
        label = self._font_small.render("CAUSAL SIGHT", True, (180, 180, 255))
        surface.blit(label, (x + 28, y + 4))
    
    def _render_messages(self, surface: pygame.Surface) -> None:
        """Render status messages."""
        x = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 100
        
        for i, message in enumerate(self._messages):
            # Get message color
            if message.type == "info":
                color = (200, 200, 200)
            elif message.type == "warning":
                color = (255, 200, 80)
            elif message.type == "success":
                color = (80, 255, 80)
            elif message.type == "causal":
                color = (180, 180, 255)
            elif message.type == "error":
                color = (255, 80, 80)
            else:
                color = (200, 200, 200)
            
            # Render with alpha
            text = self._font_medium.render(message.text, True, color)
            text.set_alpha(int(message.alpha))
            
            # Center horizontally
            text_x = x - text.get_width() // 2
            text_y = y - i * 28
            
            # Background
            bg_rect = pygame.Rect(
                text_x - 10, text_y - 2,
                text.get_width() + 20, text.get_height() + 4
            )
            bg_surface = pygame.Surface(
                (bg_rect.width, bg_rect.height), 
                pygame.SRCALPHA
            )
            bg_surface.fill((0, 0, 0, int(message.alpha * 0.5)))
            surface.blit(bg_surface, (bg_rect.x, bg_rect.y))
            
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
        """Render a subtle controls reminder at the bottom of the screen."""
        # Context-sensitive controls
        controls_left = "WASD: Move"
        controls_mid = "SPACE: Switch Universe  |  E: Interact  |  F: Attack"
        controls_right = "TAB: Causal Sight  |  ESC: Pause"
        
        full_text = f"{controls_left}  |  {controls_mid}  |  {controls_right}"
        
        # Render with subtle styling
        text = self._font_small.render(full_text, True, HUD_TEXT_DIM)
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT - 25
        
        # Dark background for readability
        bg_rect = pygame.Rect(x - 12, y - 4, text.get_width() + 24, text.get_height() + 8)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 100))
        pygame.draw.rect(bg_surface, (60, 60, 80, 80), (0, 0, bg_rect.width, bg_rect.height), 1, border_radius=6)
        surface.blit(bg_surface, (bg_rect.x, bg_rect.y))
        
        surface.blit(text, (x, y))
