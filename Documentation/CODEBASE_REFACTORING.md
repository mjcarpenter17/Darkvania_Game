# Game Codebase Refactoring

## Overview
The game codebase has been reorganized into a clean, modular architecture that separates concerns and makes the code much more maintainable.

## New Directory Structure

```
src/
├── game/           # Core game logic
│   ├── __init__.py
│   ├── game.py     # Main Game class that coordinates everything
│   └── player.py   # Player character with physics and animation
├── engine/         # Game engine components  
│   ├── __init__.py
│   ├── world.py    # World/TileMap for level management and collision
│   └── camera.py   # Camera system for viewport management
├── ui/             # User interface components
│   ├── __init__.py
│   ├── menu.py     # Menu system with navigation
│   └── game_state.py # Game state management and transitions
└── utils/          # Utility modules
    ├── __init__.py
    ├── assets.py   # Asset loading and animation management
    └── spritesheet.py # Sprite sheet utilities

# Root level
main.py             # New main entry point
game.py             # Original file (now legacy)
```

## Module Breakdown

### `src/game/game.py` - Main Game Class
- **Purpose**: Coordinates all game systems and manages the main game loop
- **Key Features**:
  - Initializes pygame and all game systems
  - Manages state transitions between menu and gameplay
  - Handles the main game loop with proper event handling
  - Coordinates Player, World, and Camera updates
  - Handles death/respawn logic
- **Dependencies**: Player, World, Camera, GameState

### `src/game/player.py` - Player Character
- **Purpose**: Handles player physics, animation, input, and collision
- **Key Features**:
  - Complete physics system (gravity, jumping, movement)
  - Animation state management (idle, walk, jump, fall, transition)
  - Input handling (keyboard controls)
  - Collision detection with world tiles
  - Configurable movement parameters
- **Dependencies**: AnimationLoader from utils

### `src/engine/world.py` - World/Level Management
- **Purpose**: Manages game levels, tiles, and collision detection
- **Key Features**:
  - Loads maps from JSON format (map editor compatible)
  - Handles tile rendering with camera offset
  - Comprehensive collision detection system
  - Object management (spawns, events, etc.)
  - Efficient tile lookup and rendering
- **Dependencies**: pygame

### `src/engine/camera.py` - Camera System
- **Purpose**: Manages viewport and smooth camera following
- **Key Features**:
  - Smooth camera following with dead zones
  - World boundary clamping
  - Configurable smoothing and dead zone sizes
  - World-to-screen coordinate conversion
  - Viewport visibility testing
- **Dependencies**: pygame

### `src/ui/menu.py` - Menu System
- **Purpose**: Handles menu navigation and rendering
- **Key Features**:
  - Keyboard-based menu navigation
  - Customizable menu items and actions
  - Clean menu rendering with fonts and colors
  - Support for nested menu systems
- **Dependencies**: pygame

### `src/ui/game_state.py` - Game State Management  
- **Purpose**: Manages game state transitions and map selection
- **Key Features**:
  - State machine for menu/game transitions
  - Automatic map discovery and loading
  - Map selection menu generation
  - State persistence and transitions
- **Dependencies**: Menu system

### `src/utils/assets.py` - Asset Loading
- **Purpose**: Handles loading of sprites and animations
- **Key Features**:
  - Comprehensive animation loading system
  - Fallback handling for missing assets
  - Support for trimmed sprites and custom pivots
  - AnimationLoader class for managing all character animations
- **Dependencies**: SpriteSheet, animation data files

### `src/utils/spritesheet.py` - Sprite Utilities
- **Purpose**: Utilities for slicing and loading sprite sheets
- **Key Features**:
  - Flexible sprite sheet slicing
  - Support for margins, spacing, and custom layouts
  - Backwards compatibility with existing code
- **Dependencies**: pygame

## Benefits of New Structure

### 1. **Separation of Concerns**
- Each module has a single, clear responsibility
- Game logic separated from UI and engine components
- Easier to understand and modify individual systems

### 2. **Maintainability**
- Smaller, focused files instead of one large 946-line file
- Clear dependencies between modules
- Easy to find and fix issues in specific systems

### 3. **Reusability**
- Engine components (World, Camera) can be reused for other games
- UI components are independent and reusable
- Player class can be easily extended or modified

### 4. **Testability**
- Individual modules can be tested in isolation
- Clear interfaces make mocking and testing easier
- Reduced coupling between systems

### 5. **Extensibility**
- Easy to add new features to specific systems
- Clear place for new functionality (e.g., enemies in game/, new UI in ui/)
- Plugin-style architecture for game systems

## Migration Guide

### Running the New Code
```bash
# Instead of: python game.py
python main.py
```

### Key Changes from Original
1. **No Breaking Changes**: All existing functionality preserved
2. **Same Assets**: Uses the same sprite sheets and map files
3. **Same Controls**: Identical control scheme and gameplay
4. **Enhanced Features**: Better organized code with improved camera system

### Backwards Compatibility
- The original `game.py` file is preserved
- All existing map files work without changes
- Asset files and directory structure unchanged
- Same pygame and Python requirements

## Future Enhancements Made Easy

With this structure, you can easily add:

### New Game Systems
```python
# src/game/enemies.py - Enemy management
# src/game/powerups.py - Collectible items  
# src/game/weapons.py - Combat system
```

### Enhanced Engine Features
```python
# src/engine/physics.py - Advanced physics engine
# src/engine/audio.py - Sound and music management
# src/engine/particles.py - Particle effects
```

### Extended UI
```python
# src/ui/hud.py - In-game HUD
# src/ui/settings.py - Settings menu
# src/ui/inventory.py - Inventory system
```

This refactored structure provides a solid foundation for continued game development while maintaining all existing functionality!
