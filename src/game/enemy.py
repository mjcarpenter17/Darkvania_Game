"""Enemy character classes with animation and rendering."""
import pygame
from typing import List, Tuple

from ..utils.aseprite_animation_loader import AsepriteAnimationLoader


class Enemy:
    """Base enemy class with position, sprite rendering, and animation."""
    
    def __init__(self, x: float, y: float, scale: int = 2):
        # Position (pivot point - feet center)
        self.pos_x = x
        self.pos_y = y
        
        # Physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        
        # Animation
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Config
        self.scale = scale
        self.direction = 1  # 1=right, -1=left
        self.gravity = 1400.0  # Same as player
        
        # Animation loader (to be set by subclasses)
        self.animation_loader = None
        
    def update(self, dt: float, world_map=None):
        """Update enemy animation, physics, and logic."""
        # Apply physics
        self._apply_physics(dt)
        
        # Handle collisions if world map is provided
        if world_map:
            self._handle_collisions(world_map, dt)
        else:
            # Fallback collision (ground level)
            self._handle_basic_collision()
        
        # Update animation timer
        if self.animation_loader and self.state in self.animation_loader.animations:
            animation_data = self.animation_loader.get_animation(self.state)
            if animation_data and animation_data['durations']:
                durations = animation_data['durations']
                frame_duration = durations[min(self.current_frame, len(durations) - 1)]
                self.frame_timer += dt
                
                if self.frame_timer >= frame_duration:
                    self.frame_timer = 0.0
                    
                    # Get frame count
                    frames = animation_data['surfaces_right']
                    if frames:
                        self.current_frame = (self.current_frame + 1) % len(frames)
    
    def _apply_physics(self, dt: float):
        """Apply gravity and basic physics."""
        self.velocity_y += self.gravity * dt
        
    def _handle_collisions(self, world_map, dt: float):
        """Handle collision detection and response with the world."""
        # Horizontal movement with collision (enemies don't move horizontally for now)
        # new_x = self.pos_x + self.velocity_x * dt
        # For basic enemies, we'll skip horizontal movement for now
        
        # Vertical movement with collision
        new_y = self.pos_y + self.velocity_y * dt
        
        if self.velocity_y > 0:  # Falling
            # Check at foot level (slightly below pivot)
            foot_y = new_y + 2
            
            # Check for solid tiles (always stop)
            if world_map.is_solid_at_any_layer(self.pos_x, foot_y):
                # Find the exact ground level
                tile_size = world_map.tile_size * world_map.scale
                tile_y = int(foot_y // tile_size) * tile_size
                self.pos_y = float(tile_y - 2)  # Stand on top of the tile
                self.velocity_y = 0.0
                self.on_ground = True
            # Check for platform tiles (only stop if falling onto them from above)
            elif world_map.is_platform_at_any_layer(self.pos_x, foot_y):
                # Only land on platform if we're falling from above
                tile_size = world_map.tile_size * world_map.scale
                tile_y = int(foot_y // tile_size) * tile_size
                # Check if our previous position was above this tile
                prev_foot_y = self.pos_y + 2
                if prev_foot_y <= tile_y:
                    self.pos_y = float(tile_y - 2)  # Stand on top of the platform
                    self.velocity_y = 0.0
                    self.on_ground = True
                else:
                    # We're inside or below the platform, pass through
                    self.pos_y = new_y
                    self.on_ground = False
            else:
                self.pos_y = new_y
                self.on_ground = False
        else:  # Moving up (shouldn't happen much for basic enemies)
            # Check at head level (only solid tiles block upward movement)
            head_y = new_y - 35
            if world_map.is_solid_at_any_layer(self.pos_x, head_y):
                # Hit ceiling
                self.velocity_y = 0.0
                # Don't update position to prevent clipping into ceiling
            else:
                self.pos_y = new_y
                self.on_ground = False
                
        # Keep enemy within map bounds
        map_width = world_map.map_cols * world_map.tile_size * world_map.scale
        if self.pos_x < 0:
            self.pos_x = 0
        if self.pos_x > map_width:
            self.pos_x = map_width
            
    def _handle_basic_collision(self):
        """Basic collision for when no world map is available."""
        ground_y = 400.0  # Default ground level
        
        # Apply vertical movement
        self.pos_y += self.velocity_y * (1/60.0)  # Assume 60 FPS for fallback
        
        # Check ground collision
        if self.pos_y >= ground_y:
            self.pos_y = ground_y
            self.velocity_y = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
    
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float):
        """Render the enemy on screen."""
        if not self.animation_loader or self.state not in self.animation_loader.animations:
            return
            
        # Get animation data
        animation_data = self.animation_loader.get_animation(self.state)
        if not animation_data:
            return
        
        # Get frames based on direction
        frames = animation_data['surfaces_right'] if self.direction > 0 else animation_data['surfaces_left']
        pivots = animation_data['pivots_right'] if self.direction > 0 else animation_data['pivots_left']
        
        if not frames or self.current_frame >= len(frames):
            return
        
        # Get current frame and pivot
        current_surface = frames[self.current_frame]
        pivot_x, pivot_y = pivots[self.current_frame] if pivots else (0, 0)
        
        # Calculate screen position (subtract camera offset)
        screen_x = int(self.pos_x - camera_x - pivot_x)
        screen_y = int(self.pos_y - camera_y - pivot_y)
        
        # Draw the sprite
        screen.blit(current_surface, (screen_x, screen_y))
    
    def get_position(self) -> Tuple[float, float]:
        """Get enemy position."""
        return (self.pos_x, self.pos_y)


class AssassinEnemy(Enemy):
    """Assassin enemy that uses the Assassin.json animation data."""
    
    def __init__(self, x: float, y: float, scale: int = 2):
        super().__init__(x, y, scale)
        
        # Load Aseprite animations
        aseprite_json_path = "Assests/enemies/assassin/Assassin.json"
        self.animation_loader = AsepriteAnimationLoader(aseprite_json_path, scale)
        
        # Define which animations to load for the assassin
        assassin_animations = {
            'idle': 'idle',
            'run': 'run', 
            'jump': 'jump',
            'fall': 'fall',
            'attack1': 'attack 1',
            'attack2': 'attack 2'
        }
        
        self.animation_loader.load_all_animations(assassin_animations)
        
        # Set initial state to idle
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0