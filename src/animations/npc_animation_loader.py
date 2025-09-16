"""NPC (Non-Player Character) animation loader.

This module provides animation loaders for NPCs in the game world.
NPCs are friendly or neutral characters that the player can interact with
for dialogue, quests, shops, or story elements.

NPC Types:
1. Dialogue NPCs: Characters with conversation interactions
2. Shop NPCs: Merchants and vendors
3. Quest NPCs: Characters that give quests or story information  
4. Ambient NPCs: Background characters for atmosphere
5. Guide NPCs: Tutorial or help characters

Each NPC type has specific animation patterns for their role.
"""

from typing import Dict
import pygame
from .entity_animation_loader import EntityAnimationLoader


class NPCAnimationLoader(EntityAnimationLoader):
    """
    Base animation loader for all NPC types.
    
    Provides common NPC animation functionality including:
    - Idle/ambient animations
    - Dialogue state animations
    - Interaction feedback animations
    - Emotion/expression animations
    
    Features:
    - Social interaction animation patterns
    - Emotion-based animation sets
    - Conversation state management
    - Ambient behavior animations
    """
    
    def __init__(self, json_path: str, scale: int = 2, npc_type: str = "generic"):
        """
        Initialize NPC animation loader.
        
        Args:
            json_path: Path to NPC Aseprite JSON file
            scale: Scale factor for rendering
            npc_type: Specific type of NPC
        """
        super().__init__(json_path, scale, entity_type=f"NPC-{npc_type}")
        self.npc_type = npc_type
        
    def _create_fallback_animations(self):
        """
        Create NPC-specific fallback animations.
        
        Creates friendly placeholder animations for when Aseprite data fails to load.
        """
        # Create NPC-specific placeholder (yellow color for friendly NPCs)
        placeholder_size = (50 * self.scale, 50 * self.scale)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill((255, 255, 80))  # Yellow color for NPCs
        
        flipped_placeholder = pygame.transform.flip(placeholder, True, False)
        
        # NPC pivot point (bottom center)
        pivot_x = 25 * self.scale
        pivot_y = 49 * self.scale
        
        placeholder_data = {
            'surfaces_right': [placeholder],
            'surfaces_left': [flipped_placeholder],
            'pivots_right': [(pivot_x, pivot_y)],
            'pivots_left': [(pivot_x, pivot_y)],
            'durations': [0.2],  # Moderate pace for NPCs
            'direction': 'forward',
            'frame_count': 1
        }
        
        # Create basic NPC animations
        basic_npc_anims = ['idle', 'talk', 'wave', 'nod']
        for anim_name in basic_npc_anims:
            self.animations[anim_name] = placeholder_data.copy()
            
        print(f"Created {len(basic_npc_anims)} NPC fallback animations")


