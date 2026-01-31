"""
MULTIVERSE CAUSALITY
====================
A puzzle-adventure game where every action creates ripples across parallel universes.

Entry point for the game.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.game import Game


def main():
    """Main entry point."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
