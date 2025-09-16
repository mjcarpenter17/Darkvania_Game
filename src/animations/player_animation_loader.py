"""Player-specific animation loader.

This module provides the animation loader specifically designed for the player character.
It defines all player animations, their mappings, fallback chains, and player-specific
animation behavior.

Player Animation Categories:
1. Basic Movement: idle, walk, jump, fall, trans
2. Combat: attack1, attack2, roll, fall_attack, slam_attack
3. Health States: spawn, hit, death
4. Advanced Movement: ledge_grab, wall_hold, wall_transition, wall_slide, wall_slide_stop
5. Special Abilities: dash

Each animation is mapped to its corresponding Aseprite animation name and includes
appropriate fallback chains for robustness.
"""

from typing import Dict
import pygame
from .entity_animation_loader import EntityAnimationLoader


class PlayerAnimationLoader(EntityAnimationLoader):
    """
    Animation loader specifically for the player character.
    
    Manages all player animations including movement, combat, health states,
    and advanced abilities. Provides player-specific fallback chains and
    validation to ensure the player always has functional animations.
    
    Features:
    - Complete player animation set (25+ animations)
    - Combat ability animations (attacks, roll, slam)
    - Advanced movement animations (wall climbing, ledge grab)
    - Health state animations (spawn, hit, death)
    - Robust fallback chains for missing animations
    """
    
    # Player animation mappings from game states to Aseprite animation names
    PLAYER_ANIMATIONS = {
        # Basic Movement
        'idle': 'Idle',
        'walk': 'Walk',
        'jump': 'Jump',
        'trans': 'trans',  # Transition animation
        'fall': 'Fall',
        'dash': 'Dash',
        
        # Combat Attacks
        'attack1': 'Slash 1',
        'attack2': 'Slash 2',
        
        # Health States
        'spawn': 'Appear Tele',
        'hit': 'Hit',
        'death': 'death',
        
        # Advanced Movement - Ledge System
        'ledge_grab': 'Ledge Grab',
        
        # Advanced Movement - Wall System
        'wall_hold': 'Wall hold',
        'wall_transition': 'Wall Transition',
        'wall_slide': 'Wall Slide',
        'wall_slide_stop': 'Wall slide Stop',
        
        # Combat Abilities
        'roll': 'Roll',
        'fall_attack': 'Fall Attack',
        'slam_attack': 'Slam',
    }
    
    # Required animations that the player must have to function properly
    REQUIRED_ANIMATIONS = [
        'idle', 'walk', 'jump', 'fall',  # Basic movement
        'attack1', 'spawn', 'hit', 'death'  # Essential states
    ]
    
    # Fallback chains for missing animations
    FALLBACK_CHAINS = {
        # Movement fallbacks
        'walk': ['idle'],
        'jump': ['idle'],
        'trans': ['walk', 'idle'],
        'fall': ['jump', 'idle'],
        'dash': ['walk', 'idle'],
        
        # Combat fallbacks
        'attack2': ['attack1'],
        'roll': ['dash', 'walk'],
        'fall_attack': ['attack1', 'fall'],
        'slam_attack': ['attack1'],
        
        # Health state fallbacks
        'hit': ['idle'],
        'death': ['hit', 'idle'],
        'spawn': ['idle'],
        
        # Advanced movement fallbacks
        'ledge_grab': ['idle'],
        'wall_hold': ['idle'],
        'wall_transition': ['wall_hold', 'idle'],
        'wall_slide': ['wall_transition', 'fall', 'idle'],
        'wall_slide_stop': ['wall_slide', 'idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """
        Initialize player animation loader.
        
        Args:
            json_path: Path to player Aseprite JSON file
            scale: Scale factor for rendering
        """
        super().__init__(json_path, scale, entity_type="Player")
        
        # Set up player-specific configuration
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        
        # Set up fallback chains
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_player_animations(self) -> bool:
        """
        Load all player animations.
        
        Returns:
            bool: True if player animations were loaded successfully
        """
        success = self.load_animations(self.PLAYER_ANIMATIONS)
        
        if success:
            print(f"Player animation system loaded successfully:")
            print(f"  - {len(self.animations)} animations loaded")
            print(f"  - Pivot point: {self.pivot_point}")
            print(f"  - Scale: {self.scale}x")
            
            # Validate that we have all required animations
            if self.validate_animations():
                print("  - All required animations validated ✓")
            else:
                print("  - Some required animations missing ⚠")
                
        return success
        
    def _create_fallback_animations(self):
        """
        Create player-specific fallback animations.
        
        Creates a basic player sprite placeholder when Aseprite data fails to load.
        """
        # Create player-specific placeholder (blue color for player)
        placeholder_size = (60 * self.scale, 60 * self.scale)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill((80, 150, 255))  # Blue color for player
        
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        # Player-specific pivot point (bottom center)
        pivot_x = 30 * self.scale
        pivot_y = 59 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.1],
            'direction': 'forward',
            'frame_count': 1
        }
        
        # Create all required player animations as fallbacks
        for anim_name in self.REQUIRED_ANIMATIONS:
            self.animations[anim_name] = placeholder_data.copy()
            
        print(f"Created {len(self.REQUIRED_ANIMATIONS)} player fallback animations")
        
    def get_combat_animations(self) -> Dict[str, Dict]:
        """
        Get all combat-related animations.
        
        Returns:
            Dictionary of combat animations
        """
        combat_anims = ['attack1', 'attack2', 'roll', 'fall_attack', 'slam_attack']
        return {name: self.get_animation(name) for name in combat_anims if self.has_animation(name)}
        
    def get_movement_animations(self) -> Dict[str, Dict]:
        """
        Get all movement-related animations.
        
        Returns:
            Dictionary of movement animations
        """
        movement_anims = ['idle', 'walk', 'jump', 'fall', 'trans', 'dash']
        return {name: self.get_animation(name) for name in movement_anims if self.has_animation(name)}
        
    def get_wall_animations(self) -> Dict[str, Dict]:
        """
        Get all wall climbing related animations.
        
        Returns:
            Dictionary of wall animations
        """
        wall_anims = ['wall_hold', 'wall_transition', 'wall_slide', 'wall_slide_stop', 'ledge_grab']
        return {name: self.get_animation(name) for name in wall_anims if self.has_animation(name)}
        
    def get_health_animations(self) -> Dict[str, Dict]:
        """
        Get all health state related animations.
        
        Returns:
            Dictionary of health state animations
        """
        health_anims = ['spawn', 'hit', 'death']
        return {name: self.get_animation(name) for name in health_anims if self.has_animation(name)}
        
    def has_combat_abilities(self) -> bool:
        """
        Check if advanced combat abilities are available.
        
        Returns:
            bool: True if roll, fall_attack, and slam_attack are available
        """
        return all(self.has_animation(anim) for anim in ['roll', 'fall_attack', 'slam_attack'])
        
    def has_wall_abilities(self) -> bool:
        """
        Check if wall climbing abilities are available.
        
        Returns:
            bool: True if wall climbing animations are available
        """
        return all(self.has_animation(anim) for anim in ['wall_hold', 'wall_slide', 'ledge_grab'])
        
    def get_player_info(self) -> Dict[str, any]:
        """
        Get comprehensive player animation system information.
        
        Returns:
            Dictionary containing detailed player animation info
        """
        base_info = self.get_entity_info()
        
        player_info = {
            **base_info,
            'combat_abilities': self.has_combat_abilities(),
            'wall_abilities': self.has_wall_abilities(),
            'combat_animations': list(self.get_combat_animations().keys()),
            'movement_animations': list(self.get_movement_animations().keys()),
            'wall_animations': list(self.get_wall_animations().keys()),
            'health_animations': list(self.get_health_animations().keys()),
        }
        
        return player_info