import os
import sys
import json
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from datetime import datetime

import pygame

# Icon cache for loaded PNG images
ICON_CACHE = {}

# Unicode icon fallbacks for consistent UI
ICONS = {
    'gear': '⚙',           # Settings/gear icon - fallback: '*'
    'eye_open': '●',       # Visibility on - solid circle
    'eye_closed': '○',     # Visibility off - hollow circle
    'lock_open': '○',      # Unlocked - hollow circle  
    'lock_closed': '●',    # Locked - solid circle
    'plus': '+',           # Add/create
    'minus': '-',          # Remove/delete (changed from −)
    'duplicate': '=',      # Duplicate/copy (changed from ⧉)
    'up_arrow': '^',       # Move up (changed from ▲)
    'down_arrow': 'v',     # Move down (changed from ▼)
    'close': 'x',          # Close/cancel (changed from ×)
    'triangle_right': '>',  # Collapsed panel (changed from ▶)
    'triangle_down': 'v',  # Expanded panel (changed from ▼)
    'circle': 'o',         # Circle brush shape
    'square': '#',         # Square brush shape  
    'diamond': '<>',       # Diamond brush shape
}

# Fallback dictionary for problematic fonts
ICON_FALLBACKS = {
    'gear': '*',
    'eye_open': 'O',
    'eye_closed': 'o', 
    'duplicate': '||',
    'up_arrow': '^',
    'down_arrow': 'v',
    'triangle_right': '>',
    'triangle_down': 'v',
    'circle': 'O',
    'diamond': '<>',
}


def resource_path(relative: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative)


