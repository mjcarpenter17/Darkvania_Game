# Darkvania Game - 2D Action Platformer

**Complete 2D side-scrolling action game with combat, AI enemies, health system, and professional animations.**

## 🎮 Game Features

- **Complete Player System**: Movement, combat combos, health management, and respawn
- **Intelligent Enemy AI**: Patrol behavior, combat reactions, and death sequences  
- **Health & Combat**: 2 HP system with visual feedback and invulnerability frames
- **Professional Animations**: 39+ animations with state-based management
- **World System**: Tile-based levels with collision detection and camera following

## 🚀 Quick Start

**Setup (Windows PowerShell):**
1. Create virtual environment: `py -3 -m venv .venv`
2. Activate: `.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. **Run the game**: `python main.py`

## 🎯 Game Controls

- **Move**: A/D or Arrow Keys
- **Jump**: Space or W  
- **Attack**: Left Mouse Button (combo: Slash 1 → Slash 2)
- **Dash**: Shift (evasive movement)
- **Respawn**: Space (when dead)

## 🏗️ Project Structure

```
src/
├── game/          # Core game systems
│   ├── player.py  # Player character (607 lines)
│   ├── enemy.py   # Enemy AI system (420+ lines)
│   └── game.py    # Main game coordinator
├── engine/        # World and physics
├── ui/           # User interface
└── utils/        # Animation framework

Documentation/     # Complete system documentation
Assests/          # Sprite sheets and animations
maps/             # Level data
```

## 📖 Documentation

- **[Game Progress Report](Documentation/Game_Progress_Status_Report.md)**: Complete system overview
- **[Developer Quick Reference](Documentation/Developer_Quick_Reference.md)**: Fast setup and common tasks
- **[Player Health System](Documentation/Player_Health_Respawn_System.md)**: Health and respawn mechanics
- **[Assassin AI System](Documentation/Assassin_AI_Task_List.md)**: Enemy AI implementation

## 🛠️ Developer Tools

- **Animation Viewer**: `python viewer.py` - Interactive frame selection
- **Map Editor**: Tiled map editor integration  
- **Debug Mode**: Collision visualization and system monitoring

## ✨ Current Status: Production Ready

All core systems are complete and fully tested:
- ✅ Player movement, combat, and health systems
- ✅ Advanced enemy AI with 4-phase behavior system
- ✅ Complete animation framework with 216 frames
- ✅ World engine with collision detection  
- ✅ UI system with real-time health display
- ✅ Death/respawn cycle with level restart

## 🎯 Technical Highlights

- **State Machines**: Clean behavior management for player and enemies
- **Aseprite Integration**: Professional animation pipeline with 153 frames
- **Physics System**: Gravity, collision detection, and platform navigation
- **Modular Architecture**: Extensible design for future development
- **Performance Optimized**: Smooth 60 FPS gameplay

---

**Ready for**: Gameplay testing, feature expansion, or production deployment.
- It looks for these animation module files by name under the folder you choose (default data):
	- walk_selection.py (for walking)
	- idle_selection.py (for idle)
	- fall_selection.py (for jump/fall)
- When saving from the viewer, use animation names walk, idle, and fall to match the current game setup (or adjust imports in game.py).

Files:
- game.py — Character controller with idle/walk/air animations and basic physics.
- spritesheet.py — Helper to slice frames from the sprite sheet.
- viewer.py — Interactive sprite-sheet frame picker with named save dialog.
- requirements.txt — Dependencies list.
- .gitignore — Common Python ignores.
