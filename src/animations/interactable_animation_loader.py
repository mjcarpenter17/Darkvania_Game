"""Interactable object animation loader.

This module provides animation loaders for interactive objects in the game world.
Interactables include chests, doors, switches, collectibles, and other objects
that the player can interact with.

Interactable Types:
1. Chests: Containers that open/close with rewards
2. Doors: Entrances that can be locked/unlocked
3. Collectibles: Items that can be picked up
4. Switches: Levers, buttons, and other activatable objects
5. Environmental: Background objects with ambient animations

Each interactable type has specific animation patterns and states.
"""

from typing import Dict
import pygame
from .entity_animation_loader import EntityAnimationLoader


class InteractableAnimationLoader(EntityAnimationLoader):
    """
    Base animation loader for all interactable objects.
    
    Provides common interactable animation functionality including:
    - Idle/ambient animations
    - Interaction feedback animations
    - State change animations (open/close, activate/deactivate)
    - Visual feedback for player proximity
    
    Features:
    - Simple animation patterns suitable for objects
    - State-based animation management
    - Minimal resource usage for background objects
    """
    
    def __init__(self, json_path: str, scale: int = 2, interactable_type: str = "generic"):
        """
        Initialize interactable animation loader.
        
        Args:
            json_path: Path to interactable Aseprite JSON file
            scale: Scale factor for rendering
            interactable_type: Specific type of interactable object
        """
        super().__init__(json_path, scale, entity_type=f"Interactable-{interactable_type}")
        self.interactable_type = interactable_type
        
    def _create_fallback_animations(self):
        """
        Create interactable-specific fallback animations.
        
        Creates simple placeholder animations for when Aseprite data fails to load.
        """
        # Create interactable-specific placeholder (green color for objects)
        placeholder_size = (32 * self.scale, 32 * self.scale)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill((80, 255, 80))  # Green color for interactables
        
        # Interactables typically don't need flipped versions, but include for consistency
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        # Interactable pivot point (bottom center)
        pivot_x = 16 * self.scale
        pivot_y = 31 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.5],  # Slow animations for ambient objects
            'direction': 'forward',
            'frame_count': 1
        }
        
        # Create basic interactable animations
        basic_anims = ['idle', 'highlight', 'activate']
        for anim_name in basic_anims:
            self.animations[anim_name] = placeholder_data.copy()
            
        print(f"Created {len(basic_anims)} interactable fallback animations")


