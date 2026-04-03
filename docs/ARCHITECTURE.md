# ARCHITECTURE

## How It's Built

The engine is split into clean layers:

**Input** → **Update** → **Physics Check** → **Causal Propagation** → **Render**

Each system is isolated. The multiverse engine doesn't care about graphics. The causal graph doesn't touch input. They communicate through events (pub/sub), keeping everything loosely coupled.

## The Multiverse Engine

Three universes (Prime/Blue, Echo/Green, Fracture/Red) exist simultaneously. Each has its own entities and tilemap. When you switch, you swap which one is "active" — nothing gets destroyed.

The **Causal Graph** sits at the center, tracking which entities depend on each other across universes. When you destroy something, the graph propagates that change to everything connected to it.

The **Paradox Manager** watches for causal contradictions — situations where reality breaks. Too much paradox = game over.

## The Entity System

All objects inherit from a base `Entity` class. They come in three flavors:

- **ANCHORED**: Exists in all universes at the same position (like the player)
- **VARIANT**: Independent state in each universe (keys, doors)
- **EXCLUSIVE**: Only exists in one home universe (some enemies)

## Why This Works

Everything is modular. Want to add a new entity type? Write a class that inherits from Entity. New game mechanic? Emit an event. New puzzle type? Add to the level loader. It's all designed to expand without breaking.

        if evaluate_condition(condition):
            target_node.entity.set_state(source_state)
    
    elif operator == CausalOperator.EXCLUSIVE:
        for other_universe in get_other_universes(source_universe):
            target = get_entity_in_universe(target_node.entity_id, other_universe)
            if target:
                target.prevent_existence()
    
    elif operator == CausalOperator.CASCADE:
        # Apply to next universe, then next, with increasing paradox
        pass
```

---

# 6. SAVE/LOAD STRATEGY

## 6.1 Save Data Structure

```python
@dataclass
class SaveData:
    version: str
    timestamp: float
    current_level: int
    
    # Player state
    player_position: Tuple[float, float]
    player_universe: str
    
    # Universe states
    universe_states: Dict[str, UniverseState]
    
    # Causal graph
    causal_graph_state: CausalGraphState
    
    # Paradox
    paradox_level: float
    
    # Collectibles
    collected_items: List[str]
    
    # Progress
    levels_completed: List[int]
```

## 6.2 Serialization

```python
class SaveManager:
    SAVE_DIR = "saves/"
    
    def save_game(self, slot: int, game_state: GameState) -> bool:
        data = self._serialize_state(game_state)
        path = f"{self.SAVE_DIR}slot_{slot}.json"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    
    def load_game(self, slot: int) -> Optional[SaveData]:
        path = f"{self.SAVE_DIR}slot_{slot}.json"
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            data = json.load(f)
        return self._deserialize_state(data)
```

## 6.3 Causal Graph Serialization

The causal graph requires special handling:

```python
def serialize_causal_graph(graph: CausalGraph) -> dict:
    return {
        "nodes": [
            {
                "id": node.node_id,
                "entity_id": node.entity.entity_id,
                "exists": node.exists,
                "state": node.current_state,
            }
            for node in graph.nodes.values()
        ],
        "edges": [
            {
                "from": dep.from_id,
                "to": dep.to_id,
                "operator": dep.operator.value,
                "metadata": dep.metadata
            }
            for dep in graph.get_all_dependencies()
        ]
    }
```

---

# 7. PERFORMANCE CONSIDERATIONS

## 7.1 Optimization Strategies

### Lazy Universe Updates
Only fully update the active universe each frame. Other universes:
- Skip animation updates
- Skip physics not affecting cross-universe entities
- Only process causal change propagation

### Causal Graph Pruning
- Only recalculate affected branches on change
- Cache dependency chains for common lookups
- Limit propagation depth per frame

### Rendering Optimization
- Only render active universe fully
- Other universes rendered to cached surfaces (update on change)
- Particle systems pooled and reused

## 7.2 Memory Management

### Entity Pooling
Pre-allocate entity pools per type to avoid runtime allocation.

### Surface Caching
Cache rendered universe states as surfaces; invalidate on state change.

---

# 8. DEBUG TOOLS

## 8.1 Debug Overlay

```python
class DebugOverlay:
    def render(self, surface):
        if not settings.DEBUG_MODE:
            return
        
        self._draw_fps(surface)
        self._draw_entity_bounds(surface)
        self._draw_causal_graph(surface)
        self._draw_paradox_sources(surface)
        self._draw_universe_info(surface)
```

## 8.2 Causal Graph Visualizer

Interactive visualization showing:
- All nodes across universes
- Dependency lines with operator colors
- Highlighted paradox sources
- Real-time state changes

## 8.3 Console Commands

```python
# Debug console commands
"tp x y"           # Teleport player
"switch prime"     # Force universe switch
"paradox 50"       # Set paradox level
"causal show"      # Toggle causal visualization
"entity spawn X"   # Spawn entity
"level load N"     # Load specific level
```

---

# 9. TESTING STRATEGY

## 9.1 Unit Tests

- CausalGraph propagation correctness
- Paradox calculation accuracy
- Entity state transitions
- Save/load integrity

## 9.2 Integration Tests

- Universe switching with various entity states
- Full causal chain propagation
- Level load/complete cycles

## 9.3 Playtest Scenarios

- "Can player soft-lock?" — Always a recovery path
- "Is paradox manageable?" — Never forced into annihilation
- "Are solutions discoverable?" — Within N attempts

---

*Architecture document complete. Ready for implementation.*
