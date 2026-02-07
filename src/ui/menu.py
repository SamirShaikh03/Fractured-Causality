"""
Menu System - Game menus and UI navigation.

Handles main menu, pause menu, and level select.
Features clean design with proper spacing and layout.
"""

import pygame
import math
from typing import List, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# CLEAN THEME COLORS
# =============================================================================
THEME_BG_DARK = (20, 22, 30)
THEME_BG_MEDIUM = (30, 32, 45)
THEME_BG_PANEL = (25, 28, 40)
THEME_ACCENT_PRIMARY = (100, 160, 255)  # Blue
THEME_ACCENT_SECONDARY = (255, 180, 100)  # Orange/Gold
THEME_ACCENT_SUCCESS = (100, 220, 130)  # Green
THEME_ACCENT_DANGER = (255, 100, 100)  # Red
THEME_TEXT_BRIGHT = (255, 255, 255)
THEME_TEXT_DIM = (160, 160, 180)
THEME_TEXT_DISABLED = (80, 80, 100)


class MenuState(Enum):
    """Menu states."""
    MAIN = auto()
    HOW_TO_PLAY = auto()
    PAUSE = auto()
    LEVEL_SELECT = auto()
    SETTINGS = auto()
    CREDITS = auto()
    GAME_OVER = auto()
    LEVEL_COMPLETE = auto()


@dataclass
class MenuItem:
    """A menu item with click support."""
    label: str
    action: Callable[[], None]
    enabled: bool = True
    selected: bool = False
    hover: bool = False
    rect: pygame.Rect = None


