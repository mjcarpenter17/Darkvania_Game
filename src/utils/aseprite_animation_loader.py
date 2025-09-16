"""Aseprite-based animation loader for the player character."""
import os
import pygame
from typing import Dict, List, Tuple, Optional

from .aseprite_loader import AsepriteLoader, AsepriteAnimation, AsepriteFrame


class AsepriteAnimationLoader:
    """Manages loading of character animations from Aseprite data."""
    
    def __init__(self, json_path: str, scale: int = 2):
        self.scale = scale
        self.aseprite_loader = AsepriteLoader(json_path, scale=scale)
        self.animations = {}
        self.pivot_point = (0, 0)
        
    def load_all_animations(self, animation_list=None) -> bool:
        """Load all character animations from Aseprite data."""
        if not self.aseprite_loader.load():
            print("Failed to load Aseprite data, creating placeholder animations")
            self._create_placeholder_animations()
            return False
            
        # Get pivot point
        self.pivot_point = self.aseprite_loader.get_scaled_pivot()
        print(f"Using pivot point: {self.pivot_point}")
        
        # Load specific animations - use provided list or default player animations
        if animation_list is None:
            # Default player animations
            self._load_animation('idle', 'Idle')
            self._load_animation('walk', 'Walk') 
            self._load_animation('jump', 'Jump')
            self._load_animation('trans', 'trans')
            self._load_animation('fall', 'Fall')
            self._load_animation('dash', 'Dash')
            self._load_animation('attack1', 'Slash 1')
            self._load_animation('attack2', 'Slash 2')
            # Special animations for health system
            self._load_animation('spawn', 'Appear Tele')
            self._load_animation('hit', 'Hit')
            self._load_animation('death', 'death')
            # Movement abilities
            self._load_animation('ledge_grab', 'Ledge Grab')
            # Wall mechanics
            self._load_animation('wall_hold', 'Wall hold')
            self._load_animation('wall_transition', 'Wall Transition')
            self._load_animation('wall_slide', 'Wall Slide')
            self._load_animation('wall_slide_stop', 'Wall slide Stop')
            # Combat abilities
            self._load_animation('roll', 'Roll')
        else:
            # Custom animation list (for enemies, etc.)
            for state_name, aseprite_name in animation_list.items():
                self._load_animation(state_name, aseprite_name)
        
        # Create fallbacks for missing animations
        self._ensure_all_animations_exist()
        
        return True
        
    def _load_animation(self, key: str, aseprite_name: str):
        """Load a specific animation from Aseprite data."""
        animation = self.aseprite_loader.get_animation(aseprite_name)
        if not animation:
            print(f"Warning: Animation '{aseprite_name}' not found in Aseprite data")
            return
            
        # Convert to the format expected by the player class
        right_surfaces = []
        left_surfaces = []
        piv_right = []
        piv_left = []
        durations = []
        
        for frame in animation.frames:
            # Get frame surface
            surface = self.aseprite_loader.get_frame_surface(frame)
            
            # Create flipped version
            flipped_surface = pygame.transform.flip(surface, True, False)
            
            right_surfaces.append(surface)
            left_surfaces.append(flipped_surface)
            
            # Calculate pivot points relative to frame
            # Use the global pivot point from slice data
            pivot_x, pivot_y = self.pivot_point
            
            # For right-facing sprite, pivot is as-is
            piv_right.append((pivot_x, pivot_y))
            
            # For left-facing sprite, flip the X coordinate
            flipped_pivot_x = surface.get_width() - pivot_x
            piv_left.append((flipped_pivot_x, pivot_y))
            
            # Store frame duration (convert from ms to seconds)
            durations.append(frame.duration / 1000.0)
            
        self.animations[key] = {
            'surfaces_right': right_surfaces,
            'surfaces_left': left_surfaces,
            'pivots_right': piv_right,
            'pivots_left': piv_left,
            'durations': durations,
            'direction': animation.direction
        }
        
        print(f"Loaded animation '{key}' with {len(right_surfaces)} frames")
        
    def _create_placeholder_animations(self):
        """Create placeholder animations when Aseprite data fails to load."""
        placeholder = pygame.Surface((60 * self.scale, 60 * self.scale), pygame.SRCALPHA)
        placeholder.fill((200, 80, 80))
        
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        pivot_x = 30 * self.scale
        pivot_y = 59 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.1],  # 100ms default
            'direction': 'forward'
        }
        
        for anim_name in ['idle', 'walk', 'jump', 'trans', 'fall']:
            self.animations[anim_name] = placeholder_data.copy()
            
    def _ensure_all_animations_exist(self):
        """Ensure all required animations exist, using fallbacks if necessary."""
        required_animations = ['idle', 'walk', 'jump', 'trans', 'fall', 'spawn', 'hit', 'death']
        
        # Use walk as primary fallback, then idle
        primary_fallback = self.animations.get('walk') or self.animations.get('idle')
        
        for anim_name in required_animations:
            if anim_name not in self.animations and primary_fallback:
                self.animations[anim_name] = primary_fallback
                print(f"Using fallback for animation '{anim_name}'")
            elif anim_name not in self.animations:
                print(f"Warning: Animation '{anim_name}' not found and no fallback available")
                
    def get_animation(self, name: str) -> Optional[Dict]:
        """Get animation data by name."""
        return self.animations.get(name)
        
    def get_legacy_format(self, name: str) -> Tuple[List, List, List, List]:
        """Get animation in legacy format for backward compatibility."""
        anim_data = self.get_animation(name)
        if not anim_data:
            # Return empty lists if animation not found
            return ([], [], [], [])
            
        return (
            anim_data['surfaces_right'],
            anim_data['surfaces_left'], 
            anim_data['pivots_right'],
            anim_data['pivots_left']
        )
        
    def get_frame_duration(self, animation_name: str, frame_index: int) -> float:
        """Get the duration of a specific frame in seconds."""
        anim_data = self.get_animation(animation_name)
        if not anim_data or frame_index >= len(anim_data['durations']):
            return 0.1  # Default 100ms
            
        return anim_data['durations'][frame_index]
        
    def get_animation_direction(self, animation_name: str) -> str:
        """Get the playback direction for an animation."""
        anim_data = self.get_animation(animation_name)
        if not anim_data:
            return 'forward'
            
        return anim_data['direction']