# MULTIVERSE CAUSALITY
## Game Design Document v1.0

---

# 1. VISION & PHILOSOPHY

## 1.1 The Core Fantasy

**You are not playing in one world — you ARE the connection between worlds.**

The player embodies The Archivist, a being who exists outside normal causality. You perceive all timelines simultaneously. Your curse: every action you take ripples across realities. Your gift: you can use this to solve impossible puzzles.

## 1.2 Design Philosophy

### "Consequences Are Spatial, Not Temporal"

Most games with "choices" show consequences over time (ending A vs B). We reject this.

In Multiverse Causality, consequences are **immediate and parallel**. Kill an enemy in Universe A, and their alternate self in Universe B may vanish, gain power, or become something else entirely. The player sees cause and effect happening simultaneously across space.

### "The Player Is The Paradox"

The player should feel like they are *breaking* the game's reality. Not through glitches, but through the logical implications of their own actions. The systems should feel like they're struggling to contain you.

### "Puzzles Emerge From Systems"

We do not design puzzles. We design **causal rules**. Puzzles emerge from the player understanding and exploiting those rules. This creates genuine "aha" moments that cannot be spoiled.

## 1.3 Unique Selling Points

1. **Live Causal Simulation** — Not branching narratives, but a real-time dependency graph
2. **Paradox as Resource** — Breaking causality is dangerous but sometimes necessary
3. **Multi-Universe Puzzle Space** — Solutions require thinking across 3+ realities simultaneously
4. **Emergent Puzzle Design** — Systems create puzzles, not scripted solutions
5. **Philosophical Depth** — Explores identity, determinism, and the nature of existence

---

# 2. CORE LOOP

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   OBSERVE ──► HYPOTHESIZE ──► ACT ──► WITNESS ──► ADAPT     │
│       │                                              │      │
│       └──────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Loop Breakdown

1. **OBSERVE**: Player examines current universe and switches to view others
2. **HYPOTHESIZE**: Player forms theory about causal connections
3. **ACT**: Player performs action (move object, defeat enemy, activate mechanism)
4. **WITNESS**: Player immediately sees effects ripple across all universes
5. **ADAPT**: Player refines understanding and plans next action

### 2.2 Session Flow

```
Level Entry
    │
    ▼
Explore all universes (establish baseline)
    │
    ▼
Identify blocked paths / locked mechanisms
    │
    ▼
Discover causal links through experimentation
    │
    ▼
Form multi-universe solution
    │
    ▼
Execute actions in correct sequence across universes
    │
    ▼
Manage paradox if causality breaks
    │
    ▼
Reach exit portal (exists in ALL universes simultaneously)
```

---

# 3. MULTIVERSE RULES

## 3.1 Universe Types

### Prime Universe (Blue)
- The "original" timeline
- Most stable
- Actions here have the strongest causal echoes
- Paradox generated here is most dangerous

### Echo Universe (Green)  
- A timeline where one major historical event differed
- Objects may exist in different states
- Some entities only exist here
- Causally dependent on Prime

### Fracture Universe (Red)
- A timeline that "shouldn't exist"
- Reality is unstable here
- Objects may flicker or behave strangely
- High paradox generation
- Contains solutions impossible in stable universes

## 3.2 Switching Mechanics

- Player can switch universes at any time (cooldown: 0.5s)
- Player position is SHARED across universes
- If player would spawn inside solid matter, they're pushed to nearest valid space
- Switching creates a brief "between" moment where all universes are visible

## 3.3 Object Persistence

Objects exist in one of three states:

| State | Description | Visual |
|-------|-------------|--------|
| **Anchored** | Exists in all universes identically | Solid, bright |
| **Variant** | Different form in each universe | Slight shimmer |
| **Exclusive** | Only exists in one universe | Strong glow, unstable edges |

---

# 4. CAUSALITY MECHANICS

## 4.1 The Causal Graph

