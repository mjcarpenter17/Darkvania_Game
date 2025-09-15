#!/usr/bin/env python3
"""
Walk Animation Game - Main Entry Point

Reorganized codebase with modular architecture:
- src/game/: Core game logic (Game, Player)
- src/engine/: Game engine components (World, Camera)  
- src/ui/: User interface (Menu, GameState)
- src/utils/: Utilities (Assets, SpriteSheet)
"""

import sys
import os

# Add src directory to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.game.game import Game


def main():
    """Main entry point for the game."""
    try:
        # Create and run the game
        game = Game(width=800, height=450)
        game.run()
    except Exception as e:
        print(f"Game crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
