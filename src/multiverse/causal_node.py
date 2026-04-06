from enum import Enum
from typing import List, Dict, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from .universe import UniverseType


class CausalOperator(Enum):
    ECHO = "echo"
                                                                                    
    
    INVERSE = "inverse"
                                                                            
    
    CONDITIONAL = "conditional"
                                                                     
    
    EXCLUSIVE = "exclusive"
                                                                                                 
    
    CASCADE = "cascade"
                                                               
    
    EXISTENCE = "existence"
                                                                           


class EntityState(Enum):
                                                             
    EXISTS = "exists"
    DESTROYED = "destroyed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OPEN = "open"
    CLOSED = "closed"
    ON = "on"
    OFF = "off"


@dataclass
class CausalDependency:
    
    source_id: str
                                                    
    
    target_id: str
                                                 
    
    operator: CausalOperator
                                            
    
    source_universe: Optional[str] = None
                                                 
    
    target_universe: Optional[str] = None
                                                            
    
    condition: Optional[Callable[['CausalNode'], bool]] = None
                                                                             
    
    metadata: Dict[str, Any] = field(default_factory=dict)
                                              
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.operator))
    
    def __eq__(self, other):
        if not isinstance(other, CausalDependency):
            return False
        return (self.source_id == other.source_id and 
                self.target_id == other.target_id and 
                self.operator == other.operator)


@dataclass
class CausalEffect:
    
    target_id: str
                                  
    
    effect_type: str
                                                                 
    
    operator: CausalOperator
                                   
    
    strength: float = 1.0
                                                       


class CausalNode:
 
    def __init__(self, node_id: str, entity: 'Entity' = None):      
        self.node_id = node_id
        self.entity = entity
        
                                                 
        self.dependencies: List[CausalDependency] = []
        
                                                      
        self.effects: List[CausalEffect] = []
        
                            
        self.universe_states: Dict[str, EntityState] = {}
        
                               
        self._state: EntityState = EntityState.EXISTS
        
                                                                
        self.exists: bool = True
        
                                                                                
        self.paradox_weight: float = 1.0
        
                                     
        self.on_state_change: Optional[Callable[[EntityState, EntityState], None]] = None
    
    @property
    def state(self) -> EntityState:
                                    
        return self._state
    
    @state.setter
    def state(self, new_state: EntityState) -> None:
                                                  
        old_state = self._state
        self._state = new_state
        
        if old_state != new_state and self.on_state_change:
            self.on_state_change(old_state, new_state)
    
    def add_dependency(self, dependency: CausalDependency) -> None:
           
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
    
    def remove_dependency(self, source_id: str) -> None:
           
        self.dependencies = [d for d in self.dependencies if d.source_id != source_id]
    
    def add_effect(self, effect: CausalEffect) -> None:
           
        if effect not in self.effects:
            self.effects.append(effect)
    
    def get_dependencies_by_operator(self, operator: CausalOperator) -> List[CausalDependency]:
                                                            
        return [d for d in self.dependencies if d.operator == operator]
    
    def has_dependency_on(self, source_id: str) -> bool:
                                                         
        return any(d.source_id == source_id for d in self.dependencies)
    
    def validate(self) -> bool:
           
                                                                
                                        
        return self.exists and self.state != EntityState.DESTROYED
    
    def get_state_in_universe(self, universe_type: str) -> EntityState:
           
        return self.universe_states.get(universe_type, self._state)
    
    def set_state_in_universe(self, universe_type: str, state: EntityState) -> None:
           
        self.universe_states[universe_type] = state
    
    def apply_operator_effect(self, source_state: EntityState, operator: CausalOperator) -> EntityState:
           
        if operator == CausalOperator.ECHO:
            return source_state
        
        elif operator == CausalOperator.INVERSE:
                              
            inverses = {
                EntityState.EXISTS: EntityState.DESTROYED,
                EntityState.DESTROYED: EntityState.EXISTS,
                EntityState.ACTIVE: EntityState.INACTIVE,
                EntityState.INACTIVE: EntityState.ACTIVE,
                EntityState.OPEN: EntityState.CLOSED,
                EntityState.CLOSED: EntityState.OPEN,
                EntityState.ON: EntityState.OFF,
                EntityState.OFF: EntityState.ON,
            }
            return inverses.get(source_state, source_state)
        
        elif operator == CausalOperator.EXISTENCE:
                                                          
            if source_state == EntityState.DESTROYED:
                return EntityState.DESTROYED
            return self._state
        
        elif operator == CausalOperator.EXCLUSIVE:
                                                   
            if source_state in (EntityState.ACTIVE, EntityState.EXISTS):
                return EntityState.DESTROYED
            return self._state
        
                            
        return self._state
    
    def serialize(self) -> dict:
                                             
        return {
            "node_id": self.node_id,
            "state": self._state.value,
            "exists": self.exists,
            "universe_states": {k: v.value for k, v in self.universe_states.items()},
            "dependencies": [
                {
                    "source_id": d.source_id,
                    "target_id": d.target_id,
                    "operator": d.operator.value,
                    "metadata": d.metadata
                }
                for d in self.dependencies
            ]
        }
    
    @classmethod
    def deserialize(cls, data: dict, entity: 'Entity' = None) -> 'CausalNode':
                                                
        node = cls(data["node_id"], entity)
        node._state = EntityState(data["state"])
        node.exists = data["exists"]
        node.universe_states = {
            k: EntityState(v) for k, v in data.get("universe_states", {}).items()
        }
                                                     
        return node
    
    def __repr__(self) -> str:
        return f"CausalNode({self.node_id}, state={self._state.value}, exists={self.exists})"
