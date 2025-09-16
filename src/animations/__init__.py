"""
Animation system for Darkvania Game.

This module provides a modular animation system with clear separation between
different entity types (Player, Enemy, Interactables, NPCs, etc.).

Architecture:
- BaseAnimationLoader: Core animation loading functionality
- EntityAnimationLoader: Base class for entity-specific loaders
- PlayerAnimationLoader: Player-specific animation mappings and logic
- EnemyAnimationLoader: Enemy-specific animation mappings and logic
- InteractableAnimationLoader: Interactable object animation mappings
- NPCAnimationLoader: NPC-specific animation mappings

Each entity type has its own dedicated loader that inherits from the base
classes but defines its own animation mappings and entity-specific behavior.

Usage Examples:
    # Player animations
    from src.animations import PlayerAnimationLoader
    player_loader = PlayerAnimationLoader("assets/player.json", scale=2)
    player_loader.load_player_animations()
    
    # Enemy animations
    from src.animations.enemy_animation_loader import create_enemy_loader
    assassin_loader = create_enemy_loader("assassin", "assets/assassin.json", scale=2)
    assassin_loader.load_assassin_animations()
    
    # Interactable animations
    from src.animations.interactable_animation_loader import create_interactable_loader
    chest_loader = create_interactable_loader("chest", "assets/chest.json", scale=2)
    chest_loader.load_chest_animations()
"""

from .base_animation_loader import BaseAnimationLoader
from .entity_animation_loader import EntityAnimationLoader
from .player_animation_loader import PlayerAnimationLoader
from .enemy_animation_loader import (
    EnemyAnimationLoader, 
    AssassinAnimationLoader, 
    ArcherAnimationLoader, 
    WaspAnimationLoader,
    create_enemy_loader
)
from .interactable_animation_loader import (
    InteractableAnimationLoader,
    ChestAnimationLoader,
    DoorAnimationLoader, 
    CollectibleAnimationLoader,
    SwitchAnimationLoader,
    create_interactable_loader
)
from .npc_animation_loader import (
    NPCAnimationLoader,
    DialogueNPCLoader,
    ShopNPCLoader,
    QuestNPCLoader,
    AmbientNPCLoader,
    create_npc_loader
)

__all__ = [
    # Base classes
    'BaseAnimationLoader',
    'EntityAnimationLoader',
    
    # Player animations
    'PlayerAnimationLoader',
    
    # Enemy animations
    'EnemyAnimationLoader',
    'AssassinAnimationLoader', 
    'ArcherAnimationLoader',
    'WaspAnimationLoader',
    'create_enemy_loader',
    
    # Interactable animations
    'InteractableAnimationLoader',
    'ChestAnimationLoader',
    'DoorAnimationLoader',
    'CollectibleAnimationLoader',
    'SwitchAnimationLoader',
    'create_interactable_loader',
    
    # NPC animations
    'NPCAnimationLoader',
    'DialogueNPCLoader',
    'ShopNPCLoader',
    'QuestNPCLoader',
    'AmbientNPCLoader',
    'create_npc_loader'
]
