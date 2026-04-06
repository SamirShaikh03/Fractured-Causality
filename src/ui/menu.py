   

import pygame
from typing import List, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, get_ui_font
from .design_system import UI_PALETTE


                                                                               
                    
                                                                               
THEME_BG_DARK = UI_PALETTE.bg
THEME_BG_MEDIUM = UI_PALETTE.panel
THEME_BG_PANEL = UI_PALETTE.panel_soft
THEME_ACCENT_PRIMARY = UI_PALETTE.info
THEME_ACCENT_SECONDARY = UI_PALETTE.warning
THEME_ACCENT_SUCCESS = UI_PALETTE.success
THEME_ACCENT_DANGER = UI_PALETTE.error
THEME_TEXT_BRIGHT = UI_PALETTE.text_primary
THEME_TEXT_DIM = UI_PALETTE.text_secondary
THEME_TEXT_DISABLED = (95, 100, 110)


class MenuState(Enum):
                      
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
                                         
    label: str
    action: Callable[[], None]
    enabled: bool = True
    selected: bool = False
    hover: bool = False
    rect: pygame.Rect = None


class Menu:
       
    
    def __init__(self):
                                         
        pygame.font.init()
        
               
        self._font_title = get_ui_font(74)
        self._font_title_compact = get_ui_font(58)
        self._font_subtitle = get_ui_font(32)
        self._font_subtitle_compact = get_ui_font(24)
        self._font_large = get_ui_font(40)
        self._font_medium = get_ui_font(30)
        self._font_small = get_ui_font(24)
        self._font_tiny = get_ui_font(20)
        self._font_micro = get_ui_font(14)

                                         
        self._font_howto_title = get_ui_font(52)
        self._font_howto_section = get_ui_font(26)
        self._font_howto_label = get_ui_font(18)
        self._font_howto_body = get_ui_font(15)

        
               
        self._state: MenuState = MenuState.MAIN
        self._items: List[MenuItem] = []
        self._selected_index: int = 0
        self._is_visible: bool = True
        
                                           
        self._time: float = 0.0
        
                        
        self._mouse_pos: Tuple[int, int] = (0, 0)
        
                   
        self._on_play: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        self._on_resume: Optional[Callable] = None
        self._on_restart: Optional[Callable] = None
        self._on_next_level: Optional[Callable] = None
        self._on_main_menu: Optional[Callable] = None
        
                              
        self._setup_main_menu()
    
    def _setup_main_menu(self) -> None:
                                                        
        self._items = [
            MenuItem("START GAME", self._on_play_clicked),
            MenuItem("HOW TO PLAY", self._on_how_to_play_clicked),
            MenuItem("QUIT", self._on_quit_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_how_to_play(self) -> None:
                                        
        self._items = [
            MenuItem("BACK TO MENU", lambda: self.set_state(MenuState.MAIN)),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_pause_menu(self) -> None:
                                      
        self._items = [
            MenuItem("RESUME", self._on_resume_clicked),
            MenuItem("RESTART LEVEL", self._on_restart_clicked),
            MenuItem("MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_game_over(self) -> None:
                                    
        self._items = [
            MenuItem("TRY AGAIN", self._on_restart_clicked),
            MenuItem("MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _setup_level_complete(self) -> None:
                                         
        self._items = [
            MenuItem("NEXT LEVEL", self._on_next_level_clicked),
            MenuItem("REPLAY", self._on_restart_clicked),
            MenuItem("MAIN MENU", self._on_main_menu_clicked),
        ]
        self._selected_index = 0
        self._update_selection()
    
    def _update_selection(self) -> None:
                                           
        for i, item in enumerate(self._items):
            item.selected = (i == self._selected_index)
    
    def set_state(self, state: MenuState) -> None:
                                
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
                            
        self._is_visible = True
    
    def hide(self) -> None:
                            
        self._is_visible = False
    
    def navigate_up(self) -> None:
                                      
        if not self._items:
            return
        
        self._selected_index -= 1
        if self._selected_index < 0:
            self._selected_index = len(self._items) - 1
        
                             
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index -= 1
            if self._selected_index < 0:
                self._selected_index = len(self._items) - 1
            attempts += 1
        
        self._update_selection()
    
    def navigate_down(self) -> None:
                                        
        if not self._items:
            return
        
        self._selected_index += 1
        if self._selected_index >= len(self._items):
            self._selected_index = 0
        
                             
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index += 1
            if self._selected_index >= len(self._items):
                self._selected_index = 0
            attempts += 1
        
        self._update_selection()
    
    def select(self) -> None:
                                           
        if not self._items:
            return
        
        item = self._items[self._selected_index]
        if item.enabled and item.action:
            item.action()
    
    def handle_input(self, event: pygame.event.Event) -> bool:
                                                  
        if not self._is_visible:
            return False
        
                                            
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
            self._update_hover_states()
            return True
        
                                   
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, item in enumerate(self._items):
                if item.rect and item.rect.collidepoint(event.pos) and item.enabled:
                    self._selected_index = i
                    self._update_selection()
                    item.action()
                    return True
        
                        
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
                                                               
        for i, item in enumerate(self._items):
            if item.rect and item.rect.collidepoint(self._mouse_pos):
                item.hover = True
                if item.enabled:
                    self._selected_index = i
                    self._update_selection()
            else:
                item.hover = False
    
    def update(self, dt: float) -> None:
                                
        self._time += dt
    
    def render(self, surface: pygame.Surface) -> None:
                                                
        if not self._is_visible:
            return
        
                         
        self._draw_background(surface)
        
                        
        self._draw_borders(surface)
        
                                  
        if self._state == MenuState.HOW_TO_PLAY:
            self._draw_how_to_play(surface)
        else:
            self._draw_standard_menu(surface)
        
                                 
        self._draw_controls_hint(surface)
    
    def _draw_background(self, surface: pygame.Surface) -> None:
                                            
        surface.fill(THEME_BG_DARK)

        panel = pygame.Rect(24, 24, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 48)
        pygame.draw.rect(surface, THEME_BG_PANEL, panel)
        pygame.draw.rect(surface, THEME_BG_MEDIUM, panel, 2)
    
    def _draw_borders(self, surface: pygame.Surface) -> None:
                                                
        pygame.draw.line(surface, THEME_BG_MEDIUM, (40, 110), (SCREEN_WIDTH - 40, 110), 1)
        pygame.draw.line(surface, THEME_BG_MEDIUM, (40, SCREEN_HEIGHT - 70), (SCREEN_WIDTH - 40, SCREEN_HEIGHT - 70), 1)
    
    def _draw_standard_menu(self, surface: pygame.Surface) -> None:
                                                        
                                   
        self._draw_title(surface)
        
                               
        self._draw_menu_items(surface)
    
    def _draw_title(self, surface: pygame.Surface) -> None:
                                      
        title_text = self._get_title()
        subtitle_text = self._get_subtitle()

        title_font = self._font_title
        subtitle_font = self._font_subtitle
        subtitle_gap = 18

        if self._state == MenuState.MAIN:
            subtitle_gap = 35
        elif self._state == MenuState.LEVEL_COMPLETE:
            title_font = self._font_title_compact
            subtitle_font = self._font_subtitle_compact
            subtitle_gap = 14
        
        title_y = 64
        title = title_font.render(title_text, True, THEME_TEXT_BRIGHT)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, title_y))

        line_y = title_y + title.get_height() + 10
        pygame.draw.line(
            surface,
            THEME_ACCENT_SECONDARY,
            (SCREEN_WIDTH // 2 - 90, line_y),
            (SCREEN_WIDTH // 2 + 90, line_y),
            2,
        )
        
                  
        if subtitle_text:
            subtitle = subtitle_font.render(subtitle_text, True, THEME_TEXT_DIM)
            subtitle_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
            subtitle_y = line_y + subtitle_gap
            surface.blit(subtitle, (subtitle_x, subtitle_y))
    
    def _draw_menu_items(self, surface: pygame.Surface) -> None:
                                       
        if self._state == MenuState.MAIN:
            btn_width = 440
            btn_height = 62
        elif self._state == MenuState.LEVEL_COMPLETE:
            btn_width = 420
            btn_height = 51
        else:
            btn_width = 300
            btn_height = 50
        btn_spacing = 14

        start_y = SCREEN_HEIGHT // 2 + 50
        
        for i, item in enumerate(self._items):
            x = (SCREEN_WIDTH - btn_width) // 2
            y = start_y + i * (btn_height + btn_spacing)
            
            rect = pygame.Rect(x, y, btn_width, btn_height)
            item.rect = rect
            
            if not item.enabled:
                bg_color = THEME_BG_MEDIUM
                border_color = THEME_TEXT_DISABLED
                text_color = THEME_TEXT_DISABLED
            else:
                selected = item.selected or item.hover
                bg_color = (40, 48, 58) if selected else THEME_BG_MEDIUM
                border_color = THEME_ACCENT_PRIMARY if selected else (80, 90, 105)
                text_color = THEME_TEXT_BRIGHT if selected else THEME_TEXT_DIM
            
            pygame.draw.rect(surface, bg_color, rect)
            pygame.draw.rect(surface, border_color, rect, 2)
            
            text = self._font_large.render(item.label, True, text_color)
            text_x = x + (btn_width - text.get_width()) // 2
            text_y = y + (btn_height - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))
    
    def _draw_controls_hint(self, surface: pygame.Surface) -> None:
                                           
        hint = "Arrow keys or mouse to move, Enter/click to select, Esc to go back"
        text = self._font_micro.render(hint, True, THEME_TEXT_DIM)
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT - 46
        surface.blit(text, (x, y))
    
                                                                               
                        
                                                                               
    
    def _draw_how_to_play(self, surface: pygame.Surface) -> None:
        outer_margin = 32
        gap_title_to_panels = 32
        gap_panels_to_universe = 32
        gap_universe_to_tip = 16
        gap_tip_to_button = 32
        gap_button_to_footer = 16
        gutter = 12
        grid_width = SCREEN_WIDTH - (outer_margin * 2)
        col_w = (grid_width - gutter * 11) // 12
        left_x = outer_margin
        left_w = col_w * 6 + gutter * 5
        right_x = left_x + left_w + gutter
        right_w = left_w

        full_x = outer_margin
        full_w = grid_width

        title = self._font_howto_title.render("HOW TO PLAY", True, THEME_TEXT_BRIGHT)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        title_y = 32
        surface.blit(title, (title_x, title_y))

        line_y = title_y + title.get_height() + 10
        pygame.draw.line(
            surface,
            THEME_ACCENT_SECONDARY,
            (SCREEN_WIDTH // 2 - 150, line_y),
            (SCREEN_WIDTH // 2 + 150, line_y),
            2
        )

        top_y = line_y + gap_title_to_panels
        top_h = 220

        self._draw_tutorial_panel(
            surface, left_x, top_y, left_w, top_h,
            "CONTROLS", THEME_ACCENT_PRIMARY, [
                ("WASD", "Move your character"),
                ("SPACE", "Switch between universes"),
                ("E", "Interact with objects"),
                ("F", "Attack enemies"),
                ("TAB", "Toggle Causal Sight"),
                ("ESC", "Pause the game"),
            ]
        )

        self._draw_tutorial_panel(
            surface, right_x, top_y, right_w, top_h,
            "OBJECTIVE", THEME_ACCENT_SECONDARY, [
                ("Goal", "Reach the EXIT PORTAL"),
                ("Keys", "Collect to unlock doors"),
                ("Enemy", "Defeat or avoid them"),
                ("Health", "Don't let it reach zero"),
                ("Paradox", "Keep it low to survive"),
            ]
        )

        bottom_y = top_y + top_h + gap_panels_to_universe
        bottom_h = 150
        self._draw_tutorial_panel(
            surface, full_x, bottom_y, full_w, bottom_h,
            "UNIVERSE SYSTEM", THEME_ACCENT_SUCCESS, [
                ("PRIME (Blue)", "The original, stable timeline - your starting point"),
                ("ECHO (Green)", "A parallel dimension where things are different"),
                ("FRACTURE (Red)", "An unstable reality with unique challenges"),
            ]
        )

        tip_y = bottom_y + bottom_h + gap_universe_to_tip
        tip_text = "TIP: If a path is blocked, try switching to another universe!"
        tip = self._font_howto_body.render(tip_text, True, THEME_ACCENT_SUCCESS)
        tip_x = (SCREEN_WIDTH - tip.get_width()) // 2

        tip_bg = pygame.Rect(tip_x - 16, tip_y - 6, tip.get_width() + 32, tip.get_height() + 12)
        pygame.draw.rect(surface, (25, 40, 30), tip_bg, border_radius=6)
        pygame.draw.rect(surface, THEME_ACCENT_SUCCESS, tip_bg, 1, border_radius=6)
        surface.blit(tip, (tip_x, tip_y))

        btn_w = 370
        btn_h = 60
        btn_x = (SCREEN_WIDTH - btn_w) // 2
        btn_y = tip_bg.bottom + gap_tip_to_button

        self._items[0].rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        item = self._items[0]
        is_selected = item.selected or item.hover

        bg_color = (40, 50, 70) if is_selected else (30, 35, 50)
        border_color = THEME_ACCENT_PRIMARY if is_selected else (60, 65, 85)
        text_color = THEME_TEXT_BRIGHT if is_selected else THEME_TEXT_DIM

        pygame.draw.rect(surface, bg_color, item.rect, border_radius=10)
        pygame.draw.rect(surface, border_color, item.rect, 2, border_radius=10)

        text = self._font_medium.render(item.label, True, text_color)
        text_x = btn_x + (btn_w - text.get_width()) // 2
        text_y = btn_y + (btn_h - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))
    
    def _draw_tutorial_panel(self, surface: pygame.Surface, x: int, y: int,
                             width: int, height: int, title: str, 
                             accent_color: tuple, items: list) -> None:
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, THEME_BG_PANEL, panel_rect, border_radius=12)
        pygame.draw.rect(surface, accent_color, panel_rect, 2, border_radius=12)

        pad_x = 20
        pad_y = 14
        title_bar_height = 42
    
        title_bar = pygame.Surface((width, title_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(
            title_bar, (*accent_color[:3], 40), (0, 0, width, title_bar_height),
            border_top_left_radius=12, border_top_right_radius=12
        )
        surface.blit(title_bar, (x, y))
    
        title_surf = self._font_howto_section.render(title, True, accent_color)
        title_x = x + (width - title_surf.get_width()) // 2
        surface.blit(title_surf, (title_x, y + 8))
    
        content_x = x + pad_x
        content_y = y + title_bar_height + pad_y
        content_w = width - (pad_x * 2)
    
        label_strings = [f"{k}:" for k, _ in items]
        max_label_w = 0
        for label in label_strings:
            max_label_w = max(max_label_w, self._font_howto_label.size(label)[0])
    
        label_col_w = min(max_label_w + 14, int(content_w * 0.36))
        value_x = content_x + label_col_w
        value_w = content_w - label_col_w
    
        row_gap = 8
        for key, value in items:
            key_text = f"{key}:"
            key_surf = self._font_howto_label.render(key_text, True, THEME_ACCENT_PRIMARY)
            surface.blit(key_surf, (content_x, content_y))
    
            wrapped_lines = self._wrap_panel_text(value, self._font_howto_body, value_w)
            line_y = content_y
            for line in wrapped_lines:
                value_surf = self._font_howto_body.render(line, True, THEME_TEXT_DIM)
                surface.blit(value_surf, (value_x, line_y))
                line_y += value_surf.get_height() + 2
    
            row_h = max(key_surf.get_height(), line_y - content_y)
            content_y += row_h + row_gap
    
    def _wrap_panel_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        words = text.split()
        if not words:
            return [""]

        lines: List[str] = []
        current = words[0]

        for word in words[1:]:
            test = f"{current} {word}"
            if font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word

        lines.append(current)
        return lines

    def _get_title(self) -> str:
                                       
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
                                          
        if self._state == MenuState.MAIN:
            return "A simple multiverse puzzle game"
        elif self._state == MenuState.GAME_OVER:
            return "The paradox has consumed all timelines."
        elif self._state == MenuState.LEVEL_COMPLETE:
            return "Balance restored. Next dimension awaits."
        return ""
    
               
    def set_callbacks(self, 
                     on_play: Callable = None,
                     on_quit: Callable = None,
                     on_resume: Callable = None,
                     on_restart: Callable = None,
                     on_next_level: Callable = None,
                     on_main_menu: Callable = None) -> None:
                                 
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
