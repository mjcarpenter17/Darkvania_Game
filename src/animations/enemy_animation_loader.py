"""Enemy-specific animation loader.

This module provides animation loaders for different enemy types in the game.
Each enemy type has its own animation mappings and behaviors while sharing
common enemy functionality.

Enemy Types:
1. AssassinEnemy: Stealth-based melee enemy with multiple attack patterns
2. ArcherEnemy: Ranged enemy with bow attacks
3. WaspEnemy: Flying enemy with aerial movement patterns

Each enemy type defines its own animation mappings and required animations
while inheriting common enemy behavior from the base enemy loader.
"""

from typing import Dict
import pygame
from .entity_animation_loader import EntityAnimationLoader


class EnemyAnimationLoader(EntityAnimationLoader):
    """
    Base animation loader for all enemy types.
    
    Provides common enemy animation functionality that all enemy types inherit.
    Specific enemy types (Assassin, Archer, Wasp) extend this class with their
    own animation mappings and behaviors.
    
    Features:
    - Common enemy animation patterns
    - Enemy-specific fallback mechanisms  
    - AI state animation support
    - Enemy health state animations
    """
    
    def __init__(self, json_path: str, scale: int = 2, enemy_type: str = "generic"):
        """
        Initialize enemy animation loader.
        
        Args:
            json_path: Path to enemy Aseprite JSON file
            scale: Scale factor for rendering
            enemy_type: Specific type of enemy
        """
        super().__init__(json_path, scale, entity_type=f"Enemy-{enemy_type}")
        self.enemy_type = enemy_type
        
    def _create_fallback_animations(self):
        """
        Create enemy-specific fallback animations.
        
        Creates basic enemy sprite placeholder when Aseprite data fails to load.
        """
        # Create enemy-specific placeholder (red color for enemies)
        placeholder_size = (40 * self.scale, 40 * self.scale)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill((255, 80, 80))  # Red color for enemies
        
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        # Enemy-specific pivot point (bottom center)
        pivot_x = 20 * self.scale
        pivot_y = 39 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.15],  # Slightly slower for enemies
            'direction': 'forward',
            'frame_count': 1
        }
        
        # Create basic enemy animations
        basic_enemy_anims = ['idle', 'run', 'attack1', 'hit', 'death']
        for anim_name in basic_enemy_anims:
            self.animations[anim_name] = placeholder_data.copy()
            
        print(f"Created {len(basic_enemy_anims)} enemy fallback animations")


