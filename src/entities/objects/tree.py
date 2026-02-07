"""
Tree - A causal origin entity that can affect other entities.

Trees can be the origin point for other entities like Shades.
Destroying a tree affects its dependents across universes.
"""

import pygame
from typing import Tuple
import math

from ..entity import Entity, EntityConfig, EntityPersistence
from ...core.settings import TILE_SIZE
from ...multiverse.causal_node import EntityState
from ...core.events import EventSystem, GameEvent


class Tree(Entity):
    """
    Tree - A living entity that can be a causal origin.
    
    Trees exist in different states across universes:
    - Living (green, full)
    - Dead (brown, bare)
    - Destroyed (stump only)
    
    Other entities (like Shades) may depend on trees for their existence.
    Destroying a tree propagates causal changes to its dependents.
    """
    
    def __init__(self, position: Tuple[float, float],
                 tree_id: str = None,
                 state: str = "living"):
        """
        Initialize a Tree.
        
        Args:
            position: Position
            tree_id: Unique identifier
            state: Initial state ("living", "dead", "stump")
        """
        config = EntityConfig(
            position=position,
            size=(TILE_SIZE + 16, TILE_SIZE + 32),
            color=(80, 150, 80),
            persistence=EntityPersistence.VARIANT,
            solid=True,
            interactive=True,
            entity_id=tree_id or f"tree_{id(self)}"
        )
        super().__init__(config)
        
        # Tree state
        self.tree_state: str = state
        self.health: int = 100 if state == "living" else 0
        
        # Animation
        self._sway: float = 0.0
        self._destruction_timer: float = 0.0
        self._is_falling: bool = False
        
        # Create causal node (trees are important causal anchors)
        self.create_causal_node(paradox_weight=10.0)
        if self.causal_node:
            if state == "living":
                self.causal_node.state = EntityState.EXISTS
            else:
                self.causal_node.state = EntityState.DESTROYED
        
        # Create sprite
        self._create_sprite()
    
    def _create_sprite(self) -> None:
        """Create the tree's appearance based on state."""
        self.sprite = pygame.Surface(self.size, pygame.SRCALPHA)
        
        w, h = self.size
        trunk_x = w // 2 - 8
        trunk_y = h * 2 // 3
        
        if self.tree_state == "stump":
            # Just a stump
            pygame.draw.rect(self.sprite, (100, 70, 40),
                           (trunk_x - 4, h - 20, 24, 20), border_radius=4)
            pygame.draw.ellipse(self.sprite, (80, 60, 40),
                              (trunk_x - 4, h - 24, 24, 8))
        
        elif self.tree_state == "dead":
            # Dead tree - brown, no leaves
            # Trunk
            pygame.draw.rect(self.sprite, (80, 60, 40),
                           (trunk_x, trunk_y, 16, h - trunk_y))
            
            # Bare branches
            pygame.draw.line(self.sprite, (80, 60, 40),
                           (w // 2, trunk_y), (w // 4, trunk_y // 2), 4)
            pygame.draw.line(self.sprite, (80, 60, 40),
                           (w // 2, trunk_y), (3 * w // 4, trunk_y // 2), 4)
            pygame.draw.line(self.sprite, (80, 60, 40),
                           (w // 2, trunk_y + 10), (w // 3, trunk_y - 10), 3)
        
        else:
            # Living tree
            # Trunk
            pygame.draw.rect(self.sprite, (100, 70, 40),
                           (trunk_x, trunk_y, 16, h - trunk_y))
            
            # Foliage (multiple circles for fullness)
            foliage_positions = [
                (w // 2, h // 3, w // 3),
                (w // 3, h // 2 - 5, w // 4),
                (2 * w // 3, h // 2 - 5, w // 4),
                (w // 2, h // 2 + 5, w // 3.5),
            ]
            
            for fx, fy, radius in foliage_positions:
                pygame.draw.circle(self.sprite, (60, 130, 60), 
                                 (int(fx), int(fy)), int(radius))
            
            # Highlights
            pygame.draw.circle(self.sprite, (90, 160, 90),
                             (w // 2 - 5, h // 3 - 5), w // 5)
        
        # Shadow at base
        shadow_surface = pygame.Surface((w, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 50), (w // 4, 0, w // 2, 10))
        self.sprite.blit(shadow_surface, (0, h - 8))
    
    def damage(self, amount: int = 100) -> bool:
        """
        Damage the tree.
        
        Args:
            amount: Damage amount
            
        Returns:
            True if tree was destroyed
        """
        if self.tree_state != "living":
            return False
        
        self.health -= amount
        
        if self.health <= 0:
            self.destroy_tree()
            return True
        
        return False
    
    def destroy_tree(self) -> None:
        """Destroy the tree (turn to stump)."""
        self._is_falling = True
        self._destruction_timer = 0.0
        
        # After animation, change state
        self.tree_state = "stump"
        self.health = 0
        
        # Reduce size for stump
        self.size = (TILE_SIZE, 20)
        self.solid = False  # Can walk over stump
        
        # Update causal state - this triggers propagation
        if self.causal_node:
            self.causal_node.state = EntityState.DESTROYED
        
        self._create_sprite()
        
        EventSystem.emit(GameEvent.ENTITY_STATE_CHANGED, {
            "entity_id": self.entity_id,
            "change": "destroyed",
            "previous_state": "living"
        })
    
    def on_interact(self, player) -> bool:
        """Handle player interaction."""
        if self.tree_state == "living":
            # Player can damage/destroy tree
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "You push against the ancient tree...",
                "type": "info"
            })
            return self.damage(100)
        
        elif self.tree_state == "stump":
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "Only a stump remains.",
                "type": "info"
            })
        
        elif self.tree_state == "dead":
            EventSystem.emit(GameEvent.UI_MESSAGE, {
                "message": "The dead tree crumbles at your touch.",
                "type": "info"
            })
            self.destroy_tree()
            return True
        
        return False
    
    def on_causal_change(self, new_state: EntityState, source_id: str = None) -> None:
        """Handle causal changes from other universes."""
        if new_state == EntityState.DESTROYED:
            if self.tree_state == "living":
                self.destroy_tree()
    
    def update(self, dt: float) -> None:
        """Update the tree."""
        # Gentle sway for living trees
        if self.tree_state == "living":
            self._sway = math.sin(pygame.time.get_ticks() / 1000) * 2
        
        # Falling animation
        if self._is_falling:
            self._destruction_timer += dt
            if self._destruction_timer > 1.0:
                self._is_falling = False
        
        super().update(dt)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Render the tree."""
        if not self.visible or not self.exists:
            return
        
        ox, oy = camera_offset
        render_x = int(self.x - ox + self._sway)
        render_y = int(self.y - oy)
        
        # Falling animation
        if self._is_falling:
            # Rotate and fade
            progress = min(1.0, self._destruction_timer)
            
            rotated = pygame.transform.rotate(self.sprite, progress * 90)
            alpha = int(255 * (1 - progress))
            rotated.set_alpha(alpha)
            
            # Offset for rotation
            offset_x = int(progress * self.width)
            offset_y = int(progress * self.height * 0.3)
            
            surface.blit(rotated, (render_x + offset_x, render_y + offset_y))
        else:
            surface.blit(self.sprite, (render_x, render_y))
    
    def serialize(self) -> dict:
        """Serialize state."""
        data = super().serialize()
        data.update({
            "tree_state": self.tree_state,
            "health": self.health
        })
        return data
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Tree':
        """Deserialize from save data."""
        tree = cls(
            position=tuple(data["position"]),
            tree_id=data["entity_id"],
            state=data.get("tree_state", "living")
        )
        tree.health = data.get("health", 100)
        tree.exists = data["exists"]
        return tree
