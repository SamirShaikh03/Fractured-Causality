"""
Causal Node - Represents an entity's causal data and dependencies.

Every entity that participates in the causal system has a CausalNode.
This tracks what the entity depends on and what depends on it.
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..entities.entity import Entity
    from .universe import UniverseType


class CausalOperator(Enum):
    """
    Types of causal relationships between entities.
    
    These define how a change in one entity affects another.
    """
    
    ECHO = "echo"
    """Same effect occurs in linked entity. Push button A, door opens in A AND B."""
    
    INVERSE = "inverse"
    """Opposite effect occurs. Light torch in A, torch extinguishes in B."""
    
    CONDITIONAL = "conditional"
    """Effect only occurs if condition is met in another universe."""
    
    EXCLUSIVE = "exclusive"
    """Taking action prevents the same in other universes. Pick up key in A, can't exist in B."""
    
    CASCADE = "cascade"
    """Effects chain through multiple universes in sequence."""
    
    EXISTENCE = "existence"
    """Target only exists if source exists. Tree exists -> Shade exists."""


class EntityState(Enum):
    """Possible states for an entity in the causal system."""
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
    """
    Represents a causal dependency between two nodes.
    
    The source node's state affects the target node according to the operator.
    """
    
    source_id: str
    """ID of the node this dependency comes from."""
    
    target_id: str
    """ID of the node this dependency affects."""
    
    operator: CausalOperator
    """How the source affects the target."""
    
    source_universe: Optional[str] = None
    """Universe the source is in (None = any)."""
    
    target_universe: Optional[str] = None
    """Universe the target is in (None = same as source)."""
    
    condition: Optional[Callable[['CausalNode'], bool]] = None
    """For CONDITIONAL operator: function that checks if condition is met."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional data for this dependency."""
    
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
    """
    Represents an effect this node has on others.
    
    This is the inverse view of CausalDependency - what this node causes.
    """
    
    target_id: str
    """ID of the affected node."""
    
    effect_type: str
    """Type of effect (e.g., 'destroy', 'activate', 'create')."""
    
    operator: CausalOperator
    """The causal operator used."""
    
    strength: float = 1.0
    """Strength of the effect (for gradual effects)."""


class CausalNode:
    """
    Represents an entity's position in the causal graph.
    
    Every entity that can be affected by or cause causal changes has a node.
    The node tracks:
    - What this entity depends on (dependencies)
    - What this entity affects (effects)
    - Current state
    - Universe bindings (different states in different universes)
    
    Example:
        A tree in Universe A has a CausalNode.
        A Shade enemy depends on that tree (EXISTENCE operator).
        If the tree is destroyed, the CausalGraph propagates this,
        and the Shade's CausalNode marks it as DESTROYED.
    """
    
    def __init__(self, node_id: str, entity: 'Entity' = None):
        """
        Initialize a causal node.
        
        Args:
            node_id: Unique identifier for this node
            entity: The entity this node represents
        """
        self.node_id = node_id
        self.entity = entity
        
        # Dependencies: what this node depends on
        self.dependencies: List[CausalDependency] = []
        
        # Effects: what changes when this node changes
        self.effects: List[CausalEffect] = []
        
        # State per universe
        self.universe_states: Dict[str, EntityState] = {}
        
        # Current primary state
        self._state: EntityState = EntityState.EXISTS
        
        # Whether this node currently exists in the causal graph
        self.exists: bool = True
        
        # Paradox contribution (how much paradox this node generates if invalid)
        self.paradox_weight: float = 1.0
        
        # Callback when state changes
        self.on_state_change: Optional[Callable[[EntityState, EntityState], None]] = None
    
    @property
    def state(self) -> EntityState:
        """Get the current state."""
        return self._state
    
    @state.setter
    def state(self, new_state: EntityState) -> None:
        """Set the state, triggering callbacks."""
        old_state = self._state
        self._state = new_state
        
        if old_state != new_state and self.on_state_change:
            self.on_state_change(old_state, new_state)
    
    def add_dependency(self, dependency: CausalDependency) -> None:
        """
        Add a dependency to this node.
        
        Args:
            dependency: The dependency to add
        """
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
    
    def remove_dependency(self, source_id: str) -> None:
        """
        Remove all dependencies from a source.
        
        Args:
            source_id: ID of the source node
        """
        self.dependencies = [d for d in self.dependencies if d.source_id != source_id]
    
    def add_effect(self, effect: CausalEffect) -> None:
        """
        Add an effect that this node causes.
        
        Args:
            effect: The effect to add
        """
        if effect not in self.effects:
            self.effects.append(effect)
    
    def get_dependencies_by_operator(self, operator: CausalOperator) -> List[CausalDependency]:
        """Get all dependencies with a specific operator."""
        return [d for d in self.dependencies if d.operator == operator]
    
    def has_dependency_on(self, source_id: str) -> bool:
        """Check if this node depends on another node."""
        return any(d.source_id == source_id for d in self.dependencies)
    
    def validate(self) -> bool:
        """
        Check if all dependencies are satisfied.
        
        Returns:
            True if valid, False if dependencies are broken
        """
        # This is called by CausalGraph with access to all nodes
        # Here we just check local state
        return self.exists and self.state != EntityState.DESTROYED
    
    def get_state_in_universe(self, universe_type: str) -> EntityState:
        """
        Get this node's state in a specific universe.
        
        Args:
            universe_type: The universe type string
            
        Returns:
            The state in that universe
        """
        return self.universe_states.get(universe_type, self._state)
    
    def set_state_in_universe(self, universe_type: str, state: EntityState) -> None:
        """
        Set this node's state in a specific universe.
        
        Args:
            universe_type: The universe type string
            state: The new state
        """
        self.universe_states[universe_type] = state
    
    def apply_operator_effect(self, source_state: EntityState, operator: CausalOperator) -> EntityState:
        """
        Determine new state based on source state and operator.
        
        Args:
            source_state: The state of the source node
            operator: The causal operator
            
        Returns:
            The resulting state for this node
        """
        if operator == CausalOperator.ECHO:
            return source_state
        
        elif operator == CausalOperator.INVERSE:
            # Invert the state
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
            # If source doesn't exist, neither does target
            if source_state == EntityState.DESTROYED:
                return EntityState.DESTROYED
            return self._state
        
        elif operator == CausalOperator.EXCLUSIVE:
            # If source took action, we can't exist
            if source_state in (EntityState.ACTIVE, EntityState.EXISTS):
                return EntityState.DESTROYED
            return self._state
        
        # Default: no change
        return self._state
    
    def serialize(self) -> dict:
        """Serialize this node for saving."""
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
        """Deserialize a node from save data."""
        node = cls(data["node_id"], entity)
        node._state = EntityState(data["state"])
        node.exists = data["exists"]
        node.universe_states = {
            k: EntityState(v) for k, v in data.get("universe_states", {}).items()
        }
        # Dependencies are reconnected by CausalGraph
        return node
    
    def __repr__(self) -> str:
        return f"CausalNode({self.node_id}, state={self._state.value}, exists={self.exists})"
