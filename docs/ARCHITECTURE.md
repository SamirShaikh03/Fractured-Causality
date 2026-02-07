# MULTIVERSE CAUSALITY
## Technical Architecture Document v1.0

---

# 1. ARCHITECTURE OVERVIEW

## 1.1 Design Principles

### Separation of Concerns
Each system is isolated with clear interfaces. The multiverse engine doesn't know about rendering. The causal graph doesn't know about input.

### Event-Driven Communication
Systems communicate via events, not direct calls. This allows loose coupling and easier debugging.

### Data-Oriented Entities
Entities are compositions of data components, not deep inheritance hierarchies.

### Immutable Universe States
When switching universes, we don't mutate — we swap active references. This prevents state corruption.

## 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           GAME LOOP                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │  Input  │─►│  Update │─►│ Physics │─►│ Causal  │─►│ Render  │  │
│  │ Handler │  │ Systems │  │  Check  │  │  Prop.  │  │  Pass   │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │  Universe   │  │  Universe   │  │  Universe   │
          │   Prime     │  │    Echo     │  │  Fracture   │
          │   (Blue)    │  │   (Green)   │  │    (Red)    │
          └─────────────┘  └─────────────┘  └─────────────┘
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                         ┌─────────────────┐
                         │  CAUSAL GRAPH   │
                         │  (Cross-Universe│
                         │   Dependencies) │
                         └─────────────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ PARADOX MANAGER │
                         └─────────────────┘
```

---

# 2. FOLDER STRUCTURE

```
Multiverse/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # Project documentation
│
├── docs/
│   ├── GDD.md                  # Game Design Document
│   └── ARCHITECTURE.md         # This document
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                   # Core engine systems
│   │   ├── __init__.py
│   │   ├── game.py             # Main game class, loop
│   │   ├── settings.py         # Constants, configuration
│   │   ├── events.py           # Event system
│   │   └── states.py           # Game state machine
│   │
│   ├── multiverse/             # Multiverse engine
│   │   ├── __init__.py
│   │   ├── multiverse_manager.py   # Coordinates all universes
│   │   ├── universe.py         # Single universe container
│   │   ├── causal_graph.py     # Causal dependency system
│   │   ├── causal_node.py      # Individual causal entity
│   │   └── paradox_manager.py  # Paradox tracking and effects
│   │
│   ├── entities/               # Game entities
│   │   ├── __init__.py
│   │   ├── entity.py           # Base entity class
│   │   ├── player.py           # Player entity
│   │   ├── enemies/
│   │   │   ├── __init__.py
│   │   │   ├── shade.py
│   │   │   ├── echo_walker.py
│   │   │   └── paradox_wraith.py
│   │   └── objects/
│   │       ├── __init__.py
│   │       ├── causal_stone.py
│   │       ├── echo_switch.py
│   │       ├── variant_door.py
│   │       ├── paradox_vessel.py
│   │       └── exit_portal.py
│   │
│   ├── levels/                 # Level definitions
│   │   ├── __init__.py
│   │   ├── level_loader.py     # Level loading system
│   │   ├── level_base.py       # Base level class
│   │   ├── level_01.py         # First Fracture
│   │   ├── level_02.py         # The Echo Stone
│   │   └── level_03.py         # Shade of the Tree
│   │
│   ├── systems/                # Game systems
│   │   ├── __init__.py
│   │   ├── input_handler.py    # Input processing
│   │   ├── physics.py          # Collision, movement
│   │   ├── camera.py           # Camera system
│   │   └── animation.py        # Animation controller
│   │
│   ├── ui/                     # User interface
│   │   ├── __init__.py
│   │   ├── hud.py              # Heads-up display
│   │   ├── menu.py             # Menu screens
│   │   ├── universe_indicator.py   # Current universe display
│   │   ├── paradox_meter.py    # Paradox visualization
│   │   └── causal_sight_overlay.py # Dependency visualization
│   │
│   ├── rendering/              # Rendering systems
│   │   ├── __init__.py
│   │   ├── renderer.py         # Main renderer
│   │   ├── effects.py          # Visual effects
│   │   ├── particles.py        # Particle system
│   │   └── shaders.py          # Screen effects (pygame surfaces)
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── vector.py           # Vector math
│       ├── timer.py            # Timing utilities
│       └── debug.py            # Debug tools
│
├── assets/
│   ├── sprites/
│   │   ├── player/
│   │   ├── enemies/
│   │   ├── objects/
│   │   └── tiles/
│   ├── fonts/
│   ├── sounds/
│   └── music/
│
└── saves/
    └── (save files generated at runtime)
