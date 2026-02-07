"""
FRACTURED CAUSALITY
===================
A puzzle-adventure game where every action creates ripples across parallel universes.

Entry point for the game.
"""

import sys
import os
import asyncio

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.game import Game


async def main():
    """Main entry point (async for pygbag web deployment)."""
    game = Game()
    await game.run()


asyncio.run(main())
