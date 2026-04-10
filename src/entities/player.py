import pygame
from typing import Tuple, Optional, List, TYPE_CHECKING
import math

from .entity import Entity, EntityConfig, EntityPersistence
from ..core.settings import (
    PLAYER_SPEED, PLAYER_SIZE, PLAYER_INTERACTION_RANGE,
    COLOR_PLAYER, KEY_MOVE_UP, KEY_MOVE_DOWN, KEY_MOVE_LEFT, KEY_MOVE_RIGHT,
    KEY_INTERACT, KEY_ATTACK, KEY_CAUSAL_SIGHT, KEY_PARADOX_PULSE,
    KEY_SWITCH_PRIME, KEY_SWITCH_ECHO, KEY_SWITCH_FRACTURE,
    UNIVERSE_SWITCH_COOLDOWN, TILE_SIZE,
    PLAYER_MAX_HEALTH, PLAYER_ATTACK_DAMAGE, PLAYER_ATTACK_RANGE,
    PLAYER_ATTACK_COOLDOWN, PLAYER_INVINCIBILITY_TIME,
    GHOST_BUFFER_SECONDS, get_ui_font
)
from ..core.events import EventSystem, GameEvent
from ..multiverse.universe import UniverseType
from ..utils.sprite_loader import load_entity_sprite

if TYPE_CHECKING:
    from ..multiverse.multiverse_manager import MultiverseManager