```

---

# 3. CLASS RESPONSIBILITIES

## 3.1 Core Classes

### Game (core/game.py)
**Responsibility:** Main game loop, system coordination, state management.
```python
class Game:
    - run()                 # Main loop
    - handle_events()       # Process pygame events
    - update(dt)            # Update all systems
    - render()              # Render current frame
    - change_state(state)   # Transition game states
```

### Settings (core/settings.py)
**Responsibility:** Global constants, configuration.
```python
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64
UNIVERSE_COUNT = 3
PARADOX_MAX = 100
# etc.
```

### EventSystem (core/events.py)
**Responsibility:** Pub/sub event system for decoupled communication.
```python
class EventSystem:
    - subscribe(event_type, callback)
    - unsubscribe(event_type, callback)
    - emit(event_type, data)
```

### GameState (core/states.py)
**Responsibility:** State machine for game flow.
```python
class GameState(Enum):
    MENU, PLAYING, PAUSED, LEVEL_COMPLETE, GAME_OVER

class StateManager:
    - current_state
    - push_state(state)
    - pop_state()
    - update()
```

## 3.2 Multiverse Classes

### MultiverseManager (multiverse/multiverse_manager.py)
**Responsibility:** Coordinates all universes, handles switching.
```python
class MultiverseManager:
    - universes: Dict[UniverseType, Universe]
    - active_universe: Universe
    - switch_universe(target: UniverseType)
    - get_universe(type: UniverseType) -> Universe
    - update_all(dt)
    - propagate_causal_changes()
```

### Universe (multiverse/universe.py)
**Responsibility:** Container for a single universe's state.
```python
class Universe:
    - universe_type: UniverseType
    - entities: List[Entity]
    - tilemap: TileMap
    - add_entity(entity)
    - remove_entity(entity)
    - get_entities_at(position) -> List[Entity]
    - update(dt)
    - render(surface)
```

### CausalGraph (multiverse/causal_graph.py)
**Responsibility:** Manages causal dependencies across all universes.
```python
class CausalGraph:
    - nodes: Dict[str, CausalNode]
    - add_node(node: CausalNode)
    - remove_node(node_id: str)
    - add_dependency(from_id, to_id, operator: CausalOperator)
    - propagate_change(node_id, change_type)
    - get_dependents(node_id) -> List[CausalNode]
    - get_dependencies(node_id) -> List[CausalNode]
    - check_paradoxes() -> List[Paradox]
    - visualize() -> List[Line]  # For causal sight
```

### CausalNode (multiverse/causal_node.py)
**Responsibility:** Represents a single entity's causal data.
```python
class CausalNode:
    - node_id: str
    - entity: Entity
    - dependencies: List[CausalDependency]
    - effects: List[CausalEffect]
    - universe_bindings: Dict[UniverseType, EntityState]
    - exists: bool
    - validate() -> bool  # Check if dependencies satisfied
```

### ParadoxManager (multiverse/paradox_manager.py)
**Responsibility:** Tracks and applies paradox effects.
```python
class ParadoxManager:
    - current_level: float
    - max_level: float = 100
    - add_paradox(amount, source)
    - reduce_paradox(amount)
    - get_paradox_tier() -> ParadoxTier
    - apply_paradox_effects()
    - check_annihilation() -> bool
```

## 3.3 Entity Classes

### Entity (entities/entity.py)
**Responsibility:** Base class for all game objects.
```python
class Entity:
    - entity_id: str
    - position: Vector2
    - size: Vector2
    - sprite: pygame.Surface
    - causal_node: Optional[CausalNode]
    - persistence: EntityPersistence  # ANCHORED, VARIANT, EXCLUSIVE
    - update(dt)
    - render(surface, camera)
    - on_interact(player)
    - on_causal_change(change_type)
```

### Player (entities/player.py)
**Responsibility:** Player entity with special abilities.
```python
class Player(Entity):
    - current_universe: UniverseType
    - switch_cooldown: float
    - causal_sight_active: bool
    - move(direction)
    - switch_universe(target: UniverseType)
    - activate_causal_sight()
    - paradox_pulse()
    - interact()
```

### Shade (entities/enemies/shade.py)
**Responsibility:** Enemy bound to causal origin.
```python
class Shade(Entity):
    - origin_node_id: str
    - patrol_path: List[Vector2]
    - update(dt)
    - check_origin_exists() -> bool
    - on_origin_destroyed()