Every entity in the game has a **Causal Node** with:
- `dependencies`: What must exist/be true for this to exist
- `effects`: What this entity's existence causes
- `universe_bindings`: Which universes this affects

### Example Causal Chain:
```
Universe A: Ancient Tree exists
    │
    ├──► Universe B: Tree was cut down, stump exists
    │         │
    │         └──► Universe B: Wooden bridge exists (made from tree)
    │
    └──► Universe C: Tree died from disease
              │
              └──► Universe C: Hollow log exists (shelter for creature)
```

**If player destroys tree in Universe A:**
- Universe B: Bridge vanishes (never built)
- Universe C: Creature dies (no shelter)
- Paradox generated: Medium (logical but disruptive)

## 4.2 Causal Operators

### ECHO
Action in one universe creates identical effect in linked universe.
> Push a button in A, door opens in A AND B.

### INVERSE
Action in one universe creates opposite effect in linked universe.
> Light a torch in A, torch extinguishes in B.

### CONDITIONAL
Effect only occurs if specific state exists in another universe.
> Door in A only opens if its counterpart in B is closed.

### EXCLUSIVE
Action prevents the possibility in all other universes.
> Picking up a key in A means it can never exist in B or C.

### CASCADE
Effects chain through multiple universes in sequence.
> Killing enemy in A weakens their B version, which dies, causing their C version to never be born.

## 4.3 Causal Locks

Some doors/paths require specific causal states:

- **Harmony Lock**: Object must be in same state in 2+ universes
- **Dissonance Lock**: Object must be in different states across universes
- **Paradox Lock**: Can only open when paradox level is elevated
- **Echo Lock**: Requires action to have echoed through all universes

---

# 5. PARADOX SYSTEM

## 5.1 What Is Paradox?

Paradox is a resource, a threat, and a puzzle element.

**Paradox accumulates when:**
- An entity is destroyed but its effects still exist
- The player exists in a space they couldn't logically reach
- Causal chains become circular
- An entity's dependency no longer exists

## 5.2 Paradox Levels

| Level | Range | Effects |
|-------|-------|---------|
| **Stable** | 0-25% | Normal gameplay |
| **Unstable** | 26-50% | Visual glitches, some paths become accessible |
| **Critical** | 51-75% | Reality tears, new traversal options, enemies empowered |
| **Collapse** | 76-99% | Extreme distortion, some solutions only possible here |
| **Annihilation** | 100% | Game over — reality reset |

## 5.3 Paradox as Tool

Some puzzles REQUIRE paradox:
- Paradox tears can be walked through as shortcuts
- High paradox can "unanchor" stuck objects
- Paradox entities only spawn at certain levels
- Some locks require paradox to open

## 5.4 Paradox Reduction

- **Causal Mending**: Restore a broken dependency
- **Paradox Crystals**: Collectibles that absorb paradox
- **Harmony Actions**: Actions that sync universes reduce paradox
- **Time**: Paradox slowly decays if player takes no cross-universe actions

---

# 6. ENTITY DESIGN

## 6.1 The Player — The Archivist

**Abilities:**
- Universe Switch (instant, 0.5s cooldown)
- Interact (context-sensitive)
- Causal Sight (hold to see dependency lines)
- Paradox Pulse (spend paradox to phase through matter briefly)

**No combat** — The Archivist cannot kill directly. They can only manipulate causality.

## 6.2 Enemies — The Tethered

Beings bound to specific causal chains. They exist because of something.

### Shade
- Exists only if its "origin event" occurred
- Patrols, blocks paths
- Cannot be killed directly
- Defeated by preventing its origin across universes

### Echo Walker
- Exists in multiple universes simultaneously
- Copies your movements with delay in other universes
- Can block your own alternate paths
- Defeated by creating paradox in its existence

### The Anchor
- Massive, immobile
- Holds reality together in its area
- Cannot be defeated — must be circumvented
- If destroyed, paradox spikes dangerously

