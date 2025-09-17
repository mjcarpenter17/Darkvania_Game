"""
Collectible system for the game.

This module provides the collectible system that allows players to find and collect
various items throughout the game world. Collectibles float above their spawn position
and gently bob up and down to attract player attention.

Classes:
    Collectible: Base class for all collectible items
    BandageCollectible: Health restoration item
"""

import math
import pygame
from typing import Optional, Dict, Any

from ..animations import CollectibleAnimationLoader


class Collectible:
    """
    Base class for all collectible items in the game.
    
    Collectibles are items that players can pick up throughout the game world.
    They float above their spawn position with gentle bobbing animation and
    play spinning/glowing animations to attract attention.
    
    Features:
    - Floating animation (hovers 32 pixels above spawn point)
    - Gentle up/down bobbing motion
    - Animated sprite using CollectibleAnimationLoader
    - Collision detection with player
    - Pickup behavior and effects
    """
    
    def __init__(self, spawn_x: float, spawn_y: float, collectible_type: str, scale: int = 2):
        """
        Initialize a collectible item.
        
        Args:
            spawn_x: X coordinate where collectible was placed in map
            spawn_y: Y coordinate where collectible was placed in map
            collectible_type: Type of collectible (e.g., 'bandage', 'key', 'ammo')
            scale: Scale factor for rendering
        """
        # Position and movement
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.scale = scale
        
        # Floating mechanics
        self.float_height = 32.0 * scale  # Float 32 pixels above spawn point
        self.current_x = spawn_x
        self.current_y = spawn_y - self.float_height  # Start at floating position
        
        # Bobbing animation
        self.bob_amplitude = 8.0 * scale  # How far up/down to bob
        self.bob_speed = 2.0  # Bobbing frequency (cycles per second)
        self.bob_time = 0.0  # Time accumulator for sine wave
        self.base_float_y = self.current_y  # Base floating Y position
        
        # Collectible properties
        self.collectible_type = collectible_type
        self.is_active = True  # Can be collected
        self.is_collected = False  # Has been picked up
        
        # Animation system
        self.animation_loader: Optional[CollectibleAnimationLoader] = None
        self.current_animation = "idle"
        self.animation_time = 0.0
        self.current_frame = 0  # Current frame index
        self.sprite_surface: Optional[pygame.Surface] = None
        
        # Collision detection
        self.collision_width = 16 * scale  # Width of collision box
        self.collision_height = 16 * scale  # Height of collision box
        
        # Initialize animation
        self._setup_animation()
    
    def _setup_animation(self):
        """Initialize the animation system for this collectible."""
        try:
            # Use collectibles sprite sheet
            collectibles_json = "Assests/collectibles/collects.json"
            
            # Create animation loader
            self.animation_loader = CollectibleAnimationLoader(
                collectibles_json, 
                scale=self.scale
            )
            
            # Check if the animation loader loaded properly
            if self.animation_loader.load():
                print(f"Loaded animation system for {self.collectible_type} collectible")
                
                # For collectibles, we directly use the collectible type name as animation
                # (e.g., 'bandage' collectible uses 'bandage' animation)
                if self.animation_loader.aseprite_loader.get_animation(self.collectible_type):
                    print(f"Found animation '{self.collectible_type}' in sprite data")
                    self.current_animation = self.collectible_type
                    # Load this specific animation
                    if self.animation_loader._load_animation(self.collectible_type, self.collectible_type):
                        print(f"Successfully loaded {self.collectible_type} animation")
                    else:
                        print(f"Failed to load {self.collectible_type} animation, using fallback")
                        self._create_fallback_animation()
                else:
                    print(f"Animation '{self.collectible_type}' not found in sprite data")
                    self._create_fallback_animation()
            else:
                print(f"Warning: Failed to load animation loader for {self.collectible_type} collectible")
                self._create_fallback_animation()
                
        except Exception as e:
            print(f"Error setting up collectible animation: {e}")
            self.animation_loader = None
            self._create_fallback_animation()
    
    def _create_fallback_animation(self):
        """Create a simple fallback animation when sprites aren't available."""
        # Create a simple colored rectangle as fallback
        fallback_size = 16 * self.scale
        fallback_surface = pygame.Surface((fallback_size, fallback_size), pygame.SRCALPHA)
        
        # Choose color based on collectible type
        color_map = {
            'bandage': (255, 100, 100),  # Red for health
            'key': (255, 255, 0),        # Yellow for keys  
            'ammo': (100, 100, 255),     # Blue for ammo
            'bottle': (0, 255, 100),     # Green for potions
        }
        color = color_map.get(self.collectible_type, (255, 255, 255))  # White default
        
        pygame.draw.rect(fallback_surface, color, (2, 2, fallback_size-4, fallback_size-4))
        pygame.draw.rect(fallback_surface, (255, 255, 255), (0, 0, fallback_size, fallback_size), 2)
        
        self.sprite_surface = fallback_surface
        print(f"Created fallback animation for {self.collectible_type} collectible")
    
    def update(self, dt: float):
        """
        Update the collectible state.
        
        Args:
            dt: Delta time in seconds
        """
        if not self.is_active or self.is_collected:
            return
        
        # Update bobbing animation
        self._update_floating_movement(dt)
        
        # Update sprite animation
        self._update_animation(dt)
    
    def _update_floating_movement(self, dt: float):
        """Update the floating/bobbing movement."""
        # Increment bobbing time
        self.bob_time += dt * self.bob_speed
        
        # Calculate bobbing offset using sine wave
        bob_offset = math.sin(self.bob_time) * self.bob_amplitude
        
        # Update current position
        self.current_x = self.spawn_x  # No horizontal movement
        self.current_y = self.base_float_y + bob_offset
    
    def _update_animation(self, dt: float):
        """Update the sprite animation."""
        if not self.animation_loader:
            return
        
        # Get animation data
        animation_data = self.animation_loader.get_animation(self.current_animation)
        if not animation_data:
            # No animation data, keep using current sprite_surface
            return
        
        # Update animation timing
        self.animation_time += dt
        
        # Get frame information
        frame_duration = self.animation_loader.get_frame_duration(self.current_animation, self.current_frame)
        if frame_duration and self.animation_time >= frame_duration:
            self.animation_time = 0.0
            
            # Get frames for animation
            frames = animation_data.get('surfaces_right', [])
            if frames:
                self.current_frame = (self.current_frame + 1) % len(frames)
        
        # Get current frame surface
        new_surface = self.animation_loader.get_frame_surface(
            self.current_animation, 
            self.current_frame, 
            facing_right=True
        )
        
        if new_surface:
            self.sprite_surface = new_surface
    
    def play_animation(self, animation_name: str):
        """
        Play a specific animation.
        
        Args:
            animation_name: Name of animation to play ('idle', 'highlight', 'collect', etc.)
        """
        if self.animation_loader and animation_name != self.current_animation:
            self.current_animation = animation_name
            self.animation_time = 0.0
            self.current_frame = 0  # Reset frame index
            print(f"Collectible playing animation: {animation_name}")
    
    def get_collision_rect(self) -> pygame.Rect:
        """
        Get the collision rectangle for this collectible.
        
        Returns:
            pygame.Rect: Collision rectangle
        """
        return pygame.Rect(
            self.current_x - self.collision_width // 2,
            self.current_y - self.collision_height // 2,
            self.collision_width,
            self.collision_height
        )
    
    def check_player_collision(self, player_rect: pygame.Rect) -> bool:
        """
        Check if the player is colliding with this collectible.
        
        Args:
            player_rect: Player's collision rectangle
            
        Returns:
            bool: True if collision detected
        """
        if not self.is_active or self.is_collected:
            return False
        
        return self.get_collision_rect().colliderect(player_rect)
    
    def collect(self, player) -> Dict[str, Any]:
        """
        Handle collection of this item by the player.
        
        Args:
            player: Player object that collected this item
            
        Returns:
            dict: Collection result with effect information
        """
        if not self.is_active or self.is_collected:
            return {"collected": False, "reason": "Already collected"}
        
        # Mark as collected
        self.is_collected = True
        self.is_active = False
        
        # Play collection animation
        self.play_animation("collect")
        
        print(f"Player collected {self.collectible_type}!")
        
        # Return collection result
        return {
            "collected": True,
            "item_type": self.collectible_type,
            "effects": self._get_collection_effects()
        }
    
    def _get_collection_effects(self) -> Dict[str, Any]:
        """
        Get the effects of collecting this item.
        
        Returns:
            dict: Effects to apply to player
        """
        # Base collectible provides no effects
        # Override in specific collectible classes
        return {}
    
    def render(self, screen: pygame.Surface, camera_offset_x: float, camera_offset_y: float):
        """
        Render the collectible to the screen.
        
        Args:
            screen: Surface to render to
            camera_offset_x: Camera X offset
            camera_offset_y: Camera Y offset
        """
        if not self.is_active or self.is_collected or not self.sprite_surface:
            return
        
        # Calculate screen position
        screen_x = self.current_x - camera_offset_x
        screen_y = self.current_y - camera_offset_y
        
        # Center the sprite on the position
        sprite_rect = self.sprite_surface.get_rect()
        sprite_rect.center = (screen_x, screen_y)
        
        # Render sprite
        screen.blit(self.sprite_surface, sprite_rect)
        
        # Debug: Draw collision box
        if hasattr(screen, '_debug_collision') and getattr(screen, '_debug_collision', False):
            collision_rect = self.get_collision_rect()
            debug_rect = pygame.Rect(
                collision_rect.x - camera_offset_x,
                collision_rect.y - camera_offset_y,
                collision_rect.width,
                collision_rect.height
            )
            pygame.draw.rect(screen, (0, 255, 255), debug_rect, 2)


