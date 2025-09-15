# Walk Animation Test (Python + Pygame)

Small Pygame project with a character controller and simple animations (idle, walk, air). Frames are cut from the included sprite sheet via an interactive viewer.

Setup (Windows PowerShell):
1. Create a virtual environment: py -3 -m venv .venv
2. Activate it: . .venv/Scripts/Activate.ps1
3. Install dependencies: pip install -r requirements.txt
4. Run the game: python game.py

Sprite sheet in this workspace: Assests/Sword Master Sprite Sheet 90x37.png

Game controls and behavior:
- Move: A / Left and D / Right
- Jump: Space or W
- States: idle (standing), walk (on ground and moving), air (jump/fall)
- Facing flips automatically based on movement direction

Frame Viewer (to pick frames and save animations):
- Run: python viewer.py
- Keys:
	- Arrows move cursor, Space toggles a frame, R selects entire row, C clears selection
	- S starts an interactive save dialog that asks for:
		- Animation name (default: walk)
		- Folder (default: data)
	- G grid on/off, H help on/off, [ ] decrease/increase spacing, ; ' decrease/increase margin
- Header panel keeps help text separate from the image; resizing is supported.
- Files are saved as <folder>/<animation>_selection.json and <folder>/<animation>_selection.py.

Important for the included game.py:
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
