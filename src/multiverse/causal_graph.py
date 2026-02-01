"""
Causal Graph - The heart of the multiverse causality system.

This module manages all causal dependencies across all universes.
When an entity changes state, the graph propagates those changes
to all dependent entities according to their causal operators.
"""

from typing import Dict, List, Set, Optional, Tuple, TYPE_CHECKING
from collections import deque
import logging

from .causal_node import CausalNode, CausalDependency, CausalOperator, EntityState
from ..core.events import EventSystem, GameEvent

if TYPE_CHECKING:
    from ..entities.entity import Entity

logger = logging.getLogger(__name__)


class CausalChange:
    """Represents a change that occurred in the causal graph."""
    
    def __init__(self, node_id: str, old_state: EntityState, new_state: EntityState,
                 source_id: Optional[str] = None, operator: Optional[CausalOperator] = None):
        self.node_id = node_id
        self.old_state = old_state
        self.new_state = new_state
        self.source_id = source_id
        self.operator = operator
        self.paradox_generated = 0.0


class CausalGraph:
    """
    Manages causal dependencies across all universes.
    
    The causal graph is a directed graph where:
    - Nodes represent entities
    - Edges represent causal dependencies with operators
    
    When an entity changes, the graph:
    1. Finds all dependents
    2. Applies the appropriate operator to each
    3. Propagates recursively
    4. Checks for paradoxes
    5. Reports total paradox generated
    
    Example:
        graph = CausalGraph()
        
        # Add nodes
        tree_node = CausalNode("tree_01", tree_entity)
        shade_node = CausalNode("shade_01", shade_entity)
        graph.add_node(tree_node)
        graph.add_node(shade_node)
        
        # Create dependency: shade depends on tree
        graph.add_dependency("tree_01", "shade_01", CausalOperator.EXISTENCE)
        
        # When tree is destroyed:
        changes = graph.propagate_change("tree_01", EntityState.DESTROYED)
        # shade_01 is now also DESTROYED
    """
    
    def __init__(self):
        """Initialize the causal graph."""
        # All nodes in the graph
        self.nodes: Dict[str, CausalNode] = {}
        
        # Adjacency lists for efficient traversal
        self._dependents: Dict[str, Set[str]] = {}  # node_id -> set of dependent node_ids
        self._dependencies: Dict[str, Set[str]] = {}  # node_id -> set of dependency node_ids
        
        # For visualization
        self._last_propagation_path: List[Tuple[str, str]] = []
        
        # Paradox tracking
        self._orphaned_nodes: Set[str] = set()
        
    def add_node(self, node: CausalNode) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: The CausalNode to add
        """
        self.nodes[node.node_id] = node
        self._dependents[node.node_id] = set()
        self._dependencies[node.node_id] = set()
        
        logger.debug(f"Added causal node: {node.node_id}")
    
    def remove_node(self, node_id: str) -> Optional[CausalNode]:
        """
        Remove a node from the graph.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            The removed node, or None if not found
        """
        if node_id not in self.nodes:
            return None
        
        node = self.nodes[node_id]
        
        # Remove all edges involving this node
        for dep_id in list(self._dependencies.get(node_id, set())):
            if dep_id in self._dependents:
                self._dependents[dep_id].discard(node_id)
        
        for target_id in list(self._dependents.get(node_id, set())):
            if target_id in self._dependencies:
                self._dependencies[target_id].discard(node_id)
        
        # Remove from graph
        del self.nodes[node_id]
        self._dependents.pop(node_id, None)
        self._dependencies.pop(node_id, None)
        
        logger.debug(f"Removed causal node: {node_id}")
        return node
    
    def add_dependency(self, source_id: str, target_id: str, 
                       operator: CausalOperator,
                       source_universe: str = None,
                       target_universe: str = None,
                       metadata: dict = None) -> bool:
        """
        Add a causal dependency between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node (depends on source)
            operator: How source affects target
            source_universe: Universe the source is in
            target_universe: Universe the target is in
            metadata: Additional dependency data
            
        Returns:
            True if added, False if nodes don't exist
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot add dependency: node not found ({source_id} -> {target_id})")
            return False
        
        # Create dependency object
        dependency = CausalDependency(
            source_id=source_id,
            target_id=target_id,
            operator=operator,
            source_universe=source_universe,
            target_universe=target_universe,
            metadata=metadata or {}
        )
        
        # Add to target node
        self.nodes[target_id].add_dependency(dependency)
        
        # Update adjacency lists
        self._dependents[source_id].add(target_id)
        self._dependencies[target_id].add(source_id)
        
        logger.debug(f"Added dependency: {source_id} --[{operator.value}]--> {target_id}")
        
        EventSystem.emit(GameEvent.CAUSAL_LINK_CREATED, {
            "source_id": source_id,
            "target_id": target_id,
            "operator": operator
        })
        
        return True
    
    def remove_dependency(self, source_id: str, target_id: str) -> bool:
        """
        Remove a dependency between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            
        Returns:
            True if removed, False if didn't exist
        """
        if target_id in self.nodes:
            self.nodes[target_id].remove_dependency(source_id)
        
        if source_id in self._dependents:
            self._dependents[source_id].discard(target_id)
        if target_id in self._dependencies:
            self._dependencies[target_id].discard(source_id)
        
        EventSystem.emit(GameEvent.CAUSAL_LINK_BROKEN, {
            "source_id": source_id,
            "target_id": target_id
        })
        
        return True
    
    def get_node(self, node_id: str) -> Optional[CausalNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_dependents(self, node_id: str) -> List[CausalNode]:
        """
        Get all nodes that depend on a node.
        
        Args:
            node_id: ID of the source node
            
        Returns:
            List of dependent nodes
        """
        dependent_ids = self._dependents.get(node_id, set())
        return [self.nodes[did] for did in dependent_ids if did in self.nodes]
    
    def get_dependencies(self, node_id: str) -> List[CausalNode]:
        """
        Get all nodes that a node depends on.
        
        Args:
            node_id: ID of the target node
            
        Returns:
            List of dependency nodes
        """
        dep_ids = self._dependencies.get(node_id, set())
        return [self.nodes[did] for did in dep_ids if did in self.nodes]
    
    def propagate_change(self, node_id: str, new_state: EntityState,
                         universe_type: str = None) -> List[CausalChange]:
        """
        Propagate a state change through the causal graph.
        
        This is the core of the causality system. When a node changes:
        1. Find all nodes that depend on it
        2. Apply the appropriate causal operator
        3. If they change, propagate to their dependents
        4. Track all changes for paradox calculation
        
        Args:
            node_id: ID of the changed node
            new_state: The new state
            universe_type: The universe this change occurred in
            
        Returns:
            List of all changes that occurred
        """
        if node_id not in self.nodes:
            return []
        
        changes: List[CausalChange] = []
        visited: Set[str] = set()
        queue: deque = deque()
        
        self._last_propagation_path = []
        
        # Start with the initial node
        source_node = self.nodes[node_id]
        old_state = source_node.state
        
        if old_state == new_state:
            return []  # No change
        
        # Apply initial change
        source_node.state = new_state
        if universe_type:
            source_node.set_state_in_universe(universe_type, new_state)
        
        initial_change = CausalChange(node_id, old_state, new_state)
        changes.append(initial_change)
        
        # Queue dependents for processing
        for dep_node in self.get_dependents(node_id):
            queue.append((node_id, dep_node.node_id, new_state))
        
        EventSystem.emit(GameEvent.CAUSAL_PROPAGATION_START, {
            "source_id": node_id,
            "new_state": new_state.value
        })
        
        # BFS propagation
        while queue:
            source_id, target_id, source_state = queue.popleft()
            
            if target_id in visited:
                continue
            visited.add(target_id)
            
            target_node = self.nodes.get(target_id)
            if not target_node:
                continue
            
            # Find the dependency that links source to target
            dependency = self._find_dependency(target_node, source_id)
            if not dependency:
                continue
            
            # Check universe constraints
            if dependency.source_universe and universe_type:
                if dependency.source_universe != universe_type:
                    continue
            
            # Apply operator
            old_target_state = target_node.state
            new_target_state = target_node.apply_operator_effect(source_state, dependency.operator)
            
            # Check conditional operators
            if dependency.operator == CausalOperator.CONDITIONAL:
                if dependency.condition and not dependency.condition(target_node):
                    continue
            
            if old_target_state != new_target_state:
                # State changed, record it
                target_node.state = new_target_state
                if dependency.target_universe:
                    target_node.set_state_in_universe(dependency.target_universe, new_target_state)
                
                change = CausalChange(
                    target_id, old_target_state, new_target_state,
                    source_id=source_id, operator=dependency.operator
                )
                changes.append(change)
                
                self._last_propagation_path.append((source_id, target_id))
                
                # Notify the entity
                if target_node.entity:
                    target_node.entity.on_causal_change(new_target_state, source_id)
                
                # Continue propagation to this node's dependents
                for next_dep in self.get_dependents(target_id):
                    if next_dep.node_id not in visited:
                        queue.append((target_id, next_dep.node_id, new_target_state))
        
        # Check for paradoxes created
        paradox_amount = self._check_paradoxes(changes)
        
        EventSystem.emit(GameEvent.CAUSAL_PROPAGATION_COMPLETE, {
            "changes": len(changes),
            "paradox_generated": paradox_amount
        })
        
        return changes
    
    def _find_dependency(self, node: CausalNode, source_id: str) -> Optional[CausalDependency]:
        """Find the dependency linking a node to a source."""
        for dep in node.dependencies:
            if dep.source_id == source_id:
                return dep
        return None
    
    def _check_paradoxes(self, changes: List[CausalChange]) -> float:
        """
        Check for paradoxes created by changes.
        
        A paradox occurs when:
        - An entity is destroyed but its effects still exist
        - A circular dependency is broken
        - An entity's dependency no longer exists
        
        Returns:
            Amount of paradox generated
        """
        paradox = 0.0
        
        for change in changes:
            if change.new_state == EntityState.DESTROYED:
                node = self.nodes.get(change.node_id)
                if node:
                    # Check if any dependents still exist
                    for dependent in self.get_dependents(change.node_id):
                        if dependent.exists and dependent.state != EntityState.DESTROYED:
                            # Orphaned dependent = paradox
                            paradox += node.paradox_weight
                            self._orphaned_nodes.add(dependent.node_id)
                            change.paradox_generated += node.paradox_weight
        
        if paradox > 0:
            EventSystem.emit(GameEvent.PARADOX_CHANGED, {
                "amount": paradox,
                "source": "causal_propagation"
            })
        
        return paradox
    
    def validate_graph(self) -> Tuple[bool, List[str]]:
        """
        Validate the entire causal graph.
        
        Checks:
        - All dependencies reference existing nodes
        - No circular dependencies without proper handling
        - No orphaned nodes
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep.source_id not in self.nodes:
                    issues.append(f"Node {node_id} depends on non-existent node {dep.source_id}")
        
        # Check for orphans
        for orphan_id in self._orphaned_nodes:
            if orphan_id in self.nodes and self.nodes[orphan_id].exists:
                issues.append(f"Node {orphan_id} is orphaned (dependency destroyed)")
        
        return len(issues) == 0, issues
    
    def get_visualization_data(self) -> dict:
        """
        Get data for visualizing the causal graph.
        
        Returns:
            Dictionary with nodes and edges for rendering
        """
        nodes_data = []
        edges_data = []
        
        for node_id, node in self.nodes.items():
            if not node.exists:
                continue
                
            pos = (0, 0)
            if node.entity:
                pos = node.entity.position
            
            nodes_data.append({
                "id": node_id,
                "position": pos,
                "state": node.state.value,
                "is_orphan": node_id in self._orphaned_nodes
            })
            
            for dep in node.dependencies:
                if dep.source_id in self.nodes:
                    edges_data.append({
                        "from": dep.source_id,
                        "to": node_id,
                        "operator": dep.operator.value
                    })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "last_propagation": self._last_propagation_path
        }
    
    def get_all_dependencies(self) -> List[CausalDependency]:
        """Get all dependencies in the graph."""
        all_deps = []
        for node in self.nodes.values():
            all_deps.extend(node.dependencies)
        return all_deps
    
    def clear(self) -> None:
        """Clear the entire graph."""
        self.nodes.clear()
        self._dependents.clear()
        self._dependencies.clear()
        self._orphaned_nodes.clear()
        self._last_propagation_path.clear()
    
    def serialize(self) -> dict:
        """Serialize the graph for saving."""
        return {
            "nodes": {nid: node.serialize() for nid, node in self.nodes.items()},
            "orphaned": list(self._orphaned_nodes)
        }
    
    def deserialize(self, data: dict, entity_map: Dict[str, 'Entity']) -> None:
        """
        Deserialize the graph from save data.
        
        Args:
            data: Serialized graph data
            entity_map: Map of entity IDs to entities for reconnection
        """
        self.clear()
        
        # Restore nodes
        for node_id, node_data in data.get("nodes", {}).items():
            entity = entity_map.get(node_id)
            node = CausalNode.deserialize(node_data, entity)
            self.add_node(node)
            
            if entity:
                entity.causal_node = node
        
        # Restore dependencies (edges)
        for node_id, node_data in data.get("nodes", {}).items():
            for dep_data in node_data.get("dependencies", []):
                self.add_dependency(
                    dep_data["source_id"],
                    dep_data["target_id"],
                    CausalOperator(dep_data["operator"]),
                    metadata=dep_data.get("metadata", {})
                )
        
        # Restore orphaned set
        self._orphaned_nodes = set(data.get("orphaned", []))