class Menu:
    """
    Menu system for the game.
    
    Features:
    - Clean, readable design
    - Smooth transitions
    - Proper spacing and layout
    - Mouse and keyboard support
    """
    
    def __init__(self):
        """Initialize the menu system."""
        pygame.font.init()
        
        # Fonts - varied sizes for hierarchy
        self._font_title = pygame.font.Font(None, 82)
        self._font_subtitle = pygame.font.Font(None, 36)
        self._font_large = pygame.font.Font(None, 42)
        self._font_medium = pygame.font.Font(None, 32)
        self._font_small = pygame.font.Font(None, 26)
        self._font_tiny = pygame.font.Font(None, 22)
        
        # State
        self._state: MenuState = MenuState.MAIN
        self._items: List[MenuItem] = []
        self._selected_index: int = 0
        self._is_visible: bool = True
        
        # Animation
        self._pulse: float = 0.0
        self._time: float = 0.0
        
        # Mouse tracking
        self._mouse_pos: Tuple[int, int] = (0, 0)
        
        # Callbacks
        self._on_play: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        self._on_resume: Optional[Callable] = None
        self._on_restart: Optional[Callable] = None
        self._on_next_level: Optional[Callable] = None
        self._on_main_menu: Optional[Callable] = None
        
        # Initialize main menu
        self._setup_main_menu()
    
    def _setup_main_menu(self) -> None:
        """Set up main menu items - simple and clear."""
        self._items = [
            MenuItem("▶  START GAME", self._on_play_clicked),
            MenuItem("?  HOW TO PLAY", self._on_how_to_play_clicked),
            MenuItem("✕  QUIT", self._on_quit_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_how_to_play(self) -> None:
        """Set up how to play screen."""
        self._items = [
            MenuItem("◄  BACK TO MENU", lambda: self.set_state(MenuState.MAIN)),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_pause_menu(self) -> None:
        """Set up pause menu items."""
        self._items = [
            MenuItem("▶  RESUME", self._on_resume_clicked),
            MenuItem("↺  RESTART LEVEL", self._on_restart_clicked),
            MenuItem("⌂  MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_game_over(self) -> None:
        """Set up game over menu."""
        self._items = [
            MenuItem("↺  TRY AGAIN", self._on_restart_clicked),
            MenuItem("⌂  MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_level_complete(self) -> None:
        """Set up level complete menu."""
        self._items = [
            MenuItem("▶  NEXT LEVEL", self._on_next_level_clicked),
            MenuItem("↺  REPLAY", self._on_restart_clicked),
            MenuItem("⌂  MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _update_selection(self) -> None:
        """Update item selection states."""
        for i, item in enumerate(self._items):
            item.selected = (i == self._selected_index)
    
    def set_state(self, state: MenuState) -> None:
        """Change menu state."""
        self._state = state
        
        if state == MenuState.MAIN:
            self._setup_main_menu()
        elif state == MenuState.HOW_TO_PLAY:
            self._setup_how_to_play()
        elif state == MenuState.PAUSE:
            self._setup_pause_menu()
        elif state == MenuState.GAME_OVER:
            self._setup_game_over()
        elif state == MenuState.LEVEL_COMPLETE:
            self._setup_level_complete()
    
    def show(self) -> None:
        """Show the menu."""
        self._is_visible = True
    
    def hide(self) -> None:
        """Hide the menu."""
        self._is_visible = False
    
    def navigate_up(self) -> None:
        """Navigate up in the menu."""
        if not self._items:
            return
        
        self._selected_index -= 1
        if self._selected_index < 0:
            self._selected_index = len(self._items) - 1
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index -= 1
            if self._selected_index < 0:
                self._selected_index = len(self._items) - 1
            attempts += 1
        
        self._update_selection()
    
    def navigate_down(self) -> None:
        """Navigate down in the menu."""
        if not self._items:
            return
        
        self._selected_index += 1
        if self._selected_index >= len(self._items):
            self._selected_index = 0
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index += 1
            if self._selected_index >= len(self._items):
                self._selected_index = 0
            attempts += 1
        
        self._update_selection()
    
    def select(self) -> None:
        """Select the current menu item."""
        if not self._items:
            return
        
        item = self._items[self._selected_index]
        if item.enabled and item.action:
            item.action()
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input events including mouse."""
        if not self._is_visible:
            return False
        
        # Mouse motion - update hover states
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
            self._update_hover_states()
            return True
        
        # Mouse click - select item
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, item in enumerate(self._items):
                if item.rect and item.rect.collidepoint(event.pos) and item.enabled:
                    self._selected_index = i
                    self._update_selection()
                    item.action()
                    return True
        
        # Keyboard input
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.navigate_up()
                return True
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.navigate_down()
                return True
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.select()
                return True
            elif event.key == pygame.K_ESCAPE:
                if self._state == MenuState.PAUSE:
                    self._on_resume_clicked()
                    return True
                elif self._state in [MenuState.HOW_TO_PLAY, MenuState.CREDITS]:
                    self.set_state(MenuState.MAIN)
                    return True
        
        return False
    
    def _update_hover_states(self) -> None:
        """Update item hover states based on mouse position."""
        for i, item in enumerate(self._items):
            if item.rect and item.rect.collidepoint(self._mouse_pos):
                item.hover = True
                if item.enabled:
                    self._selected_index = i
                    self._update_selection()
            else:
                item.hover = False
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        self._pulse += dt * 3.0
        self._time += dt
        if self._pulse > 6.28:
            self._pulse -= 6.28
    
    def render(self, surface: pygame.Surface) -> None:
        """Render the menu with clean design."""
        if not self._is_visible:
            return
        
        # Dark background
        self._draw_background(surface)
        
        # Simple borders
        self._draw_borders(surface)
        
        # State-specific rendering
        if self._state == MenuState.HOW_TO_PLAY:
            self._draw_how_to_play(surface)
        else:
            self._draw_standard_menu(surface)
        
        # Controls hint at bottom
        self._draw_controls_hint(surface)
    
    def _draw_background(self, surface: pygame.Surface) -> None:
        """Draw gradient background."""
        # Vertical gradient
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(20 + progress * 10)
            g = int(22 + progress * 10)
            b = int(35 + progress * 15)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def _draw_borders(self, surface: pygame.Surface) -> None:
        """Draw simple border lines."""
        border_color = THEME_ACCENT_PRIMARY
        
        # Top border
        pygame.draw.line(surface, border_color, (60, 30), (SCREEN_WIDTH - 60, 30), 2)
        # Bottom border
        pygame.draw.line(surface, border_color, (60, SCREEN_HEIGHT - 30), 
                        (SCREEN_WIDTH - 60, SCREEN_HEIGHT - 30), 2)
    
    def _draw_standard_menu(self, surface: pygame.Surface) -> None:
        """Draw standard menu with title and buttons."""
        # Title section (top third)
        self._draw_title(surface)
        
        # Menu buttons (center)
        self._draw_menu_items(surface)
    
    def _draw_title(self, surface: pygame.Surface) -> None:
        """Draw title."""
        title_text = self._get_title()
        subtitle_text = self._get_subtitle()
        
        # Calculate positions
        title_y = 80
        
        # Main title
        title = self._font_title.render(title_text, True, THEME_TEXT_BRIGHT)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, title_y))
        
        # Subtitle
        if subtitle_text:
            subtitle = self._font_subtitle.render(subtitle_text, True, THEME_TEXT_DIM)
            subtitle_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
            surface.blit(subtitle, (subtitle_x, title_y + 75))
        
        # Decorative line under title
        line_y = title_y + 110
        line_width = 250
        line_x = (SCREEN_WIDTH - line_width) // 2
        pygame.draw.line(surface, THEME_ACCENT_SECONDARY, 
                        (line_x, line_y), (line_x + line_width, line_y), 2)
    
    def _draw_menu_items(self, surface: pygame.Surface) -> None:
        """Draw menu items with clean styling."""
        btn_width = 300
        btn_height = 55
        btn_spacing = 18
        
        # Position buttons in center-bottom area
        total_height = len(self._items) * (btn_height + btn_spacing) - btn_spacing
        start_y = SCREEN_HEIGHT // 2 + 50
        
        for i, item in enumerate(self._items):
            x = (SCREEN_WIDTH - btn_width) // 2
            y = start_y + i * (btn_height + btn_spacing)
            
            # Store rect for click detection
            rect = pygame.Rect(x, y, btn_width, btn_height)
            item.rect = rect
            
            # Determine colors based on state
            if not item.enabled:
                bg_color = THEME_BG_MEDIUM
                border_color = THEME_TEXT_DISABLED
                text_color = THEME_TEXT_DISABLED
            elif item.selected or item.hover:
                bg_color = (40, 50, 70)
                border_color = THEME_ACCENT_PRIMARY
                text_color = THEME_TEXT_BRIGHT
            else:
                bg_color = (30, 35, 50)
                border_color = (60, 65, 85)
                text_color = THEME_TEXT_DIM
            
            # Button background
            pygame.draw.rect(surface, bg_color, rect, border_radius=10)
            
            # Border
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)
            
            # Selection indicator
            if item.selected or item.hover:
                indicator = pygame.Rect(x - 5, y + 18, 3, btn_height - 36)
                pygame.draw.rect(surface, THEME_ACCENT_PRIMARY, indicator)
            
            # Item text (centered)
            text = self._font_large.render(item.label, True, text_color)
            text_x = x + (btn_width - text.get_width()) // 2
            text_y = y + (btn_height - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))
    
    def _draw_controls_hint(self, surface: pygame.Surface) -> None:
        """Draw control hints at bottom."""
        hint = "Arrow Keys / Mouse: Navigate  |  ENTER / Click: Select  |  ESC: Back"
        text = self._font_tiny.render(hint, True, THEME_TEXT_DIM)
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT - 50
        surface.blit(text, (x, y))
    
    # =========================================================================
    # HOW TO PLAY SCREEN
    # =========================================================================
    
    def _draw_how_to_play(self, surface: pygame.Surface) -> None:
        """Draw the how to play/tutorial screen with proper layout."""
        # Title at top
        title = self._font_title.render("HOW TO PLAY", True, THEME_TEXT_BRIGHT)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, 45))
        
        # Decorative line under title
        line_y = 110
        pygame.draw.line(surface, THEME_ACCENT_SECONDARY, 
                        (SCREEN_WIDTH // 2 - 120, line_y), 
                        (SCREEN_WIDTH // 2 + 120, line_y), 2)
        
        # Layout: Two columns on top, one wide panel below
        panel_margin = 40
        panel_gap = 25
        top_panel_width = (SCREEN_WIDTH - panel_margin * 2 - panel_gap) // 2
        top_panel_height = 210
        top_panel_y = 135
        
        # Left panel - Controls
        left_x = panel_margin
        self._draw_tutorial_panel(
            surface, left_x, top_panel_y, top_panel_width, top_panel_height,
            "CONTROLS", THEME_ACCENT_PRIMARY, [
                ("W A S D", "Move your character"),
                ("SPACE", "Switch between universes"),
                ("E", "Interact with objects"),
                ("F", "Attack enemies"),
                ("TAB", "Toggle Causal Sight"),
                ("ESC", "Pause the game"),
            ]
        )
        
        # Right panel - Objective
        right_x = panel_margin + top_panel_width + panel_gap
        self._draw_tutorial_panel(
            surface, right_x, top_panel_y, top_panel_width, top_panel_height,
            "OBJECTIVE", THEME_ACCENT_SECONDARY, [
                ("Goal", "Reach the EXIT PORTAL"),
                ("Keys", "Collect to unlock doors"),
                ("Enemies", "Defeat or avoid them"),
                ("Health", "Don't let it reach zero!"),
                ("Paradox", "Keep it low to survive"),
            ]
        )
        
        # Bottom panel - Universe System (full width)
        bottom_y = top_panel_y + top_panel_height + panel_gap
        bottom_width = SCREEN_WIDTH - panel_margin * 2
        self._draw_tutorial_panel(
            surface, panel_margin, bottom_y, bottom_width, 140,
            "UNIVERSE SYSTEM", THEME_ACCENT_SUCCESS, [
                ("PRIME (Blue)", "The original, stable timeline - your starting point"),
                ("ECHO (Green)", "A parallel dimension where things are different"),
                ("FRACTURE (Red)", "An unstable reality with unique challenges"),
            ], wide=True
        )
        
        # Tip box at bottom
        tip_y = bottom_y + 155
        tip_text = "TIP: If a path is blocked, try switching to another universe!"
        tip = self._font_small.render(tip_text, True, THEME_ACCENT_SUCCESS)
        tip_x = (SCREEN_WIDTH - tip.get_width()) // 2
        
        # Tip background
        tip_bg = pygame.Rect(tip_x - 15, tip_y - 5, tip.get_width() + 30, tip.get_height() + 10)
        pygame.draw.rect(surface, (25, 40, 30), tip_bg, border_radius=5)
        pygame.draw.rect(surface, THEME_ACCENT_SUCCESS, tip_bg, 1, border_radius=5)
        surface.blit(tip, (tip_x, tip_y))
        
        # Back button at very bottom
        btn_y = SCREEN_HEIGHT - 90
        btn_width = 280
        btn_height = 50
        btn_x = (SCREEN_WIDTH - btn_width) // 2
        
        self._items[0].rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        
        item = self._items[0]
        is_selected = item.selected or item.hover
        
        bg_color = (40, 50, 70) if is_selected else (30, 35, 50)
        border_color = THEME_ACCENT_PRIMARY if is_selected else (60, 65, 85)
        text_color = THEME_TEXT_BRIGHT if is_selected else THEME_TEXT_DIM
        
        pygame.draw.rect(surface, bg_color, item.rect, border_radius=10)
        pygame.draw.rect(surface, border_color, item.rect, 2, border_radius=10)
        
        text = self._font_large.render(item.label, True, text_color)
        text_x = btn_x + (btn_width - text.get_width()) // 2
        text_y = btn_y + (btn_height - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))
    
    def _draw_tutorial_panel(self, surface: pygame.Surface, x: int, y: int,
                             width: int, height: int, title: str, 
                             accent_color: tuple, items: list, wide: bool = False) -> None:
        """Draw a tutorial information panel with proper spacing."""
        # Panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, THEME_BG_PANEL, panel_rect, border_radius=12)
        
        # Accent border
        pygame.draw.rect(surface, accent_color, panel_rect, 2, border_radius=12)
        
        # Title bar
        title_bar_height = 38
        title_bar = pygame.Surface((width, title_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(title_bar, (*accent_color[:3], 40), (0, 0, width, title_bar_height),
                        border_top_left_radius=12, border_top_right_radius=12)
        surface.blit(title_bar, (x, y))
        
        # Title text
        title_surf = self._font_medium.render(title, True, accent_color)
        title_x = x + (width - title_surf.get_width()) // 2
        surface.blit(title_surf, (title_x, y + 8))
        
        # Content items
        content_y = y + title_bar_height + 12
        item_height = 26
        
        for key, value in items:
            # Key (left side)
            key_surf = self._font_small.render(key, True, THEME_ACCENT_PRIMARY)
            surface.blit(key_surf, (x + 18, content_y))
            
            # Value (right side, or offset for wide panel)
            if wide:
                value_x = x + 200
            else:
                value_x = x + 140
            
            value_surf = self._font_small.render(value, True, THEME_TEXT_DIM)
            surface.blit(value_surf, (value_x, content_y))
            
            content_y += item_height
    
    def _get_title(self) -> str:
        """Get title based on state."""
        if self._state == MenuState.MAIN:
            return "FRACTURED"
        elif self._state == MenuState.PAUSE:
            return "PAUSED"
        elif self._state == MenuState.GAME_OVER:
            return "REALITY COLLAPSED"
        elif self._state == MenuState.LEVEL_COMPLETE:
            return "TIMELINE SECURED"
        elif self._state == MenuState.CREDITS:
            return "CREDITS"
        else:
            return ""
    
    def _get_subtitle(self) -> str:
        """Get subtitle based on state."""
        if self._state == MenuState.MAIN:
            return "[ C A U S A L I T Y ]"
        elif self._state == MenuState.GAME_OVER:
            return "The paradox has consumed all timelines."
        elif self._state == MenuState.LEVEL_COMPLETE:
            return "Balance restored. Next dimension awaits."
        return ""
    
    # Callbacks
    def set_callbacks(self, 
                     on_play: Callable = None,
                     on_quit: Callable = None,
                     on_resume: Callable = None,
                     on_restart: Callable = None,
                     on_next_level: Callable = None,
                     on_main_menu: Callable = None) -> None:
        """Set menu callbacks."""
        self._on_play = on_play
        self._on_quit = on_quit
        self._on_resume = on_resume
        self._on_restart = on_restart
        self._on_next_level = on_next_level
        self._on_main_menu = on_main_menu
    
    def _on_play_clicked(self) -> None:
        if self._on_play:
            self._on_play()
    
    def _on_how_to_play_clicked(self) -> None:
        """Show how to play screen."""
        self.set_state(MenuState.HOW_TO_PLAY)
    
    def _on_quit_clicked(self) -> None:
        if self._on_quit:
            self._on_quit()
    
    def _on_resume_clicked(self) -> None:
        if self._on_resume:
            self._on_resume()
    
    def _on_restart_clicked(self) -> None:
        if self._on_restart:
            self._on_restart()
    
    def _on_next_level_clicked(self) -> None:
        if self._on_next_level:
            self._on_next_level()
    
    def _on_main_menu_clicked(self) -> None:
        if self._on_main_menu:
            self._on_main_menu()
    
    def _on_settings_clicked(self) -> None:
        pass
    
    def _on_credits_clicked(self) -> None:
        self._state = MenuState.CREDITS
        self._items = [
            MenuItem("BACK", lambda: self.set_state(MenuState.MAIN))
        ]
        self._selected_index = 0
        self._update_selection()
    
    @property
    def state(self) -> MenuState:
        return self._state
    
    @property
    def is_visible(self) -> bool:
        return self._is_visible