def render_icon(font: pygame.font.Font, icon_key: str, color: tuple, fallback_text: str = None, size: int = 16) -> pygame.Surface:
    """
    Render an icon using PNG files first, then Unicode symbols with fallbacks.
    
    Phase 1: Try to load PNG icon from MapEditor/icons/
    Phase 2: Fall back to Unicode symbols with ASCII fallbacks
    
    Args:
        font: Pygame font to render with
        icon_key: Key for icon lookup
        color: RGB color tuple for the icon
        fallback_text: Optional fallback text if icon_key not found
        size: Size of the icon in pixels (for PNG scaling)
        
    Returns:
        Rendered surface of the icon
    """
    try:
        # Phase 1: Try to load PNG icon
        png_path = None
        if icon_key == 'gear':
            png_path = os.path.join('MapEditor', 'icons', 'settings.png')
        elif icon_key == 'layers' or icon_key == 'duplicate':
            png_path = os.path.join('MapEditor', 'icons', 'layers.png')
        elif icon_key == 'diamond':
            png_path = os.path.join('MapEditor', 'icons', 'diamonds.png')
        
        if png_path and os.path.exists(png_path):
            # Check cache first
            cache_key = f"{png_path}_{size}_{color}"
            if cache_key in ICON_CACHE:
                return ICON_CACHE[cache_key]
            
            try:
                # Load and scale PNG icon
                icon_surface = pygame.image.load(png_path).convert_alpha()
                
                # Scale to desired size
                if icon_surface.get_width() != size or icon_surface.get_height() != size:
                    icon_surface = pygame.transform.scale(icon_surface, (size, size))
                
                # Apply color tinting if the icon is monochrome
                # Create a colored version by multiplying with the desired color
                colored_surface = icon_surface.copy()
                color_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
                color_overlay.fill((*color, 255))
                colored_surface.blit(color_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
                
                # Cache the result
                ICON_CACHE[cache_key] = colored_surface
                return colored_surface
                
            except Exception as e:
                print(f"Error loading PNG icon {png_path}: {e}")
                pass  # Fall through to Unicode fallback
        
        # Phase 2: Try primary Unicode symbol
        if icon_key in ICONS:
            icon_text = ICONS[icon_key]
            test_surf = font.render(icon_text, True, color)
            # Check if the character rendered properly (not as a missing glyph)
            if test_surf.get_width() > 0:
                return test_surf
        
        # Fallback level 1: Use ASCII alternatives
        if icon_key in ICON_FALLBACKS:
            icon_text = ICON_FALLBACKS[icon_key]
            return font.render(icon_text, True, color)
        
        # Fallback level 2: Use provided fallback text
        if fallback_text:
            return font.render(fallback_text, True, color)
            
        # Fallback level 3: Generic symbol
        return font.render("?", True, color)
        
    except Exception as e:
        # Emergency fallback - render a simple colored rectangle
        fallback_surf = pygame.Surface((size, size))
        fallback_surf.fill(color[:3])  # Use RGB components only
        return fallback_surf


def detect_tile_size(surface: pygame.Surface) -> int:
    w, h = surface.get_width(), surface.get_height()
    candidates = [64, 48, 40, 36, 32, 24, 20, 16, 12, 8]
    valid = [s for s in candidates if w % s == 0 and h % s == 0]
    preferred = [32, 16, 48, 24, 64, 12, 8, 20, 36, 40]
    for p in preferred:
        if p in valid:
            return p
    if valid:
        return max(valid)
    g = math.gcd(w, h)
    g = max(8, min(64, g))
    return g


@dataclass
class Layer:
    name: str
    data: List[List[int]]  # -1 empty, otherwise tile index into palette
    visible: bool = True
    locked: bool = False


@dataclass
@dataclass
class TileProperties:
    """Properties for individual tiles including collision data"""
    collision_type: str = "none"  # none, solid, platform, damage, water, ice, trigger, custom
    collision_shape: str = "rectangle"  # rectangle, circle, polygon
    collision_bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, width, height offset from tile
    friction: float = 1.0  # Surface friction (1.0 = normal, 0.0 = ice, >1.0 = sticky)
    bounce: float = 0.0  # Bounce/restitution factor (0.0 = no bounce, 1.0 = perfect bounce)
    damage: int = 0  # Damage amount for damage tiles
    trigger_id: str = ""  # ID for trigger tiles
    custom_properties: dict = None  # User-defined custom properties
    
    def __post_init__(self):
        if self.custom_properties is None:
            self.custom_properties = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "collision_type": self.collision_type,
            "collision_shape": self.collision_shape,
            "collision_bounds": self.collision_bounds,
            "friction": self.friction,
            "bounce": self.bounce,
            "damage": self.damage,
            "trigger_id": self.trigger_id,
            "custom_properties": self.custom_properties
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TileProperties':
        """Create from dictionary for deserialization"""
        return cls(
            collision_type=data.get("collision_type", "none"),
            collision_shape=data.get("collision_shape", "rectangle"),
            collision_bounds=tuple(data.get("collision_bounds", (0, 0, 0, 0))),
            friction=data.get("friction", 1.0),
            bounce=data.get("bounce", 0.0),
            damage=data.get("damage", 0),
            trigger_id=data.get("trigger_id", ""),
            custom_properties=data.get("custom_properties", {})
        )


@dataclass
class GameObject:
    """Game object for entity placement (spawns, events, etc.)"""
    object_type: str  # enemy, spawn, collectible, event, checkpoint, interactive
    color: Tuple[int, int, int]  # RGB color for visualization
    name: str  # Generated name like 'Point_01'
    x: int  # Grid X position
    y: int  # Grid Y position
    custom_properties: dict = None  # User-defined properties
    
    def __post_init__(self):
        if self.custom_properties is None:
            self.custom_properties = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.object_type,
            'color': list(self.color),  # Convert tuple to list for JSON
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'custom_properties': self.custom_properties
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameObject':
        """Create GameObject from dictionary"""
        return cls(
            object_type=data.get('type', 'spawn'),
            color=tuple(data.get('color', [255, 0, 0])),  # Convert list back to tuple
            name=data.get('name', 'Point_01'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            custom_properties=data.get('custom_properties', {})
        )


# Command Pattern for Undo/Redo System
class Command(ABC):
    """Abstract base class for all undoable commands."""
    
    @abstractmethod
    def execute(self):
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self):
        """Undo the command."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of the command for UI display."""
        pass


class PaintCommand(Command):
    """Command for painting/placing tiles."""
    
    def __init__(self, editor, layer_index: int, x: int, y: int, new_tile: int, old_tile: int):
        self.editor = editor
        self.layer_index = layer_index
        self.x = x
        self.y = y
        self.new_tile = new_tile
        self.old_tile = old_tile
    
    def execute(self):
        """Place the new tile."""
        if 0 <= self.layer_index < len(self.editor.layers):
            if 0 <= self.y < len(self.editor.layers[self.layer_index].data):
                if 0 <= self.x < len(self.editor.layers[self.layer_index].data[self.y]):
                    self.editor.layers[self.layer_index].data[self.y][self.x] = self.new_tile
    
    def undo(self):
        """Restore the old tile."""
        if 0 <= self.layer_index < len(self.editor.layers):
            if 0 <= self.y < len(self.editor.layers[self.layer_index].data):
                if 0 <= self.x < len(self.editor.layers[self.layer_index].data[self.y]):
                    self.editor.layers[self.layer_index].data[self.y][self.x] = self.old_tile
    
    def get_description(self) -> str:
        return f"Paint tile at ({self.x}, {self.y})"


class EraseCommand(Command):
    """Command for erasing tiles."""
    
    def __init__(self, editor, layer_index: int, x: int, y: int, old_tile: int):
        self.editor = editor
        self.layer_index = layer_index
        self.x = x
        self.y = y
        self.old_tile = old_tile
    
    def execute(self):
        """Erase the tile (set to -1)."""
        if 0 <= self.layer_index < len(self.editor.layers):
            if 0 <= self.y < len(self.editor.layers[self.layer_index].data):
                if 0 <= self.x < len(self.editor.layers[self.layer_index].data[self.y]):
                    self.editor.layers[self.layer_index].data[self.y][self.x] = -1
    
    def undo(self):
        """Restore the old tile."""
        if 0 <= self.layer_index < len(self.editor.layers):
            if 0 <= self.y < len(self.editor.layers[self.layer_index].data):
                if 0 <= self.x < len(self.editor.layers[self.layer_index].data[self.y]):
                    self.editor.layers[self.layer_index].data[self.y][self.x] = self.old_tile
    
    def get_description(self) -> str:
        return f"Erase tile at ({self.x}, {self.y})"


class MultiTileCommand(Command):
    """Command for operations affecting multiple tiles (flood fill, selection operations)."""
    
    def __init__(self, editor, layer_index: int, tile_changes: List[tuple]):
        """
        tile_changes: List of (x, y, old_tile, new_tile) tuples
        """
        self.editor = editor
        self.layer_index = layer_index
        self.tile_changes = tile_changes
    
    def execute(self):
        """Apply all tile changes."""
        if 0 <= self.layer_index < len(self.editor.layers):
            layer_data = self.editor.layers[self.layer_index].data
            for x, y, old_tile, new_tile in self.tile_changes:
                if 0 <= y < len(layer_data) and 0 <= x < len(layer_data[y]):
                    layer_data[y][x] = new_tile
    
    def undo(self):
        """Revert all tile changes."""
        if 0 <= self.layer_index < len(self.editor.layers):
            layer_data = self.editor.layers[self.layer_index].data
            for x, y, old_tile, new_tile in self.tile_changes:
                if 0 <= y < len(layer_data) and 0 <= x < len(layer_data[y]):
                    layer_data[y][x] = old_tile
    
    def get_description(self) -> str:
        return f"Multi-tile operation ({len(self.tile_changes)} tiles)"


class LayerAddCommand(Command):
    """Command for adding a new layer."""
    
    def __init__(self, editor, layer: Layer, insert_index: int):
        self.editor = editor
        self.layer = layer
        self.insert_index = insert_index
    
    def execute(self):
        """Add the layer at the specified index."""
        self.editor.layers.insert(self.insert_index, self.layer)
        # Update current layer if needed
        if self.editor.current_layer >= self.insert_index:
            self.editor.current_layer += 1
    
    def undo(self):
        """Remove the added layer."""
        if self.insert_index < len(self.editor.layers):
            self.editor.layers.pop(self.insert_index)
            # Update current layer if needed
            if self.editor.current_layer > self.insert_index:
                self.editor.current_layer -= 1
            elif self.editor.current_layer == self.insert_index and self.editor.layers:
                self.editor.current_layer = min(self.editor.current_layer, len(self.editor.layers) - 1)
    
    def get_description(self) -> str:
        return f"Add layer '{self.layer.name}'"


class LayerDeleteCommand(Command):
    """Command for deleting a layer."""
    
    def __init__(self, editor, layer_index: int):
        self.editor = editor
        self.layer_index = layer_index
        self.deleted_layer = None
        self.was_current = False
    
    def execute(self):
        """Delete the layer at the specified index."""
        if 0 <= self.layer_index < len(self.editor.layers):
            self.deleted_layer = self.editor.layers.pop(self.layer_index)
            self.was_current = (self.editor.current_layer == self.layer_index)
            
            # Update current layer
            if self.editor.current_layer >= self.layer_index and self.editor.layers:
                self.editor.current_layer = min(self.editor.current_layer, len(self.editor.layers) - 1)
            elif not self.editor.layers:
                # If no layers left, add a default one
                default_layer = Layer("Background", [[-1 for _ in range(self.editor.map_cols)] for _ in range(self.editor.map_rows)])
                self.editor.layers.append(default_layer)
                self.editor.current_layer = 0
    
    def undo(self):
        """Restore the deleted layer."""
        if self.deleted_layer:
            self.editor.layers.insert(self.layer_index, self.deleted_layer)
            if self.was_current:
                self.editor.current_layer = self.layer_index
    
    def get_description(self) -> str:
        layer_name = self.deleted_layer.name if self.deleted_layer else "layer"
        return f"Delete layer '{layer_name}'"


class LayerMoveCommand(Command):
    """Command for moving a layer up or down."""
    
    def __init__(self, editor, from_index: int, to_index: int):
        self.editor = editor
        self.from_index = from_index
        self.to_index = to_index
    
    def execute(self):
        """Move the layer from one index to another."""
        if (0 <= self.from_index < len(self.editor.layers) and 
            0 <= self.to_index < len(self.editor.layers)):
            
            # Remove layer from old position
            layer = self.editor.layers.pop(self.from_index)
            # Insert at new position
            self.editor.layers.insert(self.to_index, layer)
            
            # Update current layer index
            if self.editor.current_layer == self.from_index:
                self.editor.current_layer = self.to_index
            elif self.from_index < self.editor.current_layer <= self.to_index:
                self.editor.current_layer -= 1
            elif self.to_index <= self.editor.current_layer < self.from_index:
                self.editor.current_layer += 1
    
    def undo(self):
        """Move the layer back to its original position."""
        if (0 <= self.to_index < len(self.editor.layers) and 
            0 <= self.from_index < len(self.editor.layers)):
            
            # Remove layer from current position
            layer = self.editor.layers.pop(self.to_index)
            # Insert back at original position
            self.editor.layers.insert(self.from_index, layer)
            
            # Update current layer index
            if self.editor.current_layer == self.to_index:
                self.editor.current_layer = self.from_index
            elif self.to_index < self.editor.current_layer <= self.from_index:
                self.editor.current_layer += 1
            elif self.from_index <= self.editor.current_layer < self.to_index:
                self.editor.current_layer -= 1
    
    def get_description(self) -> str:
        direction = "up" if self.to_index < self.from_index else "down"
        return f"Move layer {direction}"


class LayerDuplicateCommand(Command):
    """Command for duplicating a layer."""
    
    def __init__(self, editor, source_index: int):
        self.editor = editor
        self.source_index = source_index
        self.duplicate_index = source_index + 1
        self.duplicated_layer = None
    
    def execute(self):
        """Duplicate the layer."""
        if 0 <= self.source_index < len(self.editor.layers):
            source_layer = self.editor.layers[self.source_index]
            
            # Create a deep copy of the layer
            new_data = [[cell for cell in row] for row in source_layer.data]
            self.duplicated_layer = Layer(
                f"{source_layer.name} Copy",
                new_data,
                source_layer.visible,
                source_layer.locked
            )
            
            # Insert the duplicate after the source
            self.editor.layers.insert(self.duplicate_index, self.duplicated_layer)
            
            # Update current layer if needed
            if self.editor.current_layer >= self.duplicate_index:
                self.editor.current_layer += 1
    
    def undo(self):
        """Remove the duplicated layer."""
        if (self.duplicated_layer and 
            self.duplicate_index < len(self.editor.layers) and
            self.editor.layers[self.duplicate_index] == self.duplicated_layer):
            
            self.editor.layers.pop(self.duplicate_index)
            
            # Update current layer if needed
            if self.editor.current_layer > self.duplicate_index:
                self.editor.current_layer -= 1
            elif self.editor.current_layer == self.duplicate_index and self.editor.layers:
                self.editor.current_layer = min(self.editor.current_layer, len(self.editor.layers) - 1)
    
    def get_description(self) -> str:
        return f"Duplicate layer"


class ObjectPlaceCommand(Command):
    """Command for placing a game object."""
    
    def __init__(self, editor, game_object: GameObject, replaced_object: GameObject = None):
        self.editor = editor
        self.game_object = game_object
        self.replaced_object = replaced_object  # Object that was replaced at same position
    
    def execute(self):
        """Place the object."""
        # Remove any existing object at this position first
        self.editor.remove_object_at(self.game_object.x, self.game_object.y)
        self.editor.objects.append(self.game_object)
    
    def undo(self):
        """Remove the placed object and restore replaced object if any."""
        if self.game_object in self.editor.objects:
            self.editor.objects.remove(self.game_object)
        if self.replaced_object:
            self.editor.objects.append(self.replaced_object)
    
    def get_description(self) -> str:
        return f"Place {self.game_object.object_type} '{self.game_object.name}'"


class ObjectDeleteCommand(Command):
    """Command for deleting a game object."""
    
    def __init__(self, editor, game_object: GameObject):
        self.editor = editor
        self.game_object = game_object
    
    def execute(self):
        """Delete the object."""
        if self.game_object in self.editor.objects:
            self.editor.objects.remove(self.game_object)
    
    def undo(self):
        """Restore the deleted object."""
        self.editor.objects.append(self.game_object)
    
    def get_description(self) -> str:
        return f"Delete {self.game_object.object_type} '{self.game_object.name}'"


class BatchCommand(Command):
    """Command for executing multiple commands as a single operation."""
    
    def __init__(self, commands: List[Command]):
        self.commands = commands
    
    def execute(self):
        """Execute all commands in order."""
        for command in self.commands:
            command.execute()
    
    def undo(self):
        """Undo all commands in reverse order."""
        for command in reversed(self.commands):
            command.undo()
    
    def get_description(self) -> str:
        if len(self.commands) == 1:
            return self.commands[0].get_description()
        return f"Batch operation ({len(self.commands)} commands)"


class TileEditor:
    def __init__(self, tileset_path: str):
        pygame.init()
        pygame.display.set_caption("Tile Map Editor")

        self.WIDTH, self.HEIGHT = 1100, 720
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.FONT = pygame.font.SysFont("consolas", 16)
        self.BG = (26, 28, 33)
        self.PANEL_BG = (21, 22, 26)
        self.GRID = (54, 57, 63)
        self.HUD = (200, 200, 210)
        self.SELECT = (255, 198, 0)
        self.ACTIVE = (120, 200, 255)
        
        # Menu system (initialize early)
        self.show_menu_bar = True
        self.MENU_BAR_H = 28
        
        self.TOP_H = (self.MENU_BAR_H + 40) if self.show_menu_bar else 40
        self.STATUS_H = 24

        # Theme extras
        self.HEADER_BG = (28, 30, 36)
        self.HEADER_ACCENT = (80, 170, 255)
        self.STATUS_BG = (18, 19, 22)
        self.STATUS_FG = (190, 195, 205)
        self.SPLITTER = (58, 62, 70)

        # Layout sizes
        self.left_w = 300
        self.right_w = 260
        self.min_left = 180
        self.min_right = 200
        self.min_canvas_w = 240
        self.panel_header_h = 28
        self.right_split = 0.55
        self.left_collapsed = False
        self.right_layers_collapsed = False
        self.right_props_collapsed = False
        self.drag_left_split = False
        self.drag_right_split = False
        self.drag_right_inner_split = False
        self._drag_offset = 0
        
        # Splitter visual feedback
        self.splitter_hover = None  # Track which splitter is being hovered
        self.splitter_zones = {}  # Store splitter hit areas
        self.splitter_active = None  # Track which splitter is being dragged

        # Load tileset (fall back to placeholder if missing)
        try:
            tileset_image = pygame.image.load(resource_path(tileset_path)).convert_alpha()
        except Exception as e:
            print(f"Could not load tileset '{tileset_path}': {e}. Using placeholder.")
            tileset_image = pygame.Surface((256, 256), pygame.SRCALPHA)
            for y in range(0, 256, 32):
                for x in range(0, 256, 32):
                    c = (60, 60, 64) if (x // 32 + y // 32) % 2 == 0 else (90, 90, 96)
                    pygame.draw.rect(tileset_image, c, (x, y, 32, 32))

        self.tileset_surface = tileset_image
        self.TILE_SIZE = detect_tile_size(self.tileset_surface)
        self.VIEW_SCALE = 2
        self.zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
        self.PALETTE_SCALE = max(1, 2 if self.TILE_SIZE <= 32 else 1)

        # Tileset slicing configuration
        self.margin = 0
        self.spacing = 0
        self.tiles: List[pygame.Surface] = []
        self.tiles_per_row = 0
        self.selected_tile: Optional[int] = None
        self.multi_tile_selection: List[int] = []  # List of selected tile indices
        self.multi_tile_mode: bool = False  # Whether we're in multi-tile selection mode
        self.multi_tile_brush_data: List[Tuple[int, int, int]] = []  # (relative_x, relative_y, tile_index)
        
        # Collision system
        self.COLLISION_TYPES = [
            ("none", "None", "No collision detection"),
            ("solid", "Solid", "Full collision box - walls, floors, ceilings"),
            ("platform", "Platform", "One-way collision from above - jump-through platforms"),
            ("damage", "Damage", "Hurts player - spikes, lava, hazards"),
            ("water", "Water", "Liquid physics - swimming areas, slow movement"),
            ("ice", "Ice", "Slippery surface - reduced friction"),
            ("trigger", "Trigger", "Event activation - doors, switches, checkpoints"),
            ("custom", "Custom", "User-defined collision behavior")
        ]
        
        # Tile properties - maps tile index to TileProperties
        self.tile_properties: dict[int, TileProperties] = {}
        self.show_collision_overlay = False  # Toggle collision visualization
        self.collision_overlay_opacity = 128  # 0-255
        
        # Collision menu state
        self.show_collision_menu = False
        self.collision_menu_pos = (0, 0)
        
        # Objects system
        self.objects: List[GameObject] = []  # List of placed game objects
        self.selected_object: GameObject = None  # Currently selected object
        self.object_mode = "tiles"  # "tiles" or "objects" - current tab mode
        self.object_placement_mode = False  # Whether we're actively placing objects
        self.persistent_object_mode = False  # Keep placing same object type
        self.selected_objects: List[GameObject] = []  # Multiple selected objects for copy/paste
        self.copied_objects = []  # Objects in clipboard
        self.object_paste_mode = False  # Whether we're in paste mode for objects
        
        # Object types with color coding
        self.OBJECT_TYPES = [
            ("enemy", "Enemy", (255, 80, 80)),      # Red
            ("spawn", "Spawn", (80, 150, 255)),     # Blue  
            ("collectible", "Item", (80, 255, 80)), # Green
            ("chest", "Chest", (223, 197, 123)),    # Gold (#DFC57B)
            ("event", "Event", (255, 255, 80)),     # Yellow
            ("checkpoint", "Save", (255, 150, 80)), # Orange
            ("interactive", "Door", (200, 80, 255)) # Purple
        ]
        self.selected_object_type = 0  # Index into OBJECT_TYPES
        self.object_counters = {}  # Track object counts for auto-naming
        
        # Initialize object counters
        for obj_type, _, _ in self.OBJECT_TYPES:
            self.object_counters[obj_type] = 0
        
        # Tab interface state
        self.tab_rects = {}  # Store tab hit areas for click detection
        
        # Object editing state
        self.object_type_menu_open = False
        self.object_type_menu_pos = (0, 0)
        self.object_name_editing = False
        self.object_name_edit_text = ""
        self.object_name_cursor = 0
        
        self.slice_tiles()

        # Map data
        self.map_cols = 100
        self.map_rows = 60
        self.layers: List[Layer] = [
            Layer("Background", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
            Layer("Foreground", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
        ]
        self.current_layer = 1

        # Viewport scrolling (pixels)
        self.scroll_x = 0
        self.scroll_y = 0
        self.scroll_speed = 650

        # Palette scrolling
        self.palette_scroll = 0

        # Tools & selection
        self.selected_tile = 0 if self.tiles else None
        self.tool = "paint"  # paint | erase | pick | flood_fill | select | line | rectangle | circle
        
        # Shape tool state
        self.shape_start_tile = None
        self.shape_end_tile = None
        self.shape_dragging = False
        self.shape_preview_tiles = []

        # Selection system
        self.has_selection = False
        self.selection_start_x = 0
        self.selection_start_y = 0
        self.selection_end_x = 0
        self.selection_end_y = 0
        self.selection_dragging = False
        self.selection_marching_ants_offset = 0
        
        # Multi-selection support
        self.selection_mode = "replace"  # "replace", "add", "subtract"
        self.original_selection = None  # Store original selection for add/subtract modes
        
        # Clipboard system
        self.clipboard = None  # Will store copied tile data
        self.paste_preview = False
        self.paste_x = 0
        self.paste_y = 0

        # Stamp system
        self.stamps = []  # List of saved stamps
        self.current_stamp = None  # Currently selected stamp for placement
        self.stamp_preview = False  # Whether showing stamp placement preview
        
        # Pattern system
        self.pattern_data = None  # Pattern data created from selection
        self.pattern_mode = False  # Whether pattern painting is enabled

        # Undo/Redo system
        self.command_history: List[Command] = []
        self.history_index = -1  # Points to the last executed command
        self.max_history_size = 100  # Configurable history depth

        # Settings modal state
        self.show_settings = False
        self.settings_focus = 0  # 0=tile_size,1=margin,2=spacing
        self._settings_temp = {"tile_size": self.TILE_SIZE, "margin": self.margin, "spacing": self.spacing}

        # Save path and file management
        self.save_dir = resource_path("maps")
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_path = os.path.join(self.save_dir, "last_map.json")
        self.current_file_path = None  # Path to currently opened/saved file
        self.current_file_name = "Untitled"  # Display name for window title
        self.is_modified = False  # Track if map has unsaved changes
        self.last_directory = self.save_dir  # Remember last used directory
        
        # Recent files system
        self.recent_files = []  # List of recently opened files
        self.max_recent_files = 10
        
        # Auto-save system
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes in seconds
        self.last_auto_save = time.time()
        self.auto_save_indicator = False  # Show indicator in status bar

        # Optional auto-exit for quick tests
        self.auto_exit_seconds = None
        try:
            val = os.environ.get("AUTO_EXIT_SEC")
            if val:
                self.auto_exit_seconds = float(val)
        except Exception:
            self.auto_exit_seconds = None
        self.elapsed = 0.0

        # Derived rectangles
        self.left_rect = pygame.Rect(0, 0, 0, 0)
        self.right_rect = pygame.Rect(0, 0, 0, 0)
        self.canvas_rect = pygame.Rect(0, 0, 0, 0)
        self.top_rect = pygame.Rect(0, 0, 0, 0)
        self.status_rect = pygame.Rect(0, 0, 0, 0)
        self.right_layers_rect = pygame.Rect(0, 0, 0, 0)
        self.right_props_rect = pygame.Rect(0, 0, 0, 0)

        # Toolbar buttons (updated each frame)
        self._toolbar_hitboxes = []
        self._toolbar_tooltips = {}
        self.show_zoom_menu = False
        self._zoom_menu_hitboxes = []
        self._zoom_menu_anchor = None
        
        # Menu system state variables
        self.active_menu = None  # "file", "edit", "view", "tools", etc.
        self.menu_hover = None
        self._menu_hitboxes = {}
        self._submenu_hitboxes = []
        self.show_recent_files_menu = False
        self.show_export_menu = False

        # Tool options
        self.brush_size = 1  # for paint/erase: 1,2,3
        self.brush_shape = "square"  # square, circle, diamond
        self.fill_mode = 4  # 4-connected or 8-connected flood fill
        self.shape_filled = False  # for rectangle and circle tools

        # Gear icon for tileset settings
        self.gear_rect = None

        # Middle-mouse drag panning state
        self.middle_mouse_dragging = False
        self.last_mouse_pos = None
        
        # Layer rename state
        self.layer_rename_index = -1
        self.layer_rename_text = ""
        self.layer_rename_cursor = 0
        self.last_click_time = 0
        self.last_click_layer = -1

        # User preferences path
        self.prefs_path = os.path.join(self.save_dir, "preferences.json")
        self.load_preferences()
        self.load_stamps_from_file()
        
        # Initialize file management
        self.update_window_title()
        self.check_for_auto_save_recovery()
        self.cleanup_auto_save_files()

    # --------------------------- Layout ---------------------------
    def compute_layout(self):
        win_w, win_h = self.screen.get_size()
        self.WIDTH, self.HEIGHT = win_w, win_h

        # Update TOP_H based on menu bar visibility
        self.TOP_H = (self.MENU_BAR_H + 40) if self.show_menu_bar else 40

        self.top_rect = pygame.Rect(0, 0, self.WIDTH, self.TOP_H)
        self.status_rect = pygame.Rect(0, self.HEIGHT - self.STATUS_H, self.WIDTH, self.STATUS_H)
        content_top = self.top_rect.bottom
        content_bottom = self.status_rect.top
        content_h = max(0, content_bottom - content_top)

        # Ensure collapsed panels have minimum width for header visibility
        collapsed_width = 100  # Minimum width to show panel header when collapsed
        desired_left = collapsed_width if self.left_collapsed else self.left_w
        desired_right = 0 if self.right_w <= 0 else self.right_w
        canvas_w = self.WIDTH - desired_left - desired_right
        if canvas_w < self.min_canvas_w:
            deficit = self.min_canvas_w - canvas_w
            take_left = min(deficit // 2, max(0, desired_left - self.min_left))
            desired_left -= take_left
            deficit -= take_left
            take_right = min(deficit, max(0, desired_right - self.min_right))
            desired_right -= take_right
        left_w = max(0, desired_left)
        right_w = max(0, desired_right)

        self.left_rect = pygame.Rect(0, content_top, left_w, content_h)
        self.right_rect = pygame.Rect(self.WIDTH - right_w, content_top, right_w, content_h)
        self.canvas_rect = pygame.Rect(self.left_rect.right, content_top, max(0, self.WIDTH - left_w - right_w), content_h)

        if self.right_rect.width > 0:
            if not self.right_layers_collapsed and not self.right_props_collapsed:
                layers_h = int(self.right_rect.height * self.right_split)
                props_h = self.right_rect.height - layers_h
            elif self.right_layers_collapsed and not self.right_props_collapsed:
                layers_h = self.panel_header_h
                props_h = self.right_rect.height - layers_h
            elif not self.right_layers_collapsed and self.right_props_collapsed:
                layers_h = self.right_rect.height - self.panel_header_h
                props_h = self.panel_header_h
            else:
                layers_h = self.panel_header_h
                props_h = self.right_rect.height - layers_h
            self.right_layers_rect = pygame.Rect(self.right_rect.x, self.right_rect.y, self.right_rect.width, max(0, layers_h))
            self.right_props_rect = pygame.Rect(self.right_rect.x, self.right_layers_rect.bottom, self.right_rect.width, max(0, props_h))
        else:
            self.right_layers_rect = pygame.Rect(0, 0, 0, 0)
            self.right_props_rect = pygame.Rect(0, 0, 0, 0)

    # --------------------------- Coord helpers ---------------------------
    def tile_to_screen(self, cx: int, cy: int) -> Tuple[int, int]:
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        x = self.canvas_rect.x + cx * ts - self.scroll_x
        y = self.canvas_rect.y + cy * ts - self.scroll_y
        return x, y

    def screen_to_tile(self, sx: int, sy: int) -> Tuple[int, int]:
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        cx = (sx - self.canvas_rect.x + self.scroll_x) // ts
        cy = (sy - self.canvas_rect.y + self.scroll_y) // ts
        return int(cx), int(cy)

    # --------------------------- Drawing ---------------------------
    def draw_grid(self):
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        canvas_w = max(0, self.canvas_rect.width)
        canvas_h = max(0, self.canvas_rect.height)
        cols_visible = (canvas_w + ts - 1) // ts + 1
        rows_visible = (canvas_h + ts - 1) // ts + 1
        start_c = max(0, int(self.scroll_x // ts))
        start_r = max(0, int(self.scroll_y // ts))
        end_c = min(self.map_cols, start_c + cols_visible)
        end_r = min(self.map_rows, start_r + rows_visible)

        for c in range(start_c, end_c + 1):
            x = self.canvas_rect.x + c * ts - self.scroll_x
            pygame.draw.line(self.screen, self.GRID, (x, self.canvas_rect.y), (x, self.canvas_rect.bottom))
        for r in range(start_r, end_r + 1):
            y = self.canvas_rect.y + r * ts - self.scroll_y
            pygame.draw.line(self.screen, self.GRID, (self.canvas_rect.x, y), (self.canvas_rect.right, y))

    def draw_layers(self):
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        canvas_w = max(0, self.canvas_rect.width)
        canvas_h = max(0, self.canvas_rect.height)
        cols_visible = (canvas_w + ts - 1) // ts + 1
        rows_visible = (canvas_h + ts - 1) // ts + 1
        start_c = max(0, int(self.scroll_x // ts))
        start_r = max(0, int(self.scroll_y // ts))
        end_c = min(self.map_cols, start_c + cols_visible)
        end_r = min(self.map_rows, start_r + rows_visible)

        for li, layer in enumerate(self.layers):
            if not layer.visible:
                continue
            for ry in range(start_r, end_r):
                row = layer.data[ry]
                for rx in range(start_c, end_c):
                    idx = row[rx]
                    if idx < 0 or idx >= len(self.tiles):
                        continue
                    tile = self.tiles[idx]
                    if self.VIEW_SCALE != 1:
                        tw = int(tile.get_width() * self.VIEW_SCALE)
                        th = int(tile.get_height() * self.VIEW_SCALE)
                        tile = pygame.transform.smoothscale(tile, (max(1, tw), max(1, th)))
                    sx = self.canvas_rect.x + rx * ts - self.scroll_x
                    sy = self.canvas_rect.y + ry * ts - self.scroll_y
                    self.screen.blit(tile, (sx, sy))
        
        # Draw shape preview
        self.draw_shape_preview()
        
        # Draw multi-tile brush preview
        self.draw_multi_tile_brush_preview()
        
        # Draw collision overlay
        self.draw_collision_overlay()
        
        # Draw objects (above tiles but below UI)
        self.draw_objects()

    def draw_panel_header(self, rect: pygame.Rect, title: str, collapsed: bool, show_gear: bool = False):
        if rect.height <= 0:  # Remove width check to always show header
            return None
        header_rect = pygame.Rect(rect.x, rect.y, max(rect.w, 100), self.panel_header_h)  # Ensure minimum width
        pygame.draw.rect(self.screen, self.HEADER_BG, header_rect)
        pygame.draw.line(self.screen, self.HEADER_ACCENT, (header_rect.x, header_rect.y + self.panel_header_h - 1), (header_rect.right, header_rect.y + self.panel_header_h - 1))
        
        # Use standardized triangle icons for collapse/expand state
        triangle_key = 'triangle_right' if collapsed else 'triangle_down'
        triangle_icon = render_icon(self.FONT, triangle_key, (235, 238, 245))
        
        # Render triangle + title
        self.screen.blit(triangle_icon, (header_rect.x + 8, header_rect.y + 6))
        title_x = header_rect.x + 8 + triangle_icon.get_width() + 4
        title_text = self.FONT.render(title, True, (235, 238, 245))
        self.screen.blit(title_text, (title_x, header_rect.y + 6))
        
        # Draw gear icon for settings if requested
        gear_rect = None
        if show_gear and not collapsed:  # Only show gear when panel is expanded
            gear_text = render_icon(self.FONT, 'gear', (200, 205, 215), size=16)
            gear_rect = pygame.Rect(header_rect.right - 24, header_rect.y + 4, 20, 20)
            self.screen.blit(gear_text, (gear_rect.x + 2, gear_rect.y + 2))
            # Draw subtle hover effect and tooltip
            mx, my = pygame.mouse.get_pos()
            if gear_rect.collidepoint(mx, my):
                pygame.draw.rect(self.screen, (60, 65, 75), gear_rect, border_radius=3)
                self.screen.blit(gear_text, (gear_rect.x + 2, gear_rect.y + 2))
                # Show tooltip
                tooltip_text = "Tileset Settings (Ctrl+T)"
                tooltip_surf = self.FONT.render(tooltip_text, True, (230, 235, 240))
                tooltip_w, tooltip_h = tooltip_surf.get_size()
                tooltip_x = gear_rect.x - tooltip_w + 20
                tooltip_y = gear_rect.bottom + 4
                pygame.draw.rect(self.screen, (40, 44, 52), (tooltip_x - 4, tooltip_y - 2, tooltip_w + 8, tooltip_h + 4), border_radius=4)
                pygame.draw.rect(self.screen, (70, 75, 85), (tooltip_x - 4, tooltip_y - 2, tooltip_w + 8, tooltip_h + 4), 1, border_radius=4)
                self.screen.blit(tooltip_surf, (tooltip_x, tooltip_y))
        
        return gear_rect

    def draw_palette_panel(self):
        rect = self.left_rect
        if rect.width <= 0:
            return
        pygame.draw.rect(self.screen, self.PANEL_BG, rect)
        
        # Draw tabs instead of single header
        if self.left_collapsed:
            self.gear_rect = self.draw_panel_header(rect, f"{self.object_mode.title()}", True, show_gear=True)
            return  # Don't draw content when collapsed
        
        # Draw tab interface
        tab_height = 24
        tab_y = rect.y + self.panel_header_h
        tab_rect = pygame.Rect(rect.x, tab_y, rect.w, tab_height)
        pygame.draw.rect(self.screen, self.HEADER_BG, tab_rect)
        
        # Clear tab rects for click detection
        self.tab_rects = {}
        
        # Draw tabs
        tab_width = rect.w // 2
        tabs = [("tiles", "Tiles"), ("objects", "Objects")]
        
        for i, (tab_id, tab_label) in enumerate(tabs):
            tab_x = rect.x + i * tab_width
            tab_item_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            self.tab_rects[tab_id] = tab_item_rect
            
            # Tab colors
            is_active = (tab_id == self.object_mode)
            bg_color = (45, 48, 54) if is_active else (32, 35, 41)
            text_color = (235, 238, 245) if is_active else (170, 175, 185)
            
            # Draw tab background
            pygame.draw.rect(self.screen, bg_color, tab_item_rect)
            
            # Draw tab border (bottom line for inactive tabs)
            if not is_active:
                pygame.draw.line(self.screen, self.HEADER_ACCENT, (tab_x, tab_y + tab_height - 1), (tab_x + tab_width, tab_y + tab_height - 1))
            
            # Draw tab text
            text_surf = self.FONT.render(tab_label, True, text_color)
            text_rect = text_surf.get_rect(center=tab_item_rect.center)
            self.screen.blit(text_surf, text_rect)
        
        # Draw gear icon in top right
        gear_x = rect.right - 24
        gear_y = rect.y + 6
        self.gear_rect = pygame.Rect(gear_x, gear_y, 16, 16)
        gear_icon = render_icon(self.FONT, 'gear', (200, 205, 215))
        self.screen.blit(gear_icon, self.gear_rect)
        
        # Content area below tabs
        content_y = tab_y + tab_height
        content = pygame.Rect(rect.x, content_y, rect.w, rect.h - (content_y - rect.y))
        
        # Draw content based on active tab
        if self.object_mode == "tiles":
            self.draw_tiles_content(content)
        elif self.object_mode == "objects":
            self.draw_objects_content(content)
    
    def draw_tiles_content(self, content: pygame.Rect):
        """Draw tiles palette content"""
        pad = 4
        cell = self.TILE_SIZE * self.PALETTE_SCALE + pad
        cols = max(1, (content.w - pad) // cell)
        x0, y0 = content.x + pad, content.y + pad - self.palette_scroll
        
        for i, tile in enumerate(self.tiles):
            col = i % cols
            row = i // cols
            dx = x0 + col * cell
            dy = y0 + row * cell
            
            if dy < content.bottom and dy > content.y - cell:
                pygame.draw.rect(self.screen, self.GRID, (dx - 1, dy - 1, cell - pad + 2, cell - pad + 2), 1)
                t = tile
                if self.PALETTE_SCALE != 1:
                    t = pygame.transform.scale(tile, (tile.get_width() * self.PALETTE_SCALE, tile.get_height() * self.PALETTE_SCALE))
                self.screen.blit(t, (dx, dy))
            
            if self.selected_tile == i:
                pygame.draw.rect(self.screen, self.SELECT, (dx - 2, dy - 2, cell - pad + 4, cell - pad + 4), 2)
            
            # Draw multi-tile selection indicator
            if i in self.multi_tile_selection:
                pygame.draw.rect(self.screen, self.ACTIVE, (dx - 2, dy - 2, cell - pad + 4, cell - pad + 4), 2)
                # Add a small indicator in the corner
                pygame.draw.circle(self.screen, self.ACTIVE, (dx + cell - pad - 6, dy + 6), 3)
        
        # Scrollbar for tiles
        total_rows = (len(self.tiles) + cols - 1) // cols
        content_h = total_rows * cell
        if content_h > content.h:
            bar_h = max(24, int(content.h * content.h / content_h))
            max_scroll = content_h - content.h
            ratio = 0 if max_scroll == 0 else max(0, min(1, self.palette_scroll / max_scroll))
            bar_y = content.y + int((content.h - bar_h) * ratio)
            pygame.draw.rect(self.screen, (90, 95, 105), (content.right - 8, bar_y, 6, bar_h), border_radius=3)
    
    def draw_objects_content(self, content: pygame.Rect):
        """Draw objects palette content"""
        pad = 8
        cell_size = 48
        cell = cell_size + pad
        
        # Calculate layout
        cols = max(1, (content.w - pad) // cell)
        x0, y0 = content.x + pad, content.y + pad
        
        for i, (obj_type, display_name, color) in enumerate(self.OBJECT_TYPES):
            col = i % cols
            row = i // cols
            dx = x0 + col * cell
            dy = y0 + row * cell
            
            if dy < content.bottom and dy > content.y - cell:
                # Draw object type as colored square
                obj_rect = pygame.Rect(dx, dy, cell_size, cell_size)
                pygame.draw.rect(self.screen, color, obj_rect)
                pygame.draw.rect(self.screen, self.GRID, obj_rect, 2)
                
                # Draw selection indicator
                if self.selected_object_type == i:
                    pygame.draw.rect(self.screen, self.SELECT, (dx - 2, dy - 2, cell_size + 4, cell_size + 4), 3)
                    
                    # Draw persistent mode indicator
                    if self.persistent_object_mode:
                        # Draw a small "P" indicator in the corner
                        small_font = getattr(self, 'SMALL_FONT', self.FONT)
                        p_text = small_font.render("P", True, (255, 255, 80))
                        self.screen.blit(p_text, (dx + cell_size - 12, dy + 2))
                
                # Draw object type label
                label_text = self.FONT.render(display_name, True, (255, 255, 255))
                label_rect = label_text.get_rect(center=(dx + cell_size // 2, dy + cell_size // 2))
                
                # Add background for text readability
                bg_rect = label_rect.copy()
                bg_rect.inflate(4, 2)
                pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
                self.screen.blit(label_text, label_rect)
                
                # Draw count below
                count = sum(1 for obj in self.objects if obj.object_type == obj_type)
                if count > 0:
                    count_text = self.FONT.render(f"({count})", True, (200, 200, 200))
                    count_rect = count_text.get_rect(center=(dx + cell_size // 2, dy + cell_size + 12))
                    self.screen.blit(count_text, count_rect)
        
        # Draw help text at the bottom of the objects panel
        if content.h > 200:  # Only show if panel is tall enough
            help_y = content.bottom - 80
            help_texts = [
                "Click: Select object type & place",
                "Shift+Click: Toggle persistent mode",
                "Ctrl+C/X/V: Copy/Cut/Paste objects",
                "Ctrl+Click objects: Multi-select"
            ]
            for i, help_text in enumerate(help_texts):
                text = self.FONT.render(help_text, True, (180, 185, 190))
                self.screen.blit(text, (content.x + pad, help_y + i * 16))

    def show_collision_type_menu(self, mx: int, my: int):
        """Show dropdown menu for collision type selection"""
        self.collision_menu_pos = (mx, my)
        self.show_collision_menu = True
    
    def draw_collision_type_menu(self):
        """Draw the collision type dropdown menu"""
        if not hasattr(self, 'show_collision_menu') or not self.show_collision_menu:
            return
        
        if not hasattr(self, 'collision_menu_pos'):
            return
        
        mx, my = self.collision_menu_pos
        menu_w = 200
        item_h = 22
        menu_h = len(self.COLLISION_TYPES) * item_h + 4
        
        # Position menu to fit on screen
        menu_x = min(mx, self.WIDTH - menu_w)
        menu_y = min(my, self.HEIGHT - menu_h)
        
        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        
        # Draw menu background
        pygame.draw.rect(self.screen, (45, 48, 54), menu_rect)
        pygame.draw.rect(self.screen, (80, 84, 92), menu_rect, 1)
        
        # Draw menu items
        self._collision_menu_hitboxes = []
        for i, (type_id, display_name, description) in enumerate(self.COLLISION_TYPES):
            item_y = menu_y + 2 + i * item_h
            item_rect = pygame.Rect(menu_x + 2, item_y, menu_w - 4, item_h - 1)
            
            # Highlight on hover
            mouse_pos = pygame.mouse.get_pos()
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (60, 65, 75), item_rect)
            
            # Color indicator
            color = self.get_collision_color(type_id)
            color_rect = pygame.Rect(item_rect.x + 4, item_rect.y + 4, 14, 14)
            pygame.draw.rect(self.screen, color, color_rect)
            pygame.draw.rect(self.screen, (100, 104, 112), color_rect, 1)
            
            # Display name
            text = self.FONT.render(display_name, True, (230, 235, 240))
            self.screen.blit(text, (item_rect.x + 22, item_rect.y + 3))
            
            self._collision_menu_hitboxes.append((item_rect, type_id))

    def handle_collision_menu_click(self, mx: int, my: int) -> bool:
        """Handle click on collision type menu. Returns True if handled."""
        if not hasattr(self, 'show_collision_menu') or not self.show_collision_menu:
            return False
        
        if hasattr(self, '_collision_menu_hitboxes'):
            for item_rect, collision_type in self._collision_menu_hitboxes:
                if item_rect.collidepoint(mx, my):
                    # Set collision type for selected tile
                    if self.selected_tile is not None:
                        self.set_tile_collision_type(self.selected_tile, collision_type)
                    self.show_collision_menu = False
                    return True
        
        # Click outside menu - close it
        self.show_collision_menu = False
        return False
    
    def show_object_type_menu(self, mx: int, my: int):
        """Show dropdown menu for object type selection"""
        self.object_type_menu_pos = (mx, my)
        self.object_type_menu_open = True
    
    def draw_object_type_menu(self):
        """Draw object type selection dropdown menu"""
        if not hasattr(self, 'object_type_menu_open') or not self.object_type_menu_open:
            return
        
        if not hasattr(self, 'object_type_menu_pos'):
            return
        
        mx, my = self.object_type_menu_pos
        
        # Menu dimensions
        menu_w = 120
        item_h = 24
        menu_h = len(self.OBJECT_TYPES) * item_h + 8  # 4px padding top/bottom
        
        # Ensure menu doesn't go off screen
        menu_x = min(mx, self.WIDTH - menu_w)
        menu_y = min(my, self.HEIGHT - menu_h)
        
        # Draw menu background
        menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(self.screen, (45, 50, 58), menu_rect)
        pygame.draw.rect(self.screen, (70, 75, 85), menu_rect, 1)
        
        # Draw menu items
        self._object_type_menu_hitboxes = []
        y = menu_y + 4
        
        for obj_type, display_name, color in self.OBJECT_TYPES:
            item_rect = pygame.Rect(menu_x + 4, y, menu_w - 8, item_h - 2)
            
            # Highlight current type
            if self.selected_object and obj_type == self.selected_object.object_type:
                pygame.draw.rect(self.screen, (65, 70, 80), item_rect)
            
            # Color indicator
            color_rect = pygame.Rect(item_rect.x + 4, item_rect.y + 4, 16, 16)
            pygame.draw.rect(self.screen, color, color_rect)
            pygame.draw.rect(self.screen, (80, 85, 95), color_rect, 1)
            
            # Type name
            text = self.FONT.render(display_name, True, (230, 235, 240))
            self.screen.blit(text, (item_rect.x + 24, item_rect.y + 4))
            
            self._object_type_menu_hitboxes.append((item_rect, obj_type))
            y += item_h
    
    def handle_object_type_menu_click(self, mx: int, my: int) -> bool:
        """Handle clicks on object type menu"""
        if not hasattr(self, 'object_type_menu_open') or not self.object_type_menu_open:
            return False
        
        if hasattr(self, '_object_type_menu_hitboxes'):
            for item_rect, object_type in self._object_type_menu_hitboxes:
                if item_rect.collidepoint(mx, my):
                    # Change object type
                    if self.selected_object:
                        self.selected_object.object_type = object_type
                        # Update color too
                        for obj_type, display_name, color in self.OBJECT_TYPES:
                            if obj_type == object_type:
                                self.selected_object.color = color
                                break
                        self.mark_modified()
                    self.object_type_menu_open = False
                    return True
        
        # Click outside menu - close it
        self.object_type_menu_open = False
        return True

    def draw_hud(self):
        # Draw menu bar if enabled
        if self.show_menu_bar:
            self.draw_menu_bar()
        
        # Draw existing toolbar below menu bar or at top if no menu
        menu_height = self.MENU_BAR_H if self.show_menu_bar else 0
        toolbar_rect = pygame.Rect(0, menu_height, self.WIDTH, self.TOP_H - menu_height)
        
        pygame.draw.rect(self.screen, self.HEADER_BG, toolbar_rect)
        pygame.draw.line(self.screen, self.HEADER_ACCENT, (toolbar_rect.x, toolbar_rect.bottom - 1), (toolbar_rect.right, toolbar_rect.bottom - 1))

        # Build toolbar with hover/disabled states
        self._toolbar_hitboxes = []
        self._toolbar_tooltips = {}
        mx, my = pygame.mouse.get_pos()
        x = toolbar_rect.x + 8
        y = toolbar_rect.y + 6

        # Compute zoom boundary disables
        cur_scale = self.VIEW_SCALE
        nearest_idx = min(range(len(self.zoom_levels)), key=lambda i: abs(self.zoom_levels[i] - cur_scale))
        can_zoom_out = nearest_idx > 0
        can_zoom_in = nearest_idx < len(self.zoom_levels) - 1
        can_fit = self.canvas_rect.width > 0 and self.canvas_rect.height > 0
        can_paint = self.selected_tile is not None

        def add_btn(label: str, cmd: Optional[str], disabled: bool = False, is_active: bool = False):
            nonlocal x
            if label == "|":
                x += 8
                return
            w = max(48, self.FONT.size(label)[0] + 14)
            rect = pygame.Rect(x, y, w, toolbar_rect.h - 12)
            hovered = rect.collidepoint(mx, my)
            # Colors
            base = (70, 74, 82)
            active = (95, 100, 110)
            hover = (82, 86, 94)
            disabled_bg = (50, 53, 59)
            border = (50, 54, 60)
            text_on = (230, 235, 240)
            text_off = (160, 165, 175)
            if disabled:
                color = disabled_bg
                text = text_off
            else:
                color = active if is_active else (hover if hovered else base)
                text = text_on
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=4)
            self.screen.blit(self.FONT.render(label, True, text), (rect.x + 7, rect.y + 4))
            self._toolbar_hitboxes.append((rect, cmd, disabled))
            if cmd:
                tip = {
                    "new": "New Map (Ctrl+N)",
                    "open": "Open Map (Ctrl+O)",
                    "save": "Save Map (Ctrl+S)",
                    "saveas": "Save As (Ctrl+Shift+S)",
                    "undo": f"Undo (Ctrl+Z)" + (f" - {self.get_undo_description()}" if self.can_undo() else ""),
                    "redo": f"Redo (Ctrl+Y)" + (f" - {self.get_redo_description()}" if self.can_redo() else ""),
                    "zoom_in": "Zoom In (Ctrl++)",
                    "zoom_out": "Zoom Out (Ctrl+-)",
                    "zoom_fit": "Fit to Window (Ctrl+0)",
                    "zoom_menu": "Zoom Presets",
                    "zoom_actual": "Actual Size (Ctrl+1)",
                    "tool_paint": "Paint (P)",
                    "tool_erase": "Erase (E)",
                    "tool_pick": "Eyedropper (I)",
                    "tool_flood_fill": "Flood Fill (F)",
                    "tool_select": "Select (S) - Drag to select, Ctrl+C/X/V to copy/cut/paste",
                }.get(cmd)
                if tip:
                    self._toolbar_tooltips[cmd] = (tip, rect)
            x += w + 6

        # Left group: file
        add_btn("New", "new")
        add_btn("Open", "open")
        add_btn("Save", "save")
        add_btn("Save As", "saveas")
        add_btn("|", None)
        # Import/Export group
        add_btn("Export", "export")
        add_btn("Import", "import")
        add_btn("|", None)
        # Undo/Redo group
        add_btn("Undo", "undo", disabled=not self.can_undo())
        add_btn("Redo", "redo", disabled=not self.can_redo())
        add_btn("|", None)
        # View group: zoom controls
        add_btn("Zoom -", "zoom_out", disabled=not can_zoom_out)
        add_btn("Zoom +", "zoom_in", disabled=not can_zoom_in)
        add_btn("Fit", "zoom_fit", disabled=not can_fit)
        # Zoom dropdown showing current percent
        zoom_label = f"{int(self.VIEW_SCALE * 100)}% \u25BE"  # ▼
        add_btn(zoom_label, "zoom_menu", disabled=not can_fit)
        add_btn("1:1", "zoom_actual")
        add_btn("|", None)
        # Tools
        add_btn("Paint", "tool_paint", disabled=not can_paint, is_active=self.tool == "paint")
        add_btn("Erase", "tool_erase", is_active=self.tool == "erase")
        add_btn("Pick", "tool_pick", is_active=self.tool == "pick")
        add_btn("Fill", "tool_flood_fill", disabled=not can_paint, is_active=self.tool == "flood_fill")
        add_btn("Select", "tool_select", is_active=self.tool == "select")
        add_btn("|", None)
        # Shape tools
        add_btn("Line", "tool_line", disabled=not can_paint, is_active=self.tool == "line")
        add_btn("Rect", "tool_rectangle", disabled=not can_paint, is_active=self.tool == "rectangle")
        add_btn("Circle", "tool_circle", disabled=not can_paint, is_active=self.tool == "circle")

        # Note: Zoom dropdown menu is now drawn separately after all other UI elements

        # Status bar
        pygame.draw.rect(self.screen, self.STATUS_BG, self.status_rect)
        pygame.draw.line(self.screen, (45, 48, 55), (self.status_rect.x, self.status_rect.y), (self.status_rect.right, self.status_rect.y))
        mx, my = pygame.mouse.get_pos()
        grid = "-,-"
        if self.canvas_rect.collidepoint(mx, my):
            cx, cy = self.screen_to_tile(mx, my)
            grid = f"{cx},{cy}"
        zoom_pct = int(self.VIEW_SCALE * 100)
        
        # Add undo/redo info
        undo_info = ""
        if self.can_undo() or self.can_redo():
            undo_count = self.history_index + 1
            total_count = len(self.command_history)
            undo_info = f" | History: {undo_count}/{total_count}"
        
        # Add auto-save indicator
        auto_save_info = ""
        if self.auto_save_enabled and self.is_modified:
            if self.auto_save_indicator:
                auto_save_info = " | AutoSave: pending"
            else:
                time_since_save = time.time() - self.last_auto_save
                if time_since_save > self.auto_save_interval * 0.8:  # Show countdown in last 20%
                    remaining = max(0, int(self.auto_save_interval - time_since_save))
                    auto_save_info = f" | AutoSave: {remaining}s"
        
        left = f"Cursor: {grid} | Screen: {mx},{my}{undo_info}{auto_save_info}"
        
        # Add selection info to center
        selection_info = ""
        if self.has_selection or self.selection_dragging:
            min_x = min(self.selection_start_x, self.selection_end_x)
            max_x = max(self.selection_start_x, self.selection_end_x)
            min_y = min(self.selection_start_y, self.selection_end_y)
            max_y = max(self.selection_start_y, self.selection_end_y)
            sel_w = max_x - min_x + 1
            sel_h = max_y - min_y + 1
            selection_info = f" | Selection: {sel_w}x{sel_h} tiles"
        elif self.paste_preview and self.clipboard:
            selection_info = f" | Paste: {self.clipboard['width']}x{self.clipboard['height']} at ({self.paste_x},{self.paste_y})"
        
        # Add object mode status info
        object_info = ""
        if self.object_mode == "objects":
            if self.object_paste_mode and self.copied_objects:
                object_info = f" | Paste Mode: {len(self.copied_objects)} objects"
            elif self.object_placement_mode:
                obj_type_name = self.OBJECT_TYPES[self.selected_object_type][1] if self.selected_object_type < len(self.OBJECT_TYPES) else "Unknown"
                persistent_text = " (Persistent)" if self.persistent_object_mode else ""
                object_info = f" | Placing: {obj_type_name}{persistent_text}"
            elif self.selected_objects:
                object_info = f" | Selected: {len(self.selected_objects)} objects"
            elif self.copied_objects:
                object_info = f" | Clipboard: {len(self.copied_objects)} objects"
            
        center = f"Zoom: {zoom_pct}% | Map: {self.map_cols}x{self.map_rows} tiles{selection_info}{object_info}"
        
        # Add splitter hover info
        if hasattr(self, 'splitter_hover') and self.splitter_hover:
            splitter_help = {
                'left': 'Drag to resize tileset panel width',
                'right': 'Drag to resize properties panel width', 
                'right_inner': 'Drag to resize layer/properties panel heights'
            }
            if self.splitter_hover in splitter_help:
                center += f" | {splitter_help[self.splitter_hover]}"
        
        # Add multi-tile selection help when Ctrl is held
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            center += " | Hold Ctrl + Click tiles to create multi-tile brush"
        
        # Build selection info for status bar
        if self.multi_tile_mode and self.multi_tile_selection:
            sel_info = f"{len(self.multi_tile_selection)} tiles"
        else:
            sel_info = str(self.selected_tile) if self.selected_tile is not None else '-'
        
        # Current mode info for status bar
        if self.object_mode == "objects":
            if self.selected_object_type < len(self.OBJECT_TYPES):
                obj_type_name = self.OBJECT_TYPES[self.selected_object_type][1]
                mode_info = f"Objects: {obj_type_name}"
            else:
                mode_info = "Objects"
        else:
            mode_info = f"Tool: {self.tool}"
        
        right = f"{mode_info} | Layer: {self.layers[self.current_layer].name} | Sel: {sel_info} | TS:{self.TILE_SIZE} M:{self.margin} S:{self.spacing}"
        self.screen.blit(self.FONT.render(left, True, self.STATUS_FG), (self.status_rect.x + 8, self.status_rect.y + 4))
        if self.top_rect.collidepoint(mx, my):
            for cmd, (tip, rect) in self._toolbar_tooltips.items():
                if rect.collidepoint(mx, my):
                    tw, th = self.FONT.size(tip)
                    tx = min(rect.x, self.WIDTH - tw - 8)
                    ty = rect.bottom + 4
                    pygame.draw.rect(self.screen, (40, 44, 52), (tx - 4, ty - 2, tw + 8, th + 4), border_radius=4)
                    pygame.draw.rect(self.screen, (70, 75, 85), (tx - 4, ty - 2, tw + 8, th + 4), 1, border_radius=4)
                    self.screen.blit(self.FONT.render(tip, True, (230, 235, 240)), (tx, ty))
                    break
        center_w = self.FONT.size(center)[0]
        self.screen.blit(self.FONT.render(center, True, self.STATUS_FG), (self.status_rect.centerx - center_w // 2, self.status_rect.y + 4))
        r_w = self.FONT.size(right)[0]
        self.screen.blit(self.FONT.render(right, True, self.STATUS_FG), (self.status_rect.right - r_w - 8, self.status_rect.y + 4))
        
    def draw_splitter_handles(self):
        """Draw visual feedback for resizable panel splitters"""
        mx, my = pygame.mouse.get_pos()
        
        # Define splitter zones
        self.splitter_zones = {}
        
        # Left panel splitter (tileset panel resizer)
        if self.left_rect.width > 0 and self.canvas_rect.width > 0:
            left_edge = self.left_rect.right
            splitter_rect = pygame.Rect(left_edge - 4, self.left_rect.y, 8, self.left_rect.height)
            self.splitter_zones['left'] = splitter_rect
            
            # Check if mouse is hovering
            is_hovering = splitter_rect.collidepoint(mx, my)
            is_dragging = self.drag_left_split
            
            if is_hovering or is_dragging:
                # Draw hover/drag visual feedback
                color = (120, 200, 255) if is_dragging else (80, 170, 255)
                pygame.draw.rect(self.screen, color, splitter_rect)
                
                # Draw resize icon in center
                icon_y = splitter_rect.centery - 8
                for i in range(3):
                    y_pos = icon_y + i * 6
                    pygame.draw.circle(self.screen, (240, 245, 250), (splitter_rect.centerx - 2, y_pos), 1)
                    pygame.draw.circle(self.screen, (240, 245, 250), (splitter_rect.centerx + 2, y_pos), 1)
            else:
                # Draw subtle splitter line
                pygame.draw.line(self.screen, self.SPLITTER, 
                               (left_edge, self.left_rect.y), 
                               (left_edge, self.left_rect.bottom))
        
        # Right panel splitter
        if self.right_rect.width > 0 and self.canvas_rect.width > 0:
            right_edge = self.right_rect.left
            splitter_rect = pygame.Rect(right_edge - 4, self.right_rect.y, 8, self.right_rect.height)
            self.splitter_zones['right'] = splitter_rect
            
            is_hovering = splitter_rect.collidepoint(mx, my)
            is_dragging = self.drag_right_split
            
            if is_hovering or is_dragging:
                color = (120, 200, 255) if is_dragging else (80, 170, 255)
                pygame.draw.rect(self.screen, color, splitter_rect)
                
                # Draw resize icon
                icon_y = splitter_rect.centery - 8
                for i in range(3):
                    y_pos = icon_y + i * 6
                    pygame.draw.circle(self.screen, (240, 245, 250), (splitter_rect.centerx - 2, y_pos), 1)
                    pygame.draw.circle(self.screen, (240, 245, 250), (splitter_rect.centerx + 2, y_pos), 1)
            else:
                pygame.draw.line(self.screen, self.SPLITTER, 
                               (right_edge, self.right_rect.y), 
                               (right_edge, self.right_rect.bottom))
        
        # Right inner splitter (horizontal between layers and props)
        if self.right_rect.width > 0:
            inner_y = self.right_layers_rect.bottom
            splitter_rect = pygame.Rect(self.right_rect.x, inner_y - 4, self.right_rect.width, 8)
            self.splitter_zones['right_inner'] = splitter_rect
            
            is_hovering = splitter_rect.collidepoint(mx, my)
            is_dragging = self.drag_right_inner_split
            
            if is_hovering or is_dragging:
                color = (120, 200, 255) if is_dragging else (80, 170, 255)
                pygame.draw.rect(self.screen, color, splitter_rect)
                
                # Draw horizontal resize icon
                icon_x = splitter_rect.centerx - 8
                for i in range(3):
                    x_pos = icon_x + i * 6
                    pygame.draw.circle(self.screen, (240, 245, 250), (x_pos, splitter_rect.centery - 2), 1)
                    pygame.draw.circle(self.screen, (240, 245, 250), (x_pos, splitter_rect.centery + 2), 1)
            else:
                pygame.draw.line(self.screen, self.SPLITTER, 
                               (self.right_rect.x, inner_y), 
                               (self.right_rect.right, inner_y))

    def draw_menu_bar(self):
        """Draw the professional menu bar with File, Edit, View, Tools menus"""
        if not self.show_menu_bar:
            return
            
        menu_rect = pygame.Rect(0, 0, self.WIDTH, self.MENU_BAR_H)
        
        # Background
        pygame.draw.rect(self.screen, self.HEADER_BG, menu_rect)
        pygame.draw.line(self.screen, self.HEADER_ACCENT, (0, menu_rect.bottom - 1), (self.WIDTH, menu_rect.bottom - 1))
        
        # Menu items
        self._menu_hitboxes = {}
        self._submenu_hitboxes = []
        
        mx, my = pygame.mouse.get_pos()
        x = 8
        y = 4
        
        menus = [
            ("File", "file"),
            ("Edit", "edit"), 
            ("View", "view"),
            ("Tools", "tools"),
            ("Help", "help")
        ]
        
        for label, menu_id in menus:
            w = self.FONT.size(label)[0] + 16
            rect = pygame.Rect(x, y, w, self.MENU_BAR_H - 8)
            hovered = rect.collidepoint(mx, my) or self.active_menu == menu_id
            
            # Colors
            text_color = (240, 245, 250) if hovered else (200, 205, 215)
            if hovered:
                pygame.draw.rect(self.screen, (50, 54, 62), rect, border_radius=4)
            
            # Draw menu text
            self.screen.blit(self.FONT.render(label, True, text_color), (x + 8, y + 4))
            self._menu_hitboxes[menu_id] = rect
            
            x += w + 4
            
        # Note: Dropdown menu is now drawn separately after all other UI elements
    
    def draw_zoom_menu(self):
        """Draw the zoom dropdown menu (on top of everything)"""
        if not self.show_zoom_menu or not self._zoom_menu_anchor:
            return
            
        mx, my = pygame.mouse.get_pos()
        self._zoom_menu_hitboxes.clear()
        
        presets = [0.25, 0.5, 1.0, 2.0, 4.0]
        item_h = 22
        pad = 6
        maxw = 0
        labels = [f"{int(p*100)}%" for p in presets]
        for t in labels:
            maxw = max(maxw, self.FONT.size(t)[0])
        menu_w = max(80, maxw + 16)
        menu_h = item_h * len(presets) + 8
        mx0 = self._zoom_menu_anchor.x
        my0 = self._zoom_menu_anchor.bottom + 4
        menu_rect = pygame.Rect(mx0, my0, menu_w, menu_h)
        # Keep inside window horizontally
        if menu_rect.right > self.WIDTH - 6:
            menu_rect.x = self.WIDTH - menu_rect.w - 6
        # Draw
        pygame.draw.rect(self.screen, (40, 44, 52), menu_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 75, 85), menu_rect, 1, border_radius=6)
        iy = menu_rect.y + 4
        for p, label in zip(presets, labels):
            r = pygame.Rect(menu_rect.x + 4, iy, menu_rect.w - 8, item_h)
            if r.collidepoint(mx, my):
                pygame.draw.rect(self.screen, (60, 65, 75), r, border_radius=4)
            txt_col = (230, 235, 240) if abs(self.VIEW_SCALE - p) > 1e-6 else (120, 200, 255)
            self.screen.blit(self.FONT.render(label, True, txt_col), (r.x + 6, r.y + 2))
            self._zoom_menu_hitboxes.append((r, p))
            iy += item_h
    
    def draw_dropdown_menu(self):
        """Draw the dropdown submenu for the active menu"""
        if not self.active_menu or self.active_menu not in self._menu_hitboxes:
            return
            
        anchor_rect = self._menu_hitboxes[self.active_menu]
        mx, my = pygame.mouse.get_pos()
        
        # Define menu items based on active menu
        menu_items = []
        if self.active_menu == "file":
            menu_items = [
                ("New Map...", "new", "Ctrl+N", not self.confirm_unsaved_changes),
                ("Open Map...", "open", "Ctrl+O", not self.confirm_unsaved_changes),
                ("---", None, None, False),
                ("Recent Files", "recent", None, len(self.recent_files) == 0),
                ("---", None, None, False),
                ("Save", "save", "Ctrl+S", False),
                ("Save As...", "save_as", "Ctrl+Shift+S", False),
                ("---", None, None, False),
                ("Export", "export_menu", None, False),
                ("---", None, None, False),
                ("Exit", "exit", "Ctrl+Q", False)
            ]
        elif self.active_menu == "edit":
            menu_items = [
                ("Undo", "undo", "Ctrl+Z", not self.can_undo()),
                ("Redo", "redo", "Ctrl+Y", not self.can_redo()),
                ("---", None, None, False),
                ("Copy", "copy", "Ctrl+C", not self.has_selection),
                ("Cut", "cut", "Ctrl+X", not self.has_selection),
                ("Paste", "paste", "Ctrl+V", self.clipboard is None),
                ("---", None, None, False),
                ("Select All", "select_all", "Ctrl+A", False),
                ("Clear Selection", "clear_selection", "Esc", not self.has_selection),
                ("---", None, None, False),
                ("Map Properties...", "map_properties", "", False),
                ("Preferences...", "preferences", "", False)
            ]
        elif self.active_menu == "view":
            menu_items = [
                ("Zoom In", "zoom_in", "Ctrl++", False),
                ("Zoom Out", "zoom_out", "Ctrl+-", False),
                ("Zoom to Fit", "zoom_fit", "Ctrl+0", False),
                ("Actual Size", "zoom_actual", "Ctrl+1", False),
                ("---", None, None, False),
                ("Show Grid", "toggle_grid", "G", False),
                ("Show Layer Names", "show_layer_names", "", False),
                ("---", None, None, False),
                ("Reset Layout", "reset_layout", "", False)
            ]
        elif self.active_menu == "tools":
            menu_items = [
                ("Paint Tool", "tool_paint", "P", self.selected_tile is None),
                ("Erase Tool", "tool_erase", "E", False),
                ("Eyedropper", "tool_pick", "I", False),
                ("Flood Fill", "tool_flood_fill", "F", self.selected_tile is None),
                ("Selection Tool", "tool_select", "S", False),
                ("---", None, None, False),
                ("Line Tool", "tool_line", "L", self.selected_tile is None),
                ("Rectangle Tool", "tool_rectangle", "R", self.selected_tile is None),
                ("Circle Tool", "tool_circle", "C", self.selected_tile is None),
                ("---", None, None, False),
                ("Tileset Settings...", "tileset_settings", "F3", False)
            ]
        elif self.active_menu == "help":
            menu_items = [
                ("Keyboard Shortcuts", "shortcuts", "F1", False),
                ("---", None, None, False),
                ("About", "about", "", False)
            ]
            
        if not menu_items:
            return
            
        # Calculate menu dimensions
        max_width = 0
        item_height = 24
        for item in menu_items:
            if item[0] == "---":
                continue
            text_width = self.FONT.size(item[0])[0]
            shortcut_width = self.FONT.size(item[2] or "")[0] if item[2] else 0
            total_width = text_width + shortcut_width + 60  # padding for shortcut
            max_width = max(max_width, total_width)
        
        menu_width = max(160, max_width)
        menu_height = sum(8 if item[0] == "---" else item_height for item in menu_items) + 8
        
        # Position menu
        menu_x = anchor_rect.x
        menu_y = anchor_rect.bottom
        
        # Keep menu on screen
        if menu_x + menu_width > self.WIDTH:
            menu_x = self.WIDTH - menu_width - 4
        if menu_y + menu_height > self.HEIGHT:
            menu_y = anchor_rect.y - menu_height
            
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # Draw menu background
        pygame.draw.rect(self.screen, (40, 44, 52), menu_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 75, 85), menu_rect, 1, border_radius=6)
        
        # Draw menu items
        y_offset = menu_y + 4
        self._submenu_hitboxes = []
        
        for item in menu_items:
            label, command, shortcut, disabled = item
            
            if label == "---":
                # Draw separator
                sep_y = y_offset + 2
                pygame.draw.line(self.screen, (60, 65, 75), 
                               (menu_x + 8, sep_y), (menu_x + menu_width - 8, sep_y))
                y_offset += 8
                continue
                
            item_rect = pygame.Rect(menu_x + 2, y_offset, menu_width - 4, item_height)
            hovered = item_rect.collidepoint(mx, my) and not disabled
            
            # Draw item background
            if hovered and not disabled:
                pygame.draw.rect(self.screen, (60, 65, 75), item_rect, border_radius=4)
            
            # Colors based on state
            if disabled:
                text_color = (120, 125, 135)
            elif hovered:
                text_color = (250, 255, 255)  # Fixed: was (250, 255, 260) - invalid RGB
            else:
                text_color = (210, 215, 225)
            
            # Draw label
            self.screen.blit(self.FONT.render(label, True, text_color), 
                           (item_rect.x + 8, item_rect.y + 4))
            
            # Draw shortcut
            if shortcut and not disabled:
                shortcut_surf = self.FONT.render(shortcut, True, (170, 175, 185))
                self.screen.blit(shortcut_surf, 
                               (item_rect.right - shortcut_surf.get_width() - 8, item_rect.y + 4))
            
            # Draw submenu arrow for expandable items
            if command in ["recent", "export_menu"]:
                arrow_surf = self.FONT.render(">", True, text_color)
                self.screen.blit(arrow_surf, 
                               (item_rect.right - arrow_surf.get_width() - 8, item_rect.y + 4))
            
            # Store hitbox for clicking
            if command and not disabled:
                self._submenu_hitboxes.append((item_rect, command))
                
            y_offset += item_height
        
        # Draw submenu if needed
        if self.show_recent_files_menu:
            self.draw_recent_files_submenu(menu_rect)
        elif self.show_export_menu:
            self.draw_export_submenu(menu_rect)
    
    def draw_recent_files_submenu(self, parent_rect):
        """Draw the Recent Files submenu"""
        if not self.recent_files:
            return
            
        mx, my = pygame.mouse.get_pos()
        
        # Menu items
        items = []
        for i, filepath in enumerate(self.recent_files[:10]):  # Show up to 10 recent files
            filename = os.path.basename(filepath)
            items.append((filename, ("open_recent", filepath), filepath))
            
        # Add Clear Recent Files option
        if items:
            items.append(("---", None, None))
            items.append(("Clear Recent Files", "clear_recent", ""))
        
        # Calculate dimensions
        max_width = 200
        item_height = 24
        menu_width = max_width
        menu_height = sum(8 if item[0] == "---" else item_height for item in items) + 8
        
        # Position submenu
        menu_x = parent_rect.right - 2
        menu_y = parent_rect.y + 60  # Approximate position of "Recent Files" item
        
        # Keep on screen
        if menu_x + menu_width > self.WIDTH:
            menu_x = parent_rect.x - menu_width + 2
        if menu_y + menu_height > self.HEIGHT:
            menu_y = self.HEIGHT - menu_height - 4
            
        submenu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # Draw submenu background
        pygame.draw.rect(self.screen, (36, 40, 48), submenu_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 75, 85), submenu_rect, 1, border_radius=6)
        
        # Draw items
        y_offset = menu_y + 4
        for item in items:
            label, command, tooltip = item
            
            if label == "---":
                sep_y = y_offset + 2
                pygame.draw.line(self.screen, (50, 55, 65), 
                               (menu_x + 8, sep_y), (menu_x + menu_width - 8, sep_y))
                y_offset += 8
                continue
                
            item_rect = pygame.Rect(menu_x + 2, y_offset, menu_width - 4, item_height)
            hovered = item_rect.collidepoint(mx, my)
            
            if hovered:
                pygame.draw.rect(self.screen, (55, 60, 70), item_rect, border_radius=4)
            
            text_color = (240, 245, 250) if hovered else (200, 205, 215)
            
            # Truncate long filenames
            display_label = label
            if len(label) > 25:
                display_label = label[:22] + "..."
                
            self.screen.blit(self.FONT.render(display_label, True, text_color), 
                           (item_rect.x + 8, item_rect.y + 4))
            
            if command:
                self._submenu_hitboxes.append((item_rect, command))
                
            y_offset += item_height
    
    def draw_export_submenu(self, parent_rect):
        """Draw the Export submenu"""
        mx, my = pygame.mouse.get_pos()
        
        items = [
            ("Export as PNG...", "export_png", "PNG image format"),
            ("Export as CSV...", "export_csv", "Comma-separated values"),
            ("Export as TMX...", "export_tmx", "Tiled Map Editor format"),
            ("Export as Python...", "export_python", "Python module format"),
            ("---", None, None),
            ("Export All Formats...", "export_all", "Batch export all formats"),
            ("Export Dialog...", "export_dialog", "Full export options")
        ]
        
        # Calculate dimensions
        max_width = 180
        item_height = 24
        menu_width = max_width
        menu_height = sum(8 if item[0] == "---" else item_height for item in items) + 8
        
        # Position submenu
        menu_x = parent_rect.right - 2
        menu_y = parent_rect.y + 200  # Approximate position of "Export" item
        
        # Keep on screen
        if menu_x + menu_width > self.WIDTH:
            menu_x = parent_rect.x - menu_width + 2
        if menu_y + menu_height > self.HEIGHT:
            menu_y = self.HEIGHT - menu_height - 4
            
        submenu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # Draw submenu background  
        pygame.draw.rect(self.screen, (36, 40, 48), submenu_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 75, 85), submenu_rect, 1, border_radius=6)
        
        # Draw items
        y_offset = menu_y + 4
        for item in items:
            label, command, tooltip = item
            
            if label == "---":
                sep_y = y_offset + 2
                pygame.draw.line(self.screen, (50, 55, 65), 
                               (menu_x + 8, sep_y), (menu_x + menu_width - 8, sep_y))
                y_offset += 8
                continue
                
            item_rect = pygame.Rect(menu_x + 2, y_offset, menu_width - 4, item_height)
            hovered = item_rect.collidepoint(mx, my)
            
            if hovered:
                pygame.draw.rect(self.screen, (55, 60, 70), item_rect, border_radius=4)
            
            text_color = (240, 245, 250) if hovered else (200, 205, 215)
            
            self.screen.blit(self.FONT.render(label, True, text_color), 
                           (item_rect.x + 8, item_rect.y + 4))
            
            if command:
                self._submenu_hitboxes.append((item_rect, command))
                
            y_offset += item_height

    def handle_menu_command(self, command):
        """Handle menu command execution"""
        if isinstance(command, tuple):
            cmd_type, param = command
            if cmd_type == "open_recent":
                self.load_map_from_file(param)
                self.active_menu = None
                return
        
        # File menu commands
        if command == "new":
            self.new_map()
        elif command == "open":
            self.open_map()
        elif command == "save":
            self.save_current_file()
        elif command == "save_as":
            self.save_as_map()
        elif command == "clear_recent":
            self.recent_files = []
            self.save_preferences()
        elif command == "exit":
            # Check for unsaved changes before exiting
            if self.confirm_unsaved_changes("exit"):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            
        # Export commands
        elif command == "export_dialog":
            self.show_export_dialog()
        elif command == "export_png":
            self.export_as_png()
        elif command == "export_csv":
            self.export_as_csv()
        elif command == "export_tmx":
            self.export_as_tmx()
        elif command == "export_python":
            self.export_as_python_module()
        elif command == "export_all":
            self.batch_export_all_formats()
            
        # Edit menu commands
        elif command == "undo":
            self.undo()
        elif command == "redo":
            self.redo()
        elif command == "copy":
            self.copy_selection()
        elif command == "cut":
            self.cut_selection()
        elif command == "paste":
            self.start_paste()
        elif command == "select_all":
            self.select_all_tiles()
        elif command == "clear_selection":
            self.has_selection = False
            self.selection_dragging = False
        elif command == "map_properties":
            self.show_map_properties_dialog()
        elif command == "preferences":
            self.show_preferences_dialog()
            
        # View menu commands  
        elif command == "zoom_in":
            self.zoom_step(+1, pygame.mouse.get_pos())
        elif command == "zoom_out":
            self.zoom_step(-1, pygame.mouse.get_pos())
        elif command == "zoom_fit":
            if self.canvas_rect.width > 0 and self.canvas_rect.height > 0:
                sx = self.canvas_rect.width / max(1, self.map_cols * self.TILE_SIZE)
                sy = self.canvas_rect.height / max(1, self.map_rows * self.TILE_SIZE)
                new_scale = max(self.zoom_levels[0], min(self.zoom_levels[-1], min(sx, sy)))
                self.zoom_to(new_scale, self.canvas_rect.center)
        elif command == "zoom_actual":
            self.zoom_to(1.0, self.canvas_rect.center)
            
        # Tool commands
        elif command == "tool_paint":
            self.tool = "paint"
            self.cancel_shape_drawing()
        elif command == "tool_erase":
            self.tool = "erase" 
            self.cancel_shape_drawing()
        elif command == "tool_pick":
            self.tool = "pick"
            self.cancel_shape_drawing()
        elif command == "tool_flood_fill":
            self.tool = "flood_fill"
            self.cancel_shape_drawing()
        elif command == "tool_select":
            self.tool = "select"
            self.cancel_shape_drawing()
        elif command == "tool_line":
            self.tool = "line"
            self.cancel_shape_drawing()
        elif command == "tool_rectangle":
            self.tool = "rectangle" 
            self.cancel_shape_drawing()
        elif command == "tool_circle":
            self.tool = "circle"
            self.cancel_shape_drawing()
        elif command == "tileset_settings":
            self.open_settings()
            
        # Help commands
        elif command == "shortcuts":
            self.show_shortcuts_dialog()
        elif command == "about":
            self.show_about_dialog()
        
        # Close menu after command
        self.active_menu = None
        self.show_recent_files_menu = False
        self.show_export_menu = False

    def draw_selection(self):
        """Draw selection rectangle with marching ants animation"""
        if not (self.has_selection or self.selection_dragging):
            return
            
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        
        # Get selection bounds
        if self.selection_dragging or self.has_selection:
            min_x = min(self.selection_start_x, self.selection_end_x)
            max_x = max(self.selection_start_x, self.selection_end_x)
            min_y = min(self.selection_start_y, self.selection_end_y)
            max_y = max(self.selection_start_y, self.selection_end_y)
            
            # Convert to screen coordinates
            x1, y1 = self.tile_to_screen(min_x, min_y)
            x2, y2 = self.tile_to_screen(max_x + 1, max_y + 1)
            
            # Clamp to canvas area
            x1 = max(x1, self.canvas_rect.x)
            y1 = max(y1, self.canvas_rect.y)
            x2 = min(x2, self.canvas_rect.right)
            y2 = min(y2, self.canvas_rect.bottom)
            
            if x2 > x1 and y2 > y1:
                # Draw marching ants border with mode-specific coloring
                self.draw_marching_ants(x1, y1, x2 - x1, y2 - y1)
                
                # Draw mode indicator if currently dragging
                if self.selection_dragging and self.selection_mode != "replace":
                    mode_text = "ADD" if self.selection_mode == "add" else "SUBTRACT"
                    mode_color = (100, 255, 100) if self.selection_mode == "add" else (255, 100, 100)
                    
                    # Draw mode indicator near the selection
                    text_surf = self.FONT.render(mode_text, True, mode_color)
                    indicator_x = max(x1, self.canvas_rect.x + 10)
                    indicator_y = max(y1 - 20, self.canvas_rect.y + 5)
                    
                    # Draw background for better visibility
                    bg_rect = pygame.Rect(indicator_x - 2, indicator_y - 2, 
                                        text_surf.get_width() + 4, text_surf.get_height() + 4)
                    pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
                    pygame.draw.rect(self.screen, mode_color, bg_rect, 1)
                    
                    self.screen.blit(text_surf, (indicator_x, indicator_y))

    def draw_marching_ants(self, x: int, y: int, w: int, h: int):
        """Draw animated dashed border (marching ants effect)"""
        # Update animation offset
        self.selection_marching_ants_offset = (self.selection_marching_ants_offset + 0.5) % 16
        
        dash_length = 8
        offset = int(self.selection_marching_ants_offset)
        
        # Draw alternating black and white dashes
        colors = [(0, 0, 0), (255, 255, 255)]
        phase_offsets = [0, dash_length]
        
        for i, color in enumerate(colors):
            phase_offset = phase_offsets[i]
            # Top edge
            self.draw_dashed_line(x, y, x + w, y, dash_length, offset + phase_offset, color)
            # Bottom edge  
            self.draw_dashed_line(x, y + h - 1, x + w, y + h - 1, dash_length, offset + phase_offset, color)
            # Left edge
            self.draw_dashed_line(x, y, x, y + h, dash_length, offset + phase_offset, color)
            # Right edge
            self.draw_dashed_line(x + w - 1, y, x + w - 1, y + h, dash_length, offset + phase_offset, color)

    def draw_dashed_line(self, x1: int, y1: int, x2: int, y2: int, dash_len: int, offset: int, color):
        """Draw a dashed line with specified dash length and offset"""
        dx = x2 - x1
        dy = y2 - y1
        distance = int(max(abs(dx), abs(dy)))  # Convert to integer for range()
        
        if distance == 0:
            return
            
        # Step through the line
        for i in range(distance + 1):
            t = i / distance if distance > 0 else 0
            x = int(x1 + dx * t)
            y = int(y1 + dy * t)
            
            # Determine if this point should be drawn (dash pattern)
            pos_in_pattern = (i + offset) % (dash_len * 2)
            if pos_in_pattern < dash_len:
                if self.canvas_rect.collidepoint(x, y):
                    self.screen.set_at((x, y), color)

    def draw_paste_preview(self):
        """Draw paste preview at cursor position"""
        if not self.clipboard or not self.paste_preview:
            return
            
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        data = self.clipboard['data']
        width = self.clipboard['width']
        height = self.clipboard['height']
        
        # Draw tiles with transparency effect
        alpha_surface = pygame.Surface((ts, ts), pygame.SRCALPHA)
        
        for y in range(height):
            for x in range(width):
                tile_id = data[y][x]
                if tile_id >= 0 and tile_id < len(self.tiles):
                    screen_x, screen_y = self.tile_to_screen(self.paste_x + x, self.paste_y + y)
                    
                    # Check if the tile is visible on screen
                    if (screen_x + ts > self.canvas_rect.x and screen_x < self.canvas_rect.right and
                        screen_y + ts > self.canvas_rect.y and screen_y < self.canvas_rect.bottom):
                        
                        # Draw tile with transparency
                        tile = self.tiles[tile_id]
                        scaled_tile = pygame.transform.scale(tile, (ts, ts))
                        alpha_surface.fill((0, 0, 0, 0))
                        alpha_surface.blit(scaled_tile, (0, 0))
                        alpha_surface.set_alpha(128)  # 50% transparency
                        
                        # Clip to canvas area
                        clip_rect = pygame.Rect(screen_x, screen_y, ts, ts).clip(self.canvas_rect)
                        if clip_rect.width > 0 and clip_rect.height > 0:
                            self.screen.blit(alpha_surface, (screen_x, screen_y))

    def draw_shape_preview(self):
        """Draw shape preview while dragging"""
        if not self.shape_dragging or not self.shape_preview_tiles or self.selected_tile is None:
            return
        
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        tile = self.tiles[self.selected_tile] if 0 <= self.selected_tile < len(self.tiles) else None
        
        if not tile:
            return
        
        # Create semi-transparent preview
        alpha_surface = pygame.Surface((ts, ts), pygame.SRCALPHA)
        scaled_tile = pygame.transform.scale(tile, (ts, ts))
        alpha_surface.blit(scaled_tile, (0, 0))
        alpha_surface.set_alpha(160)  # 63% transparency
        
        # Draw all preview tiles
        for cx, cy in self.shape_preview_tiles:
            if 0 <= cx < self.map_cols and 0 <= cy < self.map_rows:
                screen_x, screen_y = self.tile_to_screen(cx, cy)
                
                # Check if the tile is visible on screen
                if (screen_x + ts > self.canvas_rect.x and screen_x < self.canvas_rect.right and
                    screen_y + ts > self.canvas_rect.y and screen_y < self.canvas_rect.bottom):
                    
                    # Clip to canvas area
                    clip_rect = pygame.Rect(screen_x, screen_y, ts, ts).clip(self.canvas_rect)
                    if clip_rect.width > 0 and clip_rect.height > 0:
                        self.screen.blit(alpha_surface, (screen_x, screen_y))

    def draw_multi_tile_brush_preview(self):
        """Draw preview of multi-tile brush at cursor position"""
        if not self.multi_tile_mode or not self.multi_tile_brush_data:
            return
        
        # Get mouse position
        mx, my = pygame.mouse.get_pos()
        if not self.canvas_rect.collidepoint(mx, my):
            return
        
        # Convert mouse position to tile coordinates
        cx, cy = self.screen_to_tile(mx, my)
        if not (0 <= cx < self.map_cols and 0 <= cy < self.map_rows):
            return
        
        # Draw preview for each tile in the brush
        for rel_x, rel_y, tile_idx in self.multi_tile_brush_data:
            tx = cx + rel_x
            ty = cy + rel_y
            
            # Skip if out of bounds
            if not (0 <= tx < self.map_cols and 0 <= ty < self.map_rows):
                continue
            
            # Get screen position
            screen_x, screen_y = self.tile_to_screen(tx, ty)
            ts = int(self.TILE_SIZE * self.VIEW_SCALE)
            
            # Check if the tile preview is visible on screen
            if (screen_x + ts > self.canvas_rect.x and screen_x < self.canvas_rect.right and
                screen_y + ts > self.canvas_rect.y and screen_y < self.canvas_rect.bottom):
                
                # Create semi-transparent preview
                if 0 <= tile_idx < len(self.tiles):
                    tile = self.tiles[tile_idx]
                    scaled_tile = pygame.transform.scale(tile, (ts, ts))
                    alpha_surface = scaled_tile.copy()
                    alpha_surface.set_alpha(128)  # 50% transparency
                    
                    # Clip to canvas area
                    clip_rect = pygame.Rect(screen_x, screen_y, ts, ts).clip(self.canvas_rect)
                    if clip_rect.width > 0 and clip_rect.height > 0:
                        self.screen.blit(alpha_surface, (screen_x, screen_y))
                        
                        # Add a colored border to show it's a multi-tile brush
                        pygame.draw.rect(self.screen, self.ACTIVE, (screen_x, screen_y, ts, ts), 2)

    def draw_right_panels(self):
        rect = self.right_rect
        if rect.width <= 0:
            return
        pygame.draw.rect(self.screen, self.PANEL_BG, rect)
        lyr = self.right_layers_rect
        self.draw_panel_header(lyr, "Layers", self.right_layers_collapsed)
        if not self.right_layers_collapsed:
            content = pygame.Rect(lyr.x, lyr.y + self.panel_header_h, lyr.w, max(0, lyr.h - self.panel_header_h))
            # Layer manipulation buttons at top of content
            btn_h = 22
            pad = 6
            lbtns = [
                ('plus', "layer_add"), 
                ('duplicate', "layer_duplicate"), 
                ('minus', "layer_del"), 
                ('up_arrow', "layer_up"), 
                ('down_arrow', "layer_down"),
            ]
            bx = content.x + pad
            by = content.y + pad
            self._layer_btn_hitboxes = []
            for icon_key, cmd in lbtns:
                bw = 28
                brect = pygame.Rect(bx, by, bw, btn_h)
                pygame.draw.rect(self.screen, (55, 60, 68), brect, border_radius=4)
                pygame.draw.rect(self.screen, (35, 38, 44), brect, 1, border_radius=4)
                # Use render_icon for layer buttons
                icon_surf = render_icon(self.FONT, icon_key, (230, 235, 240), size=14)
                icon_rect = icon_surf.get_rect(center=brect.center)
                self.screen.blit(icon_surf, icon_rect)
                self._layer_btn_hitboxes.append((brect, cmd))
                bx += bw + 6

            list_top = by + btn_h + pad
            row_h = 24
            self._layer_row_hitboxes = []
            for i, layer in enumerate(self.layers):
                ry = list_top + i * row_h
                if ry + row_h > content.bottom:
                    break
                row_rect = pygame.Rect(content.x + pad, ry, content.w - pad * 2, row_h - 2)
                bg = (54, 58, 66) if i == self.current_layer else (42, 46, 54)
                pygame.draw.rect(self.screen, bg, row_rect, border_radius=4)
                # Eye/lock toggles using standardized icons
                eye_rect = pygame.Rect(row_rect.x + 6, row_rect.y + 4, 16, 16)
                lock_rect = pygame.Rect(row_rect.x + 26, row_rect.y + 4, 16, 16)
                
                # Use standardized icon rendering with proper colors
                eye_col = (180, 220, 120) if layer.visible else (110, 115, 120)
                lock_col = (255, 120, 120) if layer.locked else (110, 115, 120)
                
                eye_icon_key = 'eye_open' if layer.visible else 'eye_closed'
                lock_icon_key = 'lock_closed' if layer.locked else 'lock_open'
                
                eye_text = render_icon(self.FONT, eye_icon_key, eye_col)
                lock_text = render_icon(self.FONT, lock_icon_key, lock_col)
                
                # Center the icons in their rectangles
                eye_text_rect = eye_text.get_rect(center=eye_rect.center)
                lock_text_rect = lock_text.get_rect(center=lock_rect.center)
                
                self.screen.blit(eye_text, eye_text_rect)
                self.screen.blit(lock_text, lock_text_rect)
                # Name (or text input if renaming)
                if self.layer_rename_index == i:
                    # Draw text input box
                    text_rect = pygame.Rect(row_rect.x + 48, row_rect.y + 2, row_rect.w - 52, row_rect.h - 4)
                    pygame.draw.rect(self.screen, (40, 42, 48), text_rect)
                    pygame.draw.rect(self.screen, (80, 170, 255), text_rect, 1)
                    
                    # Draw text with cursor
                    text_surface = self.FONT.render(self.layer_rename_text, True, (230, 235, 240))
                    self.screen.blit(text_surface, (text_rect.x + 4, text_rect.y + 2))
                    
                    # Draw cursor
                    if pygame.time.get_ticks() % 1000 < 500:  # Blink every 500ms
                        cursor_x = text_rect.x + 4 + self.FONT.size(self.layer_rename_text[:self.layer_rename_cursor])[0]
                        pygame.draw.line(self.screen, (230, 235, 240), 
                                       (cursor_x, text_rect.y + 2), 
                                       (cursor_x, text_rect.bottom - 2))
                else:
                    self.screen.blit(self.FONT.render(layer.name, True, (230, 235, 240)), (row_rect.x + 48, row_rect.y + 3))
                # Track hitboxes
                self._layer_row_hitboxes.append({
                    'row': row_rect,
                    'eye': eye_rect,
                    'lock': lock_rect,
                    'index': i,
                })
        # Tool Options panel in Properties area
        prop = self.right_props_rect
        self.draw_panel_header(prop, "Properties", self.right_props_collapsed)
        if not self.right_props_collapsed:
            pc = pygame.Rect(prop.x, prop.y + self.panel_header_h, prop.w, max(0, prop.h - self.panel_header_h))
            pad = 8
            y = pc.y + pad
            self.screen.blit(self.FONT.render("Tool Options", True, (210, 214, 220)), (pc.x + pad, y))
            y += 22
            if self.tool in ("paint", "erase"):
                self.screen.blit(self.FONT.render("Brush size:", True, (200, 205, 210)), (pc.x + pad, y))
                sizes = [1, 2, 3, 5]
                bx = pc.x + pad + 100
                by = y - 2
                if not hasattr(self, '_toolopt_hitboxes'):
                    self._toolopt_hitboxes = []
                else:
                    self._toolopt_hitboxes.clear()
                for s in sizes:
                    r = pygame.Rect(bx, by, 28, 20)
                    col = (95, 100, 110) if self.brush_size == s else (70, 74, 82)
                    pygame.draw.rect(self.screen, col, r, border_radius=4)
                    pygame.draw.rect(self.screen, (50, 54, 60), r, 1, border_radius=4)
                    self.screen.blit(self.FONT.render(str(s), True, (230, 235, 240)), (r.centerx - 5, r.y + 2))
                    self._toolopt_hitboxes.append((r, ('brush', s)))
                    bx += 34
                
                y += 30
                self.screen.blit(self.FONT.render("Brush shape:", True, (200, 205, 210)), (pc.x + pad, y))
                shapes = [("square", "square"), ("circle", "circle"), ("diamond", "diamond")]
                bx = pc.x + pad + 100
                by = y - 2
                for icon_key, shape in shapes:
                    r = pygame.Rect(bx, by, 28, 20)
                    col = (95, 100, 110) if self.brush_shape == shape else (70, 74, 82)
                    pygame.draw.rect(self.screen, col, r, border_radius=4)
                    pygame.draw.rect(self.screen, (50, 54, 60), r, 1, border_radius=4)
                    
                    # Use our icon system for brush shapes
                    icon_surf = render_icon(self.FONT, icon_key, (230, 235, 240), size=14)
                    icon_rect = icon_surf.get_rect(center=r.center)
                    self.screen.blit(icon_surf, icon_rect)
                    
                    self._toolopt_hitboxes.append((r, ('shape', shape)))
                    bx += 34
            elif self.tool == "flood_fill":
                self.screen.blit(self.FONT.render("Fill mode:", True, (200, 205, 210)), (pc.x + pad, y))
                modes = [("4-way", 4), ("8-way", 8)]
                bx = pc.x + pad + 100
                by = y - 2
                if not hasattr(self, '_toolopt_hitboxes'):
                    self._toolopt_hitboxes = []
                else:
                    self._toolopt_hitboxes.clear()
                for label, mode in modes:
                    r = pygame.Rect(bx, by, 48, 20)
                    col = (95, 100, 110) if self.fill_mode == mode else (70, 74, 82)
                    pygame.draw.rect(self.screen, col, r, border_radius=4)
                    pygame.draw.rect(self.screen, (50, 54, 60), r, 1, border_radius=4)
                    text_w = self.FONT.size(label)[0]
                    self.screen.blit(self.FONT.render(label, True, (230, 235, 240)), (r.centerx - text_w//2, r.y + 2))
                    self._toolopt_hitboxes.append((r, ('fill_mode', mode)))
                    bx += 54
            elif self.tool in ("rectangle", "circle"):
                self.screen.blit(self.FONT.render("Fill mode:", True, (200, 205, 210)), (pc.x + pad, y))
                modes = [("Outline", False), ("Filled", True)]
                bx = pc.x + pad + 100
                by = y - 2
                if not hasattr(self, '_toolopt_hitboxes'):
                    self._toolopt_hitboxes = []
                else:
                    self._toolopt_hitboxes.clear()
                for label, filled in modes:
                    r = pygame.Rect(bx, by, 48, 20)
                    col = (95, 100, 110) if self.shape_filled == filled else (70, 74, 82)
                    pygame.draw.rect(self.screen, col, r, border_radius=4)
                    pygame.draw.rect(self.screen, (50, 54, 60), r, 1, border_radius=4)
                    text_w = self.FONT.size(label)[0]
                    self.screen.blit(self.FONT.render(label, True, (230, 235, 240)), (r.centerx - text_w//2, r.y + 2))
                    self._toolopt_hitboxes.append((r, ('shape_mode', filled)))
                    bx += 54
            # Tool Options and Properties Section
            y += 40
            
            # Show different content based on mode
            if self.object_mode == "objects":
                # Object Properties Section
                if self.selected_object:
                    self.screen.blit(self.FONT.render("Object Properties", True, (210, 214, 220)), (pc.x + pad, y))
                    y += 22
                    
                    # Object Name
                    self.screen.blit(self.FONT.render("Name:", True, (200, 205, 210)), (pc.x + pad, y))
                    name_rect = pygame.Rect(pc.x + pad + 60, y - 2, pc.w - pad * 2 - 60, 20)
                    
                    if self.object_name_editing:
                        # Draw text input box for editing
                        pygame.draw.rect(self.screen, (40, 42, 48), name_rect)
                        pygame.draw.rect(self.screen, (80, 170, 255), name_rect, 1)
                        
                        # Draw text with cursor
                        text_surface = self.FONT.render(self.object_name_edit_text, True, (230, 235, 240))
                        self.screen.blit(text_surface, (name_rect.x + 4, name_rect.y + 2))
                        
                        # Draw cursor
                        if pygame.time.get_ticks() % 1000 < 500:  # Blink every 500ms
                            cursor_x = name_rect.x + 4 + self.FONT.size(self.object_name_edit_text[:self.object_name_cursor])[0]
                            pygame.draw.line(self.screen, (230, 235, 240), 
                                           (cursor_x, name_rect.y + 2), 
                                           (cursor_x, name_rect.bottom - 2))
                    else:
                        # Draw normal name display
                        pygame.draw.rect(self.screen, (60, 64, 72), name_rect)
                        pygame.draw.rect(self.screen, (80, 84, 92), name_rect, 1)
                        name_text = self.FONT.render(self.selected_object.name, True, (230, 235, 240))
                        self.screen.blit(name_text, (name_rect.x + 4, name_rect.y + 2))
                    
                    # Store hitbox for name editing
                    if not hasattr(self, '_object_prop_hitboxes'):
                        self._object_prop_hitboxes = []
                    else:
                        self._object_prop_hitboxes.clear()
                    self._object_prop_hitboxes.append((name_rect, 'object_name'))
                    
                    y += 30
                    
                    # Object Type dropdown
                    self.screen.blit(self.FONT.render("Type:", True, (200, 205, 210)), (pc.x + pad, y))
                    type_rect = pygame.Rect(pc.x + pad + 60, y - 2, pc.w - pad * 2 - 60, 20)
                    
                    # Color indicator and type name
                    pygame.draw.rect(self.screen, self.selected_object.color, pygame.Rect(type_rect.x, type_rect.y, 20, 20))
                    pygame.draw.rect(self.screen, (80, 84, 92), type_rect, 1)
                    
                    # Find display name for current type
                    type_display = self.selected_object.object_type.capitalize()
                    for obj_type, display_name, color in self.OBJECT_TYPES:
                        if obj_type == self.selected_object.object_type:
                            type_display = display_name
                            break
                    
                    type_text = self.FONT.render(type_display, True, (230, 235, 240))
                    self.screen.blit(type_text, (type_rect.x + 24, type_rect.y + 2))
                    self._object_prop_hitboxes.append((type_rect, 'object_type'))
                    
                    y += 30
                    
                    # Position
                    self.screen.blit(self.FONT.render(f"Position: ({self.selected_object.x}, {self.selected_object.y})", True, (200, 205, 210)), (pc.x + pad, y))
                    y += 25
                    
                elif self.object_placement_mode:
                    # Show current object being placed
                    self.screen.blit(self.FONT.render("Placing Object", True, (210, 214, 220)), (pc.x + pad, y))
                    y += 22
                    
                    if self.selected_object_type < len(self.OBJECT_TYPES):
                        obj_type, display_name, color = self.OBJECT_TYPES[self.selected_object_type]
                        
                        # Show type being placed
                        self.screen.blit(self.FONT.render(f"Type: {display_name}", True, (200, 205, 210)), (pc.x + pad, y))
                        y += 20
                        
                        # Color indicator
                        color_rect = pygame.Rect(pc.x + pad, y, 20, 20)
                        pygame.draw.rect(self.screen, color, color_rect)
                        pygame.draw.rect(self.screen, (80, 84, 92), color_rect, 1)
                        self.screen.blit(self.FONT.render("Color", True, (200, 205, 210)), (pc.x + pad + 25, y + 2))
                        y += 30
                        
                    self.screen.blit(self.FONT.render("Click to place, Esc to cancel", True, (150, 155, 165)), (pc.x + pad, y))
                else:
                    # No object selected and not placing
                    self.screen.blit(self.FONT.render("Object Mode", True, (210, 214, 220)), (pc.x + pad, y))
                    y += 22
                    self.screen.blit(self.FONT.render("Select object from palette", True, (150, 155, 165)), (pc.x + pad, y))
                    y += 20
                    self.screen.blit(self.FONT.render("or click object to select", True, (150, 155, 165)), (pc.x + pad, y))
            else:
                # Tile Properties Section (existing code)
                if self.selected_tile is not None and 0 <= self.selected_tile < len(self.tiles):
                    self.screen.blit(self.FONT.render("Tile Properties", True, (210, 214, 220)), (pc.x + pad, y))
                    y += 22
                    
                    props = self.get_tile_properties(self.selected_tile)
                    
                    # Collision Type dropdown
                    self.screen.blit(self.FONT.render("Collision:", True, (200, 205, 210)), (pc.x + pad, y))
                    
                    # Current collision type display with color indicator
                    collision_rect = pygame.Rect(pc.x + pad + 80, y - 2, pc.w - pad * 2 - 80, 20)
                    color = self.get_collision_color(props.collision_type)
                    pygame.draw.rect(self.screen, color, pygame.Rect(collision_rect.x, collision_rect.y, 20, 20))
                    pygame.draw.rect(self.screen, (80, 84, 92), collision_rect, 1)
                    
                    # Find display name for current collision type
                    current_display = "None"
                    for type_id, display_name, _ in self.COLLISION_TYPES:
                        if type_id == props.collision_type:
                            current_display = display_name
                            break
                    
                    text = self.FONT.render(current_display, True, (230, 235, 240))
                    self.screen.blit(text, (collision_rect.x + 24, collision_rect.y + 2))
                    
                    # Store hitbox for collision type dropdown
                    if not hasattr(self, '_tile_prop_hitboxes'):
                        self._tile_prop_hitboxes = []
                    else:
                        self._tile_prop_hitboxes.clear()
                    self._tile_prop_hitboxes.append((collision_rect, 'collision_dropdown'))
                    
                    y += 30
                    
                    # Show additional properties based on collision type
                    if props.collision_type == "damage":
                        self.screen.blit(self.FONT.render("Damage:", True, (200, 205, 210)), (pc.x + pad, y))
                        damage_text = str(props.damage)
                        self.screen.blit(self.FONT.render(damage_text, True, (230, 235, 240)), (pc.x + pad + 80, y))
                        y += 25
                    elif props.collision_type == "trigger":
                        self.screen.blit(self.FONT.render("Trigger ID:", True, (200, 205, 210)), (pc.x + pad, y))
                        trigger_text = props.trigger_id if props.trigger_id else "(none)"
                        self.screen.blit(self.FONT.render(trigger_text, True, (230, 235, 240)), (pc.x + pad + 80, y))
                        y += 25
                    elif props.collision_type in ("water", "ice", "custom"):
                        self.screen.blit(self.FONT.render("Friction:", True, (200, 205, 210)), (pc.x + pad, y))
                        friction_text = f"{props.friction:.1f}"
                        self.screen.blit(self.FONT.render(friction_text, True, (230, 235, 240)), (pc.x + pad + 80, y))
                        y += 25
                    
                    # Collision overlay toggle
                    y += 10
                    overlay_rect = pygame.Rect(pc.x + pad, y, 20, 20)
                    pygame.draw.rect(self.screen, (80, 84, 92), overlay_rect, 1)
                    if self.show_collision_overlay:
                        pygame.draw.rect(self.screen, (120, 200, 255), overlay_rect.inflate(-4, -4))
                    
                    self.screen.blit(self.FONT.render("Show Collision Overlay", True, (200, 205, 210)), (pc.x + pad + 25, y + 2))
                    self._tile_prop_hitboxes.append((overlay_rect, 'collision_overlay'))
                else:
                    self.screen.blit(self.FONT.render("No tile selected", True, (150, 155, 165)), (pc.x + pad, y))

    # --------------------------- Tile Properties System ---------------------------
    def get_tile_properties(self, tile_index: int) -> TileProperties:
        """Get properties for a tile, creating default if none exist"""
        if tile_index not in self.tile_properties:
            self.tile_properties[tile_index] = TileProperties()
        return self.tile_properties[tile_index]
    
    def set_tile_collision_type(self, tile_index: int, collision_type: str):
        """Set collision type for a tile"""
        if tile_index is not None and 0 <= tile_index < len(self.tiles):
            props = self.get_tile_properties(tile_index)
            props.collision_type = collision_type
            self.mark_modified()
    
    def get_collision_color(self, collision_type: str) -> Tuple[int, int, int]:
        """Get color for collision type visualization"""
        colors = {
            "none": (128, 128, 128),      # Gray
            "solid": (255, 0, 0),         # Red
            "platform": (0, 100, 255),    # Blue
            "damage": (255, 128, 0),      # Orange
            "water": (0, 200, 255),       # Light Blue
            "ice": (150, 220, 255),       # Cyan
            "trigger": (255, 255, 0),     # Yellow
            "custom": (255, 0, 255)       # Magenta
        }
        return colors.get(collision_type, (128, 128, 128))
    
    def draw_collision_overlay(self):
        """Draw collision overlay on tiles"""
        if not self.show_collision_overlay:
            return
        
        # Get visible tile range
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        canvas_w = max(0, self.canvas_rect.width)
        canvas_h = max(0, self.canvas_rect.height)
        cols_visible = (canvas_w + ts - 1) // ts + 1
        rows_visible = (canvas_h + ts - 1) // ts + 1
        start_c = max(0, int(self.scroll_x // ts))
        start_r = max(0, int(self.scroll_y // ts))
        end_c = min(self.map_cols, start_c + cols_visible)
        end_r = min(self.map_rows, start_r + rows_visible)
        
        # Draw collision overlays for all layers
        for layer in self.layers:
            if not layer.visible:
                continue
                
            for ry in range(start_r, end_r):
                for rx in range(start_c, end_c):
                    if 0 <= ry < len(layer.data) and 0 <= rx < len(layer.data[ry]):
                        tile_idx = layer.data[ry][rx]
                        if tile_idx >= 0 and tile_idx in self.tile_properties:
                            props = self.tile_properties[tile_idx]
                            if props.collision_type != "none":
                                # Calculate screen position
                                sx = self.canvas_rect.x + rx * ts - self.scroll_x
                                sy = self.canvas_rect.y + ry * ts - self.scroll_y
                                
                                # Create collision overlay surface
                                overlay = pygame.Surface((ts, ts))
                                color = self.get_collision_color(props.collision_type)
                                overlay.fill(color)
                                overlay.set_alpha(self.collision_overlay_opacity)
                                
                                # Clip to canvas and blit
                                if (sx + ts > self.canvas_rect.x and sx < self.canvas_rect.right and
                                    sy + ts > self.canvas_rect.y and sy < self.canvas_rect.bottom):
                                    self.screen.blit(overlay, (sx, sy))
                                    
                                    # Draw collision type label
                                    if ts >= 32:  # Only show labels when tiles are large enough
                                        label = props.collision_type[:4].upper()
                                        text = self.FONT.render(label, True, (255, 255, 255))
                                        text_rect = text.get_rect(center=(sx + ts//2, sy + ts//2))
                                        self.screen.blit(text, text_rect)

    # --------------------------- Objects System ---------------------------
    def generate_object_name(self, object_type: str) -> str:
        """Generate unique name for new object"""
        self.object_counters[object_type] += 1
        return f"{object_type.capitalize()}_{self.object_counters[object_type]:02d}"
    
    def get_object_at(self, x: int, y: int) -> GameObject:
        """Get object at grid position"""
        for obj in self.objects:
            if obj.x == x and obj.y == y:
                return obj
        return None
    
    def remove_object_at(self, x: int, y: int) -> GameObject:
        """Remove and return object at position"""
        for i, obj in enumerate(self.objects):
            if obj.x == x and obj.y == y:
                return self.objects.pop(i)
        return None
    
    def place_object(self, cx: int, cy: int):
        """Place object at grid position"""
        if not (0 <= cx < self.map_cols and 0 <= cy < self.map_rows):
            return
            
        if self.selected_object_type < 0 or self.selected_object_type >= len(self.OBJECT_TYPES):
            return
            
        # Get object type info
        obj_type, display_name, color = self.OBJECT_TYPES[self.selected_object_type]
        
        # Check if there's already an object at this position
        existing_obj = self.get_object_at(cx, cy)
        
        # Generate name ONLY when actually placing (not during command creation/preview)
        new_name = self.generate_object_name(obj_type)
        
        # Create new object
        new_obj = GameObject(
            object_type=obj_type,
            color=color,
            name=new_name,
            x=cx,
            y=cy
        )
        
        # Execute placement command
        command = ObjectPlaceCommand(self, new_obj, existing_obj)
        self.execute_command(command)
        self.mark_modified()
    
    def delete_object_at(self, cx: int, cy: int):
        """Delete object at grid position"""
        obj = self.get_object_at(cx, cy)
        if obj:
            command = ObjectDeleteCommand(self, obj)
            self.execute_command(command)
            self.mark_modified()
    
    def select_object_at(self, cx: int, cy: int):
        """Select object at grid position"""
        self.selected_object = self.get_object_at(cx, cy)

    def copy_selected_objects(self):
        """Copy selected objects to clipboard"""
        if self.selected_objects:
            self.copied_objects = []
            for obj in self.selected_objects:
                # Create a copy of the object
                copied_obj = GameObject(
                    object_type=obj.object_type,
                    color=obj.color,
                    name=obj.name,
                    x=obj.x,
                    y=obj.y
                )
                # Copy custom properties if they exist
                if hasattr(obj, 'custom_properties') and obj.custom_properties:
                    copied_obj.custom_properties = obj.custom_properties.copy()
                self.copied_objects.append(copied_obj)
            return len(self.copied_objects)
        return 0

    def paste_objects_at(self, cx: int, cy: int):
        """Paste copied objects relative to the given position"""
        if not self.copied_objects:
            return 0

        if not self.copied_objects:
            return 0

        # Calculate offset from first object to maintain relative positions
        first_obj = self.copied_objects[0]
        offset_x = cx - first_obj.x
        offset_y = cy - first_obj.y

        pasted_objects = []
        for obj in self.copied_objects:
            # Calculate new position
            new_x = obj.x + offset_x
            new_y = obj.y + offset_y

            # Check bounds
            if not (0 <= new_x < self.map_cols and 0 <= new_y < self.map_rows):
                continue

            # Use original name instead of generating new one
            original_name = obj.name

            # Create new object
            new_obj = GameObject(
                object_type=obj.object_type,
                color=obj.color,
                name=original_name,
                x=new_x,
                y=new_y
            )

            # Copy custom properties
            if hasattr(obj, 'custom_properties') and obj.custom_properties:
                new_obj.custom_properties = obj.custom_properties.copy()

            # Check if there's already an object at this position
            existing_obj = self.get_object_at(new_x, new_y)

            # Execute placement command
            command = ObjectPlaceCommand(self, new_obj, existing_obj)
            self.execute_command(command)
            pasted_objects.append(new_obj)

        if pasted_objects:
            self.mark_modified()
            # Select the pasted objects
            self.selected_objects = pasted_objects
            self.selected_object = pasted_objects[0] if pasted_objects else None

        return len(pasted_objects)

    def delete_selected_objects(self):
        """Delete all selected objects"""
        if self.selected_objects:
            # Create a batch command to delete all selected objects
            commands = []
            for obj in self.selected_objects:
                commands.append(ObjectDeleteCommand(self, obj))
            
            # Execute as a batch for proper undo/redo
            if len(commands) == 1:
                self.execute_command(commands[0])
            else:
                # Create a multi-command for batch operations
                batch_command = BatchCommand(commands)
                self.execute_command(batch_command)
            
            self.selected_objects.clear()
            self.selected_object = None
            self.mark_modified()
            return True
        return False
    
    def draw_objects(self):
        """Draw all game objects"""
        ts = int(self.TILE_SIZE * self.VIEW_SCALE)
        object_size = max(8, int(ts * 0.7))  # Slightly smaller than tile size
        offset = (ts - object_size) // 2  # Center in tile
        
        for obj in self.objects:
            # Calculate screen position
            sx = self.canvas_rect.x + obj.x * ts - self.scroll_x + offset
            sy = self.canvas_rect.y + obj.y * ts - self.scroll_y + offset
            
            # Skip if outside canvas
            if (sx + object_size < self.canvas_rect.x or sx > self.canvas_rect.right or
                sy + object_size < self.canvas_rect.y or sy > self.canvas_rect.bottom):
                continue
            
            # Create object surface with transparency
            obj_surface = pygame.Surface((object_size, object_size), pygame.SRCALPHA)
            obj_surface.fill((*obj.color, 180))  # 0.7 opacity (180/255)
            
            # Draw object
            self.screen.blit(obj_surface, (sx, sy))
            
            # Draw selection highlights
            if obj in self.selected_objects:
                if obj == self.selected_object:
                    # Primary selection - bright color
                    pygame.draw.rect(self.screen, self.SELECT, (sx - 2, sy - 2, object_size + 4, object_size + 4), 2)
                else:
                    # Secondary selections - dimmer color
                    select_color = (self.SELECT[0] // 2, self.SELECT[1] // 2, self.SELECT[2] // 2)
                    pygame.draw.rect(self.screen, select_color, (sx - 1, sy - 1, object_size + 2, object_size + 2), 2)
            elif obj == self.selected_object:
                # Single selection
                pygame.draw.rect(self.screen, self.SELECT, (sx - 2, sy - 2, object_size + 4, object_size + 4), 2)
            
            # Draw object name if tile is large enough
            if ts >= 24 and object_size >= 16:
                name_text = self.FONT.render(obj.name, True, (255, 255, 255))
                text_rect = name_text.get_rect(center=(sx + object_size//2, sy + object_size + 8))
                # Add background for readability
                bg_rect = text_rect.copy()
                bg_rect.inflate(4, 2)
                pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect)
                self.screen.blit(name_text, text_rect)

    # --------------------------- Editing ---------------------------
    def paint_at(self, cx: int, cy: int, button: int):
        if not (0 <= cx < self.map_cols and 0 <= cy < self.map_rows):
            return
            
        # Handle object mode
        if self.object_mode == "objects":
            if self.object_paste_mode:
                # In paste mode
                if button == 1:  # Left click - paste objects
                    pasted_count = self.paste_objects_at(cx, cy)
                    if pasted_count > 0:
                        print(f"Pasted {pasted_count} objects")
                    self.object_paste_mode = False
                elif button == 3:  # Right click - cancel paste mode
                    self.object_paste_mode = False
                    print("Paste cancelled")
                return
            elif self.object_placement_mode:
                # In placement mode
                if button == 1:  # Left click - place object
                    self.place_object(cx, cy)
                    # Only exit placement mode if not in persistent mode
                    if not self.persistent_object_mode:
                        self.object_placement_mode = False
                elif button == 3:  # Right click - cancel placement mode
                    self.object_placement_mode = False
                    self.selected_object = None
            else:
                # In selection mode
                if button == 1:  # Left click - select object
                    obj_at_pos = self.get_object_at(cx, cy)
                    if obj_at_pos:
                        # Handle multi-selection with Ctrl
                        if pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]:
                            if obj_at_pos in self.selected_objects:
                                self.selected_objects.remove(obj_at_pos)
                            else:
                                self.selected_objects.append(obj_at_pos)
                        else:
                            # Single selection - clear others
                            self.selected_objects.clear()
                            self.selected_objects.append(obj_at_pos)
                        self.selected_object = obj_at_pos
                    else:
                        # Clicked empty space - clear selection unless Ctrl held
                        if not (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                            self.selected_objects.clear()
                            self.selected_object = None
                elif button == 3:  # Right click - delete object
                    self.delete_object_at(cx, cy)
            return
            
        # Continue with tile mode
        # Respect layer visibility/lock
        layer = self.layers[self.current_layer]
        if layer.locked or not layer.visible:
            return
        
        # Check if multi-tile brush mode is active and we're painting
        if self.multi_tile_mode and button == 1 and self.multi_tile_brush_data:
            self.paint_multi_tile_brush(cx, cy)
            return
        
        # Check if pattern painting is enabled
        if self.pattern_mode and self.pattern_data and button == 1:
            self.paint_with_pattern(cx, cy, self.brush_size)
            return
        
        # Apply brush size and shape
        half = self.brush_size // 2
        tile_changes = []
        
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                tx, ty = cx + dx, cy + dy
                if not (0 <= tx < self.map_cols and 0 <= ty < self.map_rows):
                    continue
                
                # Check if this position is within the brush shape
                if self.brush_shape == "circle":
                    distance_squared = dx * dx + dy * dy
                    if distance_squared > half * half + 0.5:  # Circle boundary
                        continue
                elif self.brush_shape == "diamond":
                    if abs(dx) + abs(dy) > half:  # Diamond boundary
                        continue
                # Square shape doesn't need additional checks
                
                # Get the current tile at this position
                old_tile = self.layers[self.current_layer].data[ty][tx]
                
                if button == 1:  # Paint
                    if self.selected_tile is None:
                        continue
                    if old_tile != self.selected_tile:  # Only paint if different
                        tile_changes.append((tx, ty, old_tile, self.selected_tile))
                elif button == 3:  # Erase
                    if old_tile != -1:  # Only erase if not already empty
                        tile_changes.append((tx, ty, old_tile, -1))
        
        # Execute the command if there are changes
        if tile_changes:
            if len(tile_changes) == 1:
                # Single tile operation
                tx, ty, old_tile, new_tile = tile_changes[0]
                if button == 1:
                    command = PaintCommand(self, self.current_layer, tx, ty, new_tile, old_tile)
                else:
                    command = EraseCommand(self, self.current_layer, tx, ty, old_tile)
            else:
                # Multi-tile operation
                command = MultiTileCommand(self, self.current_layer, tile_changes)
            
            self.execute_command(command)

    def toggle_multi_tile_selection(self, tile_index: int):
        """Toggle a tile in the multi-tile selection"""
        if tile_index in self.multi_tile_selection:
            self.multi_tile_selection.remove(tile_index)
        else:
            self.multi_tile_selection.append(tile_index)
        
        # Update the brush data when selection changes
        self.update_multi_tile_brush_data()
    
    def clear_multi_tile_selection(self):
        """Clear all multi-tile selections"""
        self.multi_tile_selection.clear()
        self.multi_tile_brush_data.clear()
        self.multi_tile_mode = False
    
    def update_multi_tile_brush_data(self):
        """Calculate relative positions for multi-tile brush based on tileset layout"""
        if not self.multi_tile_selection:
            self.multi_tile_brush_data.clear()
            self.multi_tile_mode = False
            return
        
        self.multi_tile_mode = True
        self.multi_tile_brush_data.clear()
        
        # Calculate the bounding box of selected tiles
        if not self.tiles_per_row:
            return
            
        min_col = min_row = float('inf')
        max_col = max_row = float('-inf')
        
        tile_positions = []
        for tile_idx in self.multi_tile_selection:
            col = tile_idx % self.tiles_per_row
            row = tile_idx // self.tiles_per_row
            tile_positions.append((col, row, tile_idx))
            min_col = min(min_col, col)
            min_row = min(min_row, row)
            max_col = max(max_col, col)
            max_row = max(max_row, row)
        
        # Store relative positions from top-left of selection
        for col, row, tile_idx in tile_positions:
            rel_x = col - min_col
            rel_y = row - min_row
            self.multi_tile_brush_data.append((rel_x, rel_y, tile_idx))
    
    def paint_multi_tile_brush(self, cx: int, cy: int):
        """Paint the multi-tile brush pattern at the given position"""
        if not self.multi_tile_brush_data:
            return
            
        layer = self.layers[self.current_layer]
        if layer.locked or not layer.visible:
            return
        
        tile_changes = []
        
        for rel_x, rel_y, tile_idx in self.multi_tile_brush_data:
            tx = cx + rel_x
            ty = cy + rel_y
            
            # Skip if out of bounds
            if not (0 <= tx < self.map_cols and 0 <= ty < self.map_rows):
                continue
            
            old_tile = layer.data[ty][tx]
            if old_tile != tile_idx:  # Only paint if different
                tile_changes.append((tx, ty, old_tile, tile_idx))
        
        # Execute the command if there are changes
        if tile_changes:
            command = MultiTileCommand(self, self.current_layer, tile_changes)
            self.execute_command(command)

    def pick_at(self, cx: int, cy: int):
        if not (0 <= cx < self.map_cols and 0 <= cy < self.map_rows):
            return
        for li in reversed(range(len(self.layers))):
            idx = self.layers[li].data[cy][cx]
            if idx >= 0:
                self.selected_tile = idx
                break

    def flood_fill_at(self, cx: int, cy: int, new_tile: int):
        if not (0 <= cx < self.map_cols and 0 <= cy < self.map_rows):
            return
        layer = self.layers[self.current_layer]
        if layer.locked or not layer.visible:
            return
            
        original_tile = layer.data[cy][cx]
        if original_tile == new_tile:
            return  # No change needed
            
        # Performance limits for flood fill operations
        MAX_FILL_SIZE = 10000  # Maximum tiles to fill at once
        PROGRESS_THRESHOLD = 1000  # Show progress after this many tiles
        
        # Optimized flood fill using a deque for better performance
        from collections import deque
        queue = deque([(cx, cy)])
        filled = set()
        tile_changes = []
        processed_count = 0
        
        # Check for selection bounds if we have a selection
        selection_bounds = None
        if self.has_selection:
            bounds = self.get_selection_bounds()
            if bounds:
                selection_bounds = bounds
        
        while queue and len(tile_changes) < MAX_FILL_SIZE:
            x, y = queue.popleft()
            
            # Skip if already processed or out of bounds
            if (x, y) in filled:
                continue
            if not (0 <= x < self.map_cols and 0 <= y < self.map_rows):
                continue
            
            # Check selection bounds if applicable
            if selection_bounds:
                min_x, min_y, max_x, max_y = selection_bounds
                if not (min_x <= x <= max_x and min_y <= y <= max_y):
                    continue
            
            # Check if tile matches for filling
            current_tile = layer.data[y][x]
            if current_tile != original_tile:
                continue
                
            # Record the change
            tile_changes.append((x, y, original_tile, new_tile))
            filled.add((x, y))
            processed_count += 1
            
            # Add neighbors based on fill mode
            if self.fill_mode == 4:  # 4-connected
                neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            else:  # 8-connected
                neighbors = [
                    (x+1, y), (x-1, y), (x, y+1), (x, y-1),  # 4-connected
                    (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)  # diagonals
                ]
            
            for nx, ny in neighbors:
                if (nx, ny) not in filled:
                    queue.append((nx, ny))
            
            # Show progress for large operations
            if processed_count % PROGRESS_THRESHOLD == 0:
                print(f"Flood fill progress: {processed_count} tiles processed...")
        
        # Check if operation was too large and truncated
        if len(tile_changes) >= MAX_FILL_SIZE:
            print(f"Flood fill limited to {MAX_FILL_SIZE} tiles for performance")
        
        # Execute the flood fill as a single command
        if tile_changes:
            command = MultiTileCommand(self, self.current_layer, tile_changes)
            self.execute_command(command)
            print(f"Flood fill completed: {len(tile_changes)} tiles filled")

    # --------------------------- Shape Drawing Tools ---------------------------
    def get_line_tiles(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        """Bresenham line algorithm to get tiles for a line."""
        tiles = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                tiles.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                tiles.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        tiles.append((x, y))
        return tiles
    
    def get_rectangle_tiles(self, x0: int, y0: int, x1: int, y1: int, filled: bool = False) -> List[Tuple[int, int]]:
        """Get tiles for a rectangle (outline or filled)."""
        tiles = []
        min_x, max_x = min(x0, x1), max(x0, x1)
        min_y, max_y = min(y0, y1), max(y0, y1)
        
        if filled:
            # Filled rectangle
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    tiles.append((x, y))
        else:
            # Rectangle outline
            for x in range(min_x, max_x + 1):
                tiles.append((x, min_y))  # Top edge
                if max_y != min_y:
                    tiles.append((x, max_y))  # Bottom edge
            for y in range(min_y + 1, max_y):
                tiles.append((min_x, y))  # Left edge
                if max_x != min_x:
                    tiles.append((max_x, y))  # Right edge
        
        return tiles
    
    def get_circle_tiles(self, cx: int, cy: int, radius: int, filled: bool = False) -> List[Tuple[int, int]]:
        """Bresenham circle algorithm to get tiles for a circle."""
        tiles = []
        
        if radius == 0:
            tiles.append((cx, cy))
            return tiles
        
        x = 0
        y = radius
        d = 3 - 2 * radius
        
        def add_circle_points(cx, cy, x, y, filled):
            if filled:
                # Fill horizontal lines
                for i in range(-x, x + 1):
                    tiles.append((cx + i, cy + y))
                    if y != 0:
                        tiles.append((cx + i, cy - y))
                if x != y:
                    for i in range(-y, y + 1):
                        tiles.append((cx + i, cy + x))
                        if x != 0:
                            tiles.append((cx + i, cy - x))
            else:
                # Circle outline points
                points = [
                    (cx + x, cy + y), (cx - x, cy + y),
                    (cx + x, cy - y), (cx - x, cy - y),
                    (cx + y, cy + x), (cx - y, cy + x),
                    (cx + y, cy - x), (cx - y, cy - x)
                ]
                tiles.extend(points)
        
        add_circle_points(cx, cy, x, y, filled)
        
        while y >= x:
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            add_circle_points(cx, cy, x, y, filled)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tiles = []
        for tile in tiles:
            if tile not in seen:
                seen.add(tile)
                unique_tiles.append(tile)
        
        return unique_tiles
    
    def start_shape_drawing(self, cx: int, cy: int):
        """Start drawing a shape."""
        self.shape_start_tile = (cx, cy)
        self.shape_end_tile = (cx, cy)
        self.shape_dragging = True
        self.shape_preview_tiles = []
    
    def update_shape_preview(self, cx: int, cy: int):
        """Update the shape preview while dragging."""
        if not self.shape_dragging or not self.shape_start_tile:
            return
        
        self.shape_end_tile = (cx, cy)
        x0, y0 = self.shape_start_tile
        x1, y1 = self.shape_end_tile
        
        # Generate preview tiles based on current tool
        if self.tool == "line":
            self.shape_preview_tiles = self.get_line_tiles(x0, y0, x1, y1)
        elif self.tool == "rectangle":
            self.shape_preview_tiles = self.get_rectangle_tiles(x0, y0, x1, y1, self.shape_filled)
        elif self.tool == "circle":
            # Calculate radius from center to current point
            radius = max(abs(x1 - x0), abs(y1 - y0))
            self.shape_preview_tiles = self.get_circle_tiles(x0, y0, radius, self.shape_filled)
    
    def finish_shape_drawing(self):
        """Complete the shape drawing and apply it."""
        if not self.shape_dragging or not self.shape_preview_tiles or self.selected_tile is None:
            self.cancel_shape_drawing()
            return
        
        # Apply the shape to the map
        layer = self.layers[self.current_layer]
        tile_changes = []
        
        for cx, cy in self.shape_preview_tiles:
            if 0 <= cx < self.map_cols and 0 <= cy < self.map_rows:
                old_tile = layer.data[cy][cx]
                if old_tile != self.selected_tile:
                    tile_changes.append((cx, cy, old_tile, self.selected_tile))
                    layer.data[cy][cx] = self.selected_tile
        
        if tile_changes:
            command = MultiTileCommand(self, self.current_layer, tile_changes)
            self.execute_command(command)
        
        self.cancel_shape_drawing()
    
    def cancel_shape_drawing(self):
        """Cancel the current shape drawing operation."""
        self.shape_start_tile = None
        self.shape_end_tile = None
        self.shape_dragging = False
        self.shape_preview_tiles = []

    # --------------------------- Undo/Redo System ---------------------------
    def execute_command(self, command: Command):
        """Execute a command and add it to the history."""
        # Execute the command
        command.execute()
        
        # Remove any commands after the current history index (when undoing then doing new commands)
        if self.history_index < len(self.command_history) - 1:
            self.command_history = self.command_history[:self.history_index + 1]
        
        # Add the command to history
        self.command_history.append(command)
        self.history_index = len(self.command_history) - 1
        
        # Limit history size
        if len(self.command_history) > self.max_history_size:
            self.command_history.pop(0)
            self.history_index -= 1
        
        # Mark as modified
        self.mark_modified()
    
    def undo(self):
        """Undo the last command."""
        if self.history_index >= 0 and self.history_index < len(self.command_history):
            command = self.command_history[self.history_index]
            command.undo()
            self.history_index -= 1
            return True
        return False
    
    def redo(self):
        """Redo the next command."""
        if self.history_index + 1 < len(self.command_history):
            self.history_index += 1
            command = self.command_history[self.history_index]
            command.execute()
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.history_index >= 0 and self.history_index < len(self.command_history)
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.history_index + 1 < len(self.command_history)
    
    def get_undo_description(self) -> str:
        """Get description of the command that would be undone."""
        if self.can_undo():
            return self.command_history[self.history_index].get_description()
        return ""
    
    def get_redo_description(self) -> str:
        """Get description of the command that would be redone."""
        if self.can_redo():
            return self.command_history[self.history_index + 1].get_description()
        return ""
    
    def clear_history(self):
        """Clear the command history."""
        self.command_history.clear()
        self.history_index = -1
        
    # --------------------------- File Management & Modified State ---------------------------
    def mark_modified(self):
        """Mark the map as modified (has unsaved changes)."""
        if not self.is_modified:
            self.is_modified = True
            self.update_window_title()
    
    def mark_saved(self):
        """Mark the map as saved (no unsaved changes)."""
        if self.is_modified:
            self.is_modified = False
            self.update_window_title()
    
    def update_window_title(self):
        """Update the window title to reflect current file and modified state."""
        title = f"Tile Map Editor - {self.current_file_name}"
        if self.is_modified:
            title += " *"
        pygame.display.set_caption(title)
    
    def confirm_unsaved_changes(self, action_name: str = "continue") -> bool:
        """
        Show confirmation dialog if there are unsaved changes.
        Returns True if user wants to continue, False to cancel.
        """
        if not self.is_modified:
            return True
            
        # Create a temporary tkinter window for the dialog
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Keep on top
            
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"You have unsaved changes. Do you want to save before {action_name}?\n\n"
                "Yes - Save and continue\n"
                "No - Continue without saving\n"
                "Cancel - Don't continue",
                parent=root
            )
            
            root.destroy()
            
            if result is None:  # Cancel
                return False
            elif result is True:  # Yes - save first
                return self.save_current_file()
            else:  # No - continue without saving
                return True
                
        except Exception as e:
            print(f"Error showing confirmation dialog: {e}")
            return True  # Default to continuing
    
    def add_to_recent_files(self, file_path: str):
        """Add a file to the recent files list."""
        abs_path = os.path.abspath(file_path)
        
        # Remove if already in list
        if abs_path in self.recent_files:
            self.recent_files.remove(abs_path)
        
        # Add to front
        self.recent_files.insert(0, abs_path)
        
        # Limit list size
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        # Remove files that no longer exist
        self.recent_files = [f for f in self.recent_files if os.path.exists(f)]

    # --------------------------- Selection System ---------------------------
    def copy_selection(self):
        """Copy selected area to clipboard"""
        if not self.has_selection:
            return
            
        # Get selection bounds
        min_x = min(self.selection_start_x, self.selection_end_x)
        max_x = max(self.selection_start_x, self.selection_end_x)
        min_y = min(self.selection_start_y, self.selection_end_y)
        max_y = max(self.selection_start_y, self.selection_end_y)
        
        # Clamp to map bounds
        min_x = max(0, min(min_x, self.map_cols - 1))
        max_x = max(0, min(max_x, self.map_cols - 1))
        min_y = max(0, min(min_y, self.map_rows - 1))
        max_y = max(0, min(max_y, self.map_rows - 1))
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Copy tile data from current layer
        data = []
        layer = self.layers[self.current_layer]
        for y in range(height):
            row = []
            for x in range(width):
                tile_x = min_x + x
                tile_y = min_y + y
                if 0 <= tile_x < self.map_cols and 0 <= tile_y < self.map_rows:
                    row.append(layer.data[tile_y][tile_x])
                else:
                    row.append(-1)  # Empty tile
            data.append(row)
        
        self.clipboard = {
            'data': data,
            'width': width,
            'height': height
        }
        print(f"Copied {width}x{height} selection to clipboard")

    def cut_selection(self):
        """Cut selected area to clipboard (copy + erase)"""
        if not self.has_selection:
            return
            
        self.copy_selection()
        
        # Erase the selected area
        min_x = min(self.selection_start_x, self.selection_end_x)
        max_x = max(self.selection_start_x, self.selection_end_x)
        min_y = min(self.selection_start_y, self.selection_end_y)
        max_y = max(self.selection_start_y, self.selection_end_y)
        
        # Clamp to map bounds
        min_x = max(0, min(min_x, self.map_cols - 1))
        max_x = max(0, min(max_x, self.map_cols - 1))
        min_y = max(0, min(min_y, self.map_rows - 1))
        max_y = max(0, min(max_y, self.map_rows - 1))
        
        layer = self.layers[self.current_layer]
        if layer.locked or not layer.visible:
            return
            
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= x < self.map_cols and 0 <= y < self.map_rows:
                    layer.data[y][x] = -1
        
        # Clear selection after cutting
        self.has_selection = False
        print(f"Cut selection to clipboard")

    def start_paste(self):
        """Start paste preview mode"""
        if not self.clipboard:
            return
        
        # Get mouse position in tile coordinates
        mx, my = pygame.mouse.get_pos()
        if self.canvas_rect.collidepoint(mx, my):
            self.paste_x, self.paste_y = self.screen_to_tile(mx, my)
        else:
            self.paste_x, self.paste_y = 0, 0
            
        self.paste_preview = True
        print("Paste preview mode - click to place, Escape to cancel")

    def apply_paste(self, paste_x: int, paste_y: int):
        """Apply paste at specified coordinates"""
        if not self.clipboard or not self.paste_preview:
            return
            
        layer = self.layers[self.current_layer]
        if layer.locked or not layer.visible:
            return
            
        data = self.clipboard['data']
        width = self.clipboard['width']
        height = self.clipboard['height']
        
        # Paste the data
        for y in range(height):
            for x in range(width):
                target_x = paste_x + x
                target_y = paste_y + y
                
                # Check bounds
                if 0 <= target_x < self.map_cols and 0 <= target_y < self.map_rows:
                    tile_id = data[y][x]
                    if tile_id >= 0:  # Don't paste empty tiles
                        layer.data[target_y][target_x] = tile_id
        
        self.paste_preview = False
        print(f"Pasted {width}x{height} clipboard data at ({paste_x}, {paste_y})")

    # --------------------------- Stamp System ---------------------------
    def create_stamp_from_selection(self):
        """Create a new stamp from the current selection."""
        if not self.has_selection:
            print("No selection to create stamp from")
            return
        
        bounds = self.get_selection_bounds()
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Extract tile data from current layer
        stamp_data = []
        layer = self.layers[self.current_layer]
        
        for y in range(height):
            row = []
            for x in range(width):
                map_x = min_x + x
                map_y = min_y + y
                if 0 <= map_x < self.map_cols and 0 <= map_y < self.map_rows:
                    row.append(layer.data[map_y][map_x])
                else:
                    row.append(-1)  # Empty tile
            stamp_data.append(row)
        
        # Create stamp object
        stamp = {
            'name': f'Stamp {len(self.stamps) + 1}',
            'width': width,
            'height': height,
            'data': stamp_data,
            'layer': self.current_layer
        }
        
        self.stamps.append(stamp)
        print(f"Created stamp '{stamp['name']}' ({width}x{height})")
    
    def select_stamp(self, stamp_index: int):
        """Select a stamp for placement."""
        if 0 <= stamp_index < len(self.stamps):
            self.current_stamp = self.stamps[stamp_index]
            self.stamp_preview = True
            print(f"Selected stamp '{self.current_stamp['name']}'")
    
    def apply_stamp(self, stamp_x: int, stamp_y: int):
        """Apply the current stamp at the specified position."""
        if not self.current_stamp:
            return
        
        stamp = self.current_stamp
        width = stamp['width']
        height = stamp['height']
        data = stamp['data']
        
        layer = self.layers[self.current_layer]
        if layer.locked:
            return
        
        # Record tile changes for undo support
        tile_changes = []
        
        for y in range(height):
            for x in range(width):
                target_x = stamp_x + x
                target_y = stamp_y + y
                
                # Check bounds
                if 0 <= target_x < self.map_cols and 0 <= target_y < self.map_rows:
                    tile_id = data[y][x]
                    if tile_id >= 0:  # Don't place empty tiles
                        old_tile = layer.data[target_y][target_x]
                        if old_tile != tile_id:  # Only record actual changes
                            tile_changes.append((target_x, target_y, old_tile, tile_id))
        
        # Execute as undoable command
        if tile_changes:
            command = MultiTileCommand(self, self.current_layer, tile_changes)
            self.execute_command(command)
        
        self.stamp_preview = False
        print(f"Applied stamp '{stamp['name']}' at ({stamp_x}, {stamp_y})")
    
    def save_stamps_to_file(self):
        """Save stamps to a file for persistence."""
        stamp_file = os.path.join(self.save_dir, "stamps.json")
        try:
            with open(stamp_file, 'w') as f:
                json.dump(self.stamps, f, indent=2)
            print(f"Saved {len(self.stamps)} stamps to {stamp_file}")
        except Exception as e:
            print(f"Error saving stamps: {e}")
    
    def load_stamps_from_file(self):
        """Load stamps from file."""
        stamp_file = os.path.join(self.save_dir, "stamps.json")
        try:
            if os.path.exists(stamp_file):
                with open(stamp_file, 'r') as f:
                    self.stamps = json.load(f)
                print(f"Loaded {len(self.stamps)} stamps from {stamp_file}")
        except Exception as e:
            print(f"Error loading stamps: {e}")
            self.stamps = []
    
    # --------------------------- Pattern System ---------------------------
    def create_pattern_from_selection(self):
        """Create a pattern from the current selection."""
        if not self.has_selection:
            print("No selection to create pattern from")
            return
        
        bounds = self.get_selection_bounds()
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Extract tile data from current layer
        pattern_data = []
        layer = self.layers[self.current_layer]
        
        for y in range(height):
            row = []
            for x in range(width):
                map_x = min_x + x
                map_y = min_y + y
                if 0 <= map_x < self.map_cols and 0 <= map_y < self.map_rows:
                    row.append(layer.data[map_y][map_x])
                else:
                    row.append(-1)  # Empty tile
            pattern_data.append(row)
        
        self.pattern_data = {
            'width': width,
            'height': height,
            'data': pattern_data
        }
        
        self.pattern_mode = True
        print(f"Created pattern ({width}x{height}) - Pattern painting mode enabled")
    
    def get_pattern_tile(self, x: int, y: int) -> int:
        """Get the pattern tile for the given coordinates using tiling."""
        if not self.pattern_data:
            return -1
        
        pattern_x = x % self.pattern_data['width']
        pattern_y = y % self.pattern_data['height']
        
        return self.pattern_data['data'][pattern_y][pattern_x]
    
    def paint_with_pattern(self, cx: int, cy: int, brush_size: int = 1):
        """Paint using the current pattern with the specified brush size."""
        if not self.pattern_data:
            return
        
        layer = self.layers[self.current_layer]
        if layer.locked:
            return
        
        tile_changes = []
        half_size = brush_size // 2
        
        for dy in range(-half_size, brush_size - half_size):
            for dx in range(-half_size, brush_size - half_size):
                paint_x = cx + dx
                paint_y = cy + dy
                
                # Check bounds
                if 0 <= paint_x < self.map_cols and 0 <= paint_y < self.map_rows:
                    # Get pattern tile for this position
                    pattern_tile = self.get_pattern_tile(paint_x, paint_y)
                    
                    if pattern_tile >= 0:  # Valid pattern tile
                        old_tile = layer.data[paint_y][paint_x]
                        if old_tile != pattern_tile:
                            tile_changes.append((paint_x, paint_y, old_tile, pattern_tile))
        
        # Execute as undoable command
        if tile_changes:
            command = MultiTileCommand(self, self.current_layer, tile_changes)
            self.execute_command(command)

    def get_selection_bounds(self):
        """Get normalized selection bounds"""
        if not self.has_selection:
            return None
            
        min_x = min(self.selection_start_x, self.selection_end_x)
        max_x = max(self.selection_start_x, self.selection_end_x)
        min_y = min(self.selection_start_y, self.selection_end_y)
        max_y = max(self.selection_start_y, self.selection_end_y)
        
        return (min_x, min_y, max_x, max_y)

    def get_selection_rectangles(self):
        """Get all selection rectangles as a list of (min_x, min_y, max_x, max_y) tuples"""
        bounds = self.get_selection_bounds()
        if bounds:
            return [bounds]
        return []
    
    def point_in_any_selection(self, x: int, y: int) -> bool:
        """Check if a point is within any selection rectangle"""
        bounds = self.get_selection_bounds()
        if not bounds:
            return False
        min_x, min_y, max_x, max_y = bounds
        return min_x <= x <= max_x and min_y <= y <= max_y
    
    def rectangles_intersect(self, r1, r2):
        """Check if two rectangles (min_x, min_y, max_x, max_y) intersect"""
        return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])
    
    def combine_selection_rectangles(self, new_rect):
        """Combine current selection with new rectangle based on selection mode"""
        if not self.has_selection or self.selection_mode == "replace":
            # Replace mode: just use the new rectangle
            min_x, min_y, max_x, max_y = new_rect
            self.selection_start_x = min_x
            self.selection_start_y = min_y
            self.selection_end_x = max_x
            self.selection_end_y = max_y
            self.has_selection = True
        elif self.selection_mode == "add":
            # Add mode: expand selection to include new rectangle
            current_bounds = self.get_selection_bounds()
            if current_bounds:
                min_x = min(current_bounds[0], new_rect[0])
                min_y = min(current_bounds[1], new_rect[1])
                max_x = max(current_bounds[2], new_rect[2])
                max_y = max(current_bounds[3], new_rect[3])
                
                self.selection_start_x = min_x
                self.selection_start_y = min_y
                self.selection_end_x = max_x
                self.selection_end_y = max_y
        elif self.selection_mode == "subtract":
            # Subtract mode: for simplicity, just clear selection if they overlap
            # (Full subtract implementation would require multiple rectangles)
            current_bounds = self.get_selection_bounds()
            if current_bounds and self.rectangles_intersect(current_bounds, new_rect):
                self.has_selection = False
    
    def start_selection_drag(self, cx: int, cy: int, shift_held: bool, alt_held: bool):
        """Start selection drag with proper mode detection"""
        # Determine selection mode based on modifier keys
        if shift_held:
            self.selection_mode = "add"
            # Store original selection for potential restoration
            if self.has_selection:
                self.original_selection = (self.selection_start_x, self.selection_start_y, 
                                         self.selection_end_x, self.selection_end_y)
        elif alt_held:
            self.selection_mode = "subtract"
            # Store original selection for potential restoration
            if self.has_selection:
                self.original_selection = (self.selection_start_x, self.selection_start_y, 
                                         self.selection_end_x, self.selection_end_y)
        else:
            self.selection_mode = "replace"
            self.original_selection = None
        
        # Start the drag operation
        self.selection_dragging = True
        self.selection_start_x = cx
        self.selection_start_y = cy
        self.selection_end_x = cx
        self.selection_end_y = cy
        
        # For replace mode, clear selection immediately
        if self.selection_mode == "replace":
            self.has_selection = False
        
        # Clear any paste preview when starting new selection
        self.paste_preview = False
    
    def finish_selection_drag(self):
        """Finish selection drag and apply the appropriate selection mode"""
        if not self.selection_dragging:
            return
        
        # Get the new selection rectangle
        min_x = min(self.selection_start_x, self.selection_end_x)
        max_x = max(self.selection_start_x, self.selection_end_x)
        min_y = min(self.selection_start_y, self.selection_end_y)
        max_y = max(self.selection_start_y, self.selection_end_y)
        
        # Apply the selection based on mode
        new_rect = (min_x, min_y, max_x, max_y)
        self.combine_selection_rectangles(new_rect)
        
        # Clean up drag state
        self.selection_dragging = False
        self.original_selection = None

    # --------------------------- Zoom helpers ---------------------------
    def zoom_to(self, new_scale: float, focus_px: Tuple[int, int]):
        # Clamp to nearest step from zoom_levels
        new_scale = max(self.zoom_levels[0], min(self.zoom_levels[-1], new_scale))
        old_scale = self.VIEW_SCALE
        if abs(new_scale - old_scale) < 1e-6:
            return
        # Keep mouse focus point stable in world
        mx, my = focus_px
        if not self.canvas_rect.collidepoint(mx, my):
            # use center of canvas if cursor not over canvas
            mx, my = self.canvas_rect.center
        ts_old = int(self.TILE_SIZE * old_scale)
        ts_new = int(self.TILE_SIZE * new_scale)
        # World coordinate under mouse before
        wx = self.scroll_x + (mx - self.canvas_rect.x)
        wy = self.scroll_y + (my - self.canvas_rect.y)
        # Zoom
        self.VIEW_SCALE = new_scale
        # Adjust scroll so the same world point stays under mouse
        factor = ts_new / max(1, ts_old)
        self.scroll_x = int(wx * factor - (mx - self.canvas_rect.x))
        self.scroll_y = int(wy * factor - (my - self.canvas_rect.y))
        self.scroll_x = max(0, min(self.map_cols * ts_new, self.scroll_x))
        self.scroll_y = max(0, min(self.map_rows * ts_new, self.scroll_y))

    def zoom_step(self, delta: int, focus_px: Tuple[int, int]):
        # Find nearest index in zoom_levels
        cur = self.VIEW_SCALE
        idx = min(range(len(self.zoom_levels)), key=lambda i: abs(self.zoom_levels[i] - cur))
        idx = max(0, min(len(self.zoom_levels) - 1, idx + delta))
        self.zoom_to(self.zoom_levels[idx], focus_px)

    # --------------------------- Native File Operations ---------------------------
    def new_map(self):
        """Create a new map, confirming unsaved changes first."""
        if not self.confirm_unsaved_changes("creating a new map"):
            return
        
        # Reset to default map
        self.map_cols = 100
        self.map_rows = 60
        self.layers = [
            Layer("Background", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
            Layer("Foreground", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
        ]
        self.current_layer = 1
        
        # Reset file state
        self.current_file_path = None
        self.current_file_name = "Untitled"
        self.mark_saved()
        self.clear_history()
        
        print("Created new map")
    
    def open_map(self):
        """Open a map file using native file dialog."""
        if not self.confirm_unsaved_changes("opening a file"):
            return
        
        try:
            # Create file dialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_path = filedialog.askopenfilename(
                title="Open Map File",
                initialdir=self.last_directory,
                filetypes=[
                    ("Map files", "*.json"),
                    ("TMX files", "*.tmx"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                self.load_map_from_file(file_path)
                
        except Exception as e:
            print(f"Error opening file dialog: {e}")
    
    def save_current_file(self) -> bool:
        """Save the current file. Returns True if successful."""
        if self.current_file_path:
            return self.save_map_to_file(self.current_file_path)
        else:
            return self.save_as_map()
    
    def save_as_map(self) -> bool:
        """Save As dialog. Returns True if successful."""
        try:
            # Create file dialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            file_path = filedialog.asksaveasfilename(
                title="Save Map As",
                initialdir=self.last_directory,
                defaultextension=".json",
                filetypes=[
                    ("Map files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                return self.save_map_to_file(file_path)
            return False
                
        except Exception as e:
            print(f"Error opening save dialog: {e}")
            return False
    
    def save_map_to_file(self, file_path: str) -> bool:
        """Save map to specific file path. Returns True if successful."""
        try:
            # Prepare map data
            out = {
                "tileset": "Assests/Cave_Tileset.png",
                "tile_size": self.TILE_SIZE,
                "margin": self.margin,
                "spacing": self.spacing,
                "map_cols": self.map_cols,
                "map_rows": self.map_rows,
                "layers": [],
                "tile_properties": {},  # Add tile properties to save data
                "objects": []  # Add objects array
            }
            
            # Save tile properties
            for tile_idx, props in self.tile_properties.items():
                out["tile_properties"][str(tile_idx)] = props.to_dict()
            
            # Save objects
            for obj in self.objects:
                out["objects"].append(obj.to_dict())
            
            for layer in self.layers:
                tiles = []
                for y in range(self.map_rows):
                    row = layer.data[y]
                    for x in range(self.map_cols):
                        t = row[x]
                        if t >= 0:
                            tiles.append({"x": x, "y": y, "t": t})
                out["layers"].append({
                    "name": layer.name, 
                    "tiles": tiles,
                    "visible": layer.visible,
                    "locked": layer.locked
                })

            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            
            # Update file state
            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)
            self.last_directory = os.path.dirname(file_path)
            self.mark_saved()
            self.add_to_recent_files(file_path)
            
            print(f"Saved map to {file_path}")
            return True
            
        except Exception as e:
            # Show error dialog
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Save Error", f"Failed to save map:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to save map: {e}")
            return False
    
    def load_map_from_file(self, file_path: str):
        """Load map from specific file path."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Parse map data
            self.map_cols = int(data.get("map_cols", self.map_cols))
            self.map_rows = int(data.get("map_rows", self.map_rows))
            ts = int(data.get("tile_size", self.TILE_SIZE))
            margin = int(data.get("margin", self.margin))
            spacing = int(data.get("spacing", self.spacing))
            
            # Update tileset if needed
            changed = (ts != self.TILE_SIZE) or (margin != self.margin) or (spacing != self.spacing)
            if changed:
                self.TILE_SIZE, self.margin, self.spacing = ts, margin, spacing
                self.PALETTE_SCALE = max(1, 2 if self.TILE_SIZE <= 32 else 1)
                self.slice_tiles()
            
            # Load layers
            layers_json = data.get("layers", [])
            self.layers = []
            for lj in layers_json:
                grid = [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]
                for t in lj.get("tiles", []):
                    x, y, ti = t["x"], t["y"], t["t"]
                    if 0 <= x < self.map_cols and 0 <= y < self.map_rows:
                        grid[y][x] = ti
                layer = Layer(lj.get("name", "Layer"), grid)
                layer.visible = lj.get("visible", True)
                layer.locked = lj.get("locked", False)
                self.layers.append(layer)
            
            if not self.layers:
                self.layers = [
                    Layer("Background", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
                    Layer("Foreground", [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]),
                ]
            
            self.current_layer = min(self.current_layer, len(self.layers) - 1)
            
            # Load tile properties
            self.tile_properties = {}
            tile_props_data = data.get("tile_properties", {})
            for tile_idx_str, props_dict in tile_props_data.items():
                try:
                    tile_idx = int(tile_idx_str)
                    self.tile_properties[tile_idx] = TileProperties.from_dict(props_dict)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Failed to load tile properties for tile {tile_idx_str}: {e}")
            
            # Load objects
            self.objects = []
            objects_data = data.get("objects", [])
            max_counters = {}  # Track highest numbers to resume counters properly
            for obj_data in objects_data:
                try:
                    obj = GameObject.from_dict(obj_data)
                    self.objects.append(obj)
                    
                    # Track highest counter for each object type
                    obj_type = obj.object_type
                    if obj_type not in max_counters:
                        max_counters[obj_type] = 0
                    
                    # Extract number from name (e.g., "Enemy_05" -> 5)
                    try:
                        name_parts = obj.name.split('_')
                        if len(name_parts) == 2 and name_parts[1].isdigit():
                            counter = int(name_parts[1])
                            max_counters[obj_type] = max(max_counters[obj_type], counter)
                    except:
                        pass
                        
                except (ValueError, KeyError) as e:
                    print(f"Warning: Failed to load object: {e}")
            
            # Update object counters to avoid duplicates
            for obj_type, _, _ in self.OBJECT_TYPES:
                self.object_counters[obj_type] = max_counters.get(obj_type, 0)
            
            # Update file state
            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)
            self.last_directory = os.path.dirname(file_path)
            self.mark_saved()
            self.clear_history()
            self.add_to_recent_files(file_path)
            self.apply_layer_preferences()
            
            print(f"Loaded map from {file_path}")
            
        except Exception as e:
            # Show error dialog
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Load Error", f"Failed to load map:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to load map: {e}")
    
    # Legacy methods for backward compatibility
    def save_map(self):
        """Legacy save method - now calls save_current_file."""
        self.save_current_file()

    def load_map(self):
        """Legacy load method - now calls open_map."""
        self.open_map()
        
    # --------------------------- Auto-Save System ---------------------------
    def update_auto_save(self):
        """Update auto-save system - call this in main loop."""
        if not self.auto_save_enabled or not self.is_modified:
            self.auto_save_indicator = False
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_auto_save
        
        # Show indicator when approaching auto-save time
        if time_since_last > (self.auto_save_interval - 30):  # Show 30 seconds before
            self.auto_save_indicator = True
        
        # Perform auto-save
        if time_since_last >= self.auto_save_interval:
            self.perform_auto_save()
            self.last_auto_save = current_time
    
    def perform_auto_save(self):
        """Perform an auto-save operation."""
        if not self.current_file_path:
            # No file path - create auto-save in default directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_save_path = os.path.join(self.save_dir, f"autosave_{timestamp}.json")
        else:
            # Create auto-save alongside current file
            base, ext = os.path.splitext(self.current_file_path)
            auto_save_path = f"{base}.autosave{ext}"
        
        try:
            # Prepare map data (same as regular save)
            out = {
                "tileset": "Assests/Cave_Tileset.png",
                "tile_size": self.TILE_SIZE,
                "margin": self.margin,
                "spacing": self.spacing,
                "map_cols": self.map_cols,
                "map_rows": self.map_rows,
                "layers": [],
                "auto_save_timestamp": datetime.now().isoformat(),
                "original_file": self.current_file_path
            }
            
            for layer in self.layers:
                tiles = []
                for y in range(self.map_rows):
                    row = layer.data[y]
                    for x in range(self.map_cols):
                        t = row[x]
                        if t >= 0:
                            tiles.append({"x": x, "y": y, "t": t})
                out["layers"].append({
                    "name": layer.name, 
                    "tiles": tiles,
                    "visible": layer.visible,
                    "locked": layer.locked
                })

            # Save auto-save file
            with open(auto_save_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            
            print(f"Auto-saved to {auto_save_path}")
            self.auto_save_indicator = False
            
        except Exception as e:
            print(f"Auto-save failed: {e}")
    
    def check_for_auto_save_recovery(self):
        """Check for auto-save files on startup and offer recovery."""
        auto_save_files = []
        
        # Check default directory for auto-save files
        if os.path.exists(self.save_dir):
            for filename in os.listdir(self.save_dir):
                if filename.startswith("autosave_") and filename.endswith(".json"):
                    auto_save_files.append(os.path.join(self.save_dir, filename))
        
        # Check alongside recent files
        for recent_file in self.recent_files[:5]:  # Check last 5 recent files
            if os.path.exists(recent_file):
                base, ext = os.path.splitext(recent_file)
                auto_save_path = f"{base}.autosave{ext}"
                if os.path.exists(auto_save_path):
                    auto_save_files.append(auto_save_path)
        
        if auto_save_files:
            self.offer_auto_save_recovery(auto_save_files)
    
    def offer_auto_save_recovery(self, auto_save_files: list):
        """Offer to recover from auto-save files."""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Find the most recent auto-save
            most_recent = max(auto_save_files, key=lambda f: os.path.getmtime(f))
            mod_time = datetime.fromtimestamp(os.path.getmtime(most_recent))
            
            result = messagebox.askyesno(
                "Auto-Save Recovery",
                f"Found auto-save file from {mod_time.strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
                f"Would you like to recover your unsaved work?\n\n"
                f"File: {os.path.basename(most_recent)}",
                parent=root
            )
            
            root.destroy()
            
            if result:
                self.load_map_from_file(most_recent)
                self.mark_modified()  # Mark as modified since it's recovered work
                print(f"Recovered from auto-save: {most_recent}")
            
        except Exception as e:
            print(f"Error during auto-save recovery: {e}")
    
    def cleanup_auto_save_files(self):
        """Clean up old auto-save files."""
        try:
            current_time = time.time()
            max_age = 7 * 24 * 3600  # 7 days in seconds
            
            # Clean up files in save directory
            if os.path.exists(self.save_dir):
                for filename in os.listdir(self.save_dir):
                    if filename.startswith("autosave_") and filename.endswith(".json"):
                        file_path = os.path.join(self.save_dir, filename)
                        if current_time - os.path.getmtime(file_path) > max_age:
                            os.remove(file_path)
                            print(f"Cleaned up old auto-save: {filename}")
            
        except Exception as e:
            print(f"Error cleaning up auto-save files: {e}")

    # --------------------------- Export System (Phase 3.2) ---------------------------
    def export_as_png(self, file_path: str = None, export_options: dict = None) -> bool:
        """Export map as PNG image with all visible layers composited."""
        try:
            if file_path is None:
                # Show save dialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.asksaveasfilename(
                    title="Export as PNG",
                    initialdir=self.last_directory,
                    defaultextension=".png",
                    filetypes=[
                        ("PNG files", "*.png"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse export options
            options = export_options or {}
            scale_factor = options.get('scale_factor', 1.0)
            export_layers = options.get('layers', 'all')  # 'all', 'visible', or list of indices
            include_grid = options.get('include_grid', False)
            background_color = options.get('background_color', (0, 0, 0, 0))  # Transparent by default
            
            # Calculate export dimensions
            tile_size = int(self.TILE_SIZE * scale_factor)
            export_width = self.map_cols * tile_size
            export_height = self.map_rows * tile_size
            
            # Create export surface with alpha support
            export_surface = pygame.Surface((export_width, export_height), pygame.SRCALPHA)
            
            # Fill background if not transparent
            if background_color[3] > 0:
                export_surface.fill(background_color)
            
            # Determine which layers to export
            layers_to_export = []
            if export_layers == 'all':
                layers_to_export = list(range(len(self.layers)))
            elif export_layers == 'visible':
                layers_to_export = [i for i, layer in enumerate(self.layers) if layer.visible]
            elif isinstance(export_layers, list):
                layers_to_export = export_layers
            
            # Render each layer
            for layer_index in layers_to_export:
                if 0 <= layer_index < len(self.layers):
                    layer = self.layers[layer_index]
                    if not layer.visible and export_layers != 'all':
                        continue
                    
                    # Render all tiles in this layer
                    for y in range(self.map_rows):
                        for x in range(self.map_cols):
                            tile_id = layer.data[y][x]
                            if tile_id >= 0 and tile_id < len(self.tiles):
                                tile_surface = self.tiles[tile_id]
                                
                                # Scale tile if necessary
                                if scale_factor != 1.0:
                                    scaled_size = (tile_size, tile_size)
                                    tile_surface = pygame.transform.scale(tile_surface, scaled_size)
                                
                                # Blit to export surface
                                export_surface.blit(tile_surface, (x * tile_size, y * tile_size))
            
            # Draw grid if requested
            if include_grid:
                grid_color = options.get('grid_color', (128, 128, 128, 128))
                for x in range(self.map_cols + 1):
                    pygame.draw.line(export_surface, grid_color, 
                                   (x * tile_size, 0), (x * tile_size, export_height))
                for y in range(self.map_rows + 1):
                    pygame.draw.line(export_surface, grid_color, 
                                   (0, y * tile_size), (export_width, y * tile_size))
            
            # Save as PNG
            pygame.image.save(export_surface, file_path)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Exported PNG to {file_path}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Export Error", f"Failed to export PNG:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to export PNG: {e}")
            return False
    
    def export_as_csv(self, file_path: str = None, export_options: dict = None) -> bool:
        """Export each layer as separate CSV file."""
        try:
            if file_path is None:
                # Show save dialog for base filename
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.asksaveasfilename(
                    title="Export as CSV (base filename)",
                    initialdir=self.last_directory,
                    defaultextension=".csv",
                    filetypes=[
                        ("CSV files", "*.csv"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse export options
            options = export_options or {}
            delimiter = options.get('delimiter', ',')
            include_headers = options.get('include_headers', True)
            empty_cell_value = options.get('empty_cell_value', '-1')
            export_layers = options.get('layers', 'visible')  # 'all', 'visible', or list of indices
            
            # Determine which layers to export
            layers_to_export = []
            if export_layers == 'all':
                layers_to_export = list(range(len(self.layers)))
            elif export_layers == 'visible':
                layers_to_export = [i for i, layer in enumerate(self.layers) if layer.visible]
            elif isinstance(export_layers, list):
                layers_to_export = export_layers
            
            # Get base filename without extension
            base_path, ext = os.path.splitext(file_path)
            
            exported_files = []
            
            for layer_index in layers_to_export:
                if 0 <= layer_index < len(self.layers):
                    layer = self.layers[layer_index]
                    
                    # Create filename for this layer
                    safe_layer_name = "".join(c for c in layer.name if c.isalnum() or c in (' ', '-', '_')).strip()
                    layer_file_path = f"{base_path}_{safe_layer_name}.csv"
                    
                    with open(layer_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                        # Write header if requested
                        if include_headers:
                            header = [str(x) for x in range(self.map_cols)]
                            csvfile.write(delimiter.join(header) + '\n')
                        
                        # Write map data
                        for y in range(self.map_rows):
                            row_data = []
                            for x in range(self.map_cols):
                                tile_id = layer.data[y][x]
                                if tile_id == -1:
                                    row_data.append(str(empty_cell_value))
                                else:
                                    row_data.append(str(tile_id))
                            csvfile.write(delimiter.join(row_data) + '\n')
                    
                    exported_files.append(layer_file_path)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Exported CSV files: {exported_files}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Export Error", f"Failed to export CSV:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to export CSV: {e}")
            return False
    
    def export_as_tmx(self, file_path: str = None, export_options: dict = None) -> bool:
        """Export as TMX file (basic Tiled compatibility)."""
        try:
            if file_path is None:
                # Show save dialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.asksaveasfilename(
                    title="Export as TMX",
                    initialdir=self.last_directory,
                    defaultextension=".tmx",
                    filetypes=[
                        ("TMX files", "*.tmx"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse export options
            options = export_options or {}
            compression = options.get('compression', 'none')  # 'none', 'gzip', 'zlib'
            encoding = options.get('encoding', 'csv')  # 'xml', 'csv', 'base64'
            
            # Build TMX XML structure
            tmx_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            tmx_content += f'<map version="1.5" tiledversion="1.7.2" orientation="orthogonal" renderorder="right-down" ' \
                          f'width="{self.map_cols}" height="{self.map_rows}" tilewidth="{self.TILE_SIZE}" ' \
                          f'tileheight="{self.TILE_SIZE}" infinite="0" nextlayerid="{len(self.layers) + 1}" nextobjectid="1">\n'
            
            # Add tileset reference
            tileset_name = os.path.basename(self.save_path) if hasattr(self, 'save_path') else "tileset"
            tmx_content += f'  <tileset firstgid="1" name="{tileset_name}" tilewidth="{self.TILE_SIZE}" ' \
                          f'tileheight="{self.TILE_SIZE}" tilecount="{len(self.tiles)}" columns="{self.tiles_per_row}">\n'
            tmx_content += f'    <image source="Assests/Cave_Tileset.png" width="{self.tileset_surface.get_width()}" ' \
                          f'height="{self.tileset_surface.get_height()}"/>\n'
            tmx_content += '  </tileset>\n'
            
            # Export each layer
            for layer_index, layer in enumerate(self.layers):
                if not layer.visible:
                    continue
                    
                tmx_content += f'  <layer id="{layer_index + 1}" name="{layer.name}" width="{self.map_cols}" height="{self.map_rows}"'
                if not layer.visible:
                    tmx_content += ' visible="0"'
                tmx_content += '>\n'
                
                # Layer data
                tmx_content += f'    <data encoding="{encoding}"'
                if compression != 'none':
                    tmx_content += f' compression="{compression}"'
                tmx_content += '>\n'
                
                if encoding == 'csv':
                    # CSV format (most compatible)
                    csv_data = []
                    for y in range(self.map_rows):
                        for x in range(self.map_cols):
                            tile_id = layer.data[y][x]
                            # TMX uses 0 for empty, 1+ for tiles (firstgid offset)
                            tmx_tile_id = tile_id + 1 if tile_id >= 0 else 0
                            csv_data.append(str(tmx_tile_id))
                    
                    # Format as CSV with line breaks every map_cols tiles
                    for i in range(0, len(csv_data), self.map_cols):
                        row_data = csv_data[i:i + self.map_cols]
                        tmx_content += '      ' + ','.join(row_data)
                        if i + self.map_cols < len(csv_data):
                            tmx_content += ','
                        tmx_content += '\n'
                
                tmx_content += '    </data>\n'
                tmx_content += '  </layer>\n'
            
            tmx_content += '</map>\n'
            
            # Write TMX file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tmx_content)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Exported TMX to {file_path}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Export Error", f"Failed to export TMX:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to export TMX: {e}")
            return False
    
    def export_as_python_module(self, file_path: str = None, export_options: dict = None) -> bool:
        """Export as Python module with map data constants."""
        try:
            if file_path is None:
                # Show save dialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.asksaveasfilename(
                    title="Export as Python Module",
                    initialdir=self.last_directory,
                    defaultextension=".py",
                    filetypes=[
                        ("Python files", "*.py"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse export options
            options = export_options or {}
            module_name = options.get('module_name', os.path.splitext(os.path.basename(file_path))[0])
            include_metadata = options.get('include_metadata', True)
            data_format = options.get('data_format', 'lists')  # 'lists' or 'dicts'
            
            # Generate Python module content
            py_content = f'"""Generated map data from Tile Map Editor\n'
            if include_metadata:
                py_content += f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                py_content += f'Map dimensions: {self.map_cols}x{self.map_rows} tiles\n'
                py_content += f'Tile size: {self.TILE_SIZE}px\n'
                py_content += f'Number of layers: {len(self.layers)}\n'
            py_content += '"""\n\n'
            
            # Module constants
            py_content += f'# Map constants\n'
            py_content += f'MAP_WIDTH = {self.map_cols}\n'
            py_content += f'MAP_HEIGHT = {self.map_rows}\n'
            py_content += f'TILE_SIZE = {self.TILE_SIZE}\n'
            py_content += f'TILESET_PATH = "Assests/Cave_Tileset.png"\n'
            py_content += f'TILESET_MARGIN = {self.margin}\n'
            py_content += f'TILESET_SPACING = {self.spacing}\n'
            py_content += f'TILES_PER_ROW = {self.tiles_per_row}\n'
            py_content += f'TOTAL_TILES = {len(self.tiles)}\n\n'
            
            # Layer data
            if data_format == 'lists':
                py_content += f'# Layer data as nested lists\n'
                py_content += f'# Format: LAYERS[layer_index][y][x] = tile_id (-1 = empty)\n'
                py_content += f'LAYERS = [\n'
                
                for layer_index, layer in enumerate(self.layers):
                    py_content += f'    # Layer {layer_index}: {layer.name}\n'
                    py_content += f'    [\n'
                    for y in range(self.map_rows):
                        py_content += f'        ['
                        row_data = [str(layer.data[y][x]) for x in range(self.map_cols)]
                        py_content += ', '.join(row_data)
                        py_content += ']'
                        if y < self.map_rows - 1:
                            py_content += ','
                        py_content += '\n'
                    py_content += f'    ]'
                    if layer_index < len(self.layers) - 1:
                        py_content += ','
                    py_content += '\n'
                
                py_content += f']\n\n'
                
            elif data_format == 'dicts':
                py_content += f'# Layer data as dictionaries\n'
                py_content += f'LAYERS = {{\n'
                
                for layer_index, layer in enumerate(self.layers):
                    py_content += f'    "{layer.name}": {{\n'
                    py_content += f'        "index": {layer_index},\n'
                    py_content += f'        "visible": {layer.visible},\n'
                    py_content += f'        "locked": {layer.locked},\n'
                    py_content += f'        "data": [\n'
                    
                    for y in range(self.map_rows):
                        py_content += f'            ['
                        row_data = [str(layer.data[y][x]) for x in range(self.map_cols)]
                        py_content += ', '.join(row_data)
                        py_content += ']'
                        if y < self.map_rows - 1:
                            py_content += ','
                        py_content += '\n'
                    
                    py_content += f'        ]\n'
                    py_content += f'    }}'
                    if layer_index < len(self.layers) - 1:
                        py_content += ','
                    py_content += '\n'
                
                py_content += f'}}\n\n'
            
            # Helper functions
            py_content += f'# Helper functions for map data access\n'
            py_content += f'def get_tile(layer_index, x, y):\n'
            py_content += f'    """Get tile ID at position (x, y) in specified layer."""\n'
            py_content += f'    if 0 <= layer_index < len(LAYERS) and 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:\n'
            if data_format == 'lists':
                py_content += f'        return LAYERS[layer_index][y][x]\n'
            else:
                py_content += f'        layer_name = list(LAYERS.keys())[layer_index]\n'
                py_content += f'        return LAYERS[layer_name]["data"][y][x]\n'
            py_content += f'    return -1\n\n'
            
            py_content += f'def get_tile_by_name(layer_name, x, y):\n'
            py_content += f'    """Get tile ID at position (x, y) in named layer."""\n'
            if data_format == 'dicts':
                py_content += f'    if layer_name in LAYERS and 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:\n'
                py_content += f'        return LAYERS[layer_name]["data"][y][x]\n'
            else:
                py_content += f'    # Layer names for lists format\n'
                layer_names = [f'"{layer.name}"' for layer in self.layers]
                py_content += f'    layer_names = [{", ".join(layer_names)}]\n'
                py_content += f'    if layer_name in layer_names and 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:\n'
                py_content += f'        layer_index = layer_names.index(layer_name)\n'
                py_content += f'        return LAYERS[layer_index][y][x]\n'
            py_content += f'    return -1\n\n'
            
            # Write Python module
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(py_content)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Exported Python module to {file_path}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Export Error", f"Failed to export Python module:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to export Python module: {e}")
            return False

    # --------------------------- Import System (Phase 3.2) ---------------------------
    def import_csv(self, file_path: str = None, import_options: dict = None) -> bool:
        """Import CSV file as new layer."""
        try:
            if file_path is None:
                # Show open dialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.askopenfilename(
                    title="Import CSV File",
                    initialdir=self.last_directory,
                    filetypes=[
                        ("CSV files", "*.csv"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse import options
            options = import_options or {}
            delimiter = options.get('delimiter', None)  # Auto-detect if None
            has_header = options.get('has_header', None)  # Auto-detect if None
            layer_name = options.get('layer_name', os.path.splitext(os.path.basename(file_path))[0])
            
            # Read and parse CSV file
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                content = csvfile.read().strip()
                lines = content.split('\n')
            
            if not lines:
                raise ValueError("CSV file is empty")
            
            # Auto-detect delimiter if not specified
            if delimiter is None:
                sample_line = lines[0]
                if ',' in sample_line:
                    delimiter = ','
                elif ';' in sample_line:
                    delimiter = ';'
                elif '\t' in sample_line:
                    delimiter = '\t'
                else:
                    delimiter = ','
            
            # Parse all rows
            parsed_rows = []
            for line in lines:
                if line.strip():
                    row = [cell.strip() for cell in line.split(delimiter)]
                    parsed_rows.append(row)
            
            if not parsed_rows:
                raise ValueError("No valid data rows found in CSV")
            
            # Auto-detect header if not specified
            if has_header is None:
                # Check if first row looks like numeric data
                first_row = parsed_rows[0]
                try:
                    [int(cell) if cell != '' else -1 for cell in first_row[:5]]  # Test first 5 cells
                    has_header = False
                except ValueError:
                    has_header = True
            
            # Skip header row if present
            data_rows = parsed_rows[1:] if has_header else parsed_rows
            
            if not data_rows:
                raise ValueError("No data rows found after header")
            
            # Determine dimensions
            import_height = len(data_rows)
            import_width = max(len(row) for row in data_rows) if data_rows else 0
            
            # Validate dimensions
            if import_width > self.map_cols or import_height > self.map_rows:
                result = messagebox.askyesno(
                    "Import Size Mismatch",
                    f"CSV data ({import_width}x{import_height}) is larger than current map "
                    f"({self.map_cols}x{self.map_rows}).\n\nDo you want to resize the map to fit the imported data?"
                )
                
                if result:
                    # Resize map to accommodate import
                    new_cols = max(self.map_cols, import_width)
                    new_rows = max(self.map_rows, import_height)
                    
                    # Resize all existing layers
                    for layer in self.layers:
                        # Extend existing rows
                        for row in layer.data:
                            while len(row) < new_cols:
                                row.append(-1)
                        
                        # Add new rows
                        while len(layer.data) < new_rows:
                            layer.data.append([-1] * new_cols)
                    
                    self.map_cols = new_cols
                    self.map_rows = new_rows
                else:
                    # Crop import data to fit
                    import_width = min(import_width, self.map_cols)
                    import_height = min(import_height, self.map_rows)
            
            # Create new layer with imported data
            layer_data = [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]
            
            for y, row in enumerate(data_rows[:import_height]):
                for x, cell in enumerate(row[:import_width]):
                    try:
                        if cell == '' or cell == '-1' or cell.lower() == 'null':
                            tile_id = -1
                        else:
                            tile_id = int(cell)
                            # Validate tile ID
                            if tile_id >= len(self.tiles):
                                tile_id = -1
                        layer_data[y][x] = tile_id
                    except ValueError:
                        layer_data[y][x] = -1
            
            # Create and add new layer
            new_layer = Layer(layer_name, layer_data)
            
            # Use command for undo support
            command = LayerAddCommand(self, new_layer, len(self.layers))
            self.execute_command(command)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Imported CSV as layer '{layer_name}' from {file_path}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Import Error", f"Failed to import CSV:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to import CSV: {e}")
            return False
    
    def import_tmx(self, file_path: str = None, import_options: dict = None) -> bool:
        """Import basic TMX file (Tiled map format)."""
        try:
            if file_path is None:
                # Show open dialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                file_path = filedialog.askopenfilename(
                    title="Import TMX File",
                    initialdir=self.last_directory,
                    filetypes=[
                        ("TMX files", "*.tmx"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                if not file_path:
                    return False
            
            # Parse TMX file
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root_element = tree.getroot()
            
            if root_element.tag != 'map':
                raise ValueError("Invalid TMX file: root element is not 'map'")
            
            # Extract map properties
            map_width = int(root_element.get('width', '0'))
            map_height = int(root_element.get('height', '0'))
            tile_width = int(root_element.get('tilewidth', str(self.TILE_SIZE)))
            tile_height = int(root_element.get('tileheight', str(self.TILE_SIZE)))
            
            if map_width == 0 or map_height == 0:
                raise ValueError("Invalid map dimensions in TMX file")
            
            # Check if we need to resize our map
            if map_width != self.map_cols or map_height != self.map_rows:
                result = messagebox.askyesno(
                    "Map Size Mismatch",
                    f"TMX map ({map_width}x{map_height}) has different dimensions than current map "
                    f"({self.map_cols}x{self.map_rows}).\n\nDo you want to resize the current map to match?"
                )
                
                if result:
                    # Resize current map
                    for layer in self.layers:
                        # Adjust existing rows
                        for row in layer.data:
                            if len(row) < map_width:
                                row.extend([-1] * (map_width - len(row)))
                            elif len(row) > map_width:
                                del row[map_width:]
                        
                        # Adjust number of rows
                        if len(layer.data) < map_height:
                            for _ in range(map_height - len(layer.data)):
                                layer.data.append([-1] * map_width)
                        elif len(layer.data) > map_height:
                            del layer.data[map_height:]
                    
                    self.map_cols = map_width
                    self.map_rows = map_height
            
            # Extract tilesets (for firstgid offset)
            firstgid = 1  # Default TMX firstgid
            for tileset in root_element.findall('tileset'):
                firstgid = int(tileset.get('firstgid', '1'))
                break  # Use first tileset for now
            
            # Import layers
            imported_layers = []
            for layer_element in root_element.findall('layer'):
                layer_name = layer_element.get('name', 'Imported Layer')
                layer_width = int(layer_element.get('width', str(map_width)))
                layer_height = int(layer_element.get('height', str(map_height)))
                visible = layer_element.get('visible', '1') == '1'
                
                # Find layer data
                data_element = layer_element.find('data')
                if data_element is None:
                    continue
                
                encoding = data_element.get('encoding', 'xml')
                compression = data_element.get('compression', 'none')
                
                # Parse layer data based on encoding
                layer_data = [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)]
                
                if encoding == 'csv':
                    # CSV encoding (most common)
                    csv_data = data_element.text.strip()
                    # Remove whitespace and split by commas
                    tile_ids = [int(tid.strip()) for tid in csv_data.replace('\n', '').split(',') if tid.strip()]
                    
                    # Convert to 2D array
                    for i, tile_id in enumerate(tile_ids):
                        if i >= layer_width * layer_height:
                            break
                        x = i % layer_width
                        y = i // layer_width
                        
                        if y < self.map_rows and x < self.map_cols:
                            # Convert TMX tile ID to our format
                            our_tile_id = tile_id - firstgid if tile_id > 0 else -1
                            # Validate tile ID
                            if our_tile_id >= len(self.tiles):
                                our_tile_id = -1
                            layer_data[y][x] = our_tile_id
                
                elif encoding == 'xml':
                    # XML encoding (tile elements)
                    tiles = data_element.findall('tile')
                    for i, tile_element in enumerate(tiles):
                        if i >= layer_width * layer_height:
                            break
                        x = i % layer_width
                        y = i // layer_width
                        
                        if y < self.map_rows and x < self.map_cols:
                            tile_id = int(tile_element.get('gid', '0'))
                            our_tile_id = tile_id - firstgid if tile_id > 0 else -1
                            if our_tile_id >= len(self.tiles):
                                our_tile_id = -1
                            layer_data[y][x] = our_tile_id
                
                else:
                    # Unsupported encoding (base64, etc.)
                    print(f"Warning: Unsupported encoding '{encoding}' for layer '{layer_name}'")
                    continue
                
                # Create layer
                new_layer = Layer(layer_name, layer_data, visible=visible)
                imported_layers.append(new_layer)
            
            if not imported_layers:
                raise ValueError("No valid layers found in TMX file")
            
            # Add imported layers using commands for undo support
            for layer in imported_layers:
                command = LayerAddCommand(self, layer, len(self.layers))
                self.execute_command(command)
            
            # Update last directory
            self.last_directory = os.path.dirname(file_path)
            
            print(f"Imported {len(imported_layers)} layers from TMX: {file_path}")
            return True
            
        except Exception as e:
            try:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showerror("Import Error", f"Failed to import TMX:\n{str(e)}", parent=root)
                root.destroy()
            except:
                print(f"Failed to import TMX: {e}")
            return False

    # --------------------------- Export Dialog System ---------------------------
    def show_export_dialog(self) -> bool:
        """Show unified export dialog with format selection and options."""
        try:
            # Create export dialog window
            export_root = tk.Tk()
            export_root.title("Export Map")
            export_root.geometry("500x600")
            export_root.resizable(False, False)
            
            # Center window
            export_root.update_idletasks()
            x = (export_root.winfo_screenwidth() // 2) - (500 // 2)
            y = (export_root.winfo_screenheight() // 2) - (600 // 2)
            export_root.geometry(f"500x600+{x}+{y}")
            
            result = {'format': None, 'options': {}, 'cancelled': True}
            
            # Format selection
            format_var = tk.StringVar(value="PNG")
            tk.Label(export_root, text="Export Format:", font=("Arial", 12, "bold")).pack(pady=10)
            
            format_frame = tk.Frame(export_root)
            format_frame.pack(pady=5)
            
            formats = [
                ("PNG Image", "PNG"),
                ("CSV Data", "CSV"), 
                ("TMX (Tiled)", "TMX"),
                ("Python Module", "Python")
            ]
            
            for text, value in formats:
                tk.Radiobutton(format_frame, text=text, variable=format_var, value=value).pack(anchor="w")
            
            # Options frame (will be updated based on format selection)
            options_frame = tk.Frame(export_root)
            options_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Current options widgets
            option_widgets = {}
            
            def update_options():
                # Clear previous options
                for widget in options_frame.winfo_children():
                    widget.destroy()
                option_widgets.clear()
                
                format_type = format_var.get()
                
                if format_type == "PNG":
                    # PNG options
                    tk.Label(options_frame, text="PNG Export Options", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,10))
                    
                    # Scale factor
                    scale_frame = tk.Frame(options_frame)
                    scale_frame.pack(fill="x", pady=2)
                    tk.Label(scale_frame, text="Scale Factor:").pack(side="left")
                    scale_var = tk.DoubleVar(value=1.0)
                    scale_spin = tk.Spinbox(scale_frame, from_=0.25, to=8.0, increment=0.25, textvariable=scale_var, width=10)
                    scale_spin.pack(side="right")
                    option_widgets['scale_factor'] = scale_var
                    
                    # Layer selection
                    layer_frame = tk.Frame(options_frame)
                    layer_frame.pack(fill="x", pady=2)
                    tk.Label(layer_frame, text="Export Layers:").pack(anchor="w")
                    
                    layer_var = tk.StringVar(value="visible")
                    tk.Radiobutton(layer_frame, text="Visible layers only", variable=layer_var, value="visible").pack(anchor="w")
                    tk.Radiobutton(layer_frame, text="All layers", variable=layer_var, value="all").pack(anchor="w")
                    option_widgets['layers'] = layer_var
                    
                    # Include grid
                    grid_var = tk.BooleanVar(value=False)
                    tk.Checkbutton(options_frame, text="Include grid lines", variable=grid_var).pack(anchor="w", pady=2)
                    option_widgets['include_grid'] = grid_var
                
                elif format_type == "CSV":
                    # CSV options
                    tk.Label(options_frame, text="CSV Export Options", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,10))
                    
                    # Delimiter
                    delim_frame = tk.Frame(options_frame)
                    delim_frame.pack(fill="x", pady=2)
                    tk.Label(delim_frame, text="Delimiter:").pack(side="left")
                    delim_var = tk.StringVar(value=",")
                    delim_combo = tk.OptionMenu(delim_frame, delim_var, ",", ";", "\\t")
                    delim_combo.pack(side="right")
                    option_widgets['delimiter'] = delim_var
                    
                    # Headers
                    header_var = tk.BooleanVar(value=True)
                    tk.Checkbutton(options_frame, text="Include column headers", variable=header_var).pack(anchor="w", pady=2)
                    option_widgets['include_headers'] = header_var
                    
                    # Empty cell value
                    empty_frame = tk.Frame(options_frame)
                    empty_frame.pack(fill="x", pady=2)
                    tk.Label(empty_frame, text="Empty cell value:").pack(side="left")
                    empty_var = tk.StringVar(value="-1")
                    empty_entry = tk.Entry(empty_frame, textvariable=empty_var, width=10)
                    empty_entry.pack(side="right")
                    option_widgets['empty_cell_value'] = empty_var
                
                elif format_type == "TMX":
                    # TMX options
                    tk.Label(options_frame, text="TMX Export Options", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,10))
                    
                    # Encoding
                    enc_frame = tk.Frame(options_frame)
                    enc_frame.pack(fill="x", pady=2)
                    tk.Label(enc_frame, text="Encoding:").pack(side="left")
                    enc_var = tk.StringVar(value="csv")
                    enc_combo = tk.OptionMenu(enc_frame, enc_var, "csv", "xml")
                    enc_combo.pack(side="right")
                    option_widgets['encoding'] = enc_var
                
                elif format_type == "Python":
                    # Python options
                    tk.Label(options_frame, text="Python Export Options", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,10))
                    
                    # Data format
                    data_frame = tk.Frame(options_frame)
                    data_frame.pack(fill="x", pady=2)
                    tk.Label(data_frame, text="Data Format:").pack(side="left")
                    data_var = tk.StringVar(value="lists")
                    data_combo = tk.OptionMenu(data_frame, data_var, "lists", "dicts")
                    data_combo.pack(side="right")
                    option_widgets['data_format'] = data_var
                    
                    # Include metadata
                    meta_var = tk.BooleanVar(value=True)
                    tk.Checkbutton(options_frame, text="Include metadata comments", variable=meta_var).pack(anchor="w", pady=2)
                    option_widgets['include_metadata'] = meta_var
            
            # Update options when format changes
            format_var.trace('w', lambda *args: update_options())
            update_options()  # Initial setup
            
            # Buttons
            button_frame = tk.Frame(export_root)
            button_frame.pack(pady=20)
            
            def on_export():
                # Collect options
                options = {}
                for key, widget in option_widgets.items():
                    if hasattr(widget, 'get'):
                        value = widget.get()
                        # Handle special cases
                        if key == 'delimiter' and value == '\\t':
                            value = '\t'
                        options[key] = value
                
                result['format'] = format_var.get()
                result['options'] = options
                result['cancelled'] = False
                export_root.destroy()
            
            def on_cancel():
                result['cancelled'] = True
                export_root.destroy()
            
            tk.Button(button_frame, text="Export", command=on_export, bg="#4CAF50", fg="white", padx=20).pack(side="left", padx=10)
            tk.Button(button_frame, text="Cancel", command=on_cancel, padx=20).pack(side="left", padx=10)
            
            # Show dialog
            export_root.transient()
            export_root.grab_set()
            export_root.mainloop()
            
            # Execute export if not cancelled
            if not result['cancelled']:
                format_type = result['format']
                options = result['options']
                
                if format_type == "PNG":
                    return self.export_as_png(export_options=options)
                elif format_type == "CSV":
                    return self.export_as_csv(export_options=options)
                elif format_type == "TMX":
                    return self.export_as_tmx(export_options=options)
                elif format_type == "Python":
                    return self.export_as_python_module(export_options=options)
            
            return False
            
        except Exception as e:
            print(f"Error showing export dialog: {e}")
            return False

    def show_import_dialog(self) -> bool:
        """Show import dialog for selecting import format."""
        try:
            # Create import dialog window
            import_root = tk.Tk()
            import_root.title("Import Data")
            import_root.geometry("400x300")
            import_root.resizable(False, False)
            
            # Center window
            import_root.update_idletasks()
            x = (import_root.winfo_screenwidth() // 2) - (400 // 2)
            y = (import_root.winfo_screenheight() // 2) - (300 // 2)
            import_root.geometry(f"400x300+{x}+{y}")
            
            result = {'format': None, 'cancelled': True}
            
            tk.Label(import_root, text="Select Import Format:", font=("Arial", 14, "bold")).pack(pady=20)
            
            # Format buttons
            button_frame = tk.Frame(import_root)
            button_frame.pack(expand=True)
            
            def import_csv():
                result['format'] = 'CSV'
                result['cancelled'] = False
                import_root.destroy()
            
            def import_tmx():
                result['format'] = 'TMX'
                result['cancelled'] = False
                import_root.destroy()
            
            def cancel_import():
                result['cancelled'] = True
                import_root.destroy()
            
            # Import buttons
            tk.Button(button_frame, text="Import CSV Data", command=import_csv, 
                     width=20, height=2, bg="#2196F3", fg="white").pack(pady=10)
            tk.Label(button_frame, text="Import CSV files as new layers").pack()
            
            tk.Button(button_frame, text="Import TMX File", command=import_tmx, 
                     width=20, height=2, bg="#FF9800", fg="white").pack(pady=10)
            tk.Label(button_frame, text="Import Tiled map files").pack()
            
            tk.Button(button_frame, text="Cancel", command=cancel_import, 
                     width=20, height=2).pack(pady=20)
            
            # Show dialog
            import_root.transient()
            import_root.grab_set()
            import_root.mainloop()
            
            # Execute import if not cancelled
            if not result['cancelled']:
                format_type = result['format']
                
                if format_type == 'CSV':
                    return self.import_csv()
                elif format_type == 'TMX':
                    return self.import_tmx()
            
            return False
            
        except Exception as e:
            print(f"Error showing import dialog: {e}")
            return False

    # --------------------------- Icon System (Phase 2 Ready) ---------------------------
    def audit_icons(self) -> dict:
        """
        Audit current icon usage and identify any missing icons.
        Phase 2: This can be extended to check for PNG icon files.
        
        Returns:
            Dictionary with icon usage statistics
        """
        used_icons = set()
        missing_icons = set()
        
        # Check which icons are actually used in the UI
        for key in ICONS.keys():
            # This would be extended in Phase 2 to check file existence
            used_icons.add(key)
            
        audit_results = {
            'total_icons': len(ICONS),
            'used_icons': len(used_icons),
            'missing_icons': len(missing_icons),
            'icon_coverage': len(used_icons) / max(1, len(ICONS)) * 100,
            'unicode_fallbacks': len(used_icons)  # Phase 1: all are Unicode
        }
        
        return audit_results
    
    def get_icon_path(self, icon_key: str) -> str:
        """
        Phase 2: Get the file path for an icon.
        Phase 1: Returns empty string (Unicode only)
        """
        # Phase 2 implementation:
        # icon_dir = resource_path("icons")
        # return os.path.join(icon_dir, f"{icon_key}.png")
        return ""  # Phase 1: No file-based icons yet  # Apply saved layer states
        print(f"Loaded map from {self.save_path}")

    # --------------------------- User Preferences ---------------------------
    def save_preferences(self):
        prefs = {
            "left_w": self.left_w,
            "right_w": self.right_w,
            "right_split": self.right_split,
            "left_collapsed": self.left_collapsed,
            "right_layers_collapsed": self.right_layers_collapsed,
            "right_props_collapsed": self.right_props_collapsed,
            "zoom_level": self.VIEW_SCALE,
            "layer_states": [],
            # File management preferences
            "last_directory": self.last_directory,
            "recent_files": self.recent_files,
            "auto_save_enabled": self.auto_save_enabled,
            "auto_save_interval": self.auto_save_interval,
            # Display preferences
            "background_color": self.BG
        }
        
        # Save layer visibility/lock states
        for layer in self.layers:
            prefs["layer_states"].append({
                "name": layer.name,
                "visible": layer.visible,
                "locked": layer.locked
            })
        
        try:
            with open(self.prefs_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Failed to save preferences: {e}")

    def load_preferences(self):
        try:
            with open(self.prefs_path, "r", encoding="utf-8") as f:
                prefs = json.load(f)
                
            self.left_w = prefs.get("left_w", self.left_w)
            self.right_w = prefs.get("right_w", self.right_w)
            self.right_split = prefs.get("right_split", self.right_split)
            self.left_collapsed = prefs.get("left_collapsed", self.left_collapsed)
            self.right_layers_collapsed = prefs.get("right_layers_collapsed", self.right_layers_collapsed)
            self.right_props_collapsed = prefs.get("right_props_collapsed", self.right_props_collapsed)
            self.VIEW_SCALE = prefs.get("zoom_level", self.VIEW_SCALE)
            
            # Load file management preferences
            self.last_directory = prefs.get("last_directory", self.last_directory)
            self.recent_files = prefs.get("recent_files", [])
            self.auto_save_enabled = prefs.get("auto_save_enabled", self.auto_save_enabled)
            self.auto_save_interval = prefs.get("auto_save_interval", self.auto_save_interval)
            
            # Load display preferences
            bg_color = prefs.get("background_color", self.BG)
            # Ensure it's a proper 3-tuple of integers
            if isinstance(bg_color, (list, tuple)) and len(bg_color) >= 3:
                self.BG = (int(bg_color[0]), int(bg_color[1]), int(bg_color[2]))
            else:
                self.BG = (26, 28, 33)  # Default if invalid format
            
            # Clean up recent files list (remove non-existent files)
            self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
            
        except Exception as e:
            print(f"Could not load preferences: {e}")

    def apply_layer_preferences(self):
        """Apply saved layer states after loading a map"""
        try:
            with open(self.prefs_path, "r", encoding="utf-8") as f:
                prefs = json.load(f)
                layer_states = prefs.get("layer_states", [])
                
            # Apply states by matching layer names
            for state in layer_states:
                name = state.get("name", "")
                for layer in self.layers:
                    if layer.name == name:
                        layer.visible = state.get("visible", True)
                        layer.locked = state.get("locked", False)
                        break
                        
        except Exception:
            pass  # Silently ignore if prefs don't exist

    # --------------------------- Tileset slicing ---------------------------
    def slice_tiles(self):
        self.tiles.clear()
        w, h = self.tileset_surface.get_size()
        ts = max(1, int(self.TILE_SIZE))
        m = max(0, int(self.margin))
        s = max(0, int(self.spacing))

        xs: List[int] = []
        x = m
        while x + ts <= w - m:
            xs.append(x)
            x += ts + s
        ys: List[int] = []
        y = m
        while y + ts <= h - m:
            ys.append(y)
            y += ts + s
        for ty in ys:
            for tx in xs:
                rect = pygame.Rect(tx, ty, ts, ts)
                if rect.right <= w and rect.bottom <= h:
                    self.tiles.append(self.tileset_surface.subsurface(rect).copy())
        self.tiles_per_row = len(xs) if ys else 0
        if not self.tiles:
            self.selected_tile = None
        else:
            if self.selected_tile is None or self.selected_tile >= len(self.tiles):
                self.selected_tile = 0

    # --------------------------- Settings UI ---------------------------
    def open_settings(self):
        self.show_settings = True
        self.settings_focus = 0
        self._settings_temp = {"tile_size": self.TILE_SIZE, "margin": self.margin, "spacing": self.spacing}

    def apply_settings(self):
        self.TILE_SIZE = max(1, int(self._settings_temp["tile_size"]))
        self.margin = max(0, int(self._settings_temp["margin"]))
        self.spacing = max(0, int(self._settings_temp["spacing"]))
        self.PALETTE_SCALE = max(1, 2 if self.TILE_SIZE <= 32 else 1)
        self.slice_tiles()
        self.show_settings = False

    def cancel_settings(self):
        self.show_settings = False

    # --------------------------- Menu System Helper Methods ---------------------------
    def select_all_tiles(self):
        """Select all tiles in the current layer"""
        self.has_selection = True
        self.selection_start_x = 0
        self.selection_start_y = 0
        self.selection_end_x = self.map_cols - 1
        self.selection_end_y = self.map_rows - 1
        
    def show_map_properties_dialog(self):
        """Show map properties dialog (placeholder for now)"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk() 
            root.withdraw()
            
            messagebox.showinfo("Map Properties", 
                              f"Map Size: {self.map_cols} x {self.map_rows} tiles\n"
                              f"Tile Size: {self.TILE_SIZE} pixels\n"
                              f"Layers: {len(self.layers)}\n"
                              f"Current Layer: {self.layers[self.current_layer].name}\n"
                              f"Tileset: {self.TILE_SIZE}px tiles\n"
                              f"Modified: {'Yes' if self.is_modified else 'No'}")
            
            root.destroy()
            
        except Exception as e:
            print(f"Map properties dialog error: {e}")
    
    def show_preferences_dialog(self):
        """Show preferences dialog (will implement full version later)"""
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            
            root = tk.Tk()
            root.title("Preferences")
            root.geometry("500x400")
            root.resizable(True, True)
            
            # Center window
            root.geometry("+%d+%d" % (root.winfo_screenwidth()//2 - 250, 
                                    root.winfo_screenheight()//2 - 200))
            
            # Create notebook for tabs
            notebook = ttk.Notebook(root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # General tab
            general_frame = ttk.Frame(notebook)
            notebook.add(general_frame, text="General")
            
            # Auto-save settings
            ttk.Label(general_frame, text="Auto-Save Settings:").pack(anchor=tk.W, pady=(10, 5))
            
            auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
            ttk.Checkbutton(general_frame, text="Enable auto-save", 
                          variable=auto_save_var).pack(anchor=tk.W, padx=20)
            
            interval_frame = ttk.Frame(general_frame)
            interval_frame.pack(anchor=tk.W, padx=20, pady=5)
            ttk.Label(interval_frame, text="Interval (seconds):").pack(side=tk.LEFT)
            interval_var = tk.IntVar(value=self.auto_save_interval)
            ttk.Scale(interval_frame, from_=60, to=1800, variable=interval_var, 
                     orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=10)
            interval_label = ttk.Label(interval_frame, text=str(self.auto_save_interval))
            interval_label.pack(side=tk.LEFT)
            
            def update_interval_label(*args):
                interval_label.config(text=str(interval_var.get()))
            interval_var.trace('w', update_interval_label)
            
            # Recent files limit
            ttk.Label(general_frame, text="Recent Files Limit:").pack(anchor=tk.W, pady=(20, 5))
            recent_files_var = tk.IntVar(value=self.max_recent_files)
            ttk.Scale(general_frame, from_=5, to=20, variable=recent_files_var,
                     orient=tk.HORIZONTAL, length=300).pack(anchor=tk.W, padx=20)
            
            # Display tab
            display_frame = ttk.Frame(notebook)
            notebook.add(display_frame, text="Display")
            
            ttk.Label(display_frame, text="Interface Settings:").pack(anchor=tk.W, pady=(10, 5))
            
            menu_bar_var = tk.BooleanVar(value=self.show_menu_bar)
            ttk.Checkbutton(display_frame, text="Show menu bar", 
                          variable=menu_bar_var).pack(anchor=tk.W, padx=20)
            
            # Background color section
            ttk.Label(display_frame, text="Background Color:").pack(anchor=tk.W, pady=(20, 5))
            
            bg_color_frame = ttk.Frame(display_frame)
            bg_color_frame.pack(anchor=tk.W, padx=20, pady=5)
            
            # Current background color variables
            current_bg = self.BG
            bg_r_var = tk.IntVar(value=current_bg[0])
            bg_g_var = tk.IntVar(value=current_bg[1])
            bg_b_var = tk.IntVar(value=current_bg[2])
            
            # Color preview canvas
            color_canvas = tk.Canvas(bg_color_frame, width=60, height=30, borderwidth=2, relief="sunken")
            color_canvas.pack(side=tk.LEFT, padx=(0, 10))
            
            def update_color_preview():
                r, g, b = bg_r_var.get(), bg_g_var.get(), bg_b_var.get()
                color_hex = f"#{r:02x}{g:02x}{b:02x}"
                color_canvas.configure(bg=color_hex)
                rgb_label.config(text=f"RGB({r}, {g}, {b})")
            
            # RGB sliders
            sliders_frame = ttk.Frame(bg_color_frame)
            sliders_frame.pack(side=tk.LEFT)
            
            # Red slider
            ttk.Label(sliders_frame, text="Red:").grid(row=0, column=0, sticky=tk.W)
            ttk.Scale(sliders_frame, from_=0, to=255, variable=bg_r_var, orient=tk.HORIZONTAL, length=150,
                     command=lambda x: update_color_preview()).grid(row=0, column=1, padx=5)
            ttk.Label(sliders_frame, textvariable=bg_r_var).grid(row=0, column=2)
            
            # Green slider
            ttk.Label(sliders_frame, text="Green:").grid(row=1, column=0, sticky=tk.W)
            ttk.Scale(sliders_frame, from_=0, to=255, variable=bg_g_var, orient=tk.HORIZONTAL, length=150,
                     command=lambda x: update_color_preview()).grid(row=1, column=1, padx=5)
            ttk.Label(sliders_frame, textvariable=bg_g_var).grid(row=1, column=2)
            
            # Blue slider
            ttk.Label(sliders_frame, text="Blue:").grid(row=2, column=0, sticky=tk.W)
            ttk.Scale(sliders_frame, from_=0, to=255, variable=bg_b_var, orient=tk.HORIZONTAL, length=150,
                     command=lambda x: update_color_preview()).grid(row=2, column=1, padx=5)
            ttk.Label(sliders_frame, textvariable=bg_b_var).grid(row=2, column=2)
            
            # RGB display label
            rgb_label = ttk.Label(display_frame, text=f"RGB({current_bg[0]}, {current_bg[1]}, {current_bg[2]})")
            rgb_label.pack(anchor=tk.W, padx=20, pady=(5, 0))
            
            # Preset colors section
            ttk.Label(display_frame, text="Preset Colors:").pack(anchor=tk.W, pady=(15, 5))
            
            presets_frame = ttk.Frame(display_frame)
            presets_frame.pack(anchor=tk.W, padx=20)
            
            # Define color presets
            color_presets = [
                ("Dark Grey (Default)", (26, 28, 33)),
                ("Light Grey", (60, 63, 65)),
                ("Dark Blue", (25, 30, 45)),
                ("Dark Green", (25, 35, 25)),
                ("Dark Red", (40, 25, 25)),
                ("Almost Black", (15, 15, 15)),
                ("Medium Grey", (45, 48, 50)),
                ("Dark Purple", (35, 25, 45))
            ]
            
            def apply_preset(color):
                bg_r_var.set(color[0])
                bg_g_var.set(color[1])
                bg_b_var.set(color[2])
                update_color_preview()
            
            # Create preset buttons in a grid
            for i, (name, color) in enumerate(color_presets):
                row = i // 2
                col = i % 2
                preset_btn = ttk.Button(presets_frame, text=name, 
                                      command=lambda c=color: apply_preset(c))
                preset_btn.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)
            
            # Initialize color preview
            update_color_preview()
            
            # Export tab
            export_frame = ttk.Frame(notebook)
            notebook.add(export_frame, text="Export")
            
            ttk.Label(export_frame, text="Default Export Settings:").pack(anchor=tk.W, pady=(10, 5))
            ttk.Label(export_frame, text="(Export preferences will be implemented in future update)").pack(anchor=tk.W, padx=20, pady=20)
            
            # Buttons
            button_frame = ttk.Frame(root)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            def apply_preferences():
                try:
                    # Apply settings
                    self.auto_save_enabled = auto_save_var.get()
                    self.auto_save_interval = interval_var.get()
                    self.max_recent_files = recent_files_var.get()
                    old_menu_bar = self.show_menu_bar
                    self.show_menu_bar = menu_bar_var.get()
                    
                    # Apply background color
                    new_bg_color = (bg_r_var.get(), bg_g_var.get(), bg_b_var.get())
                    self.BG = new_bg_color
                    
                    # Update TOP_H if menu bar visibility changed
                    if old_menu_bar != self.show_menu_bar:
                        self.TOP_H = (self.MENU_BAR_H + 40) if self.show_menu_bar else 40
                    
                    # Trim recent files if necessary
                    if len(self.recent_files) > self.max_recent_files:
                        self.recent_files = self.recent_files[:self.max_recent_files]
                    
                    # Save preferences
                    self.save_preferences()
                    
                    messagebox.showinfo("Preferences", "Preferences applied successfully!\nBackground color change will be visible immediately.")
                    root.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to apply preferences: {str(e)}")
            
            def cancel_preferences():
                root.destroy()
            
            ttk.Button(button_frame, text="Apply", command=apply_preferences).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel_preferences).pack(side=tk.RIGHT)
            
            root.mainloop()
            
        except Exception as e:
            print(f"Preferences dialog error: {e}")
    
    def show_shortcuts_dialog(self):
        """Show keyboard shortcuts help dialog"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            shortcuts = """KEYBOARD SHORTCUTS:

FILE OPERATIONS:
• Ctrl+N - New Map
• Ctrl+O - Open Map  
• Ctrl+S - Save Map
• Ctrl+Shift+S - Save As
• Ctrl+Q - Exit

EDITING:
• Ctrl+Z - Undo
• Ctrl+Y - Redo
• Ctrl+C - Copy Selection
• Ctrl+X - Cut Selection
• Ctrl+V - Paste
• Ctrl+A - Select All

MULTI-TILE BRUSH:
• Ctrl+Click - Select/deselect tiles for multi-tile brush
• Paint - Use multi-tile brush to paint selected tile patterns
• Escape - Clear multi-tile selection

TOOLS:
• P - Paint Tool
• E - Erase Tool
• I - Eyedropper/Pick
• F - Flood Fill
• S - Selection Tool
• L - Line Tool
• R - Rectangle Tool
• C - Circle Tool

VIEW:
• Ctrl++ - Zoom In
• Ctrl+- - Zoom Out
• Ctrl+0 - Zoom to Fit
• Ctrl+1 - Actual Size (1:1)
• C - Toggle Collision Overlay

IMPORT/EXPORT:
• Ctrl+Shift+E - Export Dialog
• Ctrl+Shift+I - Import Dialog

MISC:
• F3 - Tileset Settings
• Tab - Toggle Shape Fill Mode
• [ / ] - Brush Size
• Esc - Clear Selection/Exit"""
            
            messagebox.showinfo("Keyboard Shortcuts", shortcuts)
            root.destroy()
            
        except Exception as e:
            print(f"Shortcuts dialog error: {e}")
    
    def show_about_dialog(self):
        """Show about dialog"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            about_text = """Tile Map Editor
Professional tile-based level editor

VERSION: 1.0 (Phase 3 Complete)
FEATURES:
• Multi-layer tile editing
• Professional import/export system
• Advanced selection and clipboard
• Comprehensive undo/redo system  
• Auto-save and crash recovery
• Multiple file format support
• Professional UI with menu system

Built with Python and Pygame
© 2024 - Tile Map Editor Project"""
            
            messagebox.showinfo("About Tile Map Editor", about_text)
            root.destroy()
            
        except Exception as e:
            print(f"About dialog error: {e}")

    def batch_export_all_formats(self):
        """Export map in all available formats with a single dialog"""
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            
            # Hide main window
            root = tk.Tk()
            root.withdraw()
            
            # Ask for base filename
            base_path = filedialog.asksaveasfilename(
                title="Batch Export All Formats - Choose Base Filename",
                defaultextension=".png",
                filetypes=[
                    ("All formats", "*.*"),
                    ("PNG files", "*.png"),
                    ("CSV files", "*.csv"), 
                    ("TMX files", "*.tmx"),
                    ("Python files", "*.py")
                ],
                initialdir=self.last_directory
            )
            
            if not base_path:
                root.destroy()
                return False
            
            # Get base name without extension
            base_name = os.path.splitext(base_path)[0]
            success_count = 0
            total_formats = 4
            
            # Export each format
            formats = [
                (".png", self.export_as_png, "PNG"),
                (".csv", self.export_as_csv, "CSV"), 
                (".tmx", self.export_as_tmx, "TMX"),
                (".py", self.export_as_python_module, "Python")
            ]
            
            failed_formats = []
            
            for ext, export_func, format_name in formats:
                try:
                    file_path = base_name + ext
                    if export_func(file_path):
                        success_count += 1
                    else:
                        failed_formats.append(format_name)
                except Exception as e:
                    failed_formats.append(f"{format_name} ({str(e)})")
            
            # Show results
            if success_count == total_formats:
                messagebox.showinfo("Batch Export Complete", 
                                  f"Successfully exported map in all {total_formats} formats!\n\n" +
                                  f"Files saved with base name: {os.path.basename(base_name)}")
            elif success_count > 0:
                failed_text = ", ".join(failed_formats)
                messagebox.showwarning("Batch Export Partially Complete", 
                                     f"Exported {success_count}/{total_formats} formats.\n"
                                     f"Failed: {failed_text}")
            else:
                messagebox.showerror("Batch Export Failed", 
                                   "Failed to export any formats. Please check file permissions.")
            
            root.destroy()
            return success_count > 0
            
        except Exception as e:
            print(f"Batch export error: {e}")
            return False

    # --------------------------- Settings UI ---------------------------

    def draw_settings_overlay(self):
        dim = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))
        pw, ph = 520, 280  # Increased height for tooltips
        px = (self.WIDTH - pw) // 2
        py = (self.HEIGHT - ph) // 2
        pygame.draw.rect(self.screen, (36, 38, 45), (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(self.screen, (80, 170, 255), (px, py, pw, ph), 2, border_radius=8)
        title = self.FONT.render("Tileset Settings", True, (230, 235, 240))
        self.screen.blit(title, (px + 16, py + 12))

        # Add description text
        desc_text = "Configure how tiles are read from the tileset image. Grid size will match tile size."
        desc = pygame.font.SysFont("arial", 12).render(desc_text, True, (180, 185, 190))
        self.screen.blit(desc, (px + 16, py + 35))

        fields = [
            ("Tile Size", int(self._settings_temp["tile_size"]), "Size of each tile in pixels (affects both tileset and grid)"),
            ("Margin", int(self._settings_temp["margin"]), "Pixels between tileset edge and first tile"),
            ("Spacing", int(self._settings_temp["spacing"]), "Pixels between tiles in the tileset"),
        ]
        for i, (label, value, tooltip) in enumerate(fields):
            ly = py + 66 + i * 54  # Increased spacing for tooltips
            color = (255, 230, 120) if i == self.settings_focus else (210, 214, 220)
            self.screen.blit(self.FONT.render(f"{label}: {value}", True, color), (px + 24, ly))
            
            # Draw tooltip in smaller font
            tooltip_font = pygame.font.SysFont("arial", 11)
            tooltip_color = (160, 165, 170) if i == self.settings_focus else (140, 145, 150)
            self.screen.blit(tooltip_font.render(tooltip, True, tooltip_color), (px + 24, ly + 18))
            
        help1 = "Tab/Shift+Tab: switch  +/- or Up/Down: change  D: detect size  Enter: apply  Esc: cancel"
        self.screen.blit(self.FONT.render(help1, True, (200, 205, 210)), (px + 24, py + ph - 40))

    # --------------------------- Main Loop ---------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Update auto-save system
            self.update_auto_save()
            
            self.compute_layout()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Check for unsaved changes before quitting
                    if self.confirm_unsaved_changes("exiting"):
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.WIDTH, self.HEIGHT = event.w, event.h
                    self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    if self.show_settings:
                        if event.key == pygame.K_ESCAPE:
                            self.cancel_settings()
                        elif event.key == pygame.K_TAB:
                            if mods & pygame.KMOD_SHIFT:
                                self.settings_focus = (self.settings_focus - 1) % 3
                            else:
                                self.settings_focus = (self.settings_focus + 1) % 3
                        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_UP):
                            step = 8 if (mods & pygame.KMOD_SHIFT) else 1
                            if self.settings_focus == 0:
                                self._settings_temp["tile_size"] += step
                            elif self.settings_focus == 1:
                                self._settings_temp["margin"] += step
                            else:
                                self._settings_temp["spacing"] += step
                        elif event.key in (pygame.K_MINUS, pygame.K_DOWN):
                            step = 8 if (mods & pygame.KMOD_SHIFT) else 1
                            if self.settings_focus == 0:
                                self._settings_temp["tile_size"] = max(1, self._settings_temp["tile_size"] - step)
                            elif self.settings_focus == 1:
                                self._settings_temp["margin"] = max(0, self._settings_temp["margin"] - step)
                            else:
                                self._settings_temp["spacing"] = max(0, self._settings_temp["spacing"] - step)
                        elif event.key == pygame.K_d:
                            self._settings_temp["tile_size"] = detect_tile_size(self.tileset_surface)
                        elif event.key == pygame.K_RETURN:
                            self.apply_settings()
                    else:
                        # Handle layer rename mode
                        if self.layer_rename_index >= 0:
                            if event.key == pygame.K_RETURN:
                                # Apply rename
                                if self.layer_rename_text.strip():
                                    self.layers[self.layer_rename_index].name = self.layer_rename_text.strip()
                                self.layer_rename_index = -1
                            elif event.key == pygame.K_ESCAPE:
                                # Cancel rename
                                self.layer_rename_index = -1
                            elif event.key == pygame.K_BACKSPACE:
                                if self.layer_rename_cursor > 0:
                                    self.layer_rename_text = (
                                        self.layer_rename_text[:self.layer_rename_cursor-1] +
                                        self.layer_rename_text[self.layer_rename_cursor:]
                                    )
                                    self.layer_rename_cursor -= 1
                            elif event.key == pygame.K_DELETE:
                                if self.layer_rename_cursor < len(self.layer_rename_text):
                                    self.layer_rename_text = (
                                        self.layer_rename_text[:self.layer_rename_cursor] +
                                        self.layer_rename_text[self.layer_rename_cursor+1:]
                                    )
                            elif event.key == pygame.K_LEFT:
                                self.layer_rename_cursor = max(0, self.layer_rename_cursor - 1)
                            elif event.key == pygame.K_RIGHT:
                                self.layer_rename_cursor = min(len(self.layer_rename_text), self.layer_rename_cursor + 1)
                            elif event.unicode.isprintable():
                                # Insert character
                                self.layer_rename_text = (
                                    self.layer_rename_text[:self.layer_rename_cursor] +
                                    event.unicode +
                                    self.layer_rename_text[self.layer_rename_cursor:]
                                )
                                self.layer_rename_cursor += 1
                        # Handle object name editing mode
                        elif self.object_name_editing:
                            if event.key == pygame.K_RETURN:
                                # Apply name change
                                if self.object_name_edit_text.strip() and self.selected_object:
                                    self.selected_object.name = self.object_name_edit_text.strip()
                                    self.mark_modified()
                                self.object_name_editing = False
                            elif event.key == pygame.K_ESCAPE:
                                # Cancel name editing
                                self.object_name_editing = False
                            elif event.key == pygame.K_BACKSPACE:
                                if self.object_name_cursor > 0:
                                    self.object_name_edit_text = (
                                        self.object_name_edit_text[:self.object_name_cursor-1] +
                                        self.object_name_edit_text[self.object_name_cursor:]
                                    )
                                    self.object_name_cursor -= 1
                            elif event.key == pygame.K_DELETE:
                                if self.object_name_cursor < len(self.object_name_edit_text):
                                    self.object_name_edit_text = (
                                        self.object_name_edit_text[:self.object_name_cursor] +
                                        self.object_name_edit_text[self.object_name_cursor+1:]
                                    )
                            elif event.key == pygame.K_LEFT:
                                self.object_name_cursor = max(0, self.object_name_cursor - 1)
                            elif event.key == pygame.K_RIGHT:
                                self.object_name_cursor = min(len(self.object_name_edit_text), self.object_name_cursor + 1)
                            elif event.unicode.isprintable():
                                # Insert character
                                self.object_name_edit_text = (
                                    self.object_name_edit_text[:self.object_name_cursor] +
                                    event.unicode +
                                    self.object_name_edit_text[self.object_name_cursor:]
                                )
                                self.object_name_cursor += 1
                        else:
                            # Normal keyboard handling
                            if event.key == pygame.K_ESCAPE:
                                # Clear selection, paste preview, shape drawing, multi-tile selection, object selection and placement
                                # No longer exits the application - just clears active states
                                if (self.has_selection or self.selection_dragging or self.paste_preview or 
                                    self.shape_dragging or self.multi_tile_mode or self.selected_object or self.object_placement_mode or self.object_name_editing or self.object_paste_mode):
                                    self.has_selection = False
                                    self.selection_dragging = False
                                    self.paste_preview = False
                                    self.cancel_shape_drawing()
                                    if self.multi_tile_mode:
                                        self.clear_multi_tile_selection()
                                    if self.selected_object or self.selected_objects:
                                        self.selected_objects.clear()
                                        self.selected_object = None
                                    if self.object_placement_mode:
                                        self.object_placement_mode = False  # Exit object placement mode
                                    if self.object_paste_mode:
                                        self.object_paste_mode = False  # Exit object paste mode
                                        print("Paste cancelled")
                                    if self.object_name_editing:
                                        self.object_name_editing = False  # Exit object name editing
                                # No longer exits the application on Escape
                            elif event.key == pygame.K_F3:
                                self.open_settings()
                            elif event.key == pygame.K_1:
                                self.current_layer = 0
                            elif event.key == pygame.K_2:
                                self.current_layer = 1
                            elif event.key == pygame.K_p:
                                self.tool = "paint"
                            elif event.key == pygame.K_e:
                                self.tool = "erase"
                            elif event.key == pygame.K_i:
                                self.tool = "pick"
                            elif event.key == pygame.K_f:
                                self.tool = "flood_fill"
                            elif event.key == pygame.K_s:
                                self.tool = "select"
                                self.cancel_shape_drawing()
                            elif event.key == pygame.K_l:
                                self.tool = "line"
                                self.cancel_shape_drawing()
                            elif event.key == pygame.K_r:
                                self.tool = "rectangle"
                                self.cancel_shape_drawing()
                            elif event.key == pygame.K_c and not (mods & pygame.KMOD_CTRL):
                                self.tool = "circle" 
                                self.cancel_shape_drawing()
                            elif event.key == pygame.K_TAB:
                                # Toggle filled/outline for shape tools
                                if self.tool in ("rectangle", "circle"):
                                    self.shape_filled = not self.shape_filled
                            elif event.key == pygame.K_LEFTBRACKET:
                                # Decrease brush size
                                if self.brush_size > 1:
                                    self.brush_size -= 1
                            elif event.key == pygame.K_RIGHTBRACKET:
                                # Increase brush size
                                if self.brush_size < 5:
                                    self.brush_size += 1
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_n:
                                # New map (Ctrl+N)
                                self.new_map()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_o:
                                # Open map (Ctrl+O)
                                self.open_map()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_s:
                                if mods & pygame.KMOD_SHIFT:
                                    # Save As (Ctrl+Shift+S)
                                    self.save_as_map()
                                else:
                                    # Save (Ctrl+S)
                                    self.save_current_file()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_q:
                                # Quit application (Ctrl+Q) - check for unsaved changes
                                if self.confirm_unsaved_changes("exit"):
                                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_l:
                                # Legacy: Open map (Ctrl+L for backward compatibility)
                                self.open_map()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_z:
                                self.undo()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_y:
                                self.redo()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_c:
                                # Copy selection or objects
                                if self.object_mode == "objects" and self.selected_objects:
                                    copied_count = self.copy_selected_objects()
                                    print(f"Copied {copied_count} objects to clipboard")
                                else:
                                    self.copy_selection()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_x:
                                # Cut selection or objects
                                if self.object_mode == "objects" and self.selected_objects:
                                    copied_count = self.copy_selected_objects()
                                    self.delete_selected_objects()
                                    print(f"Cut {copied_count} objects to clipboard")
                                else:
                                    self.cut_selection()
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_v:
                                # Paste objects or tiles
                                if self.object_mode == "objects" and self.copied_objects:
                                    # Start object paste mode - cursor will show where to paste
                                    self.object_paste_mode = True
                                    print(f"Ready to paste {len(self.copied_objects)} objects - click where you want to paste")
                                else:
                                    self.start_paste()
                            elif event.key == pygame.K_DELETE:
                                # Delete selected objects
                                if self.object_mode == "objects" and self.selected_objects:
                                    deleted_count = len(self.selected_objects)
                                    self.delete_selected_objects()
                                    print(f"Deleted {deleted_count} objects")
                            elif event.key == pygame.K_m and (mods & pygame.KMOD_SHIFT):
                                # Toggle persistent object placement mode (Shift+M)
                                if self.object_mode == "objects":
                                    self.persistent_object_mode = not self.persistent_object_mode
                                    print(f"Persistent object placement: {'ON' if self.persistent_object_mode else 'OFF'}")
                            elif (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_e:
                                # Export dialog (Ctrl+Shift+E)
                                self.show_export_dialog()
                            elif (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_i:
                                # Import dialog (Ctrl+Shift+I)
                                self.show_import_dialog()
                            elif (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_p:
                                # Create pattern from selection (Ctrl+Shift+P)
                                self.create_pattern_from_selection()
                            elif (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_t:
                                # Create stamp from selection (Ctrl+Shift+T - changed from S to avoid conflict)
                                self.create_stamp_from_selection()
                            elif event.key == pygame.K_t and self.pattern_data:
                                # Toggle pattern mode (T key)
                                self.pattern_mode = not self.pattern_mode
                                mode_text = "enabled" if self.pattern_mode else "disabled"
                                print(f"Pattern painting mode {mode_text}")
                            elif (mods & pygame.KMOD_CTRL) and event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                                self.zoom_step(+1, pygame.mouse.get_pos())
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_MINUS:
                                self.zoom_step(-1, pygame.mouse.get_pos())
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_0:
                                if self.canvas_rect.width > 0 and self.canvas_rect.height > 0:
                                    sx = self.canvas_rect.width / max(1, self.map_cols * self.TILE_SIZE)
                                    sy = self.canvas_rect.height / max(1, self.map_rows * self.TILE_SIZE)
                                    new_scale = max(self.zoom_levels[0], min(self.zoom_levels[-1], min(sx, sy)))
                                    self.zoom_to(new_scale, self.canvas_rect.center)
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_1:
                                self.zoom_to(1.0, self.canvas_rect.center)
                            elif event.key == pygame.K_c and not (mods & pygame.KMOD_CTRL):
                                # Toggle collision overlay (C key)
                                self.show_collision_overlay = not self.show_collision_overlay
                                status = "shown" if self.show_collision_overlay else "hidden"
                                print(f"Collision overlay {status}")
                            elif (mods & pygame.KMOD_CTRL) and event.key == pygame.K_t:
                                self.open_settings()
                            elif event.key == pygame.K_PAGEUP:
                                # Large upward pan
                                self.scroll_y = max(0, self.scroll_y - self.canvas_rect.height // 2)
                            elif event.key == pygame.K_PAGEDOWN:
                                # Large downward pan  
                                max_y = max(0, self.map_rows * int(self.TILE_SIZE * self.VIEW_SCALE) - self.canvas_rect.height)
                                self.scroll_y = min(max_y, self.scroll_y + self.canvas_rect.height // 2)
                            elif event.key == pygame.K_HOME:
                                # Center view on map origin
                                self.scroll_x = 0
                                self.scroll_y = 0

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_settings:
                        continue
                    mx, my = event.pos
                    
                    # Handle collision menu clicks first (highest priority)
                    if self.handle_collision_menu_click(mx, my):
                        continue
                    
                    # Handle object type menu clicks
                    if self.handle_object_type_menu_click(mx, my):
                        continue
                    
                    # Menu system handling (highest priority)
                    if self.show_menu_bar:
                        # Check for menu bar clicks
                        menu_bar_rect = pygame.Rect(0, 0, self.WIDTH, self.MENU_BAR_H)
                        if menu_bar_rect.collidepoint(mx, my):
                            # Check which menu was clicked
                            clicked_menu = None
                            for menu_id, rect in self._menu_hitboxes.items():
                                if rect.collidepoint(mx, my):
                                    clicked_menu = menu_id
                                    break
                            
                            if clicked_menu:
                                if self.active_menu == clicked_menu:
                                    # Click on already active menu - close it
                                    self.active_menu = None
                                else:
                                    # Open new menu
                                    self.active_menu = clicked_menu
                                self.show_recent_files_menu = False
                                self.show_export_menu = False
                            else:
                                # Click on menu bar but not on a menu - close active menu
                                self.active_menu = None
                                self.show_recent_files_menu = False
                                self.show_export_menu = False
                            continue
                        
                        # Check for submenu clicks  
                        if self.active_menu and self._submenu_hitboxes:
                            clicked_command = None
                            for rect, command in self._submenu_hitboxes:
                                if rect.collidepoint(mx, my):
                                    clicked_command = command
                                    break
                            
                            if clicked_command:
                                # Handle submenu expansion
                                if clicked_command == "recent":
                                    self.show_recent_files_menu = not self.show_recent_files_menu
                                    self.show_export_menu = False
                                elif clicked_command == "export_menu":
                                    self.show_export_menu = not self.show_export_menu
                                    self.show_recent_files_menu = False
                                else:
                                    # Execute the command
                                    self.handle_menu_command(clicked_command)
                                continue
                            else:
                                # Click outside menu - close it
                                if not any(rect.collidepoint(mx, my) for rect, _ in self._submenu_hitboxes):
                                    self.active_menu = None
                                    self.show_recent_files_menu = False
                                    self.show_export_menu = False
                    
                    # Start middle-mouse drag for panning
                    if event.button == 2:
                        self.middle_mouse_dragging = True
                        self.last_mouse_pos = (mx, my)
                    # Zoom menu handling (global)
                    if self.show_zoom_menu:
                        handled = False
                        for r, p in self._zoom_menu_hitboxes:
                            if r.collidepoint(mx, my):
                                self.zoom_to(p, (mx, my))
                                handled = True
                                break
                        # Close menu if click outside menu and anchor
                        anchor = self._zoom_menu_anchor
                        if handled:
                            self.show_zoom_menu = False
                            continue
                        elif not (anchor and (anchor.collidepoint(mx, my))):
                            self.show_zoom_menu = False
                    # Splitter hit tests with improved visual feedback
                    splitter_hit = False
                    
                    # Check left splitter (tileset panel resizer)
                    if 'left' in self.splitter_zones and self.splitter_zones['left'].collidepoint(mx, my):
                        self.drag_left_split = True
                        self.splitter_active = 'left'
                        self._drag_offset = mx - self.left_rect.right
                        splitter_hit = True
                    # Check right splitter
                    elif 'right' in self.splitter_zones and self.splitter_zones['right'].collidepoint(mx, my):
                        self.drag_right_split = True
                        self.splitter_active = 'right'
                        self._drag_offset = mx - self.right_rect.left
                        splitter_hit = True
                    # Check right inner splitter
                    elif 'right_inner' in self.splitter_zones and self.splitter_zones['right_inner'].collidepoint(mx, my):
                        self.drag_right_inner_split = True
                        self.splitter_active = 'right_inner'
                        self._drag_offset = my - self.right_layers_rect.bottom
                        splitter_hit = True
                    
                    if splitter_hit:
                        continue

                    # Toolbar buttons
                    if self.top_rect.collidepoint(mx, my):
                        for rect, cmd, disabled in self._toolbar_hitboxes:
                            if rect.collidepoint(mx, my) and cmd and not disabled:
                                if cmd == 'new':
                                    self.new_map()
                                elif cmd == 'open':
                                    self.open_map()
                                elif cmd == 'save':
                                    self.save_current_file()
                                elif cmd == 'saveas':
                                    self.save_as_map()
                                elif cmd == 'export':
                                    self.show_export_dialog()
                                elif cmd == 'import':
                                    # Show import menu or dialog
                                    self.show_import_dialog()
                                elif cmd == 'undo':
                                    self.undo()
                                elif cmd == 'redo':
                                    self.redo()
                                elif cmd == 'zoom_in':
                                    self.zoom_step(+1, (mx, my))
                                elif cmd == 'zoom_out':
                                    self.zoom_step(-1, (mx, my))
                                elif cmd == 'zoom_fit':
                                    if self.canvas_rect.width > 0 and self.canvas_rect.height > 0:
                                        sx = self.canvas_rect.width / max(1, self.map_cols * self.TILE_SIZE)
                                        sy = self.canvas_rect.height / max(1, self.map_rows * self.TILE_SIZE)
                                        new_scale = min(sx, sy)
                                        new_scale = max(self.zoom_levels[0], min(self.zoom_levels[-1], new_scale))
                                        self.zoom_to(new_scale, self.canvas_rect.center)
                                        sy = self.canvas_rect.height / max(1, self.map_rows * self.TILE_SIZE)
                                        new_scale = max(self.zoom_levels[0], min(self.zoom_levels[-1], min(sx, sy)))
                                        self.zoom_to(new_scale, (self.canvas_rect.centerx, self.canvas_rect.centery))
                                elif cmd == 'zoom_menu':
                                    # Toggle zoom dropdown anchored to this button
                                    self.show_zoom_menu = not self.show_zoom_menu
                                    self._zoom_menu_anchor = rect
                                elif cmd == 'zoom_actual':
                                    self.zoom_to(1.0, (self.canvas_rect.centerx, self.canvas_rect.centery))
                                elif cmd == 'tool_paint':
                                    self.tool = 'paint'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_erase':
                                    self.tool = 'erase'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_pick':
                                    self.tool = 'pick'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_flood_fill':
                                    self.tool = 'flood_fill'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_select':
                                    self.tool = 'select'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_line':
                                    self.tool = 'line'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_rectangle':
                                    self.tool = 'rectangle'
                                    self.cancel_shape_drawing()
                                elif cmd == 'tool_circle':
                                    self.tool = 'circle'
                                    self.cancel_shape_drawing()
                                break
                    # Right panel: properties/tool options click
                    elif self.right_props_rect.collidepoint(mx, my):
                        header_h = self.panel_header_h
                        content = pygame.Rect(self.right_props_rect.x, self.right_props_rect.y + header_h, self.right_props_rect.w, self.right_props_rect.h - header_h)
                        if my >= content.y and not self.right_props_collapsed:
                            # Check tool options
                            if hasattr(self, '_toolopt_hitboxes'):
                                for r, payload in self._toolopt_hitboxes:
                                    if r.collidepoint(mx, my):
                                        kind, val = payload
                                        if kind == 'brush':
                                            self.brush_size = int(val)
                                        elif kind == 'shape':
                                            self.brush_shape = val
                                        elif kind == 'fill_mode':
                                            self.fill_mode = int(val)
                                        elif kind == 'shape_mode':
                                            self.shape_filled = bool(val)
                                        break
                            
                            # Check tile properties
                            if hasattr(self, '_tile_prop_hitboxes'):
                                for r, action in self._tile_prop_hitboxes:
                                    if r.collidepoint(mx, my):
                                        if action == 'collision_dropdown':
                                            self.show_collision_type_menu(mx, my)
                                        elif action == 'collision_overlay':
                                            self.show_collision_overlay = not self.show_collision_overlay
                                        break
                            
                            # Check object properties
                            if hasattr(self, '_object_prop_hitboxes'):
                                for r, action in self._object_prop_hitboxes:
                                    if r.collidepoint(mx, my):
                                        if action == 'object_name':
                                            # Start name editing mode
                                            if self.selected_object:
                                                self.object_name_editing = True
                                                self.object_name_edit_text = self.selected_object.name
                                                self.object_name_cursor = len(self.object_name_edit_text)
                                                # Close any open menus
                                                self.show_collision_menu = False
                                                self.object_type_menu_open = False
                                        elif action == 'object_type':
                                            # Show object type dropdown
                                            self.show_object_type_menu(mx, my)
                                        break
                        continue

                    # Gear icon click for tileset settings
                    if self.gear_rect and self.gear_rect.collidepoint(mx, my):
                        self.open_settings()
                        continue

                    # Panel header toggles
                    if self.left_rect.collidepoint(mx, my) and my <= self.left_rect.y + self.panel_header_h:
                        self.left_collapsed = not self.left_collapsed
                        continue
                    if self.right_layers_rect.collidepoint(mx, my) and my <= self.right_layers_rect.y + self.panel_header_h:
                        self.right_layers_collapsed = not self.right_layers_collapsed
                        continue
                    if self.right_props_rect.collidepoint(mx, my) and my <= self.right_props_rect.y + self.panel_header_h:
                        self.right_props_collapsed = not self.right_props_collapsed
                        continue

                    # Left panel: palette and tabs
                    if self.left_rect.collidepoint(mx, my) and not self.left_collapsed:
                        # Check tab clicks first
                        tab_clicked = False
                        for tab_id, tab_rect in self.tab_rects.items():
                            if tab_rect.collidepoint(mx, my):
                                if self.object_mode != tab_id:
                                    self.object_mode = tab_id
                                    # Clear selections when switching tabs
                                    self.selected_object = None
                                    if tab_id == "tiles":
                                        self.selected_tile = 0 if self.tiles else None
                                    else:
                                        self.selected_object_type = 0
                                tab_clicked = True
                                break
                        
                        if not tab_clicked:
                            if event.button in (4, 5):
                                delta = -60 if event.button == 4 else 60
                                self.palette_scroll = max(0, self.palette_scroll + delta)
                            elif event.button == 1:
                                if self.object_mode == "tiles":
                                    # Handle tiles palette clicking
                                    pad = 4
                                    tab_height = 24
                                    content_y = self.left_rect.y + self.panel_header_h + tab_height
                                    content = pygame.Rect(self.left_rect.x, content_y, self.left_rect.w, self.left_rect.h - (content_y - self.left_rect.y))
                                    cell = self.TILE_SIZE * self.PALETTE_SCALE + pad
                                    cols = max(1, (content.w - pad) // cell)
                                    x0, y0 = content.x + pad, content.y + pad - self.palette_scroll
                                    col = (mx - x0) // cell
                                    row = (my - y0) // cell
                                    if col >= 0 and row >= 0:
                                        idx = int(row) * cols + int(col)
                                        if 0 <= idx < len(self.tiles):
                                            # Check for multi-tile selection mode (Ctrl held)
                                            keys = pygame.key.get_pressed()
                                            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                                                # Multi-tile selection mode
                                                self.toggle_multi_tile_selection(idx)
                                                # Set selected tile for visual feedback
                                                if idx not in self.multi_tile_selection and self.multi_tile_selection:
                                                    # If we just deselected and have other selections, pick the last one
                                                    self.selected_tile = self.multi_tile_selection[-1]
                                                else:
                                                    self.selected_tile = idx
                                            else:
                                                # Normal single tile selection - clear multi selection
                                                if self.multi_tile_selection:
                                                    self.clear_multi_tile_selection()
                                                self.selected_tile = idx
                                elif self.object_mode == "objects":
                                    # Handle objects palette clicking
                                    pad = 8
                                    cell_size = 48
                                    cell = cell_size + pad
                                    tab_height = 24
                                    content_y = self.left_rect.y + self.panel_header_h + tab_height
                                    content = pygame.Rect(self.left_rect.x, content_y, self.left_rect.w, self.left_rect.h - (content_y - self.left_rect.y))
                                    
                                    cols = max(1, (content.w - pad) // cell)
                                    x0, y0 = content.x + pad, content.y + pad
                                    col = (mx - x0) // cell
                                    row = (my - y0) // cell
                                    if col >= 0 and row >= 0:
                                        idx = int(row) * cols + int(col)
                                        if 0 <= idx < len(self.OBJECT_TYPES):
                                            # Check if shift is held for persistent mode toggle
                                            keys = pygame.key.get_pressed()
                                            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                                                # Toggle persistent mode
                                                self.persistent_object_mode = not self.persistent_object_mode
                                                print(f"Persistent object placement: {'ON' if self.persistent_object_mode else 'OFF'}")
                                            else:
                                                self.selected_object_type = idx
                                                self.object_placement_mode = True  # Enter object placement mode
                                                self.selected_object = None  # Clear any selected object
                                                self.selected_objects.clear()  # Clear multi-selection
                        continue
                    # Right panel: layer click
                    elif self.right_layers_rect.collidepoint(mx, my):
                        header_h = self.panel_header_h
                        content = pygame.Rect(self.right_layers_rect.x, self.right_layers_rect.y + header_h, self.right_layers_rect.w, self.right_layers_rect.h - header_h)
                        if my >= content.y and not self.right_layers_collapsed:
                            # First check manipulation buttons
                            if hasattr(self, '_layer_btn_hitboxes'):
                                for r, cmd in self._layer_btn_hitboxes:
                                    if r.collidepoint(mx, my):
                                        if cmd == 'layer_add':
                                            # Add new layer with undo support
                                            name = f"Layer {len(self.layers)+1}"
                                            new_layer = Layer(name, [[-1 for _ in range(self.map_cols)] for _ in range(self.map_rows)])
                                            command = LayerAddCommand(self, new_layer, len(self.layers))
                                            self.execute_command(command)
                                            self.current_layer = len(self.layers) - 1
                                        elif cmd == 'layer_duplicate':
                                            # Duplicate current layer with undo support
                                            command = LayerDuplicateCommand(self, self.current_layer)
                                            self.execute_command(command)
                                            self.current_layer = min(self.current_layer + 1, len(self.layers) - 1)
                                        elif cmd == 'layer_del' and len(self.layers) > 1:
                                            # Delete layer with undo support
                                            command = LayerDeleteCommand(self, self.current_layer)
                                            self.execute_command(command)
                                        elif cmd == 'layer_up' and self.current_layer > 0:
                                            # Move layer up with undo support
                                            command = LayerMoveCommand(self, self.current_layer, self.current_layer - 1)
                                            self.execute_command(command)
                                        elif cmd == 'layer_down' and self.current_layer < len(self.layers) - 1:
                                            # Move layer down with undo support  
                                            command = LayerMoveCommand(self, self.current_layer, self.current_layer + 1)
                                            self.execute_command(command)
                                        break
                            # Then check per-row hitboxes for eye/lock/name
                            if hasattr(self, '_layer_row_hitboxes'):
                                for hb in self._layer_row_hitboxes:
                                    if hb['eye'].collidepoint(mx, my):
                                        self.layers[hb['index']].visible = not self.layers[hb['index']].visible
                                        break
                                    if hb['lock'].collidepoint(mx, my):
                                        self.layers[hb['index']].locked = not self.layers[hb['index']].locked
                                        break
                                    if hb['row'].collidepoint(mx, my):
                                        # Handle double-click for rename
                                        current_time = pygame.time.get_ticks()
                                        if (hb['index'] == self.last_click_layer and 
                                            current_time - self.last_click_time < 500):  # Double-click within 500ms
                                            # Start rename mode
                                            self.layer_rename_index = hb['index']
                                            self.layer_rename_text = self.layers[hb['index']].name
                                            self.layer_rename_cursor = len(self.layer_rename_text)
                                        else:
                                            # Single click - select layer
                                            self.current_layer = hb['index']
                                            self.last_click_layer = hb['index']
                                            self.last_click_time = current_time
                                        break
                    elif self.canvas_rect.collidepoint(mx, my):
                        if event.button in (1, 3):
                            cx, cy = self.screen_to_tile(mx, my)
                            
                            # Handle object mode clicks
                            if self.object_mode == "objects":
                                keys = pygame.key.get_pressed()
                                if keys[pygame.K_ESCAPE]:
                                    # Escape key - enter selection mode
                                    self.selected_object = None
                                    self.select_object_at(cx, cy)
                                elif event.button == 1:
                                    # Left click - place object (handled in paint_at)
                                    self.paint_at(cx, cy, 1)
                                elif event.button == 3:
                                    # Right click - delete object (handled in paint_at)
                                    self.paint_at(cx, cy, 3)
                            # Handle tile mode clicks
                            elif self.paste_preview:
                                # Apply paste
                                self.apply_paste(cx, cy)
                            elif self.tool == "select":
                                # Start selection drag with modifier key support
                                keys = pygame.key.get_pressed()
                                shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                                alt_held = keys[pygame.K_LALT] or keys[pygame.K_RALT]
                                self.start_selection_drag(cx, cy, shift_held, alt_held)
                            elif self.tool == "erase" or event.button == 3:
                                self.paint_at(cx, cy, 3)
                            elif self.tool == "paint":
                                self.paint_at(cx, cy, 1)
                            elif self.tool == "pick":
                                self.pick_at(cx, cy)
                            elif self.tool == "flood_fill":
                                if self.selected_tile is not None:
                                    self.flood_fill_at(cx, cy, self.selected_tile)
                            elif self.tool in ("line", "rectangle", "circle"):
                                if self.selected_tile is not None:
                                    # Start shape drawing
                                    self.start_shape_drawing(cx, cy)
                        elif event.button == 2:
                            cx, cy = self.screen_to_tile(mx, my)
                            if self.object_mode == "objects":
                                # Middle click on objects - select object
                                self.select_object_at(cx, cy)
                            else:
                                # Middle click on tiles - pick tile
                                self.pick_at(cx, cy)
                        elif event.button in (4, 5):
                            mods = pygame.key.get_mods()
                            if mods & pygame.KMOD_CTRL:
                                self.zoom_step(+1 if event.button == 4 else -1, (mx, my))
                            else:
                                delta = -int(240 * dt) if event.button == 4 else int(240 * dt)
                                if mods & pygame.KMOD_SHIFT:
                                    self.scroll_x = max(0, min(self.map_cols * int(self.TILE_SIZE * self.VIEW_SCALE), self.scroll_x + delta))
                                else:
                                    self.scroll_y = max(0, min(self.map_rows * int(self.TILE_SIZE * self.VIEW_SCALE), self.scroll_y + delta))
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 2:
                        self.middle_mouse_dragging = False
                        self.last_mouse_pos = None
                    elif event.button == 1:
                        if self.selection_dragging:
                            # Complete selection with multi-selection support
                            self.finish_selection_drag()
                        elif self.shape_dragging:
                            # Complete shape drawing
                            self.finish_shape_drawing()
                    self.drag_left_split = False
                    self.drag_right_split = False
                    self.drag_right_inner_split = False
                    self.splitter_active = None  # Clear active splitter state
                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    
                    # Update splitter hover state for visual feedback
                    self.splitter_hover = None
                    if hasattr(self, 'splitter_zones'):
                        for zone_name, zone_rect in self.splitter_zones.items():
                            if zone_rect.collidepoint(mx, my):
                                self.splitter_hover = zone_name
                                # Set cursor to resize cursor if possible
                                if zone_name in ['left', 'right']:
                                    # Horizontal resize cursor would go here
                                    pass
                                elif zone_name == 'right_inner':
                                    # Vertical resize cursor would go here  
                                    pass
                                break
                    
                    # Menu hover handling
                    if self.show_menu_bar:
                        menu_bar_rect = pygame.Rect(0, 0, self.WIDTH, self.MENU_BAR_H)
                        if menu_bar_rect.collidepoint(mx, my):
                            # Check which menu is hovered
                            hovered_menu = None
                            for menu_id, rect in self._menu_hitboxes.items():
                                if rect.collidepoint(mx, my):
                                    hovered_menu = menu_id
                                    break
                            
                            # If we have an active menu and hover over a different menu, switch to it
                            if self.active_menu and hovered_menu and hovered_menu != self.active_menu:
                                self.active_menu = hovered_menu
                                self.show_recent_files_menu = False
                                self.show_export_menu = False
                            
                            self.menu_hover = hovered_menu
                    
                    # Handle selection dragging
                    if self.selection_dragging and self.canvas_rect.collidepoint(mx, my):
                        cx, cy = self.screen_to_tile(mx, my)
                        self.selection_end_x = cx
                        self.selection_end_y = cy
                    
                    # Handle shape preview updating
                    if self.shape_dragging and self.canvas_rect.collidepoint(mx, my):
                        cx, cy = self.screen_to_tile(mx, my)
                        self.update_shape_preview(cx, cy)
                    
                    # Handle paste preview position tracking
                    if self.paste_preview and self.canvas_rect.collidepoint(mx, my):
                        self.paste_x, self.paste_y = self.screen_to_tile(mx, my)
                    
                    # Handle middle-mouse drag panning
                    if self.middle_mouse_dragging and self.last_mouse_pos:
                        dx = mx - self.last_mouse_pos[0]  
                        dy = my - self.last_mouse_pos[1]
                        
                        # Update scroll position (inverted because we're moving the viewport)
                        max_scroll_x = max(0, self.map_cols * int(self.TILE_SIZE * self.VIEW_SCALE) - self.canvas_rect.width)
                        max_scroll_y = max(0, self.map_rows * int(self.TILE_SIZE * self.VIEW_SCALE) - self.canvas_rect.height)
                        
                        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x - dx))
                        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - dy))
                        
                        self.last_mouse_pos = (mx, my)
                        
                    # Handle panel split dragging
                    if self.drag_left_split:
                        new_left = mx - self._drag_offset
                        new_left = max(self.min_left, min(self.WIDTH - self.min_canvas_w - self.right_w, new_left))
                        self.left_w = new_left
                    elif self.drag_right_split:
                        new_right = self.WIDTH - (mx - self._drag_offset)
                        new_right = max(self.min_right, min(self.WIDTH - self.min_canvas_w - self.left_w, new_right))
                        self.right_w = new_right
                    elif self.drag_right_inner_split and self.right_rect.height > 0:
                        rel = my - self.right_rect.y - self._drag_offset
                        self.right_split = max(0.2, min(0.8, rel / self.right_rect.height))

            # keyboard panning
            keys = pygame.key.get_pressed()
            if not self.show_settings:
                pan_dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
                pan_dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
                if pan_dx:
                    self.scroll_x = max(0, min(self.map_cols * self.TILE_SIZE * self.VIEW_SCALE, self.scroll_x + pan_dx * self.scroll_speed * dt))
                if pan_dy:
                    self.scroll_y = max(0, min(self.map_rows * self.TILE_SIZE * self.VIEW_SCALE, self.scroll_y + pan_dy * self.scroll_speed * dt))

            # continuous painting while held on canvas
            if not self.show_settings and (pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]):
                mx, my = pygame.mouse.get_pos()
                if self.canvas_rect.collidepoint(mx, my):
                    cx, cy = self.screen_to_tile(mx, my)
                    if pygame.mouse.get_pressed()[2] or self.tool == "erase":
                        self.paint_at(cx, cy, 3)
                    elif self.tool == "paint":
                        self.paint_at(cx, cy, 1)

            # draw
            self.screen.fill(self.BG)
            self.draw_palette_panel()
            # canvas background - use the user-selected background color
            pygame.draw.rect(self.screen, self.BG, self.canvas_rect)
            self.draw_layers()
            self.draw_grid()
            
            # Draw selection and paste preview
            self.draw_selection()
            if self.paste_preview:
                self.draw_paste_preview()
                
            self.draw_right_panels()
            self.draw_hud()
            
            # Draw splitter handles for resizing panels
            self.draw_splitter_handles()
            
            # Draw collision type dropdown menu (on top of everything)
            self.draw_collision_type_menu()
            
            # Draw object type dropdown menu (on top of everything)
            self.draw_object_type_menu()
            
            # Draw zoom dropdown menu (on top of everything)
            self.draw_zoom_menu()
            
            # Draw main menu dropdown (on top of everything)
            if self.active_menu:
                self.draw_dropdown_menu()
            
            if self.show_settings:
                self.draw_settings_overlay()

            # cursor highlight
            mx, my = pygame.mouse.get_pos()
            if self.canvas_rect.collidepoint(mx, my):
                cx, cy = self.screen_to_tile(mx, my)
                if 0 <= cx < self.map_cols and 0 <= cy < self.map_rows:
                    ts = self.TILE_SIZE * self.VIEW_SCALE
                    x, y = self.tile_to_screen(cx, cy)
                    clip_prev = self.screen.get_clip()
                    self.screen.set_clip(self.canvas_rect)
                    pygame.draw.rect(self.screen, self.ACTIVE, (x, y, ts, ts), 2)
                    self.screen.set_clip(clip_prev)

            pygame.display.flip()

            if self.auto_exit_seconds is not None:
                self.elapsed += dt
                if self.elapsed >= self.auto_exit_seconds:
                    running = False

        # Save preferences before exiting
        self.save_preferences()
        pygame.quit()


def main():
    editor = TileEditor("Assests/Cave_Tileset.png")
    editor.run()


if __name__ == "__main__":
    main()
