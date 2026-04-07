"""
Game - Main game class that orchestrates all systems.

This is the heart of Multiverse Causality.
"""

import pygame
import sys
import asyncio
from typing import Optional, Dict, Tuple

from .settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE,
    COLOR_PRIME, COLOR_ECHO, COLOR_FRACTURE,
    ENEMY_BASE_DAMAGE, ENEMY_KNOCKBACK_FORCE, ENEMY_ATTACK_COOLDOWN
)
from .states import GameState, StateManager
from .events import EventSystem, GameEvent

from ..multiverse.multiverse_manager import MultiverseManager
from ..multiverse.universe import UniverseType

from ..entities.player import Player

from ..levels.level_loader import LevelLoader
from ..levels.level_01 import Level01
from ..levels.level_02 import Level02
from ..levels.level_03 import Level03
from ..levels.level_04 import Level04
from ..levels.level_05 import Level05
from ..levels.level_06 import Level06
from ..levels.level_07 import Level07

from ..systems.input_handler import InputHandler, InputAction
from ..systems.physics import PhysicsSystem
from ..systems.camera import Camera, CameraConfig
from ..systems.animation import AnimationSystem

from ..ui.hud import HUD
from ..ui.menu import Menu, MenuState
from ..ui.universe_indicator import UniverseIndicator
from ..ui.paradox_meter import ParadoxMeter
from ..ui.causal_sight_overlay import CausalSightOverlay

from ..rendering.renderer import Renderer
from ..rendering.effects import EffectsManager, TransitionType
from ..rendering.particles import ParticleSystem

from ..ui.tip_manager import TipManager


