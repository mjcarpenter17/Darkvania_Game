"""Entity-specific animation loader base class.

This module provides the base class for all entity-specific animation loaders.
It extends BaseAnimationLoader with entity-specific functionality such as:

1. Animation state management
2. Entity-specific fallback mechanisms
3. Animation validation
4. State transition support

Entity loaders (Player, Enemy, etc.) inherit from this class.
"""

from typing import Dict, List, Set, Optional
from .base_animation_loader import BaseAnimationLoader


class EntityAnimationLoader(BaseAnimationLoader):
    """
    Base class for entity-specific animation loaders.
    
    Provides common functionality for all game entities (Player, Enemy, Interactables, NPCs).
    Entity-specific loaders inherit from this class and define their own animation
    mappings and required animations.
    
    Features:
    - Required animation validation
    - Fallback animation chains
    - Entity-specific error handling
    - Animation state management utilities
    """
    
    def __init__(self, json_path: str, scale: int = 2, entity_type: str = "generic"):
        """
        Initialize entity animation loader.
        
        Args:
            json_path: Path to the Aseprite JSON file
            scale: Scale factor for rendering
            entity_type: Type of entity (for logging and debugging)
        """
        super().__init__(json_path, scale)
        self.entity_type = entity_type
        self.required_animations: Set[str] = set()
        self.fallback_chains: Dict[str, List[str]] = {}
        
    def set_required_animations(self, required: List[str]):
        """
        Set the list of animations that this entity requires to function.
        
        Args:
            required: List of required animation names
        """
        self.required_animations = set(required)
        
    def set_fallback_chain(self, animation: str, fallbacks: List[str]):
        """
        Set a fallback chain for an animation.
        
        If the primary animation is not found, the loader will try each fallback
        in order until one is found.
        
        Args:
            animation: Primary animation name
            fallbacks: List of fallback animation names to try in order
        """
        self.fallback_chains[animation] = fallbacks
        
    def load_animations(self, animation_mappings: Dict[str, str]) -> bool:
        """
        Load animations based on a mapping from state names to Aseprite names.
        
        Args:
            animation_mappings: Dict mapping game state names to Aseprite animation names
                                e.g., {'idle': 'Idle', 'walk': 'Walk'}
        
        Returns:
            bool: True if all required animations were loaded successfully
        """
        if not self.load():
            return False
            
        success_count = 0
        total_count = len(animation_mappings)
        
        # Load each animation
        for state_name, aseprite_name in animation_mappings.items():
            if self._load_animation(state_name, aseprite_name):
                success_count += 1
            else:
                print(f"{self.entity_type}: Failed to load animation '{state_name}' -> '{aseprite_name}'")
                
        # Ensure required animations exist using fallback chains
        self._ensure_required_animations()
        
        print(f"{self.entity_type}: Loaded {success_count}/{total_count} animations")
        return success_count > 0  # Success if at least one animation loaded
        
    def _ensure_required_animations(self):
        """
        Ensure all required animations exist, using fallback chains if necessary.
        """
        for required_anim in self.required_animations:
            if not self.has_animation(required_anim):
                self._try_fallback_chain(required_anim)
                
    def _try_fallback_chain(self, animation_name: str):
        """
        Try to create an animation using its fallback chain.
        
        Args:
            animation_name: Name of the animation to create
        """
        fallbacks = self.fallback_chains.get(animation_name, [])
        
        for fallback in fallbacks:
            if self.has_animation(fallback):
                # Copy the fallback animation
                self.animations[animation_name] = self.animations[fallback].copy()
                print(f"{self.entity_type}: Using '{fallback}' as fallback for '{animation_name}'")
                return
                
        # If no fallbacks worked, try common fallbacks
        common_fallbacks = ['idle', 'walk', 'run']
        for common in common_fallbacks:
            if self.has_animation(common):
                self.animations[animation_name] = self.animations[common].copy()
                print(f"{self.entity_type}: Using '{common}' as common fallback for '{animation_name}'")
                return
                
        print(f"{self.entity_type}: Warning - No fallback found for required animation '{animation_name}'")
        
    def validate_animations(self) -> bool:
        """
        Validate that all required animations are present.
        
        Returns:
            bool: True if all required animations exist
        """
        missing = []
        for required in self.required_animations:
            if not self.has_animation(required):
                missing.append(required)
                
        if missing:
            print(f"{self.entity_type}: Missing required animations: {missing}")
            return False
            
        print(f"{self.entity_type}: All required animations present")
        return True
        
    def get_animation_states(self) -> List[str]:
        """
        Get all available animation states for this entity.
        
        Returns:
            List of animation state names
        """
        return list(self.animations.keys())
        
    def get_entity_info(self) -> Dict[str, any]:
        """
        Get information about this entity's animation system.
        
        Returns:
            Dictionary containing entity animation info
        """
        return {
            'entity_type': self.entity_type,
            'total_animations': len(self.animations),
            'required_animations': list(self.required_animations),
            'available_animations': self.get_animation_states(),
            'fallback_chains': self.fallback_chains.copy(),
            'pivot_point': self.pivot_point,
            'scale': self.scale,
            'loaded': self.loaded
        }