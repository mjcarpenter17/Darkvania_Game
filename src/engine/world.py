"""World/TileMap class for managing game levels and collision detection."""
import json
import os
from typing import List, Dict, Tuple, Optional

import pygame


class World:
    """Manages the game world including tiles, collision, and objects."""
    
    def __init__(self, map_path: str, scale: int = 1):
        """Load a tile map from the map editor format."""
        self.scale = scale
        self.tiles = []  # List of tile surfaces
        self.layers = []  # List of layer data
        self.objects = []  # List of game objects (spawns, enemies, etc.)
        self.tile_size = 16
        self.map_cols = 0
        self.map_rows = 0
        self.tile_properties = {}  # Collision data from map editor
        
        self.load_map(map_path)
        
    def load_map(self, map_path: str):
        """Load the map data from JSON file."""
        # Load the map data
        with open(map_path, 'r') as f:
            map_data = json.load(f)
        
        # Load tileset
        tileset_path = map_data['tileset']
        if not os.path.isabs(tileset_path):
            # Make path relative to map file
            map_dir = os.path.dirname(map_path)
            tileset_path = os.path.join(map_dir, '..', tileset_path)
            tileset_path = os.path.normpath(tileset_path)
        
        self.tile_size = map_data['tile_size']
        self.map_cols = map_data['map_cols']
        self.map_rows = map_data['map_rows']
        margin = map_data['margin']
        spacing = map_data['spacing']
        
        # Load tile properties (collision data)
        self.tile_properties = map_data.get('tile_properties', {})
        collision_types = {}
        for tile_id, props in self.tile_properties.items():
            ctype = props.get('collision_type', 'none')
            collision_types[ctype] = collision_types.get(ctype, 0) + 1
        print(f"Loaded collision data for {len(self.tile_properties)} tile types:")
        for ctype, count in collision_types.items():
            print(f"  {ctype}: {count} tiles")
        
        # Load and slice tileset
        tileset_image = pygame.image.load(tileset_path).convert_alpha()
        self.slice_tileset(tileset_image, self.tile_size, margin, spacing)
        
        # Load layers
        for layer_data in map_data['layers']:
            layer = {}
            layer['name'] = layer_data['name']
            layer['tiles'] = {}
            
            # Convert tile list to dictionary for faster lookup
            for tile in layer_data['tiles']:
                key = (tile['x'], tile['y'])
                layer['tiles'][key] = tile['t']
            
            self.layers.append(layer)
        
        # Load objects (spawns, enemies, etc.)
        self.objects = map_data.get('objects', [])
        print(f"Loaded {len(self.objects)} objects:")
        for obj in self.objects:
            print(f"  {obj.get('name', 'Unnamed')} ({obj.get('type', 'unknown')}) at ({obj.get('x', 0)}, {obj.get('y', 0)})")
    
    def slice_tileset(self, tileset_surface: pygame.Surface, tile_size: int, margin: int, spacing: int):
        """Slice the tileset into individual tile surfaces."""
        self.tiles = []
        cols = (tileset_surface.get_width() - 2 * margin + spacing) // (tile_size + spacing)
        rows = (tileset_surface.get_height() - 2 * margin + spacing) // (tile_size + spacing)
        
        for row in range(rows):
            for col in range(cols):
                x = margin + col * (tile_size + spacing)
                y = margin + row * (tile_size + spacing)
                
                tile_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                tile_surf.blit(tileset_surface, (0, 0), (x, y, tile_size, tile_size))
                
                if self.scale != 1:
                    tile_surf = pygame.transform.scale(tile_surf, 
                                                     (tile_size * self.scale, tile_size * self.scale))
                
                self.tiles.append(tile_surf)
    
    def find_spawn_point(self, name: str) -> Optional[Tuple[float, float]]:
        """Find a spawn point by name. Returns (world_x, world_y) in pixels or None if not found."""
        for obj in self.objects:
            if obj.get('name') == name and obj.get('type') == 'spawn':
                # Convert grid coordinates to world coordinates
                grid_x = obj.get('x', 0)
                grid_y = obj.get('y', 0)
                world_x = float(grid_x * self.tile_size * self.scale)
                world_y = float(grid_y * self.tile_size * self.scale)
                return (world_x, world_y)
        return None
    
    def find_objects_by_type(self, object_type: str) -> List[Dict]:
        """Find all objects of a specific type."""
        return [obj for obj in self.objects if obj.get('type') == object_type]
    
    def find_objects_by_name(self, name: str) -> List[Dict]:
        """Find all objects with a specific name."""
        return [obj for obj in self.objects if obj.get('name') == name]
    
    def find_enemy_spawn_points(self) -> List[Dict]:
        """Find all enemy spawn points and convert to world coordinates."""
        enemy_spawns = []
        for obj in self.objects:
            if obj.get('type') == 'enemy':
                # Convert tile coordinates to world coordinates
                world_x = obj.get('x', 0) * self.tile_size * self.scale
                world_y = obj.get('y', 0) * self.tile_size * self.scale
                
                spawn_info = {
                    'name': obj.get('name', 'Unknown'),
                    'world_x': world_x,
                    'world_y': world_y,
                    'tile_x': obj.get('x', 0),
                    'tile_y': obj.get('y', 0),
                    'custom_properties': obj.get('custom_properties', {})
                }
                enemy_spawns.append(spawn_info)
                
        return enemy_spawns
    
    def find_collectible_spawn_points(self) -> List[Dict]:
        """Find all collectible spawn points and convert to world coordinates."""
        collectible_spawns = []
        for obj in self.objects:
            if obj.get('type') == 'collectible':
                # Convert tile coordinates to world coordinates
                world_x = obj.get('x', 0) * self.tile_size * self.scale
                world_y = obj.get('y', 0) * self.tile_size * self.scale
                
                # Determine collectible type from name (e.g., "Collectible_01" -> "bandage")
                obj_name = obj.get('name', 'Unknown')
                collectible_type = self._parse_collectible_type(obj_name, obj)
                
                spawn_info = {
                    'name': obj_name,
                    'collectible_type': collectible_type,
                    'world_x': world_x,
                    'world_y': world_y,
                    'tile_x': obj.get('x', 0),
                    'tile_y': obj.get('y', 0),
                    'custom_properties': obj.get('custom_properties', {})
                }
                collectible_spawns.append(spawn_info)
                
        return collectible_spawns
    
    def find_chest_spawn_points(self) -> List[Dict]:
        """Find all chest spawn points and convert to world coordinates."""
        chest_spawns = []
        for obj in self.objects:
            obj_name = obj.get('name', 'Unknown')
            obj_type = obj.get('type', '')
            
            is_chest = False
            chest_type = "basic"
            
            # Primary check: object type is 'chest'
            if obj_type == 'chest':
                is_chest = True
                # Parse chest type from name if present
                if 'gold' in obj_name.lower():
                    chest_type = "gold"
                elif 'silver' in obj_name.lower():
                    chest_type = "silver"
                elif 'magic' in obj_name.lower():
                    chest_type = "magic"
            
            # Fallback check: collectible type objects with 'chest' in name (legacy support)
            elif obj_type == 'collectible' and 'chest' in obj_name.lower():
                is_chest = True
                print(f"Warning: Found chest object '{obj_name}' with 'collectible' type. Consider changing to 'chest' type.")
            
            if is_chest:
                # Convert tile coordinates to world coordinates
                world_x = obj.get('x', 0) * self.tile_size * self.scale
                world_y = obj.get('y', 0) * self.tile_size * self.scale
                
                spawn_info = {
                    'name': obj_name,
                    'chest_type': chest_type,
                    'world_x': world_x,
                    'world_y': world_y,
                    'tile_x': obj.get('x', 0),
                    'tile_y': obj.get('y', 0),
                    'custom_properties': obj.get('custom_properties', {})
                }
                chest_spawns.append(spawn_info)
                print(f"Found chest spawn: {obj_name} at tile ({obj.get('x', 0)}, {obj.get('y', 0)}) -> world ({world_x}, {world_y})")
                
        return chest_spawns
    
    def _parse_collectible_type(self, obj_name: str, obj: Dict) -> str:
        """
        Parse the collectible type from object name or properties.
        
        Args:
            obj_name: Name of the object (e.g., "Collectible_01")
            obj: Full object data
            
        Returns:
            str: Collectible type (e.g., "bandage", "key", "ammo")
        """
        # Check if custom properties specify the type
        custom_props = obj.get('custom_properties', {})
        if 'collectible_type' in custom_props:
            return custom_props['collectible_type']
        
        # Check for type in the name
        obj_name_lower = obj_name.lower()
        if 'bandage' in obj_name_lower:
            return 'bandage'
        elif 'key' in obj_name_lower:
            return 'key'
        elif 'ammo' in obj_name_lower:
            return 'ammo'
        elif 'health' in obj_name_lower:
            return 'bandage'
        elif 'potion' in obj_name_lower or 'bottle' in obj_name_lower:
            return 'bottle'
        
        # Default fallback - for now, use bandage for testing
        # TODO: This could be configurable or read from map editor
        return 'bandage'
    
    def get_tile_at(self, world_x: float, world_y: float, layer_index: int = 0) -> int:
        """Get the tile ID at a world position (returns -1 if no tile)."""
        tile_x = int(world_x // (self.tile_size * self.scale))
        tile_y = int(world_y // (self.tile_size * self.scale))
        
        if layer_index < len(self.layers):
            return self.layers[layer_index]['tiles'].get((tile_x, tile_y), -1)
        return -1
    
    def get_tile_at_any_layer(self, world_x: float, world_y: float) -> int:
        """Get the first non-empty tile ID found across all layers (returns -1 if no tile)."""
        tile_x = int(world_x // (self.tile_size * self.scale))
        tile_y = int(world_y // (self.tile_size * self.scale))
        
        # Check all layers from top to bottom (last to first for visibility priority)
        for layer_index in range(len(self.layers) - 1, -1, -1):
            tile_id = self.layers[layer_index]['tiles'].get((tile_x, tile_y), -1)
            if tile_id != -1:
                return tile_id
        return -1
    
    def get_collision_type_at(self, world_x: float, world_y: float, layer_index: int = 0) -> str:
        """Get the collision type at a world position."""
        tile_id = self.get_tile_at(world_x, world_y, layer_index)
        if tile_id == -1:
            return "none"
        
        tile_props = self.tile_properties.get(str(tile_id), {})
        return tile_props.get('collision_type', 'none')
    
    def get_collision_type_at_any_layer(self, world_x: float, world_y: float) -> str:
        """Get the collision type at a world position, checking all layers."""
        tile_id = self.get_tile_at_any_layer(world_x, world_y)
        if tile_id == -1:
            return "none"
        
        tile_props = self.tile_properties.get(str(tile_id), {})
        return tile_props.get('collision_type', 'none')
    
    def is_solid_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's a solid tile at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "solid"
    
    def is_solid_at_any_layer(self, world_x: float, world_y: float) -> bool:
        """Check if there's a solid tile at the world position across any layer."""
        collision_type = self.get_collision_type_at_any_layer(world_x, world_y)
        return collision_type == "solid"
    
    def is_platform_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's a platform tile at the world position (jump-through)."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "platform"
    
    def is_platform_at_any_layer(self, world_x: float, world_y: float) -> bool:
        """Check if there's a platform tile at the world position across any layer."""
        collision_type = self.get_collision_type_at_any_layer(world_x, world_y)
        return collision_type == "platform"
    
    def is_damage_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's a damage tile at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "damage"
    
    def is_water_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's a water tile at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "water"
    
    def is_ice_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's an ice tile at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "ice"
    
    def is_trigger_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's a trigger tile at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type == "trigger"
    
    def has_collision_at(self, world_x: float, world_y: float, layer_index: int = 0) -> bool:
        """Check if there's any collision (solid or platform) at the world position."""
        collision_type = self.get_collision_type_at(world_x, world_y, layer_index)
        return collision_type in ["solid", "platform"]
    
    def get_tile_properties(self, tile_id: int) -> Dict:
        """Get the full properties dictionary for a tile ID."""
        return self.tile_properties.get(str(tile_id), {})
    
    def get_world_bounds(self) -> Tuple[int, int]:
        """Get the world dimensions in pixels."""
        width = self.map_cols * self.tile_size * self.scale
        height = self.map_rows * self.tile_size * self.scale
        return width, height
    
    def is_position_in_bounds(self, world_x: float, world_y: float) -> bool:
        """Check if a position is within the world bounds."""
        width, height = self.get_world_bounds()
        return 0 <= world_x <= width and 0 <= world_y <= height
    
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Render the tile map with camera offset."""
        scaled_tile_size = self.tile_size * self.scale
        
        # Calculate visible tile range
        start_x = max(0, int(camera_x // scaled_tile_size))
        start_y = max(0, int(camera_y // scaled_tile_size))
        end_x = min(self.map_cols, start_x + (screen.get_width() // scaled_tile_size) + 2)
        end_y = min(self.map_rows, start_y + (screen.get_height() // scaled_tile_size) + 2)
        
        # Render each layer
        for layer in self.layers:
            for tile_y in range(start_y, end_y):
                for tile_x in range(start_x, end_x):
                    tile_id = layer['tiles'].get((tile_x, tile_y), -1)
                    if tile_id != -1 and tile_id < len(self.tiles):
                        draw_x = tile_x * scaled_tile_size - camera_x
                        draw_y = tile_y * scaled_tile_size - camera_y
                        screen.blit(self.tiles[tile_id], (draw_x, draw_y))


# Legacy alias for backwards compatibility
TileMap = World
