import pygame
from typing import List, Tuple

from .entity import Entity, EntityConfig, EntityPersistence
from .objects.echo_switch import EchoSwitch
from ..core.settings import (
    PLAYER_SIZE,
    GHOST_ALPHA,
    GHOST_COLOR,
    GHOST_PARTICLE_INTERVAL,
    GHOST_INTERACTION_RANGE,
)
from ..core.events import GameEvent


class GhostEntity(Entity):
    GHOST_ALPHA = GHOST_ALPHA
    GHOST_COLOR = GHOST_COLOR

    def __init__(self, replay_buffer: list, universe):
        start_x = 0.0
        start_y = 0.0
        if replay_buffer:
            start_x = replay_buffer[0].get("x", 0.0)
            start_y = replay_buffer[0].get("y", 0.0)

        config = EntityConfig(
            position=(start_x, start_y),
            size=PLAYER_SIZE,
            color=self.GHOST_COLOR,
            persistence=EntityPersistence.LOCAL,
            solid=False,
            interactive=False,
            entity_id=f"ghost_{id(self)}"
        )
        super().__init__(config)

        self.id = self.entity_id
        self.universe = universe
        self.replay_buffer = list(replay_buffer)
        self.replay_index = 0
        self.replay_elapsed = 0.0
        self.finished = False
        self.is_solid = False
        self.solid = False
        self.is_ghost = True
        self.facing = "down"
        self._particle_timer = 0.0

    def update(self, dt: float, universe, physics_system, event_system) -> None:
        if self.finished:
            return

        self.replay_elapsed += dt

        while (
            self.replay_index < len(self.replay_buffer)
            and self.replay_elapsed >= self.replay_buffer[self.replay_index].get("dt", 0.0)
        ):
            snap = self.replay_buffer[self.replay_index]
            self.replay_elapsed -= snap.get("dt", 0.0)

            self.x = snap.get("x", self.x)
            self.y = snap.get("y", self.y)
            self.facing = snap.get("facing", self.facing)

            if snap.get("interacted", False):
                self._try_ghost_interact(universe, event_system)

            self.replay_index += 1

        if self.replay_index >= len(self.replay_buffer):
            self.finished = True
            event_system.emit(GameEvent.ENTITY_DESTROYED, {
                "entity_id": self.id,
                "reason": "ghost_expired"
            })
            return

        self._particle_timer += dt
        if self._particle_timer >= GHOST_PARTICLE_INTERVAL:
            self._particle_timer = 0.0
            event_system.emit(GameEvent.PARTICLE_SPAWN, {
                "x": self.x,
                "y": self.y,
                "color": self.GHOST_COLOR,
                "count": 2,
                "speed": 12,
                "lifetime": 0.35,
                "size": 3,
            })

    def _distance_to(self, other: Entity) -> float:
        dx = other.center[0] - self.center[0]
        dy = other.center[1] - self.center[1]
        return (dx * dx + dy * dy) ** 0.5

    def _ghost_can_trigger(self, entity: Entity) -> bool:
        return isinstance(entity, EchoSwitch) and getattr(entity, "pressure_activate", False)

    def _try_ghost_interact(self, universe, event_system) -> None:
        nearest = None
        nearest_dist = float("inf")

        for entity in universe.entities:
            if entity is self:
                continue
            if not self._ghost_can_trigger(entity):
                continue

            dist = self._distance_to(entity)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = entity

        if nearest and nearest_dist <= GHOST_INTERACTION_RANGE:
            try:
                nearest.on_interact(actor=self, event_system=event_system)
            except TypeError:
                nearest.on_interact(self)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int], renderer=None) -> None:
        ghost_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(
            ghost_surf,
            (*self.GHOST_COLOR, self.GHOST_ALPHA),
            (0, 0, self.width, self.height),
            border_radius=4,
        )
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        surface.blit(ghost_surf, (sx, sy))

    def render(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        self.draw(surface, camera_offset, None)