### Paradox Wraith
- Only exists when paradox > 50%
- Hunts the player
- Touching it removes player from current universe temporarily
- Defeated by reducing paradox

## 6.3 Interactive Objects

### Causal Stones
- Can be pushed/pulled
- Anchored across universes (move one, all move)

### Echo Switches
- Activation echoes to linked universes

### Variant Doors
- Different states in different universes
- State in one affects state in another (based on operator)

### Paradox Vessels
- Containers that store/release paradox
- Can be used to strategically increase/decrease levels

### Memory Crystals
- Collectibles revealing story
- Show what the world was like before the fracture

---

# 7. LEVEL DESIGN PHILOSOPHY

## 7.1 Principles

### "See Before You Solve"
Every level starts with exploration. Player should switch through all universes before taking any major action. Understanding comes from observation.

### "The First Answer Is Wrong"
Design levels where the obvious solution increases paradox dangerously. Optimal solutions require deeper understanding of causal rules.

### "Undo Is Possible But Costly"
Players can often reverse actions, but:
- Reversing may cause different causal effects than the original action
- Some reverses require visiting multiple universes
- Time-based reversal increases paradox

### "One Puzzle, Three Layers"
Every puzzle should have:
1. A surface layer (what you see)
2. A causal layer (dependencies)
3. A paradox layer (what happens if you break rules)

## 7.2 Level Progression

### Act 1: Foundation (Levels 1-3)
- Introduce universe switching
- Simple echo mechanics
- Low paradox tolerance
- Hand-holding causal visualization

### Act 2: Complexity (Levels 4-6)
- All causal operators in play
- Enemies introduced
- Paradox as required tool
- Multi-step solutions

### Act 3: Mastery (Levels 7-9)
- All systems interact
- Minimal guidance
- Emergent solutions possible
- High paradox risk/reward

### Finale: Convergence (Level 10)
- All universes collapsing
- Must stabilize reality
- Uses every learned mechanic
- Multiple valid endings based on final paradox level

---

# 8. LEVEL DESIGNS (FIRST THREE)

## Level 1: "First Fracture"

**Universe A (Prime):** A simple room with a door. Door is locked. Key is behind a pit too wide to jump.

**Universe B (Echo):** Same room, but a bridge exists over the pit. However, the door doesn't exist — it's a solid wall.

**Solution:**
1. Switch to B, cross bridge, stand where door would be
2. Switch to A, now on other side of pit
3. Get key
4. Unlock door

**Teaching:** Position is shared; universe switching enables traversal.

**Hidden depth:** If player picks up key in A first, they can check B — key is rusted/broken there (causal echo teaching).

---

## Level 2: "The Echo Stone"

**Setup:** Three rooms connected. A heavy stone blocks path in A. Same stone exists in B and C.

**Mechanic:** Stone is ANCHORED — moving it in any universe moves it in ALL.

**Puzzle:** Need to position stone so it:
- Opens path in A
- Doesn't block the only exit in B  
- Presses switch in C

**Solution:** Find the ONE position that satisfies all three. Requires checking all universes.

**Teaching:** Anchored objects, multi-universe spatial reasoning.

---

## Level 3: "Shade of the Tree"

**Setup:** A Shade blocks the only exit. It cannot be killed directly.

**Investigation:** Using Causal Sight reveals the Shade is connected to an old tree in Universe B.

**Universe States:**
- A: Dead garden, Shade present
- B: Living garden with tree, no Shade
- C: Overgrown garden, tree has become massive