class DialogueNPCLoader(NPCAnimationLoader):
    """
    Animation loader for dialogue NPCs.
    
    Dialogue NPCs are characters that the player can talk to for story,
    information, or casual conversation.
    
    Animation States:
    - idle: Default standing/waiting animation
    - talk: Speaking animation during dialogue
    - listen: Listening pose when player is talking
    - greet: Greeting gesture when player approaches
    - goodbye: Farewell gesture when dialogue ends
    - nod: Agreement or acknowledgment
    - shake_head: Disagreement or refusal
    - think: Contemplative pose
    """
    
    DIALOGUE_ANIMATIONS = {
        'idle': 'Idle',
        'talk': 'Talk',
        'listen': 'Listen',
        'greet': 'Greet',
        'goodbye': 'Goodbye',
        'nod': 'Nod',
        'shake_head': 'Shake Head',
        'think': 'Think',
        'wave': 'Wave',
    }
    
    REQUIRED_ANIMATIONS = ['idle', 'talk']
    
    FALLBACK_CHAINS = {
        'talk': ['idle'],
        'listen': ['idle'],
        'greet': ['wave', 'idle'],
        'goodbye': ['wave', 'idle'],
        'nod': ['idle'],
        'shake_head': ['nod', 'idle'],
        'think': ['idle'],
        'wave': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize dialogue NPC animation loader."""
        super().__init__(json_path, scale, npc_type="Dialogue")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_dialogue_animations(self) -> bool:
        """Load all dialogue NPC animations."""
        return self.load_animations(self.DIALOGUE_ANIMATIONS)
        
    def has_expression_animations(self) -> bool:
        """Check if expression animations are available."""
        return self.has_animation('nod') and self.has_animation('shake_head')
        
    def get_conversation_animations(self) -> Dict[str, Dict]:
        """Get animations used during conversations."""
        conv_anims = ['talk', 'listen', 'nod', 'shake_head', 'think']
        return {name: self.get_animation(name) for name in conv_anims if self.has_animation(name)}


class ShopNPCLoader(NPCAnimationLoader):
    """
    Animation loader for shop/merchant NPCs.
    
    Shop NPCs are vendors that sell items to the player.
    They have transaction-based animations and item handling poses.
    
    Animation States:
    - idle: Default shopkeeper pose
    - greet: Welcome gesture for customers
    - show_item: Displaying merchandise
    - count_money: Handling payment
    - package: Wrapping/preparing items
    - wave: Goodbye gesture
    - busy: Working on shop tasks
    """
    
    SHOP_ANIMATIONS = {
        'idle': 'Idle',
        'greet': 'Greet',
        'show_item': 'Show Item',
        'count_money': 'Count Money',
        'package': 'Package',
        'wave': 'Wave',
        'busy': 'Busy',
        'talk': 'Talk',
    }
    
    REQUIRED_ANIMATIONS = ['idle', 'greet']
    
    FALLBACK_CHAINS = {
        'greet': ['wave', 'idle'],
        'show_item': ['idle'],
        'count_money': ['busy', 'idle'],
        'package': ['busy', 'idle'],
        'wave': ['idle'],
        'busy': ['idle'],
        'talk': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize shop NPC animation loader."""
        super().__init__(json_path, scale, npc_type="Shop")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_shop_animations(self) -> bool:
        """Load all shop NPC animations."""
        return self.load_animations(self.SHOP_ANIMATIONS)
        
    def has_transaction_animations(self) -> bool:
        """Check if transaction animations are available."""
        return self.has_animation('show_item') and self.has_animation('count_money')


class QuestNPCLoader(NPCAnimationLoader):
    """
    Animation loader for quest-giving NPCs.
    
    Quest NPCs provide missions, objectives, and story progression.
    They have dramatic and expressive animations to convey importance.
    
    Animation States:
    - idle: Default waiting pose
    - urgent: Expressing urgency or importance
    - point: Pointing to locations or directions
    - explain: Detailed explanation gesture
    - worry: Concerned or worried expression
    - relief: Satisfied when quest is completed
    - thank: Gratitude gesture for quest completion
    """
    
    QUEST_ANIMATIONS = {
        'idle': 'Idle',
        'urgent': 'Urgent',
        'point': 'Point',
        'explain': 'Explain',
        'worry': 'Worry',
        'relief': 'Relief',
        'thank': 'Thank',
        'talk': 'Talk',
        'greet': 'Greet',
    }
    
    REQUIRED_ANIMATIONS = ['idle', 'talk']
    
    FALLBACK_CHAINS = {
        'urgent': ['talk', 'idle'],
        'point': ['idle'],
        'explain': ['talk', 'idle'],
        'worry': ['idle'],
        'relief': ['idle'],
        'thank': ['greet', 'idle'],
        'talk': ['idle'],
        'greet': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize quest NPC animation loader."""
        super().__init__(json_path, scale, npc_type="Quest")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_quest_animations(self) -> bool:
        """Load all quest NPC animations."""
        return self.load_animations(self.QUEST_ANIMATIONS)
        
    def has_emotional_range(self) -> bool:
        """Check if emotional animations are available."""
        return self.has_animation('worry') and self.has_animation('relief')


class AmbientNPCLoader(NPCAnimationLoader):
    """
    Animation loader for ambient/background NPCs.
    
    Ambient NPCs provide atmosphere and life to the game world.
    They have simple, repeating animations and don't directly interact with the player.
    
    Animation States:
    - idle: Default pose
    - work: Performing background tasks
    - walk: Moving around their area
    - sit: Sitting or resting
    - sleep: Sleeping or inactive
    - read: Reading or studying
    """
    
    AMBIENT_ANIMATIONS = {
        'idle': 'Idle',
        'work': 'Work',
        'walk': 'Walk',
        'sit': 'Sit',
        'sleep': 'Sleep',
        'read': 'Read',
        'look_around': 'Look Around',
    }
    
    REQUIRED_ANIMATIONS = ['idle']
    
    FALLBACK_CHAINS = {
        'work': ['idle'],
        'walk': ['idle'],
        'sit': ['idle'],
        'sleep': ['idle'],
        'read': ['sit', 'idle'],
        'look_around': ['idle'],
    }
    
    def __init__(self, json_path: str, scale: int = 2):
        """Initialize ambient NPC animation loader."""
        super().__init__(json_path, scale, npc_type="Ambient")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        for anim, fallbacks in self.FALLBACK_CHAINS.items():
            self.set_fallback_chain(anim, fallbacks)
            
    def load_ambient_animations(self) -> bool:
        """Load all ambient NPC animations."""
        return self.load_animations(self.AMBIENT_ANIMATIONS)
        
    def get_background_animations(self) -> Dict[str, Dict]:
        """Get animations suitable for background behavior."""
        bg_anims = ['idle', 'work', 'sit', 'read', 'look_around']
        return {name: self.get_animation(name) for name in bg_anims if self.has_animation(name)}


# Factory function for creating appropriate NPC animation loaders
def create_npc_loader(npc_type: str, json_path: str, scale: int = 2) -> NPCAnimationLoader:
    """
    Factory function to create the appropriate NPC animation loader.
    
    Args:
        npc_type: Type of NPC ('dialogue', 'shop', 'quest', 'ambient')
        json_path: Path to the NPC's Aseprite JSON file
        scale: Scale factor for rendering
        
    Returns:
        Appropriate NPC animation loader instance
    """
    npc_type = npc_type.lower()
    
    if npc_type in ['dialogue', 'talk', 'conversation']:
        return DialogueNPCLoader(json_path, scale)
    elif npc_type in ['shop', 'merchant', 'vendor']:
        return ShopNPCLoader(json_path, scale)
    elif npc_type in ['quest', 'mission', 'story']:
        return QuestNPCLoader(json_path, scale)
    elif npc_type in ['ambient', 'background', 'atmosphere']:
        return AmbientNPCLoader(json_path, scale)
    else:
        print(f"Warning: Unknown NPC type '{npc_type}', using generic NPC loader")
        return NPCAnimationLoader(json_path, scale, npc_type)