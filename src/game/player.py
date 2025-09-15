"""Player character class with physics, animation, and input handling."""
import pygame
from typing import List, Tuple

from ..utils.aseprite_animation_loader import AsepriteAnimationLoader


class Player:
    """Player character with physics, animation, and input handling."""
    
    def __init__(self, x: float, y: float, scale: int = 2):
        # Position (pivot point - feet center)
        self.pos_x = x
        self.pos_y = y
        
        # Physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = True
        self.direction = 1  # 1=right, -1=left
        
        # Animation
        self.state = "idle"  # idle, walk, jump, trans, fall, dash, attack1, attack2
        self.prev_state = self.state
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Dash mechanics
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_duration = 0.6  # Total duration of dash animation (6 frames * 100ms)
        self.dash_speed = 320.0  # Speed multiplier during dash
        self.dash_cooldown = 0.0
        self.dash_cooldown_duration = 1.0  # Cooldown between dashes
        
        # Combo attack mechanics
        self.is_attacking = False
        self.attack_timer = 0.0
        self.current_attack = 1  # 1 for Slash 1, 2 for Slash 2
        self.attack1_duration = 0.7  # Slash 1: 7 frames * 100ms
        self.attack2_duration = 0.5  # Slash 2: 5 frames * 100ms
        self.attack_cooldown = 0.0
        self.attack_cooldown_duration = 0.3  # Cooldown after combo ends
        self.combo_window_duration = 0.7  # Time window to input combo (matches attack1 duration)
        self.combo_window_timer = 0.0  # Timer for combo window
        self.combo_window_active = False  # Is combo window currently active
        
        # Attack hit tracking (to prevent multiple hits per attack)
        self.enemies_hit_this_attack = set()  # Track which enemies have been hit during current attack
        
        # Health and damage system
        self.max_health = 2
        self.health = self.max_health
        self.is_invulnerable = False  # Invulnerability frames after taking damage
        self.invulnerability_timer = 0.0
        self.invulnerability_duration = 1.0  # 1 second of invulnerability after being hit
        self.is_dead = False
        self.respawn_requested = False  # Flag for when respawn is requested
        
        # Spawn system
        self.is_spawning = False
        self.spawn_timer = 0.0
        self.spawn_duration = 0.6  # Duration of "Appear Tele" animation
        
        # Input state tracking (to detect key press events, not continuous holding)
        self.prev_input_state = {}
        
        # Config
        self.scale = scale
        self.move_speed = 160.0
        self.jump_speed = 700.0
        self.gravity = 1400.0
        
        # Load Aseprite animations
        aseprite_json_path = "Assests/SwordMaster/Sword Master Sprite Sheet3.json"
        self.animation_loader = AsepriteAnimationLoader(aseprite_json_path, scale)
        self.animation_loader.load_all_animations()
        
        # Start with spawn animation
        self.start_spawn()
        
    def start_spawn(self):
        """Start the spawn animation sequence."""
        self.is_spawning = True
        self.spawn_timer = 0.0
        self.is_invulnerable = True  # Invulnerable during spawn
        self.state = "Appear Tele"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        print("Player spawning with Appear Tele animation")  # Debug output
        
    def update(self, dt: float, input_state: dict, world_map=None):
        """Update player physics, animation, and collision."""
        # Update health and combat timers
        self._update_health_timers(dt)
        
        # Handle input (skip if dead or spawning)
        if not self.is_dead and not self.is_spawning:
            self._handle_input(input_state, dt)
        elif self.is_spawning:
            self._handle_spawn_input(input_state, dt)
        elif self.is_dead:
            self._handle_death_input(input_state, dt)
        
        # Apply physics (skip if dead)
        if not self.is_dead:
            self._apply_physics(dt)
        
        # Handle collisions if world map is provided (skip if dead or spawning)
        if world_map and not self.is_dead and not self.is_spawning:
            self._handle_collisions(world_map, dt)
        elif not self.is_dead:
            # Fallback collision (ground level)
            self._handle_basic_collision()
        
        # Update animation
        self._update_animation(dt)
        
    def _handle_input(self, input_state: dict, dt: float):
        """Process player input."""
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        jump = input_state.get('jump', False)
        dash = input_state.get('dash', False)
        attack = input_state.get('attack', False)
        
        # Detect newly pressed keys (not held keys)
        prev_attack = self.prev_input_state.get('attack', False)
        prev_dash = self.prev_input_state.get('dash', False)
        attack_just_pressed = attack and not prev_attack
        dash_just_pressed = dash and not prev_dash
        
        # Update cooldowns and timers
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Update combo window timer
        if self.combo_window_active:
            self.combo_window_timer -= dt
            if self.combo_window_timer <= 0:
                self.combo_window_active = False
                self.combo_window_timer = 0.0
        
        # Handle attack input with proper key press detection
        if attack_just_pressed:
            if not self.is_attacking and self.attack_cooldown <= 0:
                # Start first attack and begin combo window
                self._start_attack(1)
                self.combo_window_active = True
                self.combo_window_timer = self.combo_window_duration
            elif self.combo_window_active and self.current_attack == 1:
                # Second attack pressed during combo window - queue Slash 2
                self._queue_combo_attack()
        
        # Handle dash input (cannot dash during attacks)
        if dash_just_pressed and not self.is_dashing and not self.is_attacking and self.dash_cooldown <= 0:
            self._start_dash()
        
        # Update previous input state for next frame BEFORE processing attacks
        self.prev_input_state = input_state.copy()
        
        # Update attack state
        if self.is_attacking:
            self.attack_timer += dt
            current_duration = self.attack1_duration if self.current_attack == 1 else self.attack2_duration
            
            # Check if current attack should end
            if self.attack_timer >= current_duration:
                self._end_current_attack()
        
        # Update dash state
        if self.is_dashing:
            self.dash_timer += dt
            if self.dash_timer >= self.dash_duration:
                self._end_dash()
        
        # Horizontal movement (modified for dash and attack)
        if self.is_dashing:
            # During dash, maintain dash speed in current direction
            self.velocity_x = self.direction * self.dash_speed
        elif self.is_attacking:
            # During attack, reduce movement speed significantly
            attack_speed_modifier = 0.1 if self.current_attack == 2 else 0.2  # Even slower during second attack
            self.velocity_x = 0.0
            if left and not right:
                self.velocity_x = -self.move_speed * attack_speed_modifier
                # Don't change direction during attack
            elif right and not left:
                self.velocity_x = self.move_speed * attack_speed_modifier
                # Don't change direction during attack
        else:
            # Normal movement
            self.velocity_x = 0.0
            if left and not right:
                self.velocity_x = -self.move_speed
                self.direction = -1
            elif right and not left:
                self.velocity_x = self.move_speed
                self.direction = 1
            
        # Jumping (can't jump while dashing or attacking)
        if jump and self.on_ground and not self.is_dashing and not self.is_attacking:
            self.velocity_y = -self.jump_speed
            self.on_ground = False
            
    def _start_attack(self, attack_number: int):
        """Start an attack (1 = Slash 1, 2 = Slash 2)."""
        self.is_attacking = True
        self.attack_timer = 0.0
        self.current_attack = attack_number
        self.state = f"attack{attack_number}"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.enemies_hit_this_attack.clear()  # Clear hit tracking for new attack
        print(f"Started Slash {attack_number}")  # Debug output
        
    def _queue_combo_attack(self):
        """Queue the second attack to start immediately."""
        print(f"Combo queued! Transitioning to Slash 2")  # Debug output
        self._start_attack(2)
        # Disable combo window since we've used it
        self.combo_window_active = False
        self.combo_window_timer = 0.0
        
    def _end_current_attack(self):
        """End the current attack."""
        if self.current_attack == 2 or not self.combo_window_active:
            # End the entire attack sequence
            self._end_attack_sequence()
        else:
            # Slash 1 ended without combo - end sequence
            self._end_attack_sequence()
            
    def _end_attack_sequence(self):
        """End the entire attack sequence."""
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_cooldown = self.attack_cooldown_duration
        self.current_attack = 1  # Reset to first attack
        self.combo_window_active = False
        self.combo_window_timer = 0.0
        print("Attack sequence ended")  # Debug output
            
    def _start_dash(self):
        """Start a dash."""
        self.is_dashing = True
        self.dash_timer = 0.0
        self.state = "dash"
        self.current_frame = 0
        self.frame_timer = 0.0
        
    def _end_dash(self):
        """End a dash."""
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_cooldown = self.dash_cooldown_duration
            
    def _apply_physics(self, dt: float):
        """Apply gravity and basic physics."""
        self.velocity_y += self.gravity * dt
        
    def _handle_collisions(self, world_map, dt: float):
        """Handle collision detection and response with the world."""
        # Horizontal movement with collision
        new_x = self.pos_x + self.velocity_x * dt
        
        # Check horizontal collision at multiple points (upper and middle body)
        check_points = [
            self.pos_y - 30,  # Upper body
            self.pos_y - 15,  # Middle body
        ]
        can_move = True
        for check_y in check_points:
            if world_map.is_solid_at_any_layer(new_x, check_y):
                can_move = False
                break
                
        if can_move:
            self.pos_x = new_x
            
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
        else:  # Jumping up
            # Check at head level (only solid tiles block upward movement)
            head_y = new_y - 35
            if world_map.is_solid_at_any_layer(self.pos_x, head_y):
                # Hit ceiling
                self.velocity_y = 0.0
                # Don't update position to prevent clipping into ceiling
            else:
                self.pos_y = new_y
                self.on_ground = False
                
        # Keep player within map bounds
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
        
        # Ground collision
        if self.pos_y >= ground_y:
            self.pos_y = ground_y
            self.velocity_y = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
            
        # Apply horizontal movement
        self.pos_x += self.velocity_x * (1/60.0)
        
    def _update_animation(self, dt: float):
        """Update animation state and frame."""
        # Determine desired state
        desired = self.state
        in_air = not self.on_ground
        trans_animation = self.animation_loader.get_animation('trans')
        trans_available = trans_animation and len(trans_animation['surfaces_right']) > 0
        
        # Handle attack states (highest priority)
        if self.is_attacking:
            desired = f"attack{self.current_attack}"
        # Handle dash state (second highest priority)
        elif self.is_dashing:
            desired = "dash"
        elif in_air:
            if self.velocity_y < -1e-2:
                desired = "jump"
            else:
                if self.state == "trans" and trans_available:
                    desired = "trans"  # stay in trans until it finishes
                elif self.state == "jump" and trans_available:
                    desired = "trans"
                else:
                    desired = "fall"
        else:
            desired = "walk" if abs(self.velocity_x) > 1e-2 else "idle"
            
        # Change state if needed
        if desired != self.state:
            self.state = desired
            self.current_frame = 0
            self.frame_timer = 0.0
            self.prev_state = self.state
            
        # Update animation frame using Aseprite durations
        self.frame_timer += dt
        
        # Get current frame duration from Aseprite data
        frame_duration = self.animation_loader.get_frame_duration(self.state, self.current_frame)
        
        animation_data = self.animation_loader.get_animation(self.state)
        if animation_data:
            frames = animation_data['surfaces_right'] if self.direction > 0 else animation_data['surfaces_left']
            
            if frames and frame_duration > 0:
                if self.frame_timer >= frame_duration:
                    self.frame_timer = 0.0
                    
                    # Handle animation direction (forward, reverse, pingpong)
                    direction = self.animation_loader.get_animation_direction(self.state)
                    if direction == "forward":
                        # For attack and dash animations, don't loop - stay on last frame
                        if self.state in ["attack1", "attack2", "dash"] and self.current_frame >= len(frames) - 1:
                            self.current_frame = len(frames) - 1
                        else:
                            self.current_frame = (self.current_frame + 1) % len(frames)
                    elif direction == "reverse":
                        self.current_frame = (self.current_frame - 1) % len(frames)
                    else:  # pingpong or other directions - default to forward for now
                        # For attack and dash animations, don't loop - stay on last frame
                        if self.state in ["attack1", "attack2", "dash"] and self.current_frame >= len(frames) - 1:
                            self.current_frame = len(frames) - 1
                        else:
                            self.current_frame = (self.current_frame + 1) % len(frames)
                
    def draw(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Draw the player character."""
        # Get animation in the new format
        animation_data = self.animation_loader.get_animation(self.state)
        if animation_data:
            # Use new format
            frames = animation_data['surfaces_right'] if self.direction > 0 else animation_data['surfaces_left']
            pivots = animation_data['pivots_right'] if self.direction > 0 else animation_data['pivots_left']
        else:
            # Fallback to legacy format
            frames_right, frames_left, pivots_right, pivots_left = self.animation_loader.get_legacy_format(self.state)
            frames = frames_right if self.direction > 0 else frames_left
            pivots = pivots_right if self.direction > 0 else pivots_left
        
        if not frames or self.current_frame >= len(frames):
            return
            
        # Get current frame and pivot
        current_surface = frames[self.current_frame]
        pivot_x, pivot_y = pivots[self.current_frame] if pivots else (0, 0)
        
        # Calculate screen position (subtract camera offset)
        screen_x = int(self.pos_x - camera_x - pivot_x)
        screen_y = int(self.pos_y - camera_y - pivot_y)
        
        # Draw the sprite
        screen.blit(current_surface, (screen_x, screen_y))
        
    def get_spawn_position(self, world_map) -> Tuple[float, float]:
        """Get the spawn position from the world map."""
        if world_map:
            # Try to find the "Player" spawn point
            player_spawn = world_map.find_spawn_point("Player")
            if player_spawn:
                return player_spawn
            else:
                # Fallback to center of map
                spawn_x = float(world_map.map_cols * world_map.tile_size * world_map.scale // 2)
                spawn_y = float(100)  # Start above ground
                return spawn_x, spawn_y
        else:
            return 400.0, 300.0  # Default position
            
    def set_position(self, x: float, y: float):
        """Set player position."""
        self.pos_x = x
        self.pos_y = y
    
    def _update_health_timers(self, dt: float):
        """Update health-related timers."""
        # Update invulnerability timer
        if self.is_invulnerable:
            self.invulnerability_timer += dt
            if self.invulnerability_timer >= self.invulnerability_duration:
                self.is_invulnerable = False
                self.invulnerability_timer = 0.0
        
        # Update spawn timer
        if self.is_spawning:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_duration:
                self._complete_spawn()
    
    def _complete_spawn(self):
        """Complete the spawn sequence."""
        self.is_spawning = False
        self.spawn_timer = 0.0
        self.is_invulnerable = False
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        print("Player spawn complete")  # Debug output
    
    def _handle_spawn_input(self, input_state: dict, dt: float):
        """Handle input during spawn animation (no input allowed)."""
        pass  # No input during spawn
    
    def _handle_death_input(self, input_state: dict, dt: float):
        """Handle input during death state (only respawn key)."""
        # Check for respawn key (Space)
        space = input_state.get('jump', False)  # Using jump key as Space
        prev_space = self.prev_input_state.get('jump', False)
        
        if space and not prev_space:  # Space key pressed
            self.respawn()
    
    def take_damage(self, damage: int):
        """Apply damage to the player."""
        if self.is_invulnerable or self.is_dead or self.is_spawning:
            return False  # No damage taken
        
        self.health -= damage
        print(f"Player hit! Health: {self.health}/{self.max_health}")  # Debug output
        
        if self.health <= 0:
            self._trigger_death()
        else:
            self._trigger_hit()
        
        return True  # Damage was applied
    
    def _trigger_hit(self):
        """Handle player taking non-fatal damage."""
        self.is_invulnerable = True
        self.invulnerability_timer = 0.0
        self.state = "Hit"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.velocity_x *= 0.5  # Reduce velocity on hit
    
    def _trigger_death(self):
        """Handle player death."""
        self.is_dead = True
        self.health = 0
        self.state = "death"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        print("Player died!")  # Debug output
    
    def respawn(self):
        """Request respawn (to be handled by game class)."""
        self.respawn_requested = True
        print("Player respawn requested!")  # Debug output
