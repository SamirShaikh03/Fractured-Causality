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
       
    
    def __init__(self):
                                                
                          
        self.universes: Dict[UniverseType, Universe] = {}
        self._active_universe: Optional[Universe] = None
        
                      
        self.causal_graph = CausalGraph()
        self.paradox_manager = ParadoxManager()
        
                         
        self._switch_cooldown: float = 0.0
        self._is_switching: bool = False
        self._switch_progress: float = 0.0
        self._switch_from: Optional[UniverseType] = None
        self._switch_to: Optional[UniverseType] = None
        
                                           
        self.player: Optional['Player'] = None
        
                      
        self._transition_alpha: float = 0.0
        
                             
        EventSystem.subscribe(GameEvent.CAUSAL_CHANGE, self._on_causal_change)
        EventSystem.subscribe(GameEvent.PARADOX_CHANGED, self._on_paradox_changed)
    
    @property
    def active_universe(self) -> Optional[Universe]:
                                                
        return self._active_universe
    
    @property
    def active_type(self) -> Optional[UniverseType]:
                                                  
        return self._active_universe.universe_type if self._active_universe else None
    
    def create_universes(self, width: int = 20, height: int = 11) -> None:
           
        self.universes = {
            UniverseType.PRIME: Universe(UniverseType.PRIME, width, height),
            UniverseType.ECHO: Universe(UniverseType.ECHO, width, height),
            UniverseType.FRACTURE: Universe(UniverseType.FRACTURE, width, height),
        }
        
                                     
        self.set_active_universe(UniverseType.PRIME)
    
    def set_active_universe(self, universe_type: UniverseType) -> None:
           
                            
        if self._active_universe:
            self._active_universe.is_active = False
        
                      
        self._active_universe = self.universes.get(universe_type)
        if self._active_universe:
            self._active_universe.is_active = True
    
    def switch_universe(self, target_type: UniverseType) -> bool:
           
                        
        if self._switch_cooldown > 0:
            EventSystem.emit(GameEvent.UNIVERSE_SWITCH_FAILED, {
                "reason": "cooldown",
                "remaining": self._switch_cooldown
            })
            return False
        
                                    
        if self.active_type == target_type:
            return False
        
                                
        if target_type not in self.universes:
            EventSystem.emit(GameEvent.UNIVERSE_SWITCH_FAILED, {
                "reason": "invalid_universe"
            })
            return False
        
                      
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
                                     
        return self.universes.get(universe_type)
    
    def add_universe(self, universe: Universe) -> None:
           
        self.universes[universe.universe_type] = universe
        
        # Keep the active pointer in sync when a level replaces a universe instance.
        # Without this, updates can continue on a stale universe object.
        if self._active_universe is None or self._active_universe.universe_type == universe.universe_type:
            self.set_active_universe(universe.universe_type)
    
    def reset(self) -> None:
           
                             
        for universe in self.universes.values():
            universe.clear_entities()
        
                            
        self.causal_graph = CausalGraph()
        
                       
        self.paradox_manager.reset()
        
                               
        self._switch_cooldown = 0.0
        self._is_switching = False
        self._switch_progress = 0.0
        self._switch_from = None
        self._switch_to = None
        self._transition_alpha = 0.0
        
                                     
        self.set_active_universe(UniverseType.PRIME)
    
    def get_all_universes(self) -> List[Universe]:
                                
        return list(self.universes.values())
    
    def add_entity_to_universe(self, entity: 'Entity', universe_type: UniverseType) -> None:
           
        universe = self.universes.get(universe_type)
        if universe:
            universe.add_entity(entity)
            
                                                       
            if entity.causal_node:
                self.causal_graph.add_node(entity.causal_node)
    
    def add_entity_to_all_universes(self, entity: 'Entity') -> None:
           
        for universe in self.universes.values():
            universe.add_entity(entity)
    
    def remove_entity(self, entity: 'Entity') -> None:
           
        for universe in self.universes.values():
            universe.remove_entity(entity)
        
        if entity.causal_node:
            self.causal_graph.remove_node(entity.causal_node.node_id)
    
    def get_entity_across_universes(self, entity_id: str) -> Dict[UniverseType, 'Entity']:
           
        result = {}
        for utype, universe in self.universes.items():
            entity = universe.get_entity(entity_id)
            if entity:
                result[utype] = entity
        return result
    
    def update(self, dt: float) -> None:
           
                                
        if self._switch_cooldown > 0:
            self._switch_cooldown = max(0, self._switch_cooldown - dt)
        
                                     
        if self._is_switching:
            self._update_switch_transition(dt)
        
                        
        self.paradox_manager.update(dt)
        
                                
        if self._active_universe:
            self._active_universe.update(dt)
        
                                            
        self._apply_paradox_effects()
    
    def _update_switch_transition(self, dt: float) -> None:
                                                              
        self._switch_progress += dt / ANIMATION_UNIVERSE_SWITCH_DURATION
        
        if self._switch_progress >= 1.0:
                                 
            self._complete_switch()
        else:
                                                       
                                         
            self._transition_alpha = math.sin(self._switch_progress * math.pi)
    
    def _complete_switch(self) -> None:
                                         
        old_universe = self._active_universe
        self.set_active_universe(self._switch_to)
        
                                           
        if self.player:
            new_universe = self._active_universe
            old_pos = self.player.position
            new_pos = new_universe.find_valid_position(old_pos, self.player.size)
            
            if new_pos != old_pos:
                self.player.position = new_pos
        
                                
        self._is_switching = False
        self._switch_progress = 0.0
        self._transition_alpha = 0.0

        switched_to = self._switch_to
        switched_from = self._switch_from
        
        EventSystem.emit(GameEvent.UNIVERSE_SWITCHED, {
            "from": switched_from.value if switched_from else None,
            "to": switched_to.value if switched_to else None,
            "type": switched_to.value if switched_to else None,
            "universe": switched_to.name if switched_to else None,
            "color": self._active_universe.color if self._active_universe else (255, 255, 255)
        })
        
        self._switch_from = None
        self._switch_to = None
    
    def _apply_paradox_effects(self) -> None:
                                                     
        effects = self.paradox_manager.get_effects()
        
                                                       
        fracture = self.universes.get(UniverseType.FRACTURE)
        if fracture:
            fracture.stability = 1.0 - (effects["visual_distortion"] * 0.5)
        
                              
        prime = self.universes.get(UniverseType.PRIME)
        if prime:
            prime.stability = 1.0 - (effects["visual_distortion"] * 0.1)
    
    def _on_causal_change(self, event_data) -> None:
                                          
                                             
        pass                                      
    
    def _on_paradox_changed(self, event_data) -> None:
                                           
        level = event_data.get("level")
        new_level = event_data.get("new_level")
        amount = event_data.get("amount")

                                                                           
                                                                              
        if level is None and new_level is None and amount is not None and amount > 0:
            self.paradox_manager.add_paradox(
                amount,
                source_id=str(event_data.get("source", "causal_propagation")),
                source_type="causal_propagation"
            )
            return

        self._apply_paradox_effects()
    
    def render(self, surface: pygame.Surface) -> None:
           
        if not self._active_universe:
            return
        
                                              
        surface.fill(self._active_universe.bg_color)
        
                                
        self._active_universe.render(surface)
        
                                  
        if self._is_switching and self._transition_alpha > 0:
            self._render_transition(surface)
    
    def _render_transition(self, surface: pygame.Surface) -> None:
                                                           
                                   
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
                                        
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
           
        universe = self.universes.get(universe_type)
        if not universe:
            return
        
                                
        preview = pygame.Surface(rect.size)
        preview.fill(universe.bg_color)
        
                      
        scale_x = rect.width / SCREEN_WIDTH
        scale_y = rect.height / SCREEN_HEIGHT
        
                                
                                                   
        for entity in universe.entities:
            if not entity.exists:
                continue
            ex = int(entity.position[0] * scale_x)
            ey = int(entity.position[1] * scale_y)
            pygame.draw.circle(preview, universe.color, (ex, ey), 3)
        
        preview.set_alpha(alpha)
        surface.blit(preview, rect.topleft)
    
    def get_switch_cooldown_remaining(self) -> float:
                                                 
        return self._switch_cooldown
    
    def is_switch_available(self) -> bool:
                                                              
        return self._switch_cooldown <= 0 and not self._is_switching
    
    def clear(self) -> None:
                                                  
        self.causal_graph.clear()
        self.paradox_manager.reset()
        
        for universe in self.universes.values():
            universe.entities.clear()
            universe.entity_map.clear()
        
        self._active_universe = None
        self._switch_cooldown = 0
        self._is_switching = False
    
    def serialize(self) -> dict:
                                   
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
                                         
        self.paradox_manager.deserialize(data.get("paradox", {}))
        self.causal_graph.deserialize(data.get("causal_graph", {}), entity_map)
        
        active_type_str = data.get("active_universe")
        if active_type_str:
            self.set_active_universe(UniverseType(active_type_str))
