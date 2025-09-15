"""Enemy character classes with animation and rendering."""
import pygame
import random
from typing import List, Tuple

from ..utils.aseprite_animation_loader import AsepriteAnimationLoader


class Enemy:
    """Base enemy class with position, sprite rendering, and animation."""
    
    def __init__(self, x: float, y: float, scale: int = 2):
        # Position (pivot point - feet center)
        self.pos_x = x
        self.pos_y = y
        
        # Physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        
        # Animation
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Config
        self.scale = scale
        self.direction = 1  # 1=right, -1=left
        self.gravity = 1400.0  # Same as player
        
        # AI Movement properties
        self.move_speed = 80.0  # Pixels per second (slower than player)
        self.patrol_direction = 1  # 1=right, -1=left (separate from sprite direction)
        self.movement_timer = 0.0
        self.idle_timer = 0.0
        self.idle_duration = 0.0  # Current idle period length
        self.ai_state = "patrol"  # "patrol", "idle", "hit", "death"
        
        # AI behavior settings
        self.min_idle_time = 1.0  # Minimum idle time in seconds
        self.max_idle_time = 4.0  # Maximum idle time in seconds
        self.idle_chance = 0.3  # 30% chance to idle when changing direction
        
        # Health and combat system
        self.max_health = 2  # Assassin has 2 HP
        self.health = self.max_health
        self.is_invulnerable = False  # Invulnerability frames after being hit
        self.invulnerability_timer = 0.0
        self.invulnerability_duration = 0.5  # 0.5 seconds of invulnerability after being hit
        self.hit_stun_timer = 0.0
        self.hit_stun_duration = 0.3  # 0.3 seconds of hit stun
        
        # Death system
        self.death_timer = 0.0
        self.death_animation_duration = 0.8  # 8 frames * 100ms each
        self.marked_for_removal = False  # Flag to mark enemy for removal
        
        # Animation loader (to be set by subclasses)
        self.animation_loader = None
        
    def update(self, dt: float, world_map=None):
        """Update enemy animation, physics, and logic."""
        # Update combat timers
        if self.is_invulnerable:
            self.invulnerability_timer += dt
            if self.invulnerability_timer >= self.invulnerability_duration:
                self.is_invulnerable = False
                self.invulnerability_timer = 0.0
        
        if self.hit_stun_timer > 0:
            self.hit_stun_timer -= dt
            if self.hit_stun_timer <= 0:
                self.hit_stun_timer = 0.0
                # Exit hit state if we were in it
                if self.ai_state == "hit":
                    self.ai_state = "patrol"
        
        # Update death timer
        if self.ai_state == "death":
            self.death_timer += dt
            if self.death_timer >= self.death_animation_duration:
                self.marked_for_removal = True
                print(f"Enemy death animation complete, marked for removal")  # Debug output
        
        # Update AI behavior (skip if dead or in hit stun)
        if self.ai_state != "death" and self.hit_stun_timer <= 0:
            self._update_ai(dt, world_map)
        
        # Apply physics
        self._apply_physics(dt)
        
        # Handle collisions if world map is provided
        if world_map:
            self._handle_collisions(world_map, dt)
        else:
            # Fallback collision (ground level)
            self._handle_basic_collision()
        
        # Update animation timer
        if self.animation_loader and self.state in self.animation_loader.animations:
            animation_data = self.animation_loader.get_animation(self.state)
            if animation_data and animation_data['durations']:
                durations = animation_data['durations']
                frame_duration = durations[min(self.current_frame, len(durations) - 1)]
                self.frame_timer += dt
                
                if self.frame_timer >= frame_duration:
                    self.frame_timer = 0.0
                    
                    # Get frame count
                    frames = animation_data['surfaces_right']
                    if frames:
                        self.current_frame = (self.current_frame + 1) % len(frames)
    
    def _update_ai(self, dt: float, world_map=None):
        """Update AI behavior logic."""
        if self.ai_state == "patrol":
            self._update_patrol_ai(dt, world_map)
        elif self.ai_state == "idle":
            self._update_idle_ai(dt)
        elif self.ai_state == "hit":
            self._update_hit_ai(dt)
        elif self.ai_state == "death":
            self._update_death_ai(dt)
    
    def _update_patrol_ai(self, dt: float, world_map=None):
        """Handle patrol movement behavior."""
        # Set movement velocity
        self.velocity_x = self.patrol_direction * self.move_speed
        
        # Update sprite direction for rendering
        self.direction = self.patrol_direction
        
        # Set animation to run
        if self.state != "run":
            self.state = "run"
            self.current_frame = 0
            self.frame_timer = 0.0
        
        # Check for edge detection and wall collision
        if world_map and self.on_ground:
            should_turn = False
            
            # Edge detection - check if there's ground ahead
            look_ahead_distance = 20 * self.scale  # Look ahead 20 pixels
            look_ahead_x = self.pos_x + (self.patrol_direction * look_ahead_distance)
            ground_check_y = self.pos_y + 10  # Check slightly below feet
            
            if not world_map.is_solid_at_any_layer(look_ahead_x, ground_check_y) and \
               not world_map.is_platform_at_any_layer(look_ahead_x, ground_check_y):
                should_turn = True  # No ground ahead, turn around
            
            # Wall detection - check if there's a wall ahead
            wall_check_y = self.pos_y - 10  # Check at body height
            if world_map.is_solid_at_any_layer(look_ahead_x, wall_check_y):
                should_turn = True  # Wall ahead, turn around
            
            if should_turn:
                self._change_patrol_direction()
    
    def _change_patrol_direction(self):
        """Change patrol direction (called when hitting walls or edges)."""
        self.patrol_direction *= -1
        self.velocity_x = self.move_speed * self.patrol_direction
        
        # 30% chance to go idle when changing direction
        if random.random() < 0.3:
            self._enter_idle_state()
    
    def _enter_idle_state(self):
        """Enter idle state with random duration."""
        self.ai_state = "idle"
        self.idle_duration = random.uniform(1.0, 4.0)  # Random idle time 1-4 seconds
        self.idle_timer = 0.0
        self.velocity_x = 0.0
    
    def _update_idle_ai(self, dt: float):
        """Handle idle behavior."""
        self.velocity_x = 0.0  # Stop moving
        
        # Set animation to idle
        if self.state != "idle":
            self.state = "idle"
            self.current_frame = 0
            self.frame_timer = 0.0
        
        # Update idle timer
        self.idle_timer += dt
        
        # Check if idle period is over
        if self.idle_timer >= self.idle_duration:
            self.ai_state = "patrol"
            self.idle_timer = 0.0
    
    def _update_hit_ai(self, dt: float):
        """Handle hit reaction behavior."""
        self.velocity_x = 0.0  # Stop moving when hit
        
        # Set animation to hit
        if self.state != "hit":
            self.state = "hit"
            self.current_frame = 0
            self.frame_timer = 0.0
        
        # Hit stun timer is managed in the main update loop
        # This state will automatically end when hit_stun_timer expires
    
    def _update_death_ai(self, dt: float):
        """Handle death behavior."""
        self.velocity_x = 0.0  # Stop moving when dead
        
        # Set animation to death
        if self.state != "death":
            self.state = "death"
            self.current_frame = 0
            self.frame_timer = 0.0
        
        # Death behavior stays active until enemy is removed
    
    def _turn_around(self):
        """Turn around and optionally go idle."""
        self.patrol_direction *= -1  # Reverse direction
        
        # Chance to go idle when turning around
        if random.random() < self.idle_chance:
            self.ai_state = "idle"
            self.idle_duration = random.uniform(self.min_idle_time, self.max_idle_time)
            self.idle_timer = 0.0
    
    def _apply_physics(self, dt: float):
        """Apply gravity and basic physics."""
        self.velocity_y += self.gravity * dt
        
    def _handle_collisions(self, world_map, dt: float):
        """Handle collision detection and response with the world."""
        # Horizontal movement with collision (AI-controlled)
        new_x = self.pos_x + self.velocity_x * dt
        
        # Check for wall collision in movement direction
        check_x = new_x + (5 if self.velocity_x > 0 else -5)  # Check ahead of enemy
        if not world_map.is_solid_at_any_layer(check_x, self.pos_y):
            self.pos_x = new_x
        else:
            # Hit a wall - trigger direction change in AI
            self.velocity_x = 0.0
            self._change_patrol_direction()
        
        # Vertical movement with collision
        new_y = self.pos_y + self.velocity_y * dt
        
        if self.velocity_y > 0:  # Falling
            # Check at foot level (slightly below pivot)
            foot_y = new_y + 2
            
            # Check for solid tiles (always stop)
            if world_map.is_solid_at_any_layer(self.pos_x, foot_y):
                # Find the exact ground level
                tile_size = world_map.tile_size * world_map.scale
                tile_y = int(foot_y // tile_size) * tile_size
                self.pos_y = float(tile_y - 2)  # Stand on top of the tile
                self.velocity_y = 0.0
                self.on_ground = True
            # Check for platform tiles (only stop if falling onto them from above)
            elif world_map.is_platform_at_any_layer(self.pos_x, foot_y):
                # Only land on platform if we're falling from above
                tile_size = world_map.tile_size * world_map.scale
                tile_y = int(foot_y // tile_size) * tile_size
                # Check if our previous position was above this tile
                prev_foot_y = self.pos_y + 2
                if prev_foot_y <= tile_y:
                    self.pos_y = float(tile_y - 2)  # Stand on top of the platform
                    self.velocity_y = 0.0
                    self.on_ground = True
                else:
                    # We're inside or below the platform, pass through
                    self.pos_y = new_y
                    self.on_ground = False
            else:
                self.pos_y = new_y
                self.on_ground = False
        else:  # Moving up (shouldn't happen much for basic enemies)
            # Check at head level (only solid tiles block upward movement)
            head_y = new_y - 35
            if world_map.is_solid_at_any_layer(self.pos_x, head_y):
                # Hit ceiling
                self.velocity_y = 0.0
                # Don't update position to prevent clipping into ceiling
            else:
                self.pos_y = new_y
                self.on_ground = False
                
        # Keep enemy within map bounds
        map_width = world_map.map_cols * world_map.tile_size * world_map.scale
        if self.pos_x < 0:
            self.pos_x = 0
        if self.pos_x > map_width:
            self.pos_x = map_width
            
    def _handle_basic_collision(self):
        """Basic collision for when no world map is available."""
        ground_y = 400.0  # Default ground level
        
        # Apply vertical movement
        self.pos_y += self.velocity_y * (1/60.0)  # Assume 60 FPS for fallback
        
        # Check ground collision
        if self.pos_y >= ground_y:
            self.pos_y = ground_y
            self.velocity_y = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
    
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float):
        """Render the enemy on screen."""
        if not self.animation_loader or self.state not in self.animation_loader.animations:
            return
            
        # Get animation data
        animation_data = self.animation_loader.get_animation(self.state)
        if not animation_data:
            return
        
        # Get frames based on direction
        frames = animation_data['surfaces_right'] if self.direction > 0 else animation_data['surfaces_left']
        pivots = animation_data['pivots_right'] if self.direction > 0 else animation_data['pivots_left']
        
        if not frames or self.current_frame >= len(frames):
            return
        
        # Get current frame and pivot
        current_surface = frames[self.current_frame]
        pivot_x, pivot_y = pivots[self.current_frame] if pivots else (0, 0)
        
        # Calculate screen position (subtract camera offset)
        screen_x = int(self.pos_x - camera_x - pivot_x)
        screen_y = int(self.pos_y - camera_y - pivot_y)
        
        # Draw the sprite with flashing effect during invulnerability
        if self.is_invulnerable:
            # Flash every 0.1 seconds (10 Hz) during invulnerability
            flash_interval = 0.1
            if int(self.invulnerability_timer / flash_interval) % 2 == 0:
                # Create a red-tinted surface for hit feedback
                hit_surface = current_surface.copy()
                hit_surface.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)
                screen.blit(hit_surface, (screen_x, screen_y))
            else:
                # Normal rendering during flash-off frames
                screen.blit(current_surface, (screen_x, screen_y))
        else:
            # Normal rendering when not invulnerable
            screen.blit(current_surface, (screen_x, screen_y))
    
    def get_position(self) -> Tuple[float, float]:
        """Get enemy position."""
        return (self.pos_x, self.pos_y)
    
    def take_damage(self, damage: int):
        """Handle taking damage from player attacks."""
        # Check if enemy is invulnerable
        if self.is_invulnerable or self.ai_state == "death":
            return
        
        # Apply damage
        self.health -= damage
        print(f"Enemy hit! Health: {self.health}/{self.max_health}")  # Debug output
        
        # Enter hit state
        self.ai_state = "hit"
        self.hit_stun_timer = self.hit_stun_duration
        self.is_invulnerable = True
        self.invulnerability_timer = 0.0
        
        # Stop movement during hit
        self.velocity_x = 0.0
        
        # Set hit animation
        self.state = "hit"
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Check if enemy should die
        if self.health <= 0:
            self._trigger_death()
    
    def _trigger_death(self):
        """Handle enemy death."""
        self.ai_state = "death"
        self.state = "death"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.velocity_x = 0.0
        print(f"Enemy died!")  # Debug output


class AssassinEnemy(Enemy):
    """Assassin enemy that uses the Assassin.json animation data."""
    
    def __init__(self, x: float, y: float, scale: int = 2):
        super().__init__(x, y, scale)
        
        # Load Aseprite animations
        aseprite_json_path = "Assests/enemies/assassin/Assassin.json"
        self.animation_loader = AsepriteAnimationLoader(aseprite_json_path, scale)
        
        # Define which animations to load for the assassin
        assassin_animations = {
            'idle': 'idle',
            'run': 'run', 
            'jump': 'jump',
            'fall': 'fall',
            'attack1': 'attack 1',
            'attack2': 'attack 2',
            'hit': 'hit',
            'death': 'death'
        }
        
        self.animation_loader.load_all_animations(assassin_animations)
        
        # Set initial state to idle
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0