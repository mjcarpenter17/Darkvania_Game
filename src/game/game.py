"""Main game class that coordinates all systems."""
import os
import pygame
from typing import Optional, List

from .player import Player
from .enemy import Enemy, AssassinEnemy
from ..engine.world import World
from ..engine.camera import Camera
from ..ui.game_state import GameState


class Game:
    """Main game class that coordinates all game systems."""
    
    def __init__(self, width: int = 800, height: int = 450):
        # Initialize Pygame
        pygame.init()
        
        # Screen setup
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.game_state = GameState()
        self.game_state.create_main_menu()
        
        # Game objects (initialized when game starts)
        self.player: Optional[Player] = None
        self.world: Optional[World] = None
        self.camera: Optional[Camera] = None
        self.enemies: List = []  # List to store enemy instances
        
        # Colors
        self.bg_color = (20, 20, 25)
        self.game_bg_color = (30, 30, 36)
        
        # Auto-exit for testing
        self.auto_exit_seconds = self._get_auto_exit_time()
        self.elapsed_time = 0.0
        
        # Debug settings
        self.debug_collision = False
        
        # Game settings
        self.scale = 2
        
    def _get_auto_exit_time(self) -> Optional[float]:
        """Get auto-exit time from environment variable."""
        try:
            env_val = os.environ.get("AUTO_EXIT_SEC")
            if env_val:
                return float(env_val)
        except Exception:
            pass
        return None
    
    def run(self):
        """Main game loop."""
        pygame.display.set_caption("Walk Animation Game - Main Menu")
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle auto-exit for testing
            if self.auto_exit_seconds:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit_seconds:
                    self.running = False
                    continue
            
            # Handle events
            self._handle_events(dt)
            
            # Handle state changes
            if self.game_state.should_quit():
                self.running = False
            elif self.game_state.is_in_game() and self.game_state.get_selected_map_path():
                # Run the game
                self._run_game_loop()
                # After game ends, return to main menu
                self.game_state.reset_to_main_menu()
                pygame.display.set_caption("Walk Animation Game - Main Menu")
                self.screen = pygame.display.set_mode((self.width, self.height))
            
            # Render menu
            if not self.game_state.is_in_game():
                self._render_menu()
            
        pygame.quit()
    
    def _handle_events(self, dt: float):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                if self.game_state.current_menu:
                    action = self.game_state.current_menu.handle_input(event)
                    if action and action != "navigate":
                        self.game_state.handle_menu_action(action)
    
    def _render_menu(self):
        """Render the menu system."""
        self.screen.fill(self.bg_color)
        
        if self.game_state.current_menu:
            self.game_state.current_menu.draw(self.screen)
        
        pygame.display.flip()
    
    def _run_game_loop(self):
        """Run the main game loop."""
        pygame.display.set_caption("Walk Animation Game")
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        # Initialize game objects
        if not self._initialize_game():
            return
        
        # Game loop
        game_running = True
        while game_running and self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_running = False  # Return to menu
                    elif event.key == pygame.K_F2:
                        self.debug_collision = not self.debug_collision
            
            # Get input state
            input_state = self._get_input_state()
            
            # Update game objects
            self._update_game(dt, input_state)
            
            # Render game
            self._render_game()
            
            # Handle auto-exit
            if self.auto_exit_seconds:
                self.elapsed_time += dt
                if self.elapsed_time >= self.auto_exit_seconds:
                    game_running = False
        
        # Cleanup
        self._cleanup_game()
    
    def _initialize_game(self) -> bool:
        """Initialize game objects for the selected map."""
        try:
            # Load world
            self.world = World(self.game_state.get_selected_map_path(), scale=self.scale)
            print(f"Loaded world: {self.world.map_cols}x{self.world.map_rows} tiles")
            
            # Initialize camera
            self.camera = Camera(self.width, self.height)
            world_width, world_height = self.world.get_world_bounds()
            self.camera.set_world_bounds(world_width, world_height)
            
            # Initialize player
            spawn_pos = self.world.find_spawn_point("Player")
            if spawn_pos:
                player_x, player_y = spawn_pos
                print(f"Player spawned at 'Player' spawn point: ({player_x}, {player_y})")
            else:
                # Fallback to center of map
                player_x = float(self.world.map_cols * self.world.tile_size * self.scale // 2)
                player_y = float(100)  # Start above ground
                print("No 'Player' spawn point found, using map center")
            
            self.player = Player(player_x, player_y, scale=self.scale)
            
            # Initialize enemies
            self._spawn_enemies()
            
            # Center camera on player initially
            self.camera.center_on_target(self.player.pos_x, self.player.pos_y)
            
            # Center camera on player
            self.camera.center_on_target(self.player.pos_x, self.player.pos_y)
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize game: {e}")
            return False
    
    def _spawn_enemies(self):
        """Spawn enemies from the world map data."""
        if not self.world:
            return
            
        # Find all enemy spawn points
        enemy_spawns = self.world.find_enemy_spawn_points()
        
        for spawn_info in enemy_spawns:
            enemy_name = spawn_info['name']
            world_x = spawn_info['world_x']
            world_y = spawn_info['world_y']
            
            print(f"Spawning enemy '{enemy_name}' at world position ({world_x}, {world_y})")
            
            # Create appropriate enemy type based on name or properties
            # For now, just create AssassinEnemy for all enemies
            enemy = AssassinEnemy(world_x, world_y, scale=self.scale)
            self.enemies.append(enemy)
    
    def _get_input_state(self) -> dict:
        """Get current input state."""
        keys = pygame.key.get_pressed()
        return {
            'left': keys[pygame.K_LEFT] or keys[pygame.K_a],
            'right': keys[pygame.K_RIGHT] or keys[pygame.K_d],
            'jump': keys[pygame.K_SPACE] or keys[pygame.K_w],
            'dash': keys[pygame.K_q],
            'attack': keys[pygame.K_f]
        }
    
    def _update_game(self, dt: float, input_state: dict):
        """Update all game objects."""
        if self.player and self.world and self.camera:
            # Update player
            self.player.update(dt, input_state, self.world)
            
            # Update enemies
            for enemy in self.enemies:
                enemy.update(dt, self.world)
            
            # Remove dead enemies
            self._remove_dead_enemies()
            
            # Check for player attacks hitting enemies
            self._check_player_enemy_collisions()
            
            # Update camera to follow player with velocity for lookahead
            self.camera.follow_target(
                self.player.pos_x, 
                self.player.pos_y, 
                dt, 
                self.player.velocity_x
            )
            
            # Check for death objects or damage tiles
            self._check_death_conditions()
    
    def _check_death_conditions(self):
        """Check if player should respawn due to death conditions."""
        if not self.player or not self.world:
            return
            
        # Check for damage tiles
        if self.world.is_damage_at(self.player.pos_x, self.player.pos_y):
            self._respawn_player()
            return
            
        # Check for death event objects
        death_objects = self.world.find_objects_by_name("death")
        player_tile_x = int(self.player.pos_x // (self.world.tile_size * self.world.scale))
        player_tile_y = int(self.player.pos_y // (self.world.tile_size * self.world.scale))
        
        for obj in death_objects:
            if obj.get('x') == player_tile_x and obj.get('y') == player_tile_y:
                self._respawn_player()
                return
                
        # Check for falling off the map
        world_width, world_height = self.world.get_world_bounds()
        if (self.player.pos_y > world_height + 100 or  # Fell below world
            self.player.pos_x < -100 or self.player.pos_x > world_width + 100):  # Fell off sides
            self._respawn_player()
    
    def _respawn_player(self):
        """Respawn player at spawn point."""
        if not self.player or not self.world:
            return
            
        spawn_pos = self.world.find_spawn_point("Player")
        if spawn_pos:
            self.player.set_position(spawn_pos[0], spawn_pos[1])
            self.player.velocity_x = 0.0
            self.player.velocity_y = 0.0
            self.player.on_ground = False
            print("Player respawned!")
    
    def _check_player_enemy_collisions(self):
        """Check for collisions between player attacks and enemies."""
        if not self.player or not self.player.is_attacking:
            return
            
        # Get player attack box when attacking
        attack_box = self._get_player_attack_box()
        if not attack_box:
            return
            
        # Check collision with each enemy
        for enemy in self.enemies:
            if self._check_enemy_hit_by_attack(enemy, attack_box):
                enemy.take_damage(1)  # Deal 1 damage to enemy
    
    def _get_player_attack_box(self):
        """Get the collision box for the player's current attack."""
        if not self.player or not self.player.is_attacking:
            return None
            
        # Attack box dimensions (adjust these values based on the attack animation)
        attack_width = 40 * self.scale  # Width of attack reach
        attack_height = 25 * self.scale  # Height of attack reach
        
        # Calculate attack box position based on player position and direction
        if self.player.direction == 1:  # Facing right
            attack_x = self.player.pos_x + 10  # Offset forward from player
        else:  # Facing left
            attack_x = self.player.pos_x - attack_width - 10  # Offset forward from player
            
        attack_y = self.player.pos_y - attack_height + 5  # Slightly above player feet
        
        return {
            'x': attack_x,
            'y': attack_y, 
            'width': attack_width,
            'height': attack_height
        }
    
    def _check_enemy_hit_by_attack(self, enemy, attack_box):
        """Check if an enemy is hit by the player's attack box."""
        # Enemy collision box (approximate enemy size)
        enemy_width = 20 * enemy.scale
        enemy_height = 30 * enemy.scale
        enemy_x = enemy.pos_x - enemy_width // 2
        enemy_y = enemy.pos_y - enemy_height
        
        # Check rectangle overlap
        return (attack_box['x'] < enemy_x + enemy_width and
                attack_box['x'] + attack_box['width'] > enemy_x and
                attack_box['y'] < enemy_y + enemy_height and
                attack_box['y'] + attack_box['height'] > enemy_y)
    
    def _remove_dead_enemies(self):
        """Remove enemies that are marked for removal after death animation."""
        enemies_to_remove = []
        for i, enemy in enumerate(self.enemies):
            if enemy.marked_for_removal:
                enemies_to_remove.append(i)
                print(f"Removing dead enemy at position {enemy.pos_x}, {enemy.pos_y}")  # Debug output
        
        # Remove enemies in reverse order to avoid index shifting
        for i in reversed(enemies_to_remove):
            del self.enemies[i]
    
    def _render_game(self):
        """Render the game world and objects."""
        self.screen.fill(self.game_bg_color)
        
        if self.world and self.camera and self.player:
            camera_x, camera_y = self.camera.get_position()
            
            # Render world
            self.world.render(self.screen, camera_x, camera_y)
            
            # Render enemies
            for enemy in self.enemies:
                enemy.render(self.screen, camera_x, camera_y)
            
            # Render player
            self.player.draw(self.screen, camera_x, camera_y)
            
            # Render debug info
            if self.debug_collision:
                self._render_debug_info()
            
            # Render instructions
            self._render_instructions()
        
        pygame.display.flip()
    
    def _render_debug_info(self):
        """Render debug collision information."""
        if not self.player or not self.world:
            return
            
        font = pygame.font.Font(None, 24)
        debug_info = [
            f"Player: ({self.player.pos_x:.1f}, {self.player.pos_y:.1f})",
            f"Velocity: ({self.player.velocity_x:.1f}, {self.player.velocity_y:.1f})",
            f"On Ground: {self.player.on_ground}",
            f"State: {self.player.state}",
        ]
        
        for i, info in enumerate(debug_info):
            text = font.render(info, True, (255, 255, 255))
            self.screen.blit(text, (10, 10 + i * 25))
    
    def _render_instructions(self):
        """Render game instructions."""
        font = pygame.font.Font(None, 24)
        instructions = [
            "Arrow Keys / WASD: Move and Jump",
            "F2: Toggle Debug Info", 
            "ESC: Return to Menu"
        ]
        
        for i, text in enumerate(instructions):
            text_surf = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (10, self.height - 80 + i * 25))
    
    def _cleanup_game(self):
        """Clean up game objects."""
        self.player = None
        self.world = None
        self.camera = None
        self.enemies.clear()
