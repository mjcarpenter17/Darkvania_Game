"""
Interactable objects for the Darkvania game.

This module contains all interactive objects that the player can interact with,
including chests, doors, switches, and other world objects.

Classes:
    Interactable: Base class for all interactive objects
    Chest: Treasure chest that can be opened by the player
"""

import pygame
from typing import Optional, Tuple
from src.animations.interactable_animation_loader import ChestAnimationLoader


class Interactable:
    """
    Base class for all interactable objects in the game world.
    
    Provides common functionality for objects that the player can interact with,
    including proximity detection, state management, and basic rendering.
    """
    
    def __init__(self, x: int, y: int, width: int = 32, height: int = 32):
        """
        Initialize interactable object.
        
        Args:
            x: X position in world coordinates
            y: Y position in world coordinates  
            width: Collision width in pixels
            height: Collision height in pixels
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.active = True
        self.interactable = True
        
        # Animation state
        self.current_frame = 0
        self.frame_timer = 0.0
        
    def get_collision_rect(self) -> pygame.Rect:
        """Get collision rectangle for interaction detection."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def is_player_nearby(self, player_x: int, player_y: int, interaction_distance: int = 64) -> bool:
        """
        Check if player is close enough to interact.
        
        Args:
            player_x: Player's X position
            player_y: Player's Y position
            interaction_distance: Maximum distance for interaction
            
        Returns:
            True if player is within interaction distance
        """
        # Calculate distance from player to object center
        object_center_x = self.x + self.width // 2
        object_center_y = self.y + self.height // 2
        
        distance = ((player_x - object_center_x) ** 2 + (player_y - object_center_y) ** 2) ** 0.5
        return distance <= interaction_distance
        
    def interact(self, player) -> bool:
        """
        Handle player interaction.
        
        Args:
            player: Player object attempting interaction
            
        Returns:
            True if interaction was successful
        """
        # Override in subclasses
        return False
        
    def update(self, dt: float):
        """
        Update interactable object.
        
        Args:
            dt: Delta time in seconds
        """
        # Override in subclasses for animation updates
        pass
        
    def render(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """
        Render interactable object.
        
        Args:
            screen: Surface to render onto
            camera_x: Camera X offset
            camera_y: Camera Y offset
        """
        # Override in subclasses
        pass


class Chest(Interactable):
    """
    Treasure chest that can be opened by the player.
    
    States:
        - closed: Initial state, chest is closed
        - opening: Playing opening animation
        - opened: Final state, chest has been opened
    
    The chest can only be opened once and will remain in the opened state.
    """
    
    def __init__(self, x: int, y: int, chest_type: str = "basic"):
        """
        Initialize chest.
        
        Args:
            x: X position in world coordinates
            y: Y position in world coordinates
            chest_type: Type of chest (affects rewards and appearance)
        """
        super().__init__(x, y, 32, 32)  # Standard chest size
        
        self.chest_type = chest_type
        self.state = "closed"  # closed, opening, opened
        self.opened = False
        
        # Load chest animations
        self.animation_loader = ChestAnimationLoader(
            "Assests/chests/Chest_1.json", 
            scale=2
        )
        
        if not self.animation_loader.load_chest_animations():
            print(f"Warning: Failed to load chest animations from Assests/chests/Chest_1.json")
        
        # Animation state
        self.current_animation = "idle"  # Start with idle (closed) animation
        self.current_frame = 0
        self.frame_timer = 0.0
        self.animation_playing = True  # Always play animations (idle is animated)
        
        # State transition timing
        self.state_transition_timer = 0.0
        self.waiting_for_used_transition = False
        
        print(f"Chest created at ({x}, {y}) with state '{self.state}'")
        
    def interact(self, player) -> bool:
        """
        Handle player interaction with chest.
        
        Args:
            player: Player object attempting to open chest
            
        Returns:
            True if chest was successfully opened
        """
        if not self.interactable or self.opened:
            return False
            
        if self.state == "closed":
            print(f"Player opening chest at ({self.x}, {self.y})")
            self._start_opening()
            return True
            
        return False
        
    def _start_opening(self):
        """Start the chest opening process."""
        self.state = "opening"
        self.current_animation = "opening"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.animation_playing = True
        
        print(f"Chest opening animation started")
        
    def update(self, dt: float):
        """
        Update chest animation and state.
        
        Args:
            dt: Delta time in seconds
        """
        # Handle state transition timing
        if self.waiting_for_used_transition:
            self.state_transition_timer += dt
            if self.state_transition_timer >= 2.0:  # Wait 2 seconds
                self._transition_to_used()
                return
        
        if not self.animation_playing:
            return
            
        # Update animation frame timing
        if self.animation_loader.has_animation(self.current_animation):
            duration = self.animation_loader.get_frame_duration(self.current_animation, self.current_frame)
            self.frame_timer += dt
            
            if self.frame_timer >= duration:
                self.frame_timer = 0.0
                frame_count = self.animation_loader.get_frame_count(self.current_animation)
                
                # Check if we're about to go past the last frame
                if self.current_frame + 1 >= frame_count:
                    # Handle animation completion/looping
                    if self.state == "opening":
                        self._finish_opening()
                    elif self.current_animation == "idle":
                        self.current_frame = 0  # Loop idle animation
                    else:
                        # Stay on last frame for static animations
                        self.current_frame = frame_count - 1
                else:
                    # Safe to increment frame
                    self.current_frame += 1
                    
    def _finish_opening(self):
        """Complete the chest opening process."""
        print(f"Chest opening animation complete - waiting 2 seconds before transitioning to 'used' state")
        
        # Start transition timer instead of immediately switching
        self.waiting_for_used_transition = True
        self.state_transition_timer = 0.0
        self.animation_playing = False  # Stop current animation
        
    def _transition_to_used(self):
        """Transition to the used state after delay."""
        self.state = "opened"
        self.opened = True
        self.current_animation = "used"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.animation_playing = False  # Used animation is static (1 frame)
        self.waiting_for_used_transition = False
        
        print(f"Chest transitioned to 'used' state")
        
        # TODO: Add reward logic here
        # This is where we would give the player items, health, etc.
        
    def render(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """
        Render chest with current animation frame.
        
        Args:
            screen: Surface to render onto
            camera_x: Camera X offset
            camera_y: Camera Y offset
        """
        # Get current animation frame
        surface = self.animation_loader.get_frame_surface(
            self.current_animation, 
            self.current_frame, 
            facing_right=True  # Chests don't flip
        )
        
        if surface:
            # Calculate screen position
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            
            # Get pivot for proper positioning
            pivot = self.animation_loader.get_frame_pivot(
                self.current_animation, 
                self.current_frame, 
                facing_right=True
            )
            
            if pivot:
                screen_x -= pivot[0]
                screen_y -= pivot[1]
            
            screen.blit(surface, (screen_x, screen_y))
        else:
            # Fallback rendering - draw a simple rectangle
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            
            # Color based on state
            if self.state == "closed":
                color = (139, 69, 19)  # Brown for closed
            elif self.state == "opening":
                color = (255, 215, 0)  # Gold for opening
            else:
                color = (160, 82, 45)  # Lighter brown for opened
                
            pygame.draw.rect(screen, color, (screen_x, screen_y, self.width, self.height))
            
    def get_info(self) -> dict:
        """Get chest information for debugging."""
        return {
            'position': (self.x, self.y),
            'state': self.state,
            'opened': self.opened,
            'chest_type': self.chest_type,
            'current_animation': self.current_animation,
            'current_frame': self.current_frame,
            'animation_playing': self.animation_playing
        }