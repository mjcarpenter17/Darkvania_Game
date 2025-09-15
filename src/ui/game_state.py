"""Game state management and map loading."""
import os
import glob
from typing import List, Dict, Optional

from .menu import Menu, MenuItem


class GameState:
    """Manages game state transitions and map selection."""
    
    def __init__(self):
        self.current_menu = None
        self.selected_map = None
        self.state = "main_menu"  # "main_menu", "map_select", "game", "quit"
        self.maps_list = []
        self.load_available_maps()
    
    def load_available_maps(self):
        """Load list of available map files."""
        maps_dir = "maps"
        if os.path.exists(maps_dir):
            # Get all .json files except autosave and preferences
            json_files = glob.glob(os.path.join(maps_dir, "*.json"))
            self.maps_list = []
            for file_path in json_files:
                filename = os.path.basename(file_path)
                # Skip autosave and preferences files
                if not filename.endswith('.autosave.json') and filename != 'preferences.json':
                    # Remove .json extension for display
                    display_name = filename[:-5] if filename.endswith('.json') else filename
                    self.maps_list.append({
                        'display_name': display_name,
                        'file_path': file_path,
                        'filename': filename
                    })
            
            # Sort by display name
            self.maps_list.sort(key=lambda x: x['display_name'].lower())
    
    def create_main_menu(self):
        """Create the main menu."""
        items = [
            MenuItem("Play Game", "play"),
            MenuItem("Map Select", "map_select"),
            MenuItem("Quit", "quit")
        ]
        self.current_menu = Menu("Walk Animation Game", items)
    
    def create_map_select_menu(self):
        """Create the map selection menu."""
        items = []
        
        if not self.maps_list:
            items.append(MenuItem("No maps found", "back"))
        else:
            for map_info in self.maps_list:
                items.append(MenuItem(map_info['display_name'], "select_map", map_info))
        
        items.append(MenuItem("Back to Main Menu", "back"))
        self.current_menu = Menu("Select Map", items)
    
    def handle_menu_action(self, action: str):
        """Handle menu actions and state transitions."""
        if action == "play":
            # Play with default map (last_map.json if it exists)
            default_map = None
            for map_info in self.maps_list:
                if map_info['filename'] == 'last_map.json':
                    default_map = map_info
                    break
            
            if not default_map and self.maps_list:
                default_map = self.maps_list[0]
            
            if default_map:
                self.selected_map = default_map['file_path']
                self.state = "game"
            else:
                print("No maps available to play!")
        
        elif action == "map_select":
            self.state = "map_select"
            self.create_map_select_menu()
        
        elif action == "select_map":
            # Get the selected map from the current menu item
            selected_item = self.current_menu.get_selected_item()
            if selected_item.data:
                self.selected_map = selected_item.data['file_path']
                self.state = "game"
        
        elif action == "back":
            if self.state == "map_select":
                self.state = "main_menu"
                self.create_main_menu()
            elif self.state == "main_menu":
                self.state = "quit"
        
        elif action == "quit":
            self.state = "quit"
    
    def get_selected_map_path(self) -> Optional[str]:
        """Get the currently selected map path."""
        return self.selected_map
    
    def reset_to_main_menu(self):
        """Reset state back to main menu."""
        self.state = "main_menu"
        self.selected_map = None
        self.create_main_menu()
    
    def is_in_game(self) -> bool:
        """Check if currently in game state."""
        return self.state == "game"
    
    def should_quit(self) -> bool:
        """Check if game should quit."""
        return self.state == "quit"
