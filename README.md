# MULTIVERSE CAUSALITY

A puzzle-adventure game where every action creates ripples across parallel universes.

## Concept

You are The Archivist, a being who exists outside normal causality. You can switch between parallel universes at will, but every action you take echoes across realities. Killing an enemy in one universe might erase their alternate self in another—or make them stronger. Objects are causally linked. Reality is fragile.

**Break causality. Solve the impossible. Don't collapse the multiverse.**

## Requirements

- Python 3.1x+
- Pygame 2.0+

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move |
| 1, 2, 3 | Switch to Universe 1 (Prime), 2 (Echo), 3 (Fracture) |
| E | Interact |
| TAB | Toggle Causal Sight |
| SPACE | Paradox Pulse (phase through matter) |
| ESC | Pause |

## Game Mechanics

### Universes
- **Prime (Blue)**: The original timeline. Most stable.
- **Echo (Green)**: A divergent timeline. Things are different here.
- **Fracture (Red)**: A timeline that shouldn't exist. Reality is unstable.

### Causality
Objects and enemies are connected across universes. What you do in one affects the others. Use Causal Sight (TAB) to see the connections.

### Paradox
Breaking causality generates paradox. Too much paradox destabilizes reality. But some puzzles require paradox to solve...

## Project Structure

```
Multiverse/
├── main.py              # Entry point
├── src/
│   ├── core/            # Engine core
│   ├── multiverse/      # Multiverse systems
│   ├── entities/        # Game entities
│   ├── levels/          # Level definitions
│   ├── systems/         # Game systems
│   ├── ui/              # User interface
│   ├── rendering/       # Rendering
│   └── utils/           # Utilities
├── assets/              # Game assets
├── docs/                # Documentation
└── saves/               # Save files
```

## License

MIT License - See LICENSE file.