**Solution:**
1. In B, tree must be killed (push boulder onto it)
2. Tree's death echoes: In A, garden was never alive, but Shade's origin (tree's shadow) never existed
3. Shade vanishes

**Paradox risk:** If done incorrectly, can orphan the Shade's effects (it blocked something that depended on being blocked).

**Teaching:** Enemies are causal entities, investigation before action, consequence preview.

---

# 9. EMOTIONAL ARC

## 9.1 Act Structure

### Act 1: Wonder
Player discovers they can see and manipulate the multiverse. Tone is mysterious, curious. "What is this power?"

### Act 2: Power  
Player masters causal manipulation. Tone shifts to empowerment. "I understand the rules now."

### Act 3: Doubt
Player realizes their actions are accumulating damage. Paradox is rising. Universes are destabilizing. "Am I fixing this or breaking it?"

### Finale: Choice
Player must decide: stabilize reality (limiting future potential) or embrace paradox (chaos, but freedom). No "right" answer.

## 9.2 Micro-Emotions Per Level

Each level should cycle through:
1. **Confusion** — "What's the goal here?"
2. **Curiosity** — "I wonder if..."  
3. **Experimentation** — "Let me try..."
4. **Consequence** — "Oh, that changed THAT?"
5. **Understanding** — "I see the pattern!"
6. **Satisfaction** — "I solved it my way."

---

# 10. WHAT MAKES THIS UNLIKE ANYTHING ELSE

## 10.1 Comparison to Existing Games

| Game | Similarity | Key Difference |
|------|------------|----------------|
| **Braid** | Time manipulation puzzles | We manipulate SPACE between realities, not time |
| **The Witness** | Emergent puzzle understanding | We have causality systems, not pattern recognition |
| **Outer Wilds** | Multi-layered investigation | We change reality, not just observe it |
| **Antichamber** | Non-Euclidean spaces | Our spaces are Euclidean but causally linked |
| **Superliminal** | Perspective puzzles | We manipulate existence, not perspective |
| **Quantum Break** | Parallel timelines | We switch freely; our timelines are simultaneous |

## 10.2 The Core Innovation

**Causal Graph as Gameplay**

No game has made a real-time, player-visible, manipulable causal dependency graph the core mechanic. Games have had consequences. Games have had parallel worlds. No game has made **the relationship between cause and effect** the thing you directly interact with.

---

# 11. RISK ASSESSMENT

## 11.1 Design Risks

| Risk | Mitigation |
|------|------------|
| Too confusing | Strong visual language, gradual introduction |
| Paradox frustrating | Multiple recovery options, never truly stuck |
| Solutions too obscure | Causal Sight makes dependencies visible |
| Not fun to experiment | No death, quick universe switching, reversible actions |

## 11.2 Technical Risks

| Risk | Mitigation |
|------|------------|
| Causal graph performance | Limit entities per level, efficient propagation |
| State management complex | Clear universe isolation, event-driven updates |
| Debugging difficult | Comprehensive logging, visualization tools |

---

# 12. SUCCESS METRICS

For this game to succeed as a portfolio piece and potential indie release:

1. **Clarity**: First-time players understand core mechanic within 3 minutes
2. **Depth**: Players are still discovering causal interactions in Act 3
3. **Originality**: No one says "this is like [other game]"
4. **Satisfaction**: Puzzle solutions feel earned, not guessed
5. **Replayability**: Players want to find alternate solutions
6. **Discussion**: Players want to share discoveries

---

# APPENDIX A: GLOSSARY

- **Anchored**: Object exists identically in all universes
- **Causal Node**: Data structure tracking an entity's dependencies and effects
- **Causal Sight**: Player ability to visualize dependency lines
- **Echo**: Effect that mirrors across universes
- **Exclusive**: Object exists only in one universe
- **Paradox**: Accumulated causal instability
- **Prime Universe**: The "main" timeline
- **Variant**: Object with different forms across universes

---

# APPENDIX B: FUTURE EXPANSION IDEAS

- **Level Editor**: Let players create causal puzzles
- **Narrative Mode**: Deeper story about the Archivist's origin
- **Endless Mode**: Procedurally generated causal challenges
- **Multiplayer**: Two players in different universes affecting each other
- **Mobile Port**: Touch-based universe switching

---

*Document authored by the Multiverse Causality design.*
*This is a living document — updated as development reveals new insights.*