class Game:
    """
    Main game class - the orchestrator.
    
    Manages:
    - Game loop
    - State management
    - System coordination
    - Level loading
    - Input processing
    """
    
    def __init__(self):
        """Initialize the game."""
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Create display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Clock for frame timing
        self.clock = pygame.time.Clock()
        self.running: bool = True
        
        # Delta time
        self.dt: float = 0.0
        
        # Initialize systems
        self._init_systems()
        
        # Initialize game objects
        self._init_game_objects()
        
        # Initialize UI
        self._init_ui()
        
        # Register levels
        self._register_levels()
        
        # Subscribe to events
        self._setup_event_handlers()
        
        # Start in menu
        self.state_manager.change_state(GameState.MENU)
    
    def _init_systems(self) -> None:
        """Initialize all game systems."""
        # State management
        self.state_manager = StateManager()
        
        # Input
        self.input_handler = InputHandler()
        
        # Physics
        self.physics = PhysicsSystem()
        
        # Camera
        camera_config = CameraConfig(
            follow_speed=8.0,
            deadzone_x=30,
            deadzone_y=30,
            lookahead=30
        )
        self.camera = Camera(camera_config)
        
        # Animation
        self.animation_system = AnimationSystem()
        
        # Rendering
        self.renderer = Renderer(self.screen)
        self.effects = EffectsManager()
        self.particles = ParticleSystem()
        
        # Multiverse
        self.multiverse = MultiverseManager()
    
    def _init_game_objects(self) -> None:
        """Initialize game objects."""
        # Player
        self.player = Player(position=(100, 100))
        self.player.multiverse = self.multiverse
        self.multiverse.player = self.player

        # Simple reward system
        self._reward_per_level: int = 10
        self._rewarded_levels: set[str] = set()
        
        # Level loader
        self.level_loader = LevelLoader(self.multiverse)
        self.current_level = None
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        # HUD
        self.hud = HUD()
        
        # Menu
        self.menu = Menu()
        self.menu.set_callbacks(
            on_play=self._on_menu_play,
            on_quit=self._on_menu_quit,
            on_resume=self._on_menu_resume,
            on_restart=self._on_menu_restart,
            on_next_level=self._on_menu_next_level,
            on_main_menu=self._on_menu_main
        )
        
        # Universe indicator
        self.universe_indicator = UniverseIndicator()
        
        # Paradox meter
        self.paradox_meter = ParadoxMeter()
        
        # Causal sight overlay
        self.causal_sight = CausalSightOverlay()
        
        # Tip manager
        self.tip_manager = TipManager()
    
    def _register_levels(self) -> None:
        """Register all game levels."""
        self.level_loader.register_level("level_01", Level01)
        self.level_loader.register_level("level_02", Level02)
        self.level_loader.register_level("level_03", Level03)
        self.level_loader.register_level("level_04", Level04)
        self.level_loader.register_level("level_05", Level05)
        self.level_loader.register_level("level_06", Level06)
        self.level_loader.register_level("level_07", Level07)
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        EventSystem.subscribe(GameEvent.UNIVERSE_SWITCHED, self._on_universe_switched)
        EventSystem.subscribe(GameEvent.PARADOX_CHANGED, self._on_paradox_changed)
        EventSystem.subscribe(GameEvent.LEVEL_COMPLETE, self._on_level_complete)
        EventSystem.subscribe(GameEvent.LEVEL_FAILED, self._on_level_failed)
        EventSystem.subscribe(GameEvent.PLAYER_DIED, self._on_player_died)
        EventSystem.subscribe(GameEvent.CAUSAL_SIGHT_TOGGLED, self._on_causal_sight_toggled)
    
    async def run(self) -> None:
        """Main game loop (async for pygbag web deployment)."""
        while self.running:
            # Calculate delta time
            self.dt = self.clock.tick(FPS) / 1000.0
            
            # Cap delta time to prevent physics issues
            self.dt = min(self.dt, 0.05)
            
            # Process events
            self._handle_events()
            
            # Update
            self._update()
            
            # Render
            self._render()
            
            # Update display
            pygame.display.flip()
            
            # Yield to browser event loop (required for pygbag)
            await asyncio.sleep(0)
        
        # Cleanup
        self._cleanup()
    
    def _handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Menu handles its own input when visible
            if self.menu.is_visible:
                if self.menu.handle_input(event):
                    continue
            
            # Handle key events
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
    
    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle key down events."""
        # Pause
        if event.key == pygame.K_ESCAPE:
            if self.state_manager.current_state == GameState.PLAYING:
                self._pause_game()
            elif self.state_manager.current_state == GameState.PAUSED:
                self._resume_game()
        
        # Debug toggle
        if event.key == pygame.K_F3:
            self.renderer.toggle_debug()
    
    def _update(self) -> None:
        """Update game state."""
        # Update input
        input_state = self.input_handler.update(self.dt)
        
        # Update based on game state
        state = self.state_manager.current_state
        
        if state == GameState.MENU:
            self.menu.update(self.dt)
        
        elif state == GameState.PLAYING:
            self._update_gameplay()
        
        elif state == GameState.PAUSED:
            self.menu.update(self.dt)
        
        elif state == GameState.GAME_OVER:
            self.menu.update(self.dt)
        
        elif state == GameState.LEVEL_COMPLETE:
            self.menu.update(self.dt)
        
        # Always update effects
        self.effects.update(self.dt)
        self.particles.update(self.dt)
    
    def _update_gameplay(self) -> None:
        """Update gameplay systems."""
        # Update input handling for player
        self._handle_player_input()
        
        # Update player
        self.player.update(self.dt)

        enemy_previous_positions = self._capture_enemy_positions()
        
        # Update multiverse
        self.multiverse.update(self.dt)

        # Stop enemies at player contact so they don't drag the player by overlap resolution.
        self._resolve_enemy_player_overlap(enemy_previous_positions)

        # Feed player position to enemies that track or hunt the player.
        if self.current_level:
            player_pos = (self.player.x, self.player.y)
            for entity in self.current_level.get_entities():
                if not entity.exists:
                    continue
                if hasattr(entity, 'set_player_position'):
                    entity.set_player_position(player_pos)
                if hasattr(entity, 'record_player_position'):
                    entity.record_player_position(player_pos)
        
        # Update current level
        if self.current_level:
            self.current_level.update(self.dt)
        
        active_universe = self.multiverse.active_universe
        if active_universe:
            entities = self.current_level.get_entities() if self.current_level else []
            
            # Move player with collision
            velocity = (
                self.player.velocity_x,
                self.player.velocity_y
            )
            self.physics.move_and_slide(
                self.player, velocity,
                active_universe, entities,
                self.dt
            )
            
            self._check_entity_interactions()
        
        self.camera.follow(self.player)
        self.camera.update(self.dt)
        
        # Update UI components
        self.hud.update(self.dt)
        self.universe_indicator.update(self.dt)
        self.paradox_meter.update(self.dt)
        self.causal_sight.update(self.dt)
        self.tip_manager.update(self.dt)
        
        # Check proximity tips
        self.tip_manager.check_proximity(self.player.x, self.player.y)
        
        # Update causal sight connections
        if self.causal_sight.is_active():
            self._update_causal_sight()
    
    def _handle_player_input(self) -> None:
        """Handle player input during gameplay."""
        # Movement
        move_x, move_y = self.input_handler.get_movement()
        self.player.handle_input(move_x, move_y, self.dt)
        
        # Universe switching
        if self.input_handler.is_pressed(InputAction.SWITCH_UNIVERSE):
            self._switch_universe()
        
        # Causal sight
        if self.input_handler.is_pressed(InputAction.CAUSAL_SIGHT):
            self.player.toggle_causal_sight()
        
        # Interact
        if self.input_handler.is_pressed(InputAction.INTERACT):
            self._try_interact()
        
        # Attack
        if self.input_handler.is_pressed(InputAction.ATTACK):
            self.player.attack()
            self._check_attack_hits()
        
        # Paradox pulse
        if self.input_handler.is_pressed(InputAction.PARADOX_PULSE):
            self.player.paradox_pulse()
    
    def _switch_universe(self) -> None:
        """Switch to the next universe."""
        current = self.multiverse.active_type
        
        if current == UniverseType.PRIME:
            next_type = UniverseType.ECHO
        elif current == UniverseType.ECHO:
            # Check if Fracture is available
            if self.current_level and self.current_level.config.has_fracture:
                next_type = UniverseType.FRACTURE
            else:
                next_type = UniverseType.PRIME
        else:
            next_type = UniverseType.PRIME
        
        # Request switch
        self.player.request_universe_switch(next_type)
        self.multiverse.switch_universe(next_type)
        
        # Visual feedback
        color = self._get_universe_color(next_type)
        self.effects.flash(color, 0.15)
        self.camera.shake(5, 0.2)
        
        # Particle burst around player to emphasize the switch
        self.particles.emit(
            self.player.x + self.player.width / 2,
            self.player.y + self.player.height / 2,
            count=12, color=color,
            speed=80, lifetime=0.4
        )
    
    def _get_universe_color(self, u_type: UniverseType) -> tuple:
        """Get color for a universe type."""
        if u_type == UniverseType.PRIME:
            return COLOR_PRIME
        elif u_type == UniverseType.ECHO:
            return COLOR_ECHO
        else:
            return COLOR_FRACTURE
    
    def _try_interact(self) -> None:
        """Try to interact with nearby entities."""
        if not self.current_level:
            return
        
        player_rect = pygame.Rect(
            self.player.x - 10, self.player.y - 10,
            self.player.width + 20, self.player.height + 20
        )
        
        interacted = False
        for entity in self.current_level.get_entities():
            if not entity.interactive or not entity.exists:
                continue
            
            entity_rect = pygame.Rect(
                entity.x, entity.y,
                entity.width, entity.height
            )
            
            if player_rect.colliderect(entity_rect):
                if hasattr(entity, 'on_interact'):
                    entity.on_interact(self.player)
                    interacted = True
                    
                    # Interaction particle feedback
                    self.particles.emit(
                        entity.x + entity.width / 2,
                        entity.y + entity.height / 2,
                        count=6, color=(100, 255, 200),
                        speed=40, lifetime=0.3
                    )
                    break
        
        if not interacted:
            # No interactable found - show a hint
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "Nothing to interact with here. Look for switches or objects!",
                "type": "info",
                "duration": 1.5
            })

    def _capture_enemy_positions(self) -> Dict[str, Tuple[float, float]]:
        """Capture active enemy positions before universe/entity updates."""
        if not self.current_level:
            return {}

        positions: Dict[str, Tuple[float, float]] = {}
        for entity in self.current_level.get_entities():
            if entity.exists and entity.is_enemy:
                positions[entity.entity_id] = (entity.x, entity.y)
        return positions

    def _resolve_enemy_player_overlap(self, previous_positions: Dict[str, Tuple[float, float]]) -> None:
        """Rewind enemies that moved into the player this frame to avoid enemy-driven sliding."""
        if not self.current_level or not previous_positions:
            return

        player_rect = self.player.get_rect()

        for entity in self.current_level.get_entities():
            if not entity.exists or not entity.is_enemy or not entity.solid:
                continue

            previous_pos = previous_positions.get(entity.entity_id)
            if previous_pos is None:
                continue

            current_rect = entity.get_rect()
            if not player_rect.colliderect(current_rect):
                continue

            if (entity.x, entity.y) == previous_pos:
                continue

            prev_x, prev_y = previous_pos
            previous_rect = pygame.Rect(int(prev_x), int(prev_y), entity.width, entity.height)
            if not player_rect.colliderect(previous_rect):
                entity.set_position(prev_x, prev_y)

    def _rects_touch_or_overlap(self, rect_a: pygame.Rect, rect_b: pygame.Rect,
                                tolerance: int = 1) -> bool:
        """Return True for overlap or side-contact with a small pixel tolerance."""
        if rect_a.colliderect(rect_b):
            return True

        vertical_overlap = rect_a.bottom > rect_b.top and rect_a.top < rect_b.bottom
        horizontal_overlap = rect_a.right > rect_b.left and rect_a.left < rect_b.right

        touching_horizontally = (
            abs(rect_a.right - rect_b.left) <= tolerance
            or abs(rect_a.left - rect_b.right) <= tolerance
        )
        touching_vertically = (
            abs(rect_a.bottom - rect_b.top) <= tolerance
            or abs(rect_a.top - rect_b.bottom) <= tolerance
        )

        return (
            (vertical_overlap and touching_horizontally)
            or (horizontal_overlap and touching_vertically)
        )

    def _is_enemy_contact(self, enemy, player_rect: pygame.Rect,
                          enemy_rect: pygame.Rect) -> bool:
        """Check whether an enemy can currently damage the player."""
        if hasattr(enemy, 'check_player_collision'):
            return enemy.check_player_collision(player_rect)

        return self._rects_touch_or_overlap(player_rect, enemy_rect)
    
    def _check_entity_interactions(self) -> None:
        """Check for automatic entity interactions."""
        if not self.current_level:
            return
        
        player_rect = pygame.Rect(
            self.player.x, self.player.y,
            self.player.width, self.player.height
        )
        
        for entity in self.current_level.get_entities():
            if not entity.exists:
                continue
            
            entity_rect = pygame.Rect(
                entity.x, entity.y,
                entity.width, entity.height
            )

            player_overlaps = player_rect.colliderect(entity_rect)

            if player_overlaps:
                # Auto-collect items
                if hasattr(entity, 'collect'):
                    entity.collect(self.player)
                
                # Check portal entry
                if hasattr(entity, 'check_player_overlap'):
                    entity.check_player_overlap(self.player)

            # Enemy collision damage (with cooldown)
            if entity.is_enemy and hasattr(entity, 'damage'):
                if not self._is_enemy_contact(entity, player_rect, entity_rect):
                    continue

                if not hasattr(entity, '_last_damage_time'):
                    entity._last_damage_time = -ENEMY_ATTACK_COOLDOWN

                time_since_damage = self.current_level.completion_time - entity._last_damage_time
                if time_since_damage >= ENEMY_ATTACK_COOLDOWN:
                    # Calculate knockback from enemy center toward player center.
                    dx = (self.player.x + self.player.width / 2) - (entity.x + entity.width / 2)
                    dy = (self.player.y + self.player.height / 2) - (entity.y + entity.height / 2)
                    length = (dx * dx + dy * dy) ** 0.5
                    if length > 0:
                        knockback_dir = (dx / length, dy / length)
                    else:
                        knockback_dir = (1, 0)

                    damage = getattr(entity, 'damage', ENEMY_BASE_DAMAGE)
                    self.player.take_damage(damage, knockback_dir)
                    entity._last_damage_time = self.current_level.completion_time
    
    def _check_attack_hits(self) -> None:
        """Check if player's attack hits any enemies."""
        if not self.current_level or not self.player.is_attacking:
            return
        
        attack_rect = self.player.get_attack_rect()
        
        for entity in self.current_level.get_entities():
            if not entity.exists or not entity.is_enemy:
                continue
            
            entity_rect = entity.get_rect()
            
            if attack_rect.colliderect(entity_rect):
                if hasattr(entity, 'take_damage'):
                    defeated = entity.take_damage(self.player.attack_damage)
                    
                    if defeated:
                        EventSystem.emit(GameEvent.UI_MESSAGE, {
                            "message": "Enemy defeated!",
                            "type": "success",
                            "duration": 2.0
                        })
    
    def _update_causal_sight(self) -> None:
        """Update causal sight overlay with entity positions."""
        if not self.current_level:
            return
        
        offset = self.camera.get_offset()
        
        # Update entity positions for causal sight
        for entity in self.current_level.get_entities():
            if hasattr(entity, 'causal_node') and entity.causal_node:
                screen_x = entity.x + entity.width / 2 - offset[0]
                screen_y = entity.y + entity.height / 2 - offset[1]
                self.causal_sight.update_entity_position(
                    entity.entity_id,
                    (screen_x, screen_y)
                )
        
        # Update connections
        self.causal_sight.set_connections_from_graph(
            self.multiverse.causal_graph,
            offset
        )
    
    def _render(self) -> None:
        """Render the game."""
        # Clear
        self.renderer.clear()
        
        state = self.state_manager.current_state
        
        if state == GameState.MENU:
            self._render_menu_background()
            self.menu.render(self.screen)
        
        elif state in [GameState.PLAYING, GameState.PAUSED, 
                       GameState.GAME_OVER, GameState.LEVEL_COMPLETE]:
            self._render_gameplay()
            
            if state != GameState.PLAYING:
                self.menu.render(self.screen)
        
        # Render effects (always on top)
        self.effects.render(self.screen)
    
    def _render_menu_background(self) -> None:
        """Render the menu background."""
        # Simple gradient background
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(20 + progress * 10)
            g = int(20 + progress * 15)
            b = int(40 + progress * 20)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def _render_gameplay(self) -> None:
        """Render gameplay elements."""
        # Render universe
        active_universe = self.multiverse.active_universe
        if active_universe:
            self.renderer.render_universe(active_universe, self.camera)
        
        # Render level entities
        if self.current_level:
            entities = self.current_level.get_entities()
            self.renderer.render_entities(entities, self.camera)
        
        # Render player
        self.renderer.render_player(self.player, self.camera)
        
        # Apply universe overlay
        if active_universe:
            self.renderer.apply_universe_overlay(active_universe.universe_type)

        # Debug info on renderer UI layer (must happen before composite)
        if self.renderer.debug_mode:
            self.renderer.draw_debug_info({
                'FPS': int(self.clock.get_fps()),
                'Entities': len(self.current_level.get_entities()) if self.current_level else 0,
                'Particles': self.particles.particle_count,
                'Universe': self.multiverse.active_type.name if self.multiverse.active_type else 'None',
                'Player': f'({int(self.player.x)}, {int(self.player.y)})'
            })
        
        # Composite renderer layers
        self.renderer.composite()

        # Render world-space effects after compositing so they are not overwritten
        self.particles.render(self.screen, self.camera.get_offset())

        # Render causal sight overlay on top of the world
        if self.causal_sight.is_active():
            self.causal_sight.render(self.screen)
            self.causal_sight.render_legend(self.screen)
        
        # Render UI
        self.hud.render(self.screen)
        
        # Render tips
        self.tip_manager.render(self.screen)
    
    # ===== STATE TRANSITIONS =====
    
    def _start_game(self) -> None:
        """Start a new game."""
        # Reset player health
        self.player.reset_health()
        self.player.rewards = 0
        self._rewarded_levels.clear()
        
        # Load first level
        self.current_level = self.level_loader.load_level("level_01", self.player)
        
        if self.current_level:
            # Load proximity tips for this level
            self._load_level_tips("level_01")
            self.causal_sight.clear_entity_positions()
            # Set camera bounds
            self.camera.set_world_bounds(
                self.current_level.width_pixels,
                self.current_level.height_pixels
            )
            
            # Center camera on player
            self.camera.center_on(self.player.x, self.player.y)
            
            # Update HUD
            self.hud.set_keys(0, self.current_level.config.required_keys)
            self.hud.set_player_health(self.player.health, self.player.max_health)
            
            # Start playing
            self.state_manager.change_state(GameState.PLAYING)
            self.menu.hide()
            
            # Transition effect
            self.effects.transition_in(TransitionType.FADE, 0.5)
    
    def _pause_game(self) -> None:
        """Pause the game."""
        self.state_manager.change_state(GameState.PAUSED)
        self.menu.set_state(MenuState.PAUSE)
        self.menu.show()
        self.input_handler.disable()
    
    def _resume_game(self) -> None:
        """Resume the game."""
        self.state_manager.change_state(GameState.PLAYING)
        self.menu.hide()
        self.input_handler.enable()
    
    def _game_over(self) -> None:
        """Handle game over."""
        self.state_manager.change_state(GameState.GAME_OVER)
        self.menu.set_state(MenuState.GAME_OVER)
        self.menu.show()
        self.input_handler.disable()
    
    def _level_complete(self) -> None:
        """Handle level completion."""
        self.state_manager.change_state(GameState.LEVEL_COMPLETE)
        self.menu.set_state(MenuState.LEVEL_COMPLETE)
        self.menu.show()
        self.input_handler.disable()
    
    def _restart_level(self) -> None:
        """Restart the current level."""
        # Reset player health
        self.player.reset_health()
        
        self.current_level = self.level_loader.reload_current_level(self.player)
        
        if self.current_level:
            self.camera.center_on(self.player.x, self.player.y)
            self.hud.set_keys(0, self.current_level.config.required_keys)
            self.hud.set_player_health(self.player.health, self.player.max_health)
            self.paradox_meter.set_level(0)
            self.causal_sight.clear_entity_positions()
            
            # Reload tips
            self._load_level_tips(self.current_level.config.level_id)
            
            self.state_manager.change_state(GameState.PLAYING)
            self.menu.hide()
            self.input_handler.enable()
            
            self.effects.transition_in(TransitionType.FADE, 0.3)
    
    def _next_level(self) -> None:
        """Load the next level."""
        self.current_level = self.level_loader.load_next_level(self.player)
        
        if self.current_level:
            self.camera.set_world_bounds(
                self.current_level.width_pixels,
                self.current_level.height_pixels
            )
            self.camera.center_on(self.player.x, self.player.y)
            self.hud.set_keys(0, self.current_level.config.required_keys)
            self.paradox_meter.set_level(0)
            self.causal_sight.clear_entity_positions()
            
            # Load tips for the new level
            self._load_level_tips(self.current_level.config.level_id)
            
            self.state_manager.change_state(GameState.PLAYING)
            self.menu.hide()
            self.input_handler.enable()
            
            self.effects.transition_in(TransitionType.FADE, 0.5)
        else:
            # All levels complete - return to menu
            self._return_to_menu()
    
    def _return_to_menu(self) -> None:
        """Return to main menu."""
        if self.current_level:
            self.current_level.cleanup()
            self.current_level = None

        self.causal_sight.deactivate()
        self.causal_sight.clear_entity_positions()
        
        self.multiverse.reset()
        self.state_manager.change_state(GameState.MENU)
        self.menu.set_state(MenuState.MAIN)
        self.menu.show()
        self.input_handler.enable()
    
    # ===== MENU CALLBACKS =====
    
    def _on_menu_play(self) -> None:
        self.effects.transition_out(
            TransitionType.FADE, 0.3,
            callback=self._start_game
        )
    
    def _on_menu_quit(self) -> None:
        self.running = False
    
    def _on_menu_resume(self) -> None:
        self._resume_game()
    
    def _on_menu_restart(self) -> None:
        self.effects.transition_out(
            TransitionType.FADE, 0.2,
            callback=self._restart_level
        )
    
    def _on_menu_next_level(self) -> None:
        self.effects.transition_out(
            TransitionType.FADE, 0.3,
            callback=self._next_level
        )
    
    def _on_menu_main(self) -> None:
        self.effects.transition_out(
            TransitionType.FADE, 0.3,
            callback=self._return_to_menu
        )
    
    # ===== EVENT HANDLERS =====
    
    def _on_universe_switched(self, data: dict) -> None:
        """Handle universe switch."""
        u_type = data.get('type')

        if isinstance(u_type, str):
            try:
                u_type = UniverseType(u_type)
            except ValueError:
                try:
                    u_type = UniverseType[u_type]
                except (KeyError, TypeError):
                    u_type = None

        if u_type is None:
            to_value = data.get('to')
            if isinstance(to_value, str):
                try:
                    u_type = UniverseType(to_value)
                except ValueError:
                    try:
                        u_type = UniverseType[to_value]
                    except (KeyError, TypeError):
                        u_type = None

        if u_type:
            self.universe_indicator.set_universe(u_type)
    
    def _on_paradox_changed(self, data: dict) -> None:
        """Handle paradox level change."""
        level = data.get('level')
        if level is None:
            level = data.get('new_level')
        if level is None:
            level = self.multiverse.paradox_manager.level

        self.paradox_meter.set_level(level)
    
    def _on_level_complete(self, data: dict) -> None:
        """Handle level completion."""
        level_id = self.current_level.config.level_id if self.current_level else ""
        if level_id and level_id not in self._rewarded_levels:
            self._rewarded_levels.add(level_id)
            self.player.rewards += self._reward_per_level

            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": f"Reward +{self._reward_per_level} | Total: {self.player.rewards}",
                "type": "success",
                "duration": 2.5
            })

        self._level_complete()
    
    def _on_level_failed(self, data: dict) -> None:
        """Handle level failure."""
        self._game_over()
        
        # Dramatic shake
        self.camera.shake(20, 0.5)
        self.effects.flash((255, 50, 50), 0.3)
    
    def _on_player_died(self, data: dict) -> None:
        """Handle player death."""
        self._game_over()
    
    def _on_causal_sight_toggled(self, data: dict) -> None:
        """Handle causal sight toggle."""
        active = data.get('active', False)
        if active:
            self.causal_sight.activate()
        else:
            self.causal_sight.deactivate()
    
    def _load_level_tips(self, level_id: str) -> None:
        """Load proximity tips for a level."""
        self.tip_manager.reset_for_level()
        proximity_tips = self.tip_manager.get_level_proximity_tips(level_id)
        self.tip_manager.add_proximity_tips(proximity_tips)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.current_level:
            self.current_level.cleanup()
        
        self.causal_sight.clear_entity_positions()
        self.hud.cleanup()
        self.tip_manager.cleanup()
        EventSystem.clear()
        
        pygame.mixer.quit()
        pygame.quit()


def main():
    """Entry point for the game."""
    game = Game()
    asyncio.run(game.run())


if __name__ == "__main__":
    main()