class AssassinAnimationLoader(EnemyAnimationLoader):
    """
    Animation loader for Assassin enemy type.
    
    The Assassin is a melee enemy with stealth capabilities and multiple attack patterns.
    It has complex AI behavior with patrol, idle, attack, and death states.
    
    Animation Categories:
    - Movement: idle, run, jump, fall
    - Combat: attack1, attack2
    - Health: hit, death
    - Special: spawn (if available)
    """
    
    # Assassin animation mappings
    ASSASSIN_ANIMATIONS = {
        'idle': 'idle',
        'run': 'run',
        'jump': 'jump',
        'fall': 'fall',
        'attack1': 'attack 1',
        'attack2': 'attack 2',
        'hit': 'hit',
        'death': 'death',
        # Optional animations
        'spawn': 'spawn',  # May not exist in all assassin sprites
    }
    
    # Required animations for Assassin to function
    REQUIRED_ANIMATIONS = [
        'idle', 'run', 'attack1', 'hit', 'death'
    ]
    
    # Fallback chains for Assassin animations
    FALLBACK_CHAINS = {
        'run': ['idle'],
        'jump': ['idle'],
        'fall': ['jump', 'idle'],
        'attack2': ['attack1'],
        'hit': ['idle'],
        'death': ['hit', 'idle'],
        'spawn': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """
        Initialize Assassin animation loader.
        
        Args:
            json_path: Path to Assassin Aseprite JSON file
            scale: Scale factor for rendering
        """
        super().__init__(json_path, scale, enemy_type="Assassin")
        
        # Set up Assassin-specific configuration
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        
        # Set up fallback chains
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_assassin_animations(self) -> bool:
        """
        Load all Assassin animations.
        
        Returns:
            bool: True if Assassin animations were loaded successfully
        """
        success = self.load_animations(self.ASSASSIN_ANIMATIONS)
        
        if success:
            print(f"Assassin animation system loaded successfully:")
            print(f"  - {len(self.animations)} animations loaded")
            print(f"  - Pivot point: {self.pivot_point}")
            print(f"  - Scale: {self.scale}x")
            
            # Validate required animations
            if self.validate_animations():
                print("  - All required Assassin animations validated ✓")
            else:
                print("  - Some required Assassin animations missing ⚠")
                
        return success
        
    def has_advanced_attacks(self) -> bool:
        """
        Check if advanced attack animations are available.
        
        Returns:
            bool: True if attack2 is available
        """
        return self.has_animation('attack2')
        
    def get_ai_animations(self) -> Dict[str, Dict]:
        """
        Get animations used by AI system.
        
        Returns:
            Dictionary of AI-relevant animations
        """
        ai_anims = ['idle', 'run', 'attack1', 'attack2', 'hit', 'death']
        return {name: self.get_animation(name) for name in ai_anims if self.has_animation(name)}


class ArcherAnimationLoader(EnemyAnimationLoader):
    """
    Animation loader for Archer enemy type.
    
    The Archer is a ranged enemy that shoots projectiles at the player.
    It maintains distance and has reload/aiming behaviors.
    
    Animation Categories:
    - Movement: idle, walk, retreat
    - Combat: aim, shoot, reload
    - Health: hit, death
    """
    
    # Archer animation mappings (placeholder - adjust based on actual sprite)
    ARCHER_ANIMATIONS = {
        'idle': 'Idle',
        'walk': 'Walk',
        'retreat': 'Retreat',  # Or fallback to walk
        'aim': 'Aim',
        'shoot': 'Shoot',
        'reload': 'Reload',
        'hit': 'Hit',
        'death': 'Death',
    }
    
    REQUIRED_ANIMATIONS = [
        'idle', 'walk', 'aim', 'shoot', 'hit', 'death'
    ]
    
    FALLBACK_CHAINS = {
        'walk': ['idle'],
        'retreat': ['walk', 'idle'],
        'shoot': ['aim', 'idle'],
        'reload': ['idle'],
        'hit': ['idle'],
        'death': ['hit', 'idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize Archer animation loader."""
        super().__init__(json_path, scale, enemy_type="Archer")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_archer_animations(self) -> bool:
        """Load all Archer animations."""
        return self.load_animations(self.ARCHER_ANIMATIONS)


class WaspAnimationLoader(EnemyAnimationLoader):
    """
    Animation loader for Wasp enemy type.
    
    The Wasp is a flying enemy with aerial movement patterns.
    It can hover, dive, and has unique flight-based animations.
    
    Animation Categories:
    - Flight: hover, fly, dive, rise
    - Combat: attack, sting
    - Health: hit, death
    """
    
    # Wasp animation mappings (placeholder - adjust based on actual sprite)
    WASP_ANIMATIONS = {
        'hover': 'Hover',
        'fly': 'Fly',
        'dive': 'Dive',
        'rise': 'Rise',
        'attack': 'Attack',
        'sting': 'Sting',
        'hit': 'Hit',
        'death': 'Death',
    }
    
    REQUIRED_ANIMATIONS = [
        'hover', 'fly', 'attack', 'hit', 'death'
    ]
    
    FALLBACK_CHAINS = {
        'fly': ['hover'],
        'dive': ['fly', 'hover'],
        'rise': ['fly', 'hover'],
        'sting': ['attack', 'hover'],
        'hit': ['hover'],
        'death': ['hit', 'hover'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize Wasp animation loader."""
        super().__init__(json_path, scale, enemy_type="Wasp")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_wasp_animations(self) -> bool:
        """Load all Wasp animations."""
        return self.load_animations(self.WASP_ANIMATIONS)
        
    def has_flight_abilities(self) -> bool:
        """Check if flight animations are available."""
        return all(self.has_animation(anim) for anim in ['hover', 'fly', 'dive'])


# Factory function for creating appropriate enemy animation loaders
def create_enemy_loader(enemy_type: str, json_path: str, scale: int = 2) -> EnemyAnimationLoader:
    """
    Factory function to create the appropriate enemy animation loader.
    
    Args:
        enemy_type: Type of enemy ('assassin', 'archer', 'wasp')
        json_path: Path to the enemy's Aseprite JSON file
        scale: Scale factor for rendering
        
    Returns:
        Appropriate enemy animation loader instance
    """
    enemy_type = enemy_type.lower()
    
    if enemy_type == 'assassin':
        return AssassinAnimationLoader(json_path, scale)
    elif enemy_type == 'archer':
        return ArcherAnimationLoader(json_path, scale)
    elif enemy_type == 'wasp':
        return WaspAnimationLoader(json_path, scale)
    else:
        print(f"Warning: Unknown enemy type '{enemy_type}', using generic enemy loader")
        return EnemyAnimationLoader(json_path, scale, enemy_type)