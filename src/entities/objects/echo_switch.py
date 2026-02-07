"""
Echo Switch - A switch whose state echoes across universes.
"""

import pygame
from typing import Tuple, Optional, Callable
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE, COLOR_SWITCH_ON, COLOR_SWITCH_OFF
from ...multiverse.causal_node import CausalOperator, EntityState
from ...core.events import EventSystem, GameEvent


class EchoSwitch(Entity):
    """
    Echo Switch - A switch that affects linked objects across universes.
    
    When activated, the switch's effect echoes to linked objects based
    on the causal operator:
    - ECHO: Linked objects activate in the same way
    - INVERSE: Linked objects do the opposite
    
    Echo Switches:
    - Can be activated by the player
    - Can be activated by objects (stones) placed on them
    - Echo their state to linked entities
    - Are VARIANT (different state per universe possible)
    """
    
    def __init__(self, position: Tuple[float, float],
                 switch_id: str = None,
                 linked_entity_id: str = None,
                 operator: CausalOperator = CausalOperator.ECHO):
        """
        Initialize an Echo Switch.
        
        Args:
            position: Position
            switch_id: Unique identifier
            linked_entity_id: ID of the entity this switch controls
            operator: How this switch affects linked entity
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE - 8, TILE_SIZE // 2),
            color=COLOR_SWITCH_OFF,
            persistence=EntityPersistence.VARIANT,
            solid=False,
            interactive=True,
            entity_id=switch_id or f"switch_{id(self)}"
        )
        super().__init__(config)
        
        # Switch state
        self.is_on: bool = False
        self.is_locked: bool = False
        
        # Causal link
        self.linked_entity_id: str = linked_entity_id or ""
        self.operator: CausalOperator = operator
        
        # Visual
        self._activation_progress: float = 0.0
        self._glow: float = 0.0
        
        # Pressure activation (for stones)
        self._pressure_entities: set = set()
        
        # Create causal node
        self.create_causal_node(paradox_weight=3.0)
        
        # Create sprite
        self._update_sprite()
    
    def _update_sprite(self) -> None:
        """Update sprite based on state."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        
        # Base plate
        plate_color = (80, 80, 80)
        pygame.draw.rect(self.sprite, plate_color, 
                        (0, h // 2, w, h // 2), border_radius=4)
        
        # Button
        if self.is_on:
            # Pressed
            button_color = COLOR_SWITCH_ON
            button_rect = pygame.Rect(4, h // 2 - 2, w - 8, h // 2)
        else:
            # Unpressed
            button_color = COLOR_SWITCH_OFF
            button_rect = pygame.Rect(4, 0, w - 8, h // 2 + 4)
        
        pygame.draw.rect(self.sprite, button_color, button_rect, border_radius=4)
        pygame.draw.rect(self.sprite, (255, 255, 255), button_rect, 1, border_radius=4)
        
        # Indicator light
        light_color = (100, 255, 100) if self.is_on else (100, 100, 100)
        pygame.draw.circle(self.sprite, light_color, (w // 2, h // 4), 4)
    
    def activate(self, source: str = "player") -> bool:
        """
        Activate the switch.
        
        Args:
            source: What activated the switch
            
        Returns:
            True if state changed
        """
        if self.is_locked:
            return False
        
        if self.is_on:
            return False  # Already on
        
        self.is_on = True
        self._activation_progress = 0.0
        self._glow = 1.0
        self._update_sprite()
        
        # Update causal node state
        if self.causal_node:
            self.causal_node.state = EntityState.ON
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "activated",
            "source": source,
            "linked_entity": self.linked_entity_id,
            "operator": self.operator.value
        })
        
        return True
    
    def deactivate(self, source: str = "player") -> bool:
        """
        Deactivate the switch.
        
        Args:
            source: What deactivated the switch
            
        Returns:
            True if state changed
        """
        if self.is_locked:
            return False
        
        if not self.is_on:
            return False  # Already off
        
        self.is_on = False
        self._update_sprite()
        
        # Update causal node state
        if self.causal_node:
            self.causal_node.state = EntityState.OFF
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "deactivated",
            "source": source
        })
        
        return True
    
    def toggle(self, source: str = "player") -> bool:
        """Toggle the switch state."""
        if self.is_on:
            return self.deactivate(source)
        else:
            return self.activate(source)
    
    def on_interact(self, player) -> bool:
        """Handle player interaction."""
        return self.toggle("player")
    
    def add_pressure(self, entity_id: str) -> None:
        """
        Add pressure from an entity (e.g., stone placed on switch).
        
        Args:
            entity_id: ID of the entity applying pressure
        """
        was_empty = len(self._pressure_entities) == 0
        self._pressure_entities.add(entity_id)
        
        if was_empty:
            self.activate("pressure")
    
    def remove_pressure(self, entity_id: str) -> None:
        """
        Remove pressure from an entity.
        
        Args:
            entity_id: ID of the entity removing pressure
        """
        self._pressure_entities.discard(entity_id)
        
        if len(self._pressure_entities) == 0:
            self.deactivate("pressure_released")
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal state changes."""
        if new_state == EntityState.ON:
            self.activate("causal")
        elif new_state == EntityState.OFF:
            self.deactivate("causal")
        else:
            super().on_causal_change(new_state, source_id)
    
    def update(self, dt: float) -> None:
        """Update the switch."""
        # Animation
        if self._activation_progress < 1.0:
            self._activation_progress += dt * 4
        
        self._glow = max(0, self._glow - dt * 2)
        
        super().update(dt)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the switch."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox)
        render_y = int(self.y - oy)
        
        # Glow effect when just activated
        if self._glow > 0:
            glow_surface = pygame.Surface(
                (self.width + 20, self.height + 20), pygame.SRCALPHA
            )
            glow_color = (100, 255, 100, int(100 * self._glow))
            pygame.draw.rect(
                glow_surface, glow_color,
                (0, 0, self.width + 20, self.height + 20),
                border_radius=8
            )
            surface.blit(glow_surface, (render_x - 10, render_y - 10))
        
        # Main sprite
        surface.blit(self.sprite, (render_x, render_y))
        
        # Causal link indicator
        if self.linked_entity_id:
            indicator_color = (255, 200, 100) if self.operator == CausalOperator.ECHO else (255, 100, 100)
            pygame.draw.circle(surface, indicator_color,
                             (render_x + self.width - 6, render_y + 6), 4)
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "is_on": self.is_on,
            "is_locked": self.is_locked,
            "linked_entity_id": self.linked_entity_id,
            "operator": self.operator.value
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'EchoSwitch':
        """Deserialize from save data."""
        switch = cls(
            position=tuple(data["position"]),
            switch_id=data["entity_id"],
            linked_entity_id=data.get("linked_entity_id"),
            operator=CausalOperator(data.get("operator", "echo"))
        )
        switch.is_on = data.get("is_on", False)
        switch.is_locked = data.get("is_locked", False)
        switch.exists = data["exists"]
        switch._update_sprite()
        return switch
