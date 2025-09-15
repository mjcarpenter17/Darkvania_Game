"""Camera system for following the player and managing viewport."""
import pygame
from typing import Tuple


class Camera:
    """Camera system for smooth following and viewport management."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.x = 0.0
        self.y = 0.0
        
        # Camera smoothing - using lerp factor instead of smoothing
        self.lerp_speed = 8.0  # How fast camera catches up (higher = faster)
        self.target_x = 0.0
        self.target_y = 0.0
        
        # Dead zone (area where player can move without camera moving)
        self.dead_zone_width = 10  # Smaller dead zone for more responsive feel
        self.dead_zone_height = 10
        
        # Lookahead - camera anticipates player movement
        self.lookahead_distance = 50
        self.lookahead_smooth = 0.0  # Current lookahead offset
        
        # World bounds (set by world)
        self.world_width = 0
        self.world_height = 0
        
    def set_world_bounds(self, width: int, height: int):
        """Set the world boundaries for camera clamping."""
        self.world_width = width
        self.world_height = height
        
    def follow_target(self, target_x: float, target_y: float, dt: float, velocity_x: float = 0.0):
        """Update camera to follow a target position with smooth movement and lookahead."""
        # Calculate desired camera position (center target on screen)
        desired_x = target_x - self.width // 2
        desired_y = target_y - self.height // 2
        
        # Add lookahead based on velocity
        if abs(velocity_x) > 10:  # Only add lookahead when moving fast enough
            # Gradually adjust lookahead
            target_lookahead = self.lookahead_distance if velocity_x > 0 else -self.lookahead_distance
            self.lookahead_smooth += (target_lookahead - self.lookahead_smooth) * dt * 3.0
        else:
            # Return to center when not moving
            self.lookahead_smooth += (0 - self.lookahead_smooth) * dt * 2.0
            
        # Apply lookahead to desired position
        desired_x += self.lookahead_smooth
        
        # Apply dead zone
        camera_center_x = self.x + self.width // 2
        camera_center_y = self.y + self.height // 2
        
        dx = target_x - camera_center_x
        dy = target_y - camera_center_y
        
        # Only update target if outside dead zone
        if abs(dx) > self.dead_zone_width // 2:
            self.target_x = desired_x
        if abs(dy) > self.dead_zone_height // 2:
            self.target_y = desired_y
        
        # Smooth interpolation to target
        self.x += (self.target_x - self.x) * self.lerp_speed * dt
        self.y += (self.target_y - self.y) * self.lerp_speed * dt
            
        # Clamp camera to world bounds
        self._clamp_to_world()
        
    def set_position(self, x: float, y: float):
        """Set camera position directly."""
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self._clamp_to_world()
        
    def center_on_target(self, target_x: float, target_y: float):
        """Center camera on target immediately."""
        self.x = target_x - self.width // 2
        self.y = target_y - self.height // 2
        self.target_x = self.x
        self.target_y = self.y
        self._clamp_to_world()
        
    def _clamp_to_world(self):
        """Clamp camera position to world boundaries."""
        if self.world_width > 0 and self.world_height > 0:
            # Don't move camera if world is smaller than screen
            if self.world_width < self.width:
                self.x = (self.world_width - self.width) // 2
                self.target_x = self.x
            else:
                self.x = max(0, min(self.x, self.world_width - self.width))
                self.target_x = max(0, min(self.target_x, self.world_width - self.width))
                
            if self.world_height < self.height:
                self.y = (self.world_height - self.height) // 2
                self.target_y = self.y
            else:
                self.y = max(0, min(self.y, self.world_height - self.height))
                self.target_y = max(0, min(self.target_y, self.world_height - self.height))
                
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = int(world_x - self.x)
        screen_y = int(world_y - self.y)
        return screen_x, screen_y
        
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = screen_x + self.x
        world_y = screen_y + self.y
        return world_x, world_y
        
    def get_viewport_rect(self) -> pygame.Rect:
        """Get the current viewport as a pygame Rect."""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def is_visible(self, world_x: float, world_y: float, width: int = 0, height: int = 0) -> bool:
        """Check if a world position/rectangle is visible in the camera."""
        return (self.x - width <= world_x <= self.x + self.width and
                self.y - height <= world_y <= self.y + self.height)
                
    def get_position(self) -> Tuple[float, float]:
        """Get current camera position."""
        return self.x, self.y
        
    def set_smoothing(self, lerp_speed: float):
        """Set camera smoothing speed (higher = faster following)."""
        self.lerp_speed = max(0.1, lerp_speed)
        
    def set_lookahead(self, distance: float):
        """Set camera lookahead distance."""
        self.lookahead_distance = distance
        
    def set_dead_zone(self, width: int, height: int):
        """Set the size of the camera dead zone."""
        self.dead_zone_width = width
        self.dead_zone_height = height