class ChestAnimationLoader(InteractableAnimationLoader):
    """
    Animation loader for chest interactables.
    
    Chests are containers that can be opened by the player to reveal rewards.
    They have distinct open/closed states and transition animations.
    
    Animation States:
    - closed: Default state, chest is closed
    - opening: Transition animation from closed to open
    - open: Final state, chest contents visible
    - highlight: Visual feedback when player is nearby
    """
    
    CHEST_ANIMATIONS = {
        'idle': 'idle',         # Default closed state (1 frame)
        'opening': 'open',      # Opening transition animation (frames 1-34)  
        'used': 'used',         # Final opened state (1 frame)
        'closed': 'idle',       # Alias for idle state
        'open': 'used',         # Alias for used state after opening
    }
    
    REQUIRED_ANIMATIONS = ['idle', 'open', 'used']
    
    FALLBACK_CHAINS = {
        'opening': ['used', 'idle'],
        'closed': ['idle'],
        'open': ['used', 'idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize chest animation loader."""
        super().__init__(json_path, scale, interactable_type="Chest")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_chest_animations(self) -> bool:
        """Load all chest animations."""
        return self.load_animations(self.CHEST_ANIMATIONS)
        
    def has_opening_animation(self) -> bool:
        """Check if opening transition animation is available."""
        return self.has_animation('opening')
        
    def has_used_state(self) -> bool:
        """Check if used (opened) state animation is available."""
        return self.has_animation('used')


class DoorAnimationLoader(InteractableAnimationLoader):
    """
    Animation loader for door interactables.
    
    Doors can be locked/unlocked and opened/closed. They may require keys
    or other conditions to open.
    
    Animation States:
    - closed: Door is closed (default)
    - opening: Door opening transition  
    - open: Door is fully open
    - locked: Visual indication door is locked
    - unlocking: Transition from locked to unlocked
    """
    
    DOOR_ANIMATIONS = {
        'closed': 'Closed',
        'opening': 'Opening',
        'open': 'Open',
        'locked': 'Locked',
        'unlocking': 'Unlocking',
        'highlight': 'Highlight',
        'idle': 'Closed',
    }
    
    REQUIRED_ANIMATIONS = ['closed', 'open']
    
    FALLBACK_CHAINS = {
        'opening': ['open', 'closed'],
        'locked': ['closed'],
        'unlocking': ['opening', 'closed'],
        'highlight': ['closed'],
        'idle': ['closed'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize door animation loader."""
        super().__init__(json_path, scale, interactable_type="Door")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_door_animations(self) -> bool:
        """Load all door animations."""
        return self.load_animations(self.DOOR_ANIMATIONS)
        
    def has_lock_system(self) -> bool:
        """Check if lock/unlock animations are available."""
        return self.has_animation('locked') and self.has_animation('unlocking')


class CollectibleAnimationLoader(InteractableAnimationLoader):
    """
    Animation loader for collectible items.
    
    Collectibles are items that the player can pick up. They often have
    ambient animations to attract attention and collection effects.
    
    Animation States:
    - idle: Default floating/glowing animation
    - highlight: Enhanced effect when player is nearby
    - collect: Collection animation before disappearing
    - sparkle: Ambient particle-like effect
    """
    
    COLLECTIBLE_ANIMATIONS = {
        'idle': 'Idle',
        'highlight': 'Highlight',
        'collect': 'Collect',
        'sparkle': 'Sparkle',
        'glow': 'Glow',
    }
    
    REQUIRED_ANIMATIONS = ['idle']
    
    FALLBACK_CHAINS = {
        'highlight': ['idle'],
        'collect': ['highlight', 'idle'],
        'sparkle': ['idle'],
        'glow': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize collectible animation loader."""
        super().__init__(json_path, scale, interactable_type="Collectible")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_collectible_animations(self) -> bool:
        """Load all collectible animations."""
        return self.load_animations(self.COLLECTIBLE_ANIMATIONS)
        
    def has_collection_effect(self) -> bool:
        """Check if collection animation is available."""
        return self.has_animation('collect')


class SwitchAnimationLoader(InteractableAnimationLoader):
    """
    Animation loader for switch/lever interactables.
    
    Switches are objects that can be activated/deactivated to trigger
    events or unlock areas.
    
    Animation States:
    - off: Switch is in off position
    - activating: Transition to on position
    - on: Switch is in on position  
    - deactivating: Transition to off position
    """
    
    SWITCH_ANIMATIONS = {
        'off': 'Off',
        'activating': 'Activating',
        'on': 'On',
        'deactivating': 'Deactivating',
        'highlight': 'Highlight',
        'idle': 'Off',  # Default to off state
    }
    
    REQUIRED_ANIMATIONS = ['off', 'on']
    
    FALLBACK_CHAINS = {
        'activating': ['on', 'off'],
        'deactivating': ['off', 'on'],
        'highlight': ['off'],
        'idle': ['off'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize switch animation loader."""
        super().__init__(json_path, scale, interactable_type="Switch")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_switch_animations(self) -> bool:
        """Load all switch animations."""
        return self.load_animations(self.SWITCH_ANIMATIONS)
        
    def has_transitions(self) -> bool:
        """Check if transition animations are available."""
        return self.has_animation('activating') and self.has_animation('deactivating')


# Factory function for creating appropriate interactable animation loaders
def create_interactable_loader(interactable_type: str, json_path: str, scale: int = 2) -> InteractableAnimationLoader:
    """
    Factory function to create the appropriate interactable animation loader.
    
    Args:
        interactable_type: Type of interactable ('chest', 'door', 'collectible', 'switch')
        json_path: Path to the interactable's Aseprite JSON file
        scale: Scale factor for rendering
        
    Returns:
        Appropriate interactable animation loader instance
    """
    interactable_type = interactable_type.lower()
    
    if interactable_type == 'chest':
        return ChestAnimationLoader(json_path, scale)
    elif interactable_type == 'door':
        return DoorAnimationLoader(json_path, scale)
    elif interactable_type in ['collectible', 'item', 'pickup']:
        return CollectibleAnimationLoader(json_path, scale)
    elif interactable_type in ['switch', 'lever', 'button']:
        return SwitchAnimationLoader(json_path, scale)
    else:
        print(f"Warning: Unknown interactable type '{interactable_type}', using generic loader")
        return InteractableAnimationLoader(json_path, scale, interactable_type)