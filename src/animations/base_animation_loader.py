"""Base animation loader providing core Aseprite integration functionality.

This module contains the fundamental animation loading capabilities that all
entity-specific animation loaders inherit from. It provides:

1. Aseprite JSON/PNG parsing
2. Frame extraction and scaling
3. Animation data conversion
4. Pivot point management
5. Error handling and fallback mechanisms

All entity-specific loaders (Player, Enemy, etc.) build upon this foundation.
"""

import os
import pygame
from typing import Dict, List, Tuple, Optional, Any
from ..utils.aseprite_loader import AsepriteLoader, AsepriteAnimation, AsepriteFrame


class BaseAnimationLoader:
    """
    Base class for all animation loaders in the game.
    
    Provides core functionality for loading and managing Aseprite-based animations.
    Entity-specific loaders should inherit from this class and define their own
    animation mappings and behaviors.
    
    Features:
    - Aseprite JSON/PNG file loading
    - Frame extraction and scaling
    - Pivot point management
    - Animation data conversion to game format
    - Error handling with fallback mechanisms
    - Common animation utilities
    """
    
    def __init__(self, json_path: str, scale: int = 2):
        """
        Initialize the base animation loader.
        
        Args:
            json_path: Path to the Aseprite JSON file
            scale: Scale factor for rendering (default: 2x)
        """
        self.scale = scale
        self.json_path = json_path
        self.aseprite_loader = AsepriteLoader(json_path, scale=scale)
        self.animations: Dict[str, Dict] = {}
        self.pivot_point: Tuple[int, int] = (0, 0)
        self.loaded = False
        
    def load(self) -> bool:
        """
        Load animation data from Aseprite file.
        
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        if not os.path.exists(self.json_path):
            print(f"Warning: Animation file not found: {self.json_path}")
            self._create_fallback_animations()
            return False
            
        if not self.aseprite_loader.load():
            print(f"Failed to load Aseprite data from {self.json_path}")
            self._create_fallback_animations()
            return False
            
        # Get pivot point from Aseprite data
        self.pivot_point = self.aseprite_loader.get_scaled_pivot()
        print(f"Found pivot point at {self.pivot_point}")
        
        self.loaded = True
        return True
        
    def _load_animation(self, state_name: str, aseprite_name: str) -> bool:
        """
        Load a specific animation from Aseprite data.
        
        Args:
            state_name: Internal name used by the game (e.g., 'idle', 'walk')
            aseprite_name: Name of the animation in Aseprite (e.g., 'Idle', 'Walk')
            
        Returns:
            bool: True if animation was loaded successfully
        """
        if not self.loaded:
            print(f"Warning: Attempted to load animation '{state_name}' before calling load()")
            return False
            
        animation = self.aseprite_loader.get_animation(aseprite_name)
        if not animation:
            print(f"Warning: Animation '{aseprite_name}' not found in Aseprite data")
            return False
            
        # Convert to game format
        right_surfaces = []
        left_surfaces = []
        pivots_right = []
        pivots_left = []
        durations = []
        
        for frame in animation.frames:
            # Extract frame surface from sprite sheet
            surface = self.aseprite_loader.get_frame_surface(frame)
            
            # Create horizontally flipped version for left-facing direction
            flipped_surface = pygame.transform.flip(surface, True, False)
            
            right_surfaces.append(surface)
            left_surfaces.append(flipped_surface)
            
            # Calculate pivot points
            pivot_x, pivot_y = self.pivot_point
            
            # Right-facing: use pivot as-is
            pivots_right.append((pivot_x, pivot_y))
            
            # Left-facing: flip X coordinate
            flipped_pivot_x = surface.get_width() - pivot_x
            pivots_left.append((flipped_pivot_x, pivot_y))
            
            # Convert frame duration from milliseconds to seconds
            durations.append(frame.duration / 1000.0)
            
        # Store animation data in standardized format
        self.animations[state_name] = {
            'surfaces_right': right_surfaces,
            'surfaces_left': left_surfaces,
            'pivots_right': pivots_right,
            'pivots_left': pivots_left,
            'durations': durations,
            'direction': animation.direction,
            'frame_count': len(right_surfaces)
        }
        
        print(f"Loaded animation '{state_name}' with {len(right_surfaces)} frames")
        return True
        
    def _create_fallback_animations(self):
        """
        Create basic placeholder animations when Aseprite data cannot be loaded.
        
        This ensures the game doesn't crash if animation files are missing.
        Subclasses can override this to provide entity-specific fallbacks.
        """
        # Create a simple colored rectangle as placeholder
        placeholder_size = (60 * self.scale, 60 * self.scale)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill((200, 80, 80))  # Red placeholder
        
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        # Default pivot point (bottom center)
        pivot_x = 30 * self.scale
        pivot_y = 59 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.1],  # 100ms default
            'direction': 'forward',
            'frame_count': 1
        }
        
        # Create basic fallback animations
        basic_animations = ['idle', 'walk', 'jump', 'fall']
        for anim_name in basic_animations:
            self.animations[anim_name] = placeholder_data.copy()
            
        print(f"Created {len(basic_animations)} fallback animations")
        
    def get_animation(self, name: str) -> Optional[Dict]:
        """
        Get animation data by name.
        
        Args:
            name: Animation state name
            
        Returns:
            Dictionary containing animation data or None if not found
        """
        return self.animations.get(name)
        
    def get_frame_surface(self, animation_name: str, frame_index: int, facing_right: bool = True) -> Optional[pygame.Surface]:
        """
        Get a specific frame surface from an animation.
        
        Args:
            animation_name: Name of the animation
            frame_index: Index of the frame (0-based)
            facing_right: True for right-facing, False for left-facing
            
        Returns:
            pygame.Surface or None if frame not found
        """
        anim_data = self.get_animation(animation_name)
        if not anim_data:
            return None
            
        surfaces = anim_data['surfaces_right'] if facing_right else anim_data['surfaces_left']
        
        if frame_index < 0 or frame_index >= len(surfaces):
            return None
            
        return surfaces[frame_index]
        
    def get_frame_pivot(self, animation_name: str, frame_index: int, facing_right: bool = True) -> Optional[Tuple[int, int]]:
        """
        Get the pivot point for a specific frame.
        
        Args:
            animation_name: Name of the animation
            frame_index: Index of the frame (0-based)
            facing_right: True for right-facing, False for left-facing
            
        Returns:
            Tuple of (x, y) pivot coordinates or None if frame not found
        """
        anim_data = self.get_animation(animation_name)
        if not anim_data:
            return None
            
        pivots = anim_data['pivots_right'] if facing_right else anim_data['pivots_left']
        
        if frame_index < 0 or frame_index >= len(pivots):
            return None
            
        return pivots[frame_index]
        
    def get_frame_duration(self, animation_name: str, frame_index: int) -> float:
        """
        Get the duration of a specific frame in seconds.
        
        Args:
            animation_name: Name of the animation
            frame_index: Index of the frame (0-based)
            
        Returns:
            Frame duration in seconds (default: 0.1)
        """
        anim_data = self.get_animation(animation_name)
        if not anim_data or frame_index < 0 or frame_index >= len(anim_data['durations']):
            return 0.1  # Default 100ms
            
        return anim_data['durations'][frame_index]
        
    def get_animation_direction(self, animation_name: str) -> str:
        """
        Get the playback direction for an animation.
        
        Args:
            animation_name: Name of the animation
            
        Returns:
            Animation direction ('forward', 'reverse', 'pingpong')
        """
        anim_data = self.get_animation(animation_name)
        if not anim_data:
            return 'forward'
            
        return anim_data['direction']
        
    def get_frame_count(self, animation_name: str) -> int:
        """
        Get the total number of frames in an animation.
        
        Args:
            animation_name: Name of the animation
            
        Returns:
            Number of frames (0 if animation not found)
        """
        anim_data = self.get_animation(animation_name)
        if not anim_data:
            return 0
            
        return anim_data['frame_count']
        
    def has_animation(self, animation_name: str) -> bool:
        """
        Check if an animation exists.
        
        Args:
            animation_name: Name of the animation to check
            
        Returns:
            True if animation exists, False otherwise
        """
        return animation_name in self.animations
        
    def list_animations(self) -> List[str]:
        """
        Get a list of all available animation names.
        
        Returns:
            List of animation names
        """
        return list(self.animations.keys())
        
    def get_legacy_format(self, name: str) -> Tuple[List, List, List, List]:
        """
        Get animation data in legacy format for backward compatibility.
        
        This method maintains compatibility with existing code that expects
        the old tuple format: (surfaces_right, surfaces_left, pivots_right, pivots_left)
        
        Args:
            name: Animation name
            
        Returns:
            Tuple of (surfaces_right, surfaces_left, pivots_right, pivots_left)
        """
        anim_data = self.get_animation(name)
        if not anim_data:
            return ([], [], [], [])
            
        return (
            anim_data['surfaces_right'],
            anim_data['surfaces_left'],
            anim_data['pivots_right'],
            anim_data['pivots_left']
        )