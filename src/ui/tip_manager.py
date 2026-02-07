"""
Tip Manager - Contextual tip system for player guidance.

Shows helpful tips based on:
- Player proximity to objects/enemies
- Game events (first time actions)
- Level-specific tutorial triggers
- Timed introductory tips
"""

import pygame
import math
import time
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from ..core.events import EventSystem, GameEvent


# Tip styling colors
TIP_BG = (10, 10, 30)
TIP_BORDER_INFO = (80, 180, 255)
TIP_BORDER_HINT = (255, 215, 0)
TIP_BORDER_WARN = (255, 120, 60)
TIP_BORDER_STORY = (180, 120, 255)
TIP_TEXT_MAIN = (255, 255, 255)
TIP_TEXT_KEY = (80, 220, 255)
TIP_TEXT_DIM = (160, 160, 180)


@dataclass
class Tip:
    """A single tip/hint to display."""
    tip_id: str
    title: str
    text: str
    category: str = "info"        # info, hint, warning, story
    duration: float = 5.0         # How long to show
    priority: int = 0             # Higher = more important
    show_once: bool = True        # Only show once per session
    icon: str = "?"               # Icon character
    fade_in: float = 0.3
    fade_out: float = 0.5


@dataclass
class ProximityTip:
    """A tip triggered by player proximity to a position."""
    tip: Tip
    position: Tuple[float, float]  # World position (pixels)
    trigger_radius: float = 120.0  # Pixels
    triggered: bool = False


@dataclass
class ActiveTip:
    """A tip currently being displayed."""
    tip: Tip
    start_time: float
    alpha: float = 0.0
    phase: str = "fade_in"  # fade_in, visible, fade_out, done


class TipManager:
    """
    Manages contextual tips and player guidance.
    
    Features:
    - Proximity-based tips (triggers near objects)
    - Event-based tips (on first action)
    - Queued tip display (one at a time, with priority)
    - Beautiful cyberpunk-styled rendering
    - Tracks which tips have been shown
    """
    
    def __init__(self):
        """Initialize the TipManager."""
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 28)
        self._font_body = pygame.font.Font(None, 24)
        self._font_icon = pygame.font.Font(None, 36)
        self._font_dismiss = pygame.font.Font(None, 20)
        
        # Active tip being displayed
        self._active_tip: Optional[ActiveTip] = None
        
        # Queue of pending tips
        self._tip_queue: List[Tip] = []
        
        # Proximity tips for current level
        self._proximity_tips: List[ProximityTip] = []
        
        # Track shown tips (to avoid repeats)
        self._shown_tips: Set[str] = set()
        
        # Event-based tip mappings
        self._event_tips: Dict[str, Tip] = {}
        
        # Cooldown between tips
        self._tip_cooldown: float = 0.0
        self._min_tip_interval: float = 2.0
        
        # Animation
        self._pulse_timer: float = 0.0
        self._slide_offset: float = 0.0
        
        # Subscribe to events
        EventSystem.subscribe(GameEvent.LEVEL_STARTED, self._on_level_started)
        EventSystem.subscribe(GameEvent.UNIVERSE_SWITCHED, self._on_universe_switched)
        EventSystem.subscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.subscribe(GameEvent.ENEMY_DEFEATED, self._on_enemy_defeated)
        EventSystem.subscribe(GameEvent.PLAYER_DAMAGED, self._on_player_damaged)
        
        # Register global one-time tips
        self._register_global_tips()
    
    def _register_global_tips(self) -> None:
        """Register tips for first-time game events."""
        self._event_tips["first_universe_switch"] = Tip(
            tip_id="first_universe_switch",
            title="UNIVERSE SHIFTED!",
            text="Each universe has different layouts and objects. Switch often to find new paths!",
            category="info",
            duration=5.0,
            icon="~",
            priority=5
        )
        
        self._event_tips["first_key_collected"] = Tip(
            tip_id="first_key_collected",
            title="KEY FOUND!",
            text="Keys unlock the exit portal. Check the HUD for how many you need.",
            category="hint",
            duration=4.0,
            icon="K",
            priority=3
        )
        
        self._event_tips["first_enemy_defeated"] = Tip(
            tip_id="first_enemy_defeated",
            title="ENEMY VANQUISHED!",
            text="Some enemies can be defeated with [F]. Others require causal solutions...",
            category="info",
            duration=5.0,
            icon="!",
            priority=4
        )
        
        self._event_tips["first_damage_taken"] = Tip(
            tip_id="first_damage_taken",
            title="WATCH OUT!",
            text="Enemies deal contact damage. Keep your distance or defeat them with [F]!",
            category="warning",
            duration=4.0,
            icon="!",
            priority=6
        )
    
    def queue_tip(self, tip: Tip) -> None:
        """
        Add a tip to the display queue.
        
        Args:
            tip: The tip to queue
        """
        if tip.show_once and tip.tip_id in self._shown_tips:
            return
        
        # Don't add duplicates to queue
        for queued in self._tip_queue:
            if queued.tip_id == tip.tip_id:
                return
        
        # Don't re-queue the active tip
        if self._active_tip and self._active_tip.tip.tip_id == tip.tip_id:
            return
        
        self._tip_queue.append(tip)
        # Sort by priority (higher first)
        self._tip_queue.sort(key=lambda t: t.priority, reverse=True)
    
    def add_proximity_tips(self, tips: List[ProximityTip]) -> None:
        """
        Set proximity-based tips for the current level.
        
        Args:
            tips: List of proximity tips
        """
        self._proximity_tips = tips
    
    def clear_proximity_tips(self) -> None:
        """Clear all proximity tips."""
        self._proximity_tips.clear()
    
    def check_proximity(self, player_x: float, player_y: float) -> None:
        """
        Check if the player is near any proximity tip triggers.
        
        Args:
            player_x: Player X position
            player_y: Player Y position
        """
        for ptip in self._proximity_tips:
            if ptip.triggered:
                continue
            
            dx = player_x - ptip.position[0]
            dy = player_y - ptip.position[1]
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < ptip.trigger_radius:
                ptip.triggered = True
                self.queue_tip(ptip.tip)
    
    def update(self, dt: float) -> None:
        """
        Update the tip system.
        
        Args:
            dt: Delta time
        """
        self._pulse_timer += dt
        
        # Update cooldown
        if self._tip_cooldown > 0:
            self._tip_cooldown -= dt
        
        # Update active tip
        if self._active_tip:
            tip = self._active_tip
            elapsed = time.time() - tip.start_time
            
            if tip.phase == "fade_in":
                progress = min(1.0, elapsed / tip.tip.fade_in) if tip.tip.fade_in > 0 else 1.0
                tip.alpha = progress * 255
                self._slide_offset = (1 - progress) * 40
                if progress >= 1.0:
                    tip.phase = "visible"
            
            elif tip.phase == "visible":
                tip.alpha = 255
                self._slide_offset = 0
                visible_time = elapsed - tip.tip.fade_in
                if visible_time >= tip.tip.duration:
                    tip.phase = "fade_out"
                    tip.start_time = time.time()
            
            elif tip.phase == "fade_out":
                fade_elapsed = time.time() - tip.start_time
                progress = min(1.0, fade_elapsed / tip.tip.fade_out) if tip.tip.fade_out > 0 else 1.0
                tip.alpha = (1 - progress) * 255
                self._slide_offset = progress * 30
                if progress >= 1.0:
                    tip.phase = "done"
                    self._active_tip = None
                    self._tip_cooldown = self._min_tip_interval
        
        # Show next tip from queue if no active tip
        if not self._active_tip and self._tip_cooldown <= 0 and self._tip_queue:
            next_tip = self._tip_queue.pop(0)
            if not (next_tip.show_once and next_tip.tip_id in self._shown_tips):
                self._active_tip = ActiveTip(
                    tip=next_tip,
                    start_time=time.time()
                )
                self._shown_tips.add(next_tip.tip_id)
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the active tip.
        
        Args:
            surface: Target surface
        """
        if not self._active_tip or self._active_tip.alpha <= 0:
            return
        
        tip = self._active_tip.tip
        alpha = int(self._active_tip.alpha)
        
        # Get border color based on category
        if tip.category == "hint":
            border_color = TIP_BORDER_HINT
        elif tip.category == "warning":
            border_color = TIP_BORDER_WARN
        elif tip.category == "story":
            border_color = TIP_BORDER_STORY
        else:
            border_color = TIP_BORDER_INFO
        
        # Calculate dimensions
        padding = 16
        icon_size = 36
        max_text_width = 420
        
        # Render text to get dimensions
        title_surf = self._font_title.render(tip.title, True, border_color)
        
        # Word-wrap body text
        body_lines = self._wrap_text(tip.text, self._font_body, max_text_width - icon_size - padding)
        body_surfs = [self._font_body.render(line, True, TIP_TEXT_MAIN) for line in body_lines]
        
        # Dismiss hint
        dismiss_surf = self._font_dismiss.render("auto-dismiss", True, TIP_TEXT_DIM)
        
        # Calculate total height
        body_height = sum(s.get_height() + 2 for s in body_surfs)
        total_height = padding * 2 + title_surf.get_height() + 8 + body_height + 4 + dismiss_surf.get_height()
        total_width = max_text_width + icon_size + padding * 3
        
        # Position (top-center with slide offset)
        box_x = (SCREEN_WIDTH - total_width) // 2
        box_y = 70 + int(self._slide_offset)
        
        # Create tip surface with alpha
        tip_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        
        # Background
        bg_alpha = int(alpha * 0.85)
        pygame.draw.rect(tip_surface, (*TIP_BG, bg_alpha), 
                        (0, 0, total_width, total_height), border_radius=10)
        
        # Glowing border
        border_alpha = min(255, int(alpha * 0.9))
        border_with_alpha = (*border_color, border_alpha)
        pygame.draw.rect(tip_surface, border_with_alpha, 
                        (0, 0, total_width, total_height), 2, border_radius=10)
        
        # Neon glow effect on border (subtle)
        pulse = 0.7 + 0.3 * math.sin(self._pulse_timer * 2)
        glow_alpha = int(border_alpha * 0.3 * pulse)
        pygame.draw.rect(tip_surface, (*border_color, glow_alpha), 
                        (-2, -2, total_width + 4, total_height + 4), 4, border_radius=12)
        
        # Icon circle
        icon_cx = padding + icon_size // 2
        icon_cy = padding + icon_size // 2
        pygame.draw.circle(tip_surface, (*border_color, int(alpha * 0.3)), 
                          (icon_cx, icon_cy), icon_size // 2)
        pygame.draw.circle(tip_surface, border_with_alpha, 
                          (icon_cx, icon_cy), icon_size // 2, 2)
        
        # Icon text
        icon_surf = self._font_icon.render(tip.icon, True, (*border_color,))
        icon_surf.set_alpha(alpha)
        icon_rect = icon_surf.get_rect(center=(icon_cx, icon_cy))
        tip_surface.blit(icon_surf, icon_rect)
        
        # Title
        title_x = padding + icon_size + padding
        title_y = padding
        title_surf.set_alpha(alpha)
        tip_surface.blit(title_surf, (title_x, title_y))
        
        # Accent line under title
        line_y = title_y + title_surf.get_height() + 3
        pygame.draw.line(tip_surface, (*border_color, int(alpha * 0.5)), 
                        (title_x, line_y), 
                        (title_x + title_surf.get_width(), line_y), 1)
        
        # Body text
        body_y = line_y + 6
        for body_surf in body_surfs:
            body_surf.set_alpha(alpha)
            tip_surface.blit(body_surf, (title_x, body_y))
            body_y += body_surf.get_height() + 2
        
        # Dismiss hint
        dismiss_surf.set_alpha(int(alpha * 0.5))
        tip_surface.blit(dismiss_surf, 
                        (total_width - dismiss_surf.get_width() - padding, 
                         total_height - dismiss_surf.get_height() - 6))
        
        surface.blit(tip_surface, (box_x, box_y))
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """
        Word-wrap text to fit within max_width.
        
        Args:
            text: Text to wrap
            font: Font to measure with
            max_width: Maximum width in pixels
            
        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    # ===== EVENT HANDLERS =====
    
    def _on_level_started(self, data: dict) -> None:
        """Show level intro tips."""
        level_id = data.get("level_id", "")
        level_name = data.get("level_name", "")
        
        # Show level welcome tip
        self.queue_tip(Tip(
            tip_id=f"level_intro_{level_id}",
            title=f"~ {level_name.upper()} ~",
            text=self._get_level_intro_text(level_id),
            category="story",
            duration=6.0,
            icon="*",
            priority=10,
            show_once=True
        ))
        
        # Show controls reminder tip after intro
        self.queue_tip(Tip(
            tip_id=f"controls_reminder_{level_id}",
            title="CONTROLS",
            text="[WASD] Move | [SPACE] Switch Universe | [E] Interact | [F] Attack | [TAB] Causal Sight",
            category="info",
            duration=6.0,
            icon="?",
            priority=8,
            show_once=True
        ))
    
    def _on_universe_switched(self, data: dict) -> None:
        """Tip on first universe switch."""
        tip = self._event_tips.get("first_universe_switch")
        if tip:
            self.queue_tip(tip)
    
    def _on_item_collected(self, data: dict) -> None:
        """Tip on first key collected."""
        if data.get("item_type") == "key":
            tip = self._event_tips.get("first_key_collected")
            if tip:
                self.queue_tip(tip)
    
    def _on_enemy_defeated(self, data: dict) -> None:
        """Tip on first enemy defeated."""
        tip = self._event_tips.get("first_enemy_defeated")
        if tip:
            self.queue_tip(tip)
    
    def _on_player_damaged(self, data: dict) -> None:
        """Tip on first damage taken."""
        tip = self._event_tips.get("first_damage_taken")
        if tip:
            self.queue_tip(tip)
    
    def _get_level_intro_text(self, level_id: str) -> str:
        """Get intro text for a level."""
        intros = {
            "level_01": "Reality has fractured. Use [SPACE] to switch between parallel universes. "
                       "Paths blocked in one universe may be open in another. Find the key and reach the portal!",
            "level_02": "An ancient temple holds Echo Stones - artifacts that exist in ALL universes simultaneously. "
                       "Push them with [E] and use pressure plates to open doors. Collect both keys!",
            "level_03": "Dark Shades guard this grove, bound to the Ancient Tree. "
                       "They cannot be killed directly - find the source of their existence! "
                       "Try the Fracture universe with [SPACE]!"
        }
        return intros.get(level_id, "Explore, switch universes, and find the way forward.")
    
    def get_level_proximity_tips(self, level_id: str) -> List[ProximityTip]:
        """
        Get proximity-based tips for a specific level.
        
        Args:
            level_id: The level identifier
            
        Returns:
            List of proximity tips for the level
        """
        tips = {
            "level_01": [
                ProximityTip(
                    tip=Tip(
                        tip_id="l1_near_blocked_path",
                        title="PATH BLOCKED!",
                        text="This path is blocked in the current universe. "
                            "Press [SPACE] to switch to another universe where it might be open!",
                        category="hint",
                        duration=5.0,
                        icon="!",
                        priority=5
                    ),
                    position=(9 * TILE_SIZE, 3 * TILE_SIZE),
                    trigger_radius=100
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l1_near_switch",
                        title="ECHO SWITCH",
                        text="Press [E] to interact with this switch. It will send an echo across "
                            "universes, affecting connected objects!",
                        category="hint",
                        duration=5.0,
                        icon="S",
                        priority=4
                    ),
                    position=(10 * TILE_SIZE, 7 * TILE_SIZE),
                    trigger_radius=120
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l1_near_door",
                        title="VARIANT DOOR",
                        text="This door has different states in each universe. "
                            "Try switching universes or activating a linked switch!",
                        category="hint",
                        duration=5.0,
                        icon="D",
                        priority=4
                    ),
                    position=(14 * TILE_SIZE, 7 * TILE_SIZE),
                    trigger_radius=120
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l1_near_key",
                        title="KEY SPOTTED!",
                        text="Walk over the key to collect it. You need keys to unlock the exit portal!",
                        category="hint",
                        duration=4.0,
                        icon="K",
                        priority=3
                    ),
                    position=(16 * TILE_SIZE, 2 * TILE_SIZE),
                    trigger_radius=150
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l1_near_portal",
                        title="EXIT PORTAL",
                        text="This portal leads to the next level. You need all required keys to enter! "
                            "Walk into it when ready.",
                        category="info",
                        duration=5.0,
                        icon="P",
                        priority=5
                    ),
                    position=(17 * TILE_SIZE, 7 * TILE_SIZE),
                    trigger_radius=140
                ),
            ],
            "level_02": [
                ProximityTip(
                    tip=Tip(
                        tip_id="l2_near_stone",
                        title="CAUSAL STONE",
                        text="This Echo Stone exists in ALL universes at once! "
                            "Push it with [E] - it will move in every universe simultaneously.",
                        category="hint",
                        duration=5.0,
                        icon="O",
                        priority=5
                    ),
                    position=(4 * TILE_SIZE, 8 * TILE_SIZE),
                    trigger_radius=120
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l2_near_plate",
                        title="PRESSURE PLATE",
                        text="Push a Causal Stone onto this plate to activate it. "
                            "The plate opens a door somewhere in the temple!",
                        category="hint",
                        duration=5.0,
                        icon="=",
                        priority=4
                    ),
                    position=(7 * TILE_SIZE, 8 * TILE_SIZE),
                    trigger_radius=100
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l2_near_main_switch",
                        title="MAIN SWITCH",
                        text="This switch controls the main gate. Press [E] to activate it!",
                        category="hint",
                        duration=4.0,
                        icon="S",
                        priority=4
                    ),
                    position=(10 * TILE_SIZE, 8 * TILE_SIZE),
                    trigger_radius=120
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l2_upper_key",
                        title="KEY ABOVE!",
                        text="A key is in the treasure room above. Solve the upper path puzzle to reach it!",
                        category="hint",
                        duration=4.0,
                        icon="K",
                        priority=3
                    ),
                    position=(17 * TILE_SIZE, 4 * TILE_SIZE),
                    trigger_radius=150
                ),
            ],
            "level_03": [
                ProximityTip(
                    tip=Tip(
                        tip_id="l3_near_shade",
                        title="SHADE GUARDIAN",
                        text="Shades are bound to a causal origin. You can attack them with [F], "
                            "but the true solution is finding their source... Use [TAB] for Causal Sight!",
                        category="warning",
                        duration=6.0,
                        icon="!",
                        priority=6
                    ),
                    position=(18 * TILE_SIZE, 6 * TILE_SIZE),
                    trigger_radius=180
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l3_near_tree",
                        title="THE ANCIENT TREE",
                        text="This tree radiates causal energy. The Shades seem connected to it... "
                            "What would happen if it were destroyed in another universe?",
                        category="story",
                        duration=6.0,
                        icon="T",
                        priority=7
                    ),
                    position=(12 * TILE_SIZE, 9 * TILE_SIZE),
                    trigger_radius=150
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l3_moat_hint",
                        title="PROTECTIVE MOAT",
                        text="A moat surrounds the tree in this universe. "
                            "Try switching to a universe where the moat has dried up!",
                        category="hint",
                        duration=5.0,
                        icon="~",
                        priority=5
                    ),
                    position=(9 * TILE_SIZE, 9 * TILE_SIZE),
                    trigger_radius=100
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l3_fracture_intro",
                        title="FRACTURE UNIVERSE",
                        text="The Fracture universe is unstable and dangerous, but it offers unique paths. "
                            "Press [SPACE] to cycle through all three universes!",
                        category="warning",
                        duration=5.0,
                        icon="!",
                        priority=5
                    ),
                    position=(3 * TILE_SIZE, 9 * TILE_SIZE),
                    trigger_radius=120
                ),
                ProximityTip(
                    tip=Tip(
                        tip_id="l3_causal_hint",
                        title="CAUSAL SIGHT TIP",
                        text="Press [TAB] to activate Causal Sight. It reveals hidden connections "
                            "between objects across universes!",
                        category="info",
                        duration=5.0,
                        icon="E",
                        priority=4
                    ),
                    position=(5 * TILE_SIZE, 9 * TILE_SIZE),
                    trigger_radius=100
                ),
            ]
        }
        
        return tips.get(level_id, [])
    
    def reset_for_level(self) -> None:
        """Reset state for a new level."""
        self._proximity_tips.clear()
        self._tip_queue.clear()
        self._active_tip = None
        self._tip_cooldown = 1.0  # Small initial delay
    
    def cleanup(self) -> None:
        """Clean up event subscriptions."""
        EventSystem.unsubscribe(GameEvent.LEVEL_STARTED, self._on_level_started)
        EventSystem.unsubscribe(GameEvent.UNIVERSE_SWITCHED, self._on_universe_switched)
        EventSystem.unsubscribe(GameEvent.ITEM_COLLECTED, self._on_item_collected)
        EventSystem.unsubscribe(GameEvent.ENEMY_DEFEATED, self._on_enemy_defeated)
        EventSystem.unsubscribe(GameEvent.PLAYER_DAMAGED, self._on_player_damaged)