class Player(Entity):
    GHOST_BUFFER_SECONDS = GHOST_BUFFER_SECONDS
    
    def __init__(self, position: Tuple[float, float] = (100, 100)):
        scaled_player_size = (
            max(1, int(round(PLAYER_SIZE[0] * 1.3225))),
            max(1, int(round(PLAYER_SIZE[1] * 1.3225))),
        )

        config = EntityConfig(
            position=position,
            size=scaled_player_size,
            color=COLOR_PLAYER,
            persistence=EntityPersistence.ANCHORED,
            solid=True,
            interactive=False,
            entity_id="player"
        )
        super().__init__(config)
        
        self.speed = PLAYER_SPEED
        self.movement_input: Tuple[float, float] = (0, 0)
        self.facing: str = "down"  
        self.current_universe: UniverseType = UniverseType.PRIME
        self.switch_cooldown: float = 0.0
        
        self.causal_sight_active: bool = False
        self.paradox_pulse_cooldown: float = 0.0
        self.paradox_pulse_duration: float = 0.0
        self.is_phasing: bool = False
        
        self.nearby_interactive: Optional[Entity] = None
        self.keys_collected: int = 0
        self.total_keys_collected: int = 0
        self.rewards: int = 0
        
        self.animation_state: str = "idle"
        self.animation_frame: int = 0
        self.animation_timer: float = 0.0

        self.multiverse: Optional['MultiverseManager'] = None

        self.max_health: int = PLAYER_MAX_HEALTH
        self.health: int = PLAYER_MAX_HEALTH
        self.attack_damage: int = PLAYER_ATTACK_DAMAGE
        self.attack_range: float = PLAYER_ATTACK_RANGE
        self.attack_cooldown: float = 0.0
        self.invincibility_timer: float = 0.0
        self.is_attacking: bool = False
        self._attack_animation_timer: float = 0.0

        self._universe_glow: float = 0.0
        self._pulse_effect: float = 0.0
        self._hurt_flash: float = 0.0

        self._interaction_font = get_ui_font(24)

        self._ghost_buffer = []
        self._ghost_buffer_duration = 0.0

        self._create_player_sprite()

    def record_ghost_snapshot(self, dt: float, active_universe_type=None) -> None:
        snapshot = {
            "dt": dt,
            "x": self.x,
            "y": self.y,
            "facing": self.facing,
            "is_attacking": self.is_attacking,
            "interacted": False,
            "universe": active_universe_type if active_universe_type is not None else self.current_universe,
        }

        self._ghost_buffer.append(snapshot)
        self._ghost_buffer_duration += dt

        while self._ghost_buffer and self._ghost_buffer_duration > self.GHOST_BUFFER_SECONDS:
            removed = self._ghost_buffer.pop(0)
            self._ghost_buffer_duration -= removed.get("dt", 0.0)

    def get_ghost_buffer_copy(self, universe_type) -> list:
        target_universe = universe_type.value if hasattr(universe_type, "value") else universe_type
        filtered = []

        for snapshot in self._ghost_buffer:
            snap_universe = snapshot.get("universe")
            snap_universe_value = snap_universe.value if hasattr(snap_universe, "value") else snap_universe
            if snap_universe_value == target_universe:
                filtered.append(snapshot.copy())

        return filtered
    
    @property
    def velocity_x(self) -> float:
        return self.movement_input[0] * self.speed
    
    @property
    def velocity_y(self) -> float:
        return self.movement_input[1] * self.speed
    
    def _create_player_sprite(self) -> None:
        loaded = load_entity_sprite("player.png", self.size)
        if loaded is not None:
            self.sprite = loaded
            return

        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        center_x, center_y = w // 2, h // 2
        
        body_rect = pygame.Rect(w // 4, h // 3, w // 2, h // 2)
        pygame.draw.ellipse(self.sprite, self.color, body_rect)
        
        head_radius = w // 4
        pygame.draw.circle(self.sprite, self.color, 
                          (center_x, h // 4), head_radius)
        
        pygame.draw.circle(self.sprite, (255, 255, 255),
                          (center_x - 4, h // 4 - 2), 3)
        pygame.draw.circle(self.sprite, (255, 255, 255),
                          (center_x + 4, h // 4 - 2), 3)
        
        pygame.draw.ellipse(self.sprite, (255, 255, 255), body_rect, 2)
        pygame.draw.circle(self.sprite, (255, 255, 255),
                          (center_x, h // 4), head_radius, 2)
    
    def handle_input(self, move_x: float = 0, move_y: float = 0, dt: float = 0) -> None:
        dx, dy = move_x, move_y
        
        if dy < -0.5:
            self.facing = "up"
        elif dy > 0.5:
            self.facing = "down"
        if dx < -0.5:
            self.facing = "left"
        elif dx > 0.5:
            self.facing = "right"

        if dx != 0 and dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
        
        self.movement_input = (dx, dy)

        if dx != 0 or dy != 0:
            self.animation_state = "walk"
        else:
            self.animation_state = "idle"
    
    def handle_key_press(self, key: int) -> None:

        if key == KEY_SWITCH_PRIME:
            self.request_universe_switch(UniverseType.PRIME)
        elif key == KEY_SWITCH_ECHO:
            self.request_universe_switch(UniverseType.ECHO)
        elif key == KEY_SWITCH_FRACTURE:
            self.request_universe_switch(UniverseType.FRACTURE)

        elif key == KEY_CAUSAL_SIGHT:
            self.toggle_causal_sight()

        elif key == KEY_INTERACT:
            self.interact()

        elif key == KEY_PARADOX_PULSE:
            self.paradox_pulse()
    
    def request_universe_switch(self, target: UniverseType) -> bool:
        if not self.multiverse:
            return False
        
        if self.switch_cooldown > 0:
            return False
        
        if self.current_universe == target:
            return False
        
        if self.multiverse.switch_universe(target):
            self.current_universe = target
            self.switch_cooldown = UNIVERSE_SWITCH_COOLDOWN
            self._universe_glow = 1.0
            
            EventSystem.emit(GameEvent.PLAYER_MOVED, {
                "universe": target.value
            })
            return True
        
        return False
    
    def toggle_causal_sight(self) -> None:
        self.causal_sight_active = not self.causal_sight_active
        
        EventSystem.emit(GameEvent.PLAYER_CAUSAL_SIGHT_TOGGLE, {
            "active": self.causal_sight_active
        })
    
    def interact(self) -> bool:
        if self.nearby_interactive and self.nearby_interactive.exists:
            result = self.nearby_interactive.on_interact(self)
            
            EventSystem.emit(GameEvent.PLAYER_INTERACT, {
                "target_id": self.nearby_interactive.entity_id,
                "success": result
            })
            return result
        return False
    
    def attack(self) -> bool:

        if self.attack_cooldown > 0:
            return False
        
        self.is_attacking = True
        self._attack_animation_timer = 0.25
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN

        EventSystem.emit(GameEvent.PLAYER_ATTACK, {
            "position": (self.x, self.y),
            "facing": self.facing,
            "damage": self.attack_damage,
            "range": self.attack_range
        })
        
        return True
    
    def get_attack_rect(self) -> pygame.Rect:
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        
        attack_width = 40
        attack_height = 40
        
        if self.facing == "up":
            return pygame.Rect(cx - attack_width / 2, cy - self.attack_range, attack_width, attack_height)
        elif self.facing == "down":
            return pygame.Rect(cx - attack_width / 2, cy + self.height / 2, attack_width, attack_height)
        elif self.facing == "left":
            return pygame.Rect(cx - self.attack_range, cy - attack_height / 2, attack_width, attack_height)
        else:  # right
            return pygame.Rect(cx + self.width / 2, cy - attack_height / 2, attack_width, attack_height)
    
    def take_damage(self, amount: int, knockback_dir: Tuple[float, float] = (0, 0)) -> bool:
        if self.invincibility_timer > 0:
            return False
        
        self.health -= amount
        self.invincibility_timer = PLAYER_INVINCIBILITY_TIME
        self._hurt_flash = 0.3

        if knockback_dir[0] != 0 or knockback_dir[1] != 0:
            knockback_strength = 80
            self.position = (
                self.x + knockback_dir[0] * knockback_strength * 0.016,
                self.y + knockback_dir[1] * knockback_strength * 0.016
            )
        
        EventSystem.emit(GameEvent.PLAYER_DAMAGED, {
            "damage": amount,
            "health": self.health,
            "max_health": self.max_health
        })
        
        if self.health <= 0:
            self.health = 0
            EventSystem.emit(GameEvent.PLAYER_DIED, {})
        
        return True
    
    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)
        EventSystem.emit(GameEvent.PLAYER_HEALED, {
            "amount": amount,
            "health": self.health
        })
    
    def reset_health(self) -> None:
        self.health = self.max_health
        self.invincibility_timer = 0.0
    
    def paradox_pulse(self) -> bool:
        if self.paradox_pulse_cooldown > 0:
            return False
        
        if not self.multiverse:
            return False
        if self.multiverse.paradox_manager.consume_paradox(5):
            self.is_phasing = True
            self.paradox_pulse_duration = 0.5
            self.paradox_pulse_cooldown = 2.0 
            self._pulse_effect = 1.0
            
            EventSystem.emit(GameEvent.PLAYER_PARADOX_PULSE, {
                "duration": 0.5
            })
            return True
        
        return False
    
    def find_nearby_interactive(self, entities: List[Entity]) -> None:
        self.nearby_interactive = None
        min_distance = PLAYER_INTERACTION_RANGE
        
        for entity in entities:
            if not entity.interactive or not entity.exists:
                continue
            
            distance = self.distance_to(entity)
            if distance < min_distance:
                min_distance = distance
                self.nearby_interactive = entity
    
    def update(self, dt: float) -> None:
        if self.switch_cooldown > 0:
            self.switch_cooldown = max(0, self.switch_cooldown - dt)
        
        if self.paradox_pulse_cooldown > 0:
            self.paradox_pulse_cooldown = max(0, self.paradox_pulse_cooldown - dt)
        
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        if self.invincibility_timer > 0:
            self.invincibility_timer = max(0, self.invincibility_timer - dt)

        if self._attack_animation_timer > 0:
            self._attack_animation_timer -= dt
            if self._attack_animation_timer <= 0:
                self.is_attacking = False
        
        if self._hurt_flash > 0:
            self._hurt_flash = max(0, self._hurt_flash - dt)
        if self.paradox_pulse_duration > 0:
            self.paradox_pulse_duration -= dt
            if self.paradox_pulse_duration <= 0:
                self.is_phasing = False
        self._universe_glow = max(0, self._universe_glow - dt * 2)
        self._pulse_effect = max(0, self._pulse_effect - dt * 3)

        self.animation_timer += dt
        if self.animation_timer > 0.15:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
    
    def _try_move(self, dx: float, dy: float) -> None:
        if not self.multiverse or not self.multiverse.active_universe:
            self.move(dx, dy)
            return
        
        universe = self.multiverse.active_universe
        tilemap = universe.tilemap

        if self.is_phasing:
            self.move(dx, dy)
            return

        new_x = self.x + dx
        if self._can_move_to(new_x, self.y, tilemap):
            self.position = (new_x, self.y)
        else:
            pass
        
        new_y = self.y + dy
        if self._can_move_to(self.x, new_y, tilemap):
            self.position = (self.x, new_y)
    
    def _can_move_to(self, x: float, y: float, tilemap) -> bool:
        margin = 4 
        corners = [
            (x + margin, y + margin),
            (x + self.width - margin, y + margin),
            (x + margin, y + self.height - margin),
            (x + self.width - margin, y + self.height - margin)
        ]
        
        for cx, cy in corners:
            if tilemap.is_solid_pixel(cx, cy):
                return False
        
        return True
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        if self.is_phasing:
            ghost = self.sprite.copy()
            ghost.set_alpha(100)
            for i in range(3):
                offset = (i + 1) * 5
                surface.blit(ghost, (render_x - offset, render_y))

        if self._universe_glow > 0:
            glow_surface = pygame.Surface(
                (self.width + 20, self.height + 20), pygame.SRCALPHA
            )
            glow_color = (*self.multiverse.active_universe.color, 
                         int(100 * self._universe_glow)) if self.multiverse else (255, 255, 255, 100)
            pygame.draw.ellipse(glow_surface, glow_color,
                              (0, 0, self.width + 20, self.height + 20))
            surface.blit(glow_surface, (render_x - 10, render_y - 10))
        if self._pulse_effect > 0:
            pulse_radius = int((1 - self._pulse_effect) * 50 + 20)
            pulse_alpha = int(self._pulse_effect * 150)
            pulse_surface = pygame.Surface(
                (pulse_radius * 2, pulse_radius * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(pulse_surface, (200, 100, 255, pulse_alpha),
                             (pulse_radius, pulse_radius), pulse_radius, 3)
            cx = render_x + self.width // 2 - pulse_radius
            cy = render_y + self.height // 2 - pulse_radius
            surface.blit(pulse_surface, (cx, cy))

        if self.is_phasing:
            phasing_sprite = self.sprite.copy()
            phasing_sprite.set_alpha(150)
            surface.blit(phasing_sprite, (render_x, render_y))
        else:
            surface.blit(self.sprite, (render_x, render_y))
        if self.causal_sight_active:
            eye_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(eye_surface, (100, 200, 255, 200), (5, 5), 5)
            surface.blit(eye_surface, 
                        (render_x + self.width // 2 - 5, 
                         render_y + self.height // 4 - 5))
        if self.nearby_interactive:
            self._render_interaction_prompt(surface, render_x, render_y)
    
    def _render_interaction_prompt(self, surface: pygame.Surface, 
                                   rx: int, ry: int) -> None:

        text = self._interaction_font.render("[E]", True, (255, 255, 255))
        text_rect = text.get_rect(center=(rx + self.width // 2, ry - 15))

        bg_rect = text_rect.inflate(8, 4)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1, border_radius=4)
        
        surface.blit(text, text_rect)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data.update({
            "current_universe": self.current_universe.value,
            "causal_sight_active": self.causal_sight_active,
            "rewards": self.rewards,
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Player':
        player = cls(tuple(data["position"]))
        player.current_universe = UniverseType(data["current_universe"])
        player.causal_sight_active = data.get("causal_sight_active", False)
        player.rewards = data.get("rewards", 0)
        return player
