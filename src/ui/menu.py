"""Menu system for game navigation."""
import pygame
from typing import List, Optional, Any


class MenuItem:
    """Represents a single menu item."""
    
    def __init__(self, text: str, action: str, data: Any = None):
        self.text = text
        self.action = action
        self.data = data


class Menu:
    """Menu system with keyboard navigation."""
    
    def __init__(self, title: str, items: List[MenuItem]):
        self.title = title
        self.items = items
        self.selected_index = 0
        self.font_large = None
        self.font_medium = None
        self.font_small = None
    
    def init_fonts(self):
        """Initialize fonts - call after pygame.init()"""
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
    
    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle menu input events. Returns action string or None."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                return "navigate"
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                return "navigate"
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.items[self.selected_index].action
            elif event.key == pygame.K_ESCAPE:
                return "back"
        return None
    
    def draw(self, screen: pygame.Surface):
        """Draw the menu on screen."""
        if not self.font_large:
            self.init_fonts()
        
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Draw title
        title_surf = self.font_large.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        screen.blit(title_surf, title_rect)
        
        # Draw menu items
        start_y = 200
        item_spacing = 50
        
        for i, item in enumerate(self.items):
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
            prefix = "> " if i == self.selected_index else "  "
            
            text = f"{prefix}{item.text}"
            text_surf = self.font_medium.render(text, True, color)
            text_rect = text_surf.get_rect(center=(screen_width // 2, start_y + i * item_spacing))
            screen.blit(text_surf, text_rect)
        
        # Draw instructions
        instructions = [
            "Use Arrow Keys to navigate",
            "Enter/Space to select",
            "ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surf = self.font_small.render(instruction, True, (150, 150, 150))
            inst_rect = inst_surf.get_rect(center=(screen_width // 2, screen_height - 100 + i * 25))
            screen.blit(inst_surf, inst_rect)
    
    def get_selected_item(self) -> MenuItem:
        """Get the currently selected menu item."""
        return self.items[self.selected_index]
    
    def set_selected_index(self, index: int):
        """Set the selected menu item by index."""
        if 0 <= index < len(self.items):
            self.selected_index = index