```

## 3.4 System Classes

### InputHandler (systems/input_handler.py)
**Responsibility:** Process and abstract input.
```python
class InputHandler:
    - key_states: Dict[int, bool]
    - key_just_pressed: Dict[int, bool]
    - update()
    - is_key_held(key) -> bool
    - is_key_pressed(key) -> bool
    - get_movement_vector() -> Vector2
```

### Physics (systems/physics.py)
**Responsibility:** Collision detection and resolution.
```python
class Physics:
    - check_collision(entity, tilemap) -> CollisionResult
    - resolve_collision(entity, collision)
    - raycast(start, end, universe) -> RaycastHit
```

---

# 4. DATA FLOW

## 4.1 Universe Switch Flow

```
Player presses switch key
         │
         ▼
InputHandler detects key
         │
         ▼
Player.switch_universe(target) called
         │
         ▼
MultiverseManager.switch_universe(target)
         │
         ├──► Store player position
         │
         ├──► Set active_universe = target
         │
         ├──► Check player position validity in new universe
         │         │
         │         ├──► Valid: Keep position
         │         │
         │         └──► Invalid: Push to nearest valid position
         │
         ├──► Emit UNIVERSE_SWITCHED event
         │
         └──► Trigger switch visual effect
```

## 4.2 Causal Change Flow

```
Entity state changes (e.g., tree destroyed)
         │
         ▼
Entity calls CausalGraph.propagate_change(node_id, DESTROYED)
         │
         ▼
CausalGraph finds all dependent nodes
         │
         ▼
For each dependent node:
    │
    ├──► Evaluate causal operator (ECHO, INVERSE, etc.)
    │
    ├──► Apply effect to dependent entity
    │         │
    │         ├──► Entity state updated
    │         │
    │         └──► Entity may be destroyed/created/modified
    │
    ├──► Check for paradoxes created
    │         │
    │         └──► If paradox: ParadoxManager.add_paradox()
    │
    └──► Recursively propagate to their dependents
         │
         ▼
ParadoxManager checks for critical/annihilation thresholds
```

## 4.3 Paradox Effect Flow

```
Paradox level changes
         │
         ▼
ParadoxManager.apply_paradox_effects()
         │
         ▼
Get current ParadoxTier
         │
         ├──► STABLE: No effects
         │
         ├──► UNSTABLE: Enable visual glitches, some tears
         │
         ├──► CRITICAL: Enable reality tears, empower enemies
         │
         └──► COLLAPSE: Extreme effects, near-annihilation
         │
         ▼
Emit PARADOX_LEVEL_CHANGED event
         │
         ▼
UI updates paradox meter
Renderer applies distortion effects
Entities check for paradox-dependent behavior
```

---

# 5. MULTIVERSE ENGINE DETAILS

## 5.1 Universe State Isolation

Each universe maintains completely separate:
- Entity list
- Tilemap
- Visual effects
- Local physics state

Shared across universes:
- Player position
- Causal graph (references entities in all universes)
- Paradox level
- Game time

## 5.2 Entity Synchronization

### Anchored Entities
```python
class AnchoredEntity(Entity):
    def update_position(self, new_pos):
        # Update in ALL universes
        for universe in multiverse.get_all_universes():
            variant = universe.get_entity(self.entity_id)
            if variant:
                variant.position = new_pos
```

### Variant Entities
```python
class VariantEntity(Entity):
    # Each universe has independent state
    # Linked via CausalGraph operators
    pass
```

### Exclusive Entities
```python
class ExclusiveEntity(Entity):
    home_universe: UniverseType
    
    def update(self, dt):
        if multiverse.active_universe.type != self.home_universe:
            # Don't update — doesn't exist here
            return
```

## 5.3 Causal Operator Implementation

```python
class CausalOperator(Enum):
    ECHO = "echo"           # Same effect
    INVERSE = "inverse"     # Opposite effect
    CONDITIONAL = "cond"    # Effect if condition met
    EXCLUSIVE = "excl"      # Prevents in other universes
    CASCADE = "cascade"     # Chain through universes

def apply_operator(operator, source_state, target_node):
    if operator == CausalOperator.ECHO:
        target_node.entity.set_state(source_state)
    
    elif operator == CausalOperator.INVERSE:
        target_node.entity.set_state(invert_state(source_state))
    
    elif operator == CausalOperator.CONDITIONAL:
        condition = target_node.get_condition()
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
