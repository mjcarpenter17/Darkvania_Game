# Map Editor (Pygame) — Capabilities and Guide

This document explains what the tile map editor currently does, how to use it, and a prioritized backlog of improvements to make it great for 2D platformers and other tile-based games (top‑down, isometric, 2.5D).

## Quick start

- Run: `python map_editor.py`
- Tileset: expects `Assests/Cave_Tileset.png` by default.
- Save: Ctrl+S → writes `maps/last_map.json`.
- Load: Ctrl+L → reads `maps/last_map.json`.

## Current capabilities

### Tileset palette
- Auto-detect tile size from the tileset image (prefers 32, 16, 48, … when divisible).
- Settings menu (F3) to configure:
  - Tile Size (px)
  - Margin (outer border in the tileset)
  - Spacing (gap between tiles)
- Palette panel on the left:
  - Scrollable with mouse wheel.
  - Click to select a tile; highlight shows the current selection.
  - Palette scaling for readability (tiles <=32px are shown at 2x).

### Map canvas and grid
- Large, scrollable canvas to paint tiles on a grid.
- Panning:
  - Arrow keys or WASD.
  - Shift + mouse wheel for horizontal scroll; wheel alone for vertical.
- Visible grid lines for alignment.

### Tools
- Paint tool: Left‑click to place the selected tile.
- Erase tool: Right‑click (or switch to Erase) to clear a cell.
- Eyedropper: Middle‑click to pick a tile from the canvas, or switch to Pick tool (I).
- Continuous paint/erase while holding the mouse button.

### Layers
- Two layers:
  - Background
  - Foreground
- Layer switching with 1 (Background) / 2 (Foreground).
- Foreground is drawn on top of Background.

### Save / Load
- Export format: JSON (sparse), written to `maps/last_map.json` by default.
- Includes:
  - `tileset`, `tile_size`, `margin`, `spacing`
  - `map_cols`, `map_rows`
  - `layers`: each has a name and an array of tile placements `{x, y, t}` (t = palette index)
- Import loads the JSON and applies the saved tile slicing parameters.

### HUD and shortcuts
- HUD shows tool, layer, selected tile index, tile size (TS), margin (M), spacing (S), and basic help.
- Shortcuts:
  - F3: Settings
  - P/E/I: Paint / Erase / Pick tools
  - 1/2: Switch layer
  - Ctrl+S / Ctrl+L: Save / Load
  - Arrows or WASD: Pan canvas
  - Mouse wheel: Vertical scroll; Shift+wheel: Horizontal scroll
  - Middle‑click: Eyedropper from canvas

## JSON format

Example export (trimmed):

```
{
  "tileset": "Assests/Cave_Tileset.png",
  "tile_size": 32,
  "margin": 0,
  "spacing": 0,
  "map_cols": 100,
  "map_rows": 60,
  "layers": [
    { "name": "Background", "tiles": [ { "x": 10, "y": 5, "t": 3 } ] },
    { "name": "Foreground", "tiles": [ { "x": 10, "y": 4, "t": 12 } ] }
  ]
}
```

Notes:
- Tile indices `t` refer to the current palette ordering computed from `tile_size`, `margin`, and `spacing`.
- If you change these settings later, the palette ordering changes; existing indices may point to different source tiles. Set these before painting a final map.

## Known limitations (current build)

- No zoom in/out for the canvas (fixed 2x draw scale for readability).
- No “Save As” dialog; saves always to `maps/last_map.json` unless you change the path in code.
- No Undo/Redo.
- No selection/move/marquee/rectangle/line/fill tools; painting is cell‑by‑cell.
- No multi‑tile brush (stamps), flipping, or rotation.
- No per‑layer visibility toggles / opacity sliders.
- No map resize wizard (grid size is fixed at creation time in code).
- Changing `tile_size/margin/spacing` after painting can invalidate tile indices; the editor doesn’t remap tiles automatically.

## Roadmap — UX and feature improvements

Near‑term (low risk, high value):
- Save As / Load From dialogs with recent files.
- Undo/Redo (ring buffer of edits, e.g., Ctrl+Z / Ctrl+Y).
- Zoom controls (e.g., 0.5x/1x/2x/4x) and fit‑to‑window.
- Toggle grid visibility and color; show coordinates under cursor.
- Layer visibility/lock toggles and per‑layer opacity.
- Multi‑tile selection (drag) → copy/cut/paste; stamp brush.
- Rectangle/line/fill (bucket) tools.
- Status bar with tile and cell info, scroll position.

Platformer‑oriented features:
- Collision layer(s) and physics shapes (rects/polylines) per tile or separate “collision map”.
- Entities/objects layer with typed properties (spawns, triggers, doors, cameras, collectibles).
- Parallax layers and groups.
- Animated tiles and per‑tile metadata (e.g., hazard/spike, moving platform).
- Auto‑tiling (bitmask/Wang tiles) to speed level creation.

Cross‑genre (top‑down, isometric, 2.5D):
- Tile flipping/rotation (horizontal/vertical/90° steps) and variants.
- Support for staggered/isometric projections and isometric brushes.
- Height/altitude map and ramp tiles (for 2.5D look).
- Pathfinding annotations (walkable, cost, portals) and region tagging.
- Multiple tilesets per map and tileset switching.

Interoperability & export:
- “Export to image” (composited PNG) for quick previews.
- CSV export per layer; PNG+CSV pair for simple engines.
- Tiled (TMX/TSX) import/export to interoperate with external tools.
- Minimal runtime loader library (Python module) to render layers and resolve tiles, with collision helpers.

Power‑user / polish:
- Palette search and favorites; tile tags and folders.
- Snap settings (grid size, sub‑grid nudge), magnetize to edges.
- Mini‑map viewport.
- Configurable hotkeys and toolbars.
- Theme and UI scale options.

## Integration notes (using maps at runtime)

- Load the JSON, apply its `tile_size`, `margin`, `spacing`, and reconstruct the same palette order to render.
- Draw layers back‑to‑front; optionally cull by camera rectangle for performance.
- For collisions, either derive from a dedicated collision layer or per‑tile metadata.
- Keep tile flipping/rotation in mind for future runtime support (store flags per tile: H/V/Rot90).

## Suggested next steps

- Add Zoom + Undo/Redo + Save As.
- Implement layer visibility/lock and a selection/stamp tool.
- Decide on a collision strategy (separate layer vs per‑tile flags) for the platformer.
- Plan export to Tiled TMX to interop with other tools, plus an optional PNG export.

---

If you want, I can implement any of the near‑term items next (Zoom, Undo/Redo, Save As, or selection/stamp).
