   

import sys
import os
import asyncio

                             
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.game import Game


async def main():
                                                             
    game = Game()
    await game.run()


asyncio.run(main())