class BandageCollectible(Collectible):
    """
    Bandage collectible that restores player health.
    
    Bandages are common healing items that restore a small amount of health
    when collected. They use the 'bandage' animation from the collectibles
    sprite sheet.
    """
    
    def __init__(self, spawn_x: float, spawn_y: float, scale: int = 2):
        """
        Initialize a bandage collectible.
        
        Args:
            spawn_x: X coordinate where bandage was placed
            spawn_y: Y coordinate where bandage was placed
            scale: Scale factor for rendering
        """
        super().__init__(spawn_x, spawn_y, "bandage", scale)
        
        # Bandage-specific properties
        self.health_restore = 25  # Amount of health to restore
    
    def _get_collection_effects(self) -> Dict[str, Any]:
        """
        Get the effects of collecting a bandage.
        
        Returns:
            dict: Health restoration effect
        """
        return {
            "health_restore": self.health_restore,
            "message": f"Restored {self.health_restore} health!"
        }


def create_collectible(collectible_type: str, spawn_x: float, spawn_y: float, scale: int = 2) -> Optional[Collectible]:
    """
    Factory function to create specific collectible types.
    
    Args:
        collectible_type: Type of collectible to create
        spawn_x: X spawn coordinate
        spawn_y: Y spawn coordinate
        scale: Scale factor
        
    Returns:
        Collectible: Created collectible instance, or None if type unknown
    """
    collectible_map = {
        "bandage": BandageCollectible,
        # Add more collectible types here as needed
        # "key": KeyCollectible,
        # "ammo": AmmoCollectible,
        # etc.
    }
    
    if collectible_type in collectible_map:
        return collectible_map[collectible_type](spawn_x, spawn_y, scale)
    else:
        print(f"Warning: Unknown collectible type '{collectible_type}', creating base Collectible")
        return Collectible(spawn_x, spawn_y, collectible_type, scale)