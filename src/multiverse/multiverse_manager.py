"""
Multiverse Manager - Coordinates all parallel universes.

This is the top-level controller for the multiverse system.
It manages universe switching, coordinates causal propagation,
and maintains the relationship between universes.
"""

import pygame
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import math

from .universe import Universe, UniverseType
from .causal_graph import CausalGraph
from .paradox_manager import ParadoxManager
from .causal_node import CausalNode, CausalOperator, EntityState

from ..core.settings import (
    UNIVERSE_SWITCH_COOLDOWN, SCREEN_WIDTH, SCREEN_HEIGHT,
    UNIVERSE_PRIME, UNIVERSE_ECHO, UNIVERSE_FRACTURE,
    ANIMATION_UNIVERSE_SWITCH_DURATION
)
from ..core.events import EventSystem, GameEvent

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from ..entities.player import Player


class MultiverseManager:
    """
    Central coordinator for all parallel universes.
    
    Responsibilities:
    - Create and manage all universe instances
    - Handle universe switching
    - Coordinate causal graph updates
    - Manage cross-universe entity relationships
    - Handle paradox effects on universes
    
    Usage:
        manager = MultiverseManager()
        manager.create_universes(level_data)
        manager.set_active_universe(UniverseType.PRIME)
        
        # In game loop
        manager.update(dt)
        manager.render(screen)
        
        # To switch universes
        manager.switch_universe(UniverseType.ECHO)
    """
    
    def __init__(self):
        """Initialize the multiverse manager."""
        # Universe storage
        self.universes: Dict[UniverseType, Universe] = {}
        self._active_universe: Optional[Universe] = None
        
        # Core systems
        self.causal_graph = CausalGraph()
        self.paradox_manager = ParadoxManager()
        
        # Switching state
        self._switch_cooldown: float = 0.0
        self._is_switching: bool = False
        self._switch_progress: float = 0.0
        self._switch_from: Optional[UniverseType] = None
        self._switch_to: Optional[UniverseType] = None
        
        # Player reference (set externally)
        self.player: Optional['Player'] = None
        
        # Visual state
        self._transition_alpha: float = 0.0
        
        # Subscribe to events
        EventSystem.subscribe(GameEvent.CAUSAL_CHANGE, self._on_causal_change)
        EventSystem.subscribe(GameEvent.PARADOX_CHANGED, self._on_paradox_changed)
    
    @property
    def active_universe(self) -> Optional[Universe]:
        """Get the currently active universe."""
        return self._active_universe
    
    @property
    def active_type(self) -> Optional[UniverseType]:
        """Get the type of the active universe."""
        return self._active_universe.universe_type if self._active_universe else None
    
    def create_universes(self, width: int = 20, height: int = 11) -> None:
        """
        Create all universe instances.
        
        Args:
            width: Width in tiles
            height: Height in tiles
        """
        self.universes = {
            UniverseType.PRIME: Universe(UniverseType.PRIME, width, height),
            UniverseType.ECHO: Universe(UniverseType.ECHO, width, height),
            UniverseType.FRACTURE: Universe(UniverseType.FRACTURE, width, height),
        }
        
        # Set Prime as default active
        self.set_active_universe(UniverseType.PRIME)
    
    def set_active_universe(self, universe_type: UniverseType) -> None:
        """
        Set the active universe without transition effects.
        
        Args:
            universe_type: The universe type to activate
        """
        # Deactivate current
        if self._active_universe:
            self._active_universe.is_active = False
        
        # Activate new
        self._active_universe = self.universes.get(universe_type)
        if self._active_universe:
            self._active_universe.is_active = True
    
    def switch_universe(self, target_type: UniverseType) -> bool:
        """
        Switch to a different universe with transition effects.
        
        Args:
            target_type: The universe type to switch to
            
        Returns:
            True if switch started, False if on cooldown or invalid
        """
        # Check cooldown
        if self._switch_cooldown > 0:
            EventSystem.emit(GameEvent.UNIVERSE_SWITCH_FAILED, {
                "reason": "cooldown",
                "remaining": self._switch_cooldown
            })
            return False
        
        # Check if already in target
        if self.active_type == target_type:
            return False
        
        # Check if target exists
        if target_type not in self.universes:
            EventSystem.emit(GameEvent.UNIVERSE_SWITCH_FAILED, {
                "reason": "invalid_universe"
            })
            return False
        
        # Start switch
        self._is_switching = True
        self._switch_progress = 0.0
        self._switch_from = self.active_type
        self._switch_to = target_type
        self._switch_cooldown = UNIVERSE_SWITCH_COOLDOWN
        
        EventSystem.emit(GameEvent.UNIVERSE_SWITCH_REQUESTED, {
            "from": self._switch_from.value if self._switch_from else None,
            "to": target_type.value
        })
        
        return True
    
    def get_universe(self, universe_type: UniverseType) -> Optional[Universe]:
        """Get a universe by type."""
        return self.universes.get(universe_type)
    
    def add_universe(self, universe: Universe) -> None:
        """
        Add or replace a universe.
        
        Args:
            universe: The universe to add
        """
        self.universes[universe.universe_type] = universe
        
        # If no active universe, make this one active
        if self._active_universe is None:
            self.set_active_universe(universe.universe_type)
    
    def reset(self) -> None:
        """
        Reset the multiverse to initial state.
        
        Clears all entities, resets causal graph and paradox.
        Called when loading a new level.
        """
        # Clear all universes
        for universe in self.universes.values():
            universe.clear_entities()
        
        # Reset causal graph
        self.causal_graph = CausalGraph()
        
        # Reset paradox
        self.paradox_manager.reset()
        
        # Reset switching state
        self._switch_cooldown = 0.0
        self._is_switching = False
        self._switch_progress = 0.0
        self._switch_from = None
        self._switch_to = None
        self._transition_alpha = 0.0
        
        # Set Prime as default active
        self.set_active_universe(UniverseType.PRIME)
    
    def get_all_universes(self) -> List[Universe]:
        """Get all universes."""
        return list(self.universes.values())
    
    def add_entity_to_universe(self, entity: 'Entity', universe_type: UniverseType) -> None:
        """
        Add an entity to a specific universe.
        
        Args:
            entity: The entity to add
            universe_type: Which universe to add it to
        """
        universe = self.universes.get(universe_type)
        if universe:
            universe.add_entity(entity)
            
            # If entity has a causal node, add to graph
            if entity.causal_node:
                self.causal_graph.add_node(entity.causal_node)
    
    def add_entity_to_all_universes(self, entity: 'Entity') -> None:
        """
        Add an entity to all universes (for anchored entities).
        
        Note: For variants, add different entity instances to each universe.
        
        Args:
            entity: The entity to add
        """
        for universe in self.universes.values():
            universe.add_entity(entity)
    
    def remove_entity(self, entity: 'Entity') -> None:
        """
        Remove an entity from all universes.
        
        Args:
            entity: The entity to remove
        """
        for universe in self.universes.values():
            universe.remove_entity(entity)
        
        if entity.causal_node:
            self.causal_graph.remove_node(entity.causal_node.node_id)
    
    def get_entity_across_universes(self, entity_id: str) -> Dict[UniverseType, 'Entity']:
        """
        Get all versions of an entity across universes.
        
        Args:
            entity_id: The entity ID to search for
            
        Returns:
            Dictionary mapping universe type to entity instance
        """
        result = {}
        for utype, universe in self.universes.items():
            entity = universe.get_entity(entity_id)
            if entity:
                result[utype] = entity
        return result
    
    def update(self, dt: float) -> None:
        """
        Update the multiverse.
        
        Args:
            dt: Delta time in seconds
        """
        # Update switch cooldown
        if self._switch_cooldown > 0:
            self._switch_cooldown = max(0, self._switch_cooldown - dt)
        
        # Handle switching transition
        if self._is_switching:
            self._update_switch_transition(dt)
        
        # Update paradox
        self.paradox_manager.update(dt)
        
        # Update active universe
        if self._active_universe:
            self._active_universe.update(dt)
        
        # Apply paradox effects to universes
        self._apply_paradox_effects()
    
    def _update_switch_transition(self, dt: float) -> None:
        """Update the universe switch transition animation."""
        self._switch_progress += dt / ANIMATION_UNIVERSE_SWITCH_DURATION
        
        if self._switch_progress >= 1.0:
            # Complete the switch
            self._complete_switch()
        else:
            # Update transition alpha for visual effect
            # Bell curve for flash effect
            self._transition_alpha = math.sin(self._switch_progress * math.pi)
    
    def _complete_switch(self) -> None:
        """Complete a universe switch."""
        old_universe = self._active_universe
        self.set_active_universe(self._switch_to)
        
        # Handle player position validation
        if self.player:
            new_universe = self._active_universe
            old_pos = self.player.position
            new_pos = new_universe.find_valid_position(old_pos, self.player.size)
            
            if new_pos != old_pos:
                self.player.position = new_pos
        
        # Reset transition state
        self._is_switching = False
        self._switch_progress = 0.0
        self._transition_alpha = 0.0
        
        EventSystem.emit(GameEvent.UNIVERSE_SWITCHED, {
            "from": self._switch_from.value if self._switch_from else None,
            "to": self._switch_to.value if self._switch_to else None
        })
        
        self._switch_from = None
        self._switch_to = None
    
    def _apply_paradox_effects(self) -> None:
        """Apply paradox effects to all universes."""
        effects = self.paradox_manager.get_effects()
        
        # Fracture universe is most affected by paradox
        fracture = self.universes.get(UniverseType.FRACTURE)
        if fracture:
            fracture.stability = 1.0 - (effects["visual_distortion"] * 0.5)
        
        # Prime is most stable
        prime = self.universes.get(UniverseType.PRIME)
        if prime:
            prime.stability = 1.0 - (effects["visual_distortion"] * 0.1)
    
    def _on_causal_change(self, event_data) -> None:
        """Handle causal change events."""
        # Propagate changes and track paradox
        pass  # Main propagation handled elsewhere
    
    def _on_paradox_changed(self, event_data) -> None:
        """Handle paradox change events."""
        amount = event_data.get("amount", 0)
        if amount > 0:
            # Paradox increased - update universe stability
            self._apply_paradox_effects()
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the active universe.
        
        Args:
            surface: Surface to render to
        """
        if not self._active_universe:
            return
        
        # Clear with universe background color
        surface.fill(self._active_universe.bg_color)
        
        # Render active universe
        self._active_universe.render(surface)
        
        # Render transition effect
        if self._is_switching and self._transition_alpha > 0:
            self._render_transition(surface)
    
    def _render_transition(self, surface: pygame.Surface) -> None:
        """Render the universe switch transition effect."""
        # Create transition overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Blend colors of both universes
        if self._switch_from and self._switch_to:
            from_color = self.universes[self._switch_from].color
            to_color = self.universes[self._switch_to].color
            
            blend = self._switch_progress
            color = (
                int(from_color[0] * (1 - blend) + to_color[0] * blend),
                int(from_color[1] * (1 - blend) + to_color[1] * blend),
                int(from_color[2] * (1 - blend) + to_color[2] * blend),
            )
            overlay.fill(color)
        else:
            overlay.fill((255, 255, 255))
        
        overlay.set_alpha(int(self._transition_alpha * 200))
        surface.blit(overlay, (0, 0))
    
    def render_preview(self, surface: pygame.Surface, universe_type: UniverseType,
                       rect: pygame.Rect, alpha: int = 128) -> None:
        """
        Render a preview of a universe (for causal sight).
        
        Args:
            surface: Surface to render to
            universe_type: Which universe to preview
            rect: Rectangle to render within
            alpha: Transparency level
        """
        universe = self.universes.get(universe_type)
        if not universe:
            return
        
        # Create preview surface
        preview = pygame.Surface(rect.size)
        preview.fill(universe.bg_color)
        
        # Scale factor
        scale_x = rect.width / SCREEN_WIDTH
        scale_y = rect.height / SCREEN_HEIGHT
        
        # Render scaled universe
        # (Simplified - just show entities as dots)
        for entity in universe.entities:
            if not entity.exists:
                continue
            ex = int(entity.position[0] * scale_x)
            ey = int(entity.position[1] * scale_y)
            pygame.draw.circle(preview, universe.color, (ex, ey), 3)
        
        preview.set_alpha(alpha)
        surface.blit(preview, rect.topleft)
    
    def get_switch_cooldown_remaining(self) -> float:
        """Get remaining switch cooldown time."""
        return self._switch_cooldown
    
    def is_switch_available(self) -> bool:
        """Check if universe switch is currently available."""
        return self._switch_cooldown <= 0 and not self._is_switching
    
    def clear(self) -> None:
        """Clear all universes and reset state."""
        self.causal_graph.clear()
        self.paradox_manager.reset()
        
        for universe in self.universes.values():
            universe.entities.clear()
            universe.entity_map.clear()
        
        self._active_universe = None
        self._switch_cooldown = 0
        self._is_switching = False
    
    def serialize(self) -> dict:
        """Serialize for saving."""
        return {
            "active_universe": self.active_type.value if self.active_type else None,
            "universes": {
                utype.value: universe.serialize()
                for utype, universe in self.universes.items()
            },
            "causal_graph": self.causal_graph.serialize(),
            "paradox": self.paradox_manager.serialize()
        }
    
    def deserialize(self, data: dict, entity_map: Dict[str, 'Entity']) -> None:
        """Deserialize from save data."""
        self.paradox_manager.deserialize(data.get("paradox", {}))
        self.causal_graph.deserialize(data.get("causal_graph", {}), entity_map)
        
        active_type_str = data.get("active_universe")
        if active_type_str:
            self.set_active_universe(UniverseType(active_type_str))
