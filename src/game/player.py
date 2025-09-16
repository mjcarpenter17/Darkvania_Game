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
        
        # Double jump system
        self.jump_count = 0  # Track number of jumps performed
        self.max_jumps = 2   # Allow double jump
        
        # Ledge grab system
        self.is_ledge_grabbing = False
        self.ledge_grab_x = 0.0  # X position where ledge is grabbed
        self.ledge_grab_y = 0.0  # Y position where ledge is grabbed
        self.ledge_grab_direction = 1  # Direction of the ledge grab
        self.ledge_grab_timer = 0.0
        self.can_ledge_grab = True  # Prevent immediate re-grabbing after climb/drop
        
        # Wall hold system
        self.is_wall_holding = False
        self.wall_side = 0  # -1 for left wall, 1 for right wall, 0 for no wall
        self.wall_hold_timer = 0.0
        self.wall_hold_grace_time = 0.1  # Brief moment before sliding starts
        self.wall_slide_speed = 100.0  # Slower than gravity
        self.wall_slide_max_speed = 200.0  # Terminal velocity while sliding
        self.wall_jump_speed_x = 250.0  # Horizontal push away from wall
        self.wall_jump_speed_y = 600.0  # Slightly less than normal jump
        self.wall_jump_duration = 0.3  # Brief period of forced movement
        self.wall_jump_timer = 0.0  # Timer for wall jump forced movement
        self.can_wall_grab = True  # Prevent immediate re-grabbing same wall
        self.wall_grab_cooldown = 0.0  # Cooldown before grabbing same wall again
        self.wall_grab_cooldown_duration = 0.2  # Delay before re-grabbing
        
        # Roll system
        self.is_rolling = False
        self.roll_timer = 0.0
        self.roll_duration = 0.6  # seconds (matches animation length)
        self.roll_speed = 200.0
        self.roll_cooldown = 0.0
        self.roll_cooldown_duration = 1.0
        self.roll_invulnerability_duration = 0.6
        self.roll_direction = 1  # Direction captured at roll start
        
        # Animation
        self.state = "idle"  # idle, walk, jump, trans, fall, dash, attack1, attack2, ledge_grab, wall_hold, wall_transition, wall_slide, wall_slide_stop, roll, fall_attack, slam_attack
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
        
        # Downward attack (aerial) mechanics
        self.is_fall_attacking = False
        self.fall_attack_timer = 0.0
        self.fall_attack_duration = 0.7  # Fall Attack: 7 frames * 100ms
        self.fall_attack_damage_multiplier = 1.5  # 50% more damage than regular attacks
        self.fall_attack_speed_multiplier = 2.0  # Fall faster during attack
        self.fall_attack_cooldown = 0.0
        self.fall_attack_cooldown_duration = 1.2  # Slightly longer cooldown than regular attacks
        self.fall_attack_invulnerability_duration = 0.25  # Invulnerability during fall attack
        
        # Slam attack (charged) mechanics
        self.is_slam_charging = False
        self.is_slam_attacking = False
        self.slam_charge_timer = 0.0
        self.slam_charge_duration = 1.0  # Hold F for 1 second to charge
        self.slam_charge_delay = 0.2  # Delay before slam charging starts (allows regular attacks)
        self.slam_potential_timer = 0.0  # Timer for potential slam charge
        self.slam_attack_timer = 0.0
        self.slam_attack_duration = 0.6  # Slam animation duration
        self.slam_damage_multiplier = 2.0  # 100% more damage than regular attacks
        self.slam_aoe_radius = 60  # Area of effect radius in pixels
        self.slam_cooldown = 0.0
        self.slam_cooldown_duration = 2.0  # Longer cooldown for powerful attack
        
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
        aseprite_json_path = "Assests/SwordMaster/SwordMaster.json"
        self.animation_loader = AsepriteAnimationLoader(aseprite_json_path, scale)
        self.animation_loader.load_all_animations()
        
        # Start with spawn animation
        self.start_spawn()
        
    def start_spawn(self):
        """Start the spawn animation sequence."""
        self.is_spawning = True
        self.spawn_timer = 0.0
        self.is_invulnerable = True  # Invulnerable during spawn
        self.state = "spawn"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.jump_count = 0  # Reset jump count on spawn
        
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

        # Apply physics (skip if dead, ledge grabbing, or wall holding)
        if not self.is_dead and not self.is_ledge_grabbing and not self.is_wall_holding:
            self._apply_physics(dt)
        elif self.is_wall_holding:
            # Special physics for wall sliding
            self._update_wall_slide(dt)

        # Check for ledge grab opportunity (before collision handling)
        if world_map and not self.is_dead and not self.is_spawning and not self.is_ledge_grabbing and not self.is_wall_holding and not self.is_rolling:
            if self._detect_ledge_grab(world_map, input_state):
                # Determine grab direction based on movement
                grab_direction = 1 if self.velocity_x > 0 else -1
                self._start_ledge_grab(world_map, grab_direction)

        # Check for wall hold opportunity (after ledge grab check)
        if world_map and not self.is_dead and not self.is_spawning and not self.is_ledge_grabbing and not self.is_wall_holding and not self.on_ground and not self.is_rolling:
            wall_side = self._detect_wall_grab(world_map, input_state)
            if wall_side != 0:
                self._start_wall_hold(wall_side)

        # Handle collisions if world map is provided (skip if dead or spawning)
        if world_map and not self.is_dead and not self.is_spawning:
            self._handle_collisions(world_map, dt)
        elif not self.is_dead:
            # Fallback collision (ground level)
            self._handle_basic_collision()

        # Always update roll timer and end logic, even if rolling disables other logic
        if self.is_rolling:
            self.roll_timer += dt
            if self.roll_timer >= self.roll_duration:
                self._end_roll()
            elif self.roll_timer >= (self.roll_duration + 0.2):
                self._end_roll()

        # Update animation
        self._update_animation(dt)
        
    def _handle_input(self, input_state: dict, dt: float):
        """Process player input."""
        # Handle ledge grab input separately
        if self.is_ledge_grabbing:
            self._handle_ledge_grab_input(input_state, dt)
            self.prev_input_state = input_state.copy()
            return
            
        # Handle wall hold input separately
        if self.is_wall_holding:
            self._handle_wall_hold_input(input_state, dt)
            self.prev_input_state = input_state.copy()
            return
            
        # Handle roll input separately
        if self.is_rolling:
            self._handle_roll_input(input_state, dt)
            self.prev_input_state = input_state.copy()
            return
            
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        jump = input_state.get('jump', False)
        dash = input_state.get('dash', False)
        attack = input_state.get('attack', False)
        roll = input_state.get('roll', False)
        down = input_state.get('down', False)  # For downward attack
        
        # Detect newly pressed keys (not held keys)
        prev_attack = self.prev_input_state.get('attack', False)
        prev_dash = self.prev_input_state.get('dash', False)
        prev_jump = self.prev_input_state.get('jump', False)
        prev_roll = self.prev_input_state.get('roll', False)
        attack_just_pressed = attack and not prev_attack
        dash_just_pressed = dash and not prev_dash
        jump_just_pressed = jump and not prev_jump
        roll_just_pressed = roll and not prev_roll
        
        # Update cooldowns and timers
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt
        if self.fall_attack_cooldown > 0:
            self.fall_attack_cooldown -= dt
        if self.slam_cooldown > 0:
            self.slam_cooldown -= dt
        if self.ledge_grab_timer > 0:
            self.ledge_grab_timer -= dt
            if self.ledge_grab_timer <= 0:
                self.can_ledge_grab = True
        if self.wall_grab_cooldown > 0:
            self.wall_grab_cooldown -= dt
            if self.wall_grab_cooldown <= 0:
                self.can_wall_grab = True
        if self.wall_jump_timer > 0:
            self.wall_jump_timer -= dt
        
        # Update combo window timer
        if self.combo_window_active:
            self.combo_window_timer -= dt
            if self.combo_window_timer <= 0:
                self.combo_window_active = False
                self.combo_window_timer = 0.0
        
        # Handle attack input with proper key press detection (prioritized first)
        if attack_just_pressed:
            # Reset slam potential timer when F is pressed (gives priority to regular attacks)
            self.slam_potential_timer = 0.0
            
            # Check for downward attack (S + F while airborne/falling)
            if down and not self.on_ground and self.velocity_y > 0 and not self.is_fall_attacking and not self.is_attacking and not self.is_dashing and not self.is_rolling and not self.is_slam_charging and not self.is_slam_attacking and self.fall_attack_cooldown <= 0:
                self._start_fall_attack()
            elif not self.is_attacking and not self.is_slam_charging and not self.is_slam_attacking and self.attack_cooldown <= 0:
                # Start first attack and begin combo window
                self._start_attack(1)
                self.combo_window_active = True
                self.combo_window_timer = self.combo_window_duration
            elif self.combo_window_active and self.current_attack == 1 and not self.is_slam_charging:
                # Second attack pressed during combo window - queue Slash 2
                self._queue_combo_attack()
        
        # Handle slam attack charging (only when F is held AND no attacks are active)
        elif attack and self.on_ground and not self.is_slam_charging and not self.is_slam_attacking and not self.is_attacking and not self.is_dashing and not self.is_rolling and self.slam_cooldown <= 0 and self.attack_cooldown <= 0:
            # Build up potential slam charge timer only when not in any attack state
            self.slam_potential_timer += dt
            if self.slam_potential_timer >= self.slam_charge_delay:
                # Start actual slam charging after delay
                self._start_slam_charge()
        elif not attack:
            # F released - reset potential timer and handle slam state
            if self.slam_potential_timer > 0:
                self.slam_potential_timer = 0.0
            elif self.is_slam_charging:
                # F released during slam charging
                if self.slam_charge_timer >= self.slam_charge_duration:
                    self._execute_slam_attack()
                else:
                    self._cancel_slam_charge()
        elif self.is_slam_charging and attack:
            # Continue charging
            self.slam_charge_timer += dt
            if self.slam_charge_timer >= self.slam_charge_duration:
                # Fully charged, ready to execute
                pass  # Visual feedback could be added here
        
        # Handle dash input (cannot dash during attacks)
        if dash_just_pressed and not self.is_dashing and not self.is_attacking and not self.is_slam_charging and not self.is_slam_attacking and self.dash_cooldown <= 0:
            self._start_dash()
        
        # Handle roll input (cannot roll during attacks, dash, wall/ledge states, or while already rolling)
        if roll_just_pressed and not self.is_rolling and not self.is_attacking and not self.is_dashing and not self.is_wall_holding and not self.is_ledge_grabbing and not self.is_slam_charging and not self.is_slam_attacking and self.roll_cooldown <= 0:
            # Determine roll direction (prefer current input, fallback to facing direction)
            if left and not right:
                self.roll_direction = -1
            elif right and not left:
                self.roll_direction = 1
            else:
                self.roll_direction = self.direction
            self._start_roll(self.roll_direction)
        
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
        
        # Update roll state (time based, like dash)
        if self.is_rolling:
            self.roll_timer += dt
            if self.roll_timer >= self.roll_duration:
                self._end_roll()
            # Fail-safe: force end if somehow exceeded duration + small buffer
            elif self.roll_timer >= (self.roll_duration + 0.2):
                self._end_roll()
        
        # Update fall attack state
        if self.is_fall_attacking:
            self.fall_attack_timer += dt
            if self.fall_attack_timer >= self.fall_attack_duration:
                self._end_fall_attack()
        
        # Update slam attack state
        if self.is_slam_attacking:
            self.slam_attack_timer += dt
            if self.slam_attack_timer >= self.slam_attack_duration:
                self._end_slam_attack()
        
        # Horizontal movement (modified for dash, roll, attack, and fall attack)
        if self.is_rolling:
            # Maintain constant speed in captured roll direction
            self.velocity_x = self.roll_direction * self.roll_speed
            self.direction = self.roll_direction  # Lock facing during roll
        elif self.is_dashing:
            # During dash, maintain dash speed in current direction
            self.velocity_x = self.direction * self.dash_speed
        elif self.is_fall_attacking:
            # Slight horizontal control during fall attack
            self.velocity_x = 0.0
            if left and not right:
                self.velocity_x = -self.move_speed * 0.3  # Reduced horizontal control
            elif right and not left:
                self.velocity_x = self.move_speed * 0.3
        elif self.is_slam_charging or self.is_slam_attacking:
            # No movement during slam charge or attack
            self.velocity_x = 0.0
        elif self.is_attacking:
            attack_speed_modifier = 0.1 if self.current_attack == 2 else 0.2
            self.velocity_x = 0.0
            if left and not right:
                self.velocity_x = -self.move_speed * attack_speed_modifier
            elif right and not left:
                self.velocity_x = self.move_speed * attack_speed_modifier
        else:
            self.velocity_x = 0.0
            if left and not right:
                self.velocity_x = -self.move_speed
                self.direction = -1
            elif right and not left:
                self.velocity_x = self.move_speed
                self.direction = 1
        
        # Jumping (can't jump while dashing, rolling, attacking, or fall attacking)
        if jump_just_pressed and not self.is_dashing and not self.is_rolling and not self.is_attacking and not self.is_fall_attacking and not self.is_slam_charging and not self.is_slam_attacking:
            if self.on_ground and self.jump_count == 0:
                self.velocity_y = -self.jump_speed
                self.on_ground = False
                self.jump_count = 1
            elif not self.on_ground and self.jump_count < self.max_jumps:
                self.velocity_y = -self.jump_speed
                self.jump_count += 1
            
    def _start_attack(self, attack_number: int):
        """Start an attack (1 = Slash 1, 2 = Slash 2)."""
        self.is_attacking = True
        self.attack_timer = 0.0
        self.current_attack = attack_number
        self.state = f"attack{attack_number}"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.enemies_hit_this_attack.clear()  # Clear hit tracking for new attack
        
    def _queue_combo_attack(self):
        """Queue the second attack to start immediately."""
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
        
    def _start_roll(self, direction: int):
        """Start a roll in the specified direction."""
        self.is_rolling = True
        self.roll_timer = 0.0
        self.direction = direction  # Set roll direction
        self.state = "roll"
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Enable invulnerability during most of the roll
        self.is_invulnerable = True
        self.invulnerability_timer = self.roll_invulnerability_duration
        
    def _end_roll(self):
        """End a roll."""
        if not self.is_rolling:
            return
        self.is_rolling = False
        self.roll_timer = 0.0
        self.roll_cooldown = self.roll_cooldown_duration
        # Trim remaining i-frames
        if self.invulnerability_timer > 0 and not self.is_spawning:
            self.invulnerability_timer = min(self.invulnerability_timer, 0.1)
        # Allow animation system to naturally transition next frame
        
    def _handle_roll_input(self, input_state: dict, dt: float):
        """Handle input while rolling (limited options)."""
        # During roll, player has limited control
        # Roll movement is handled in the main movement logic
        # No input changes during roll for now - could add early roll canceling later
        pass
        
    def _start_fall_attack(self):
        """Start a downward aerial attack."""
        self.is_fall_attacking = True
        self.fall_attack_timer = 0.0
        self.state = "fall_attack"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.enemies_hit_this_attack.clear()  # Clear hit tracking for new attack
        
        # Enable invulnerability during fall attack
        self.is_invulnerable = True
        self.invulnerability_timer = self.fall_attack_invulnerability_duration
        
    def _end_fall_attack(self):
        """End the fall attack."""
        self.is_fall_attacking = False
        self.fall_attack_timer = 0.0
        self.fall_attack_cooldown = self.fall_attack_cooldown_duration
        
    def _start_slam_charge(self):
        """Start charging a slam attack."""
        self.is_slam_charging = True
        self.slam_charge_timer = 0.0
        self.slam_potential_timer = 0.0  # Reset potential timer
        print("Started charging slam attack...")  # Debug output
        
    def _cancel_slam_charge(self):
        """Cancel slam charge if not held long enough."""
        self.is_slam_charging = False
        self.slam_charge_timer = 0.0
        self.slam_potential_timer = 0.0  # Reset potential timer
        print("Slam charge cancelled - not held long enough")  # Debug output
        
    def _execute_slam_attack(self):
        """Execute the charged slam attack."""
        self.is_slam_charging = False
        self.is_slam_attacking = True
        self.slam_charge_timer = 0.0
        self.slam_potential_timer = 0.0  # Reset potential timer
        self.slam_attack_timer = 0.0
        self.state = "slam_attack"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.enemies_hit_this_attack.clear()  # Clear hit tracking for new attack
        print("Executing slam attack!")  # Debug output
        
    def _end_slam_attack(self):
        """End the slam attack."""
        self.is_slam_attacking = False
        self.slam_attack_timer = 0.0
        self.slam_cooldown = self.slam_cooldown_duration
        
    def _detect_ledge_grab(self, world_map, input_state: dict) -> bool:
        """
        Detect if player should grab a ledge.
        Returns True if ledge grab should activate.
        """
        # Only check for ledge grab if conditions are met
        if not self.can_ledge_grab:
            return False
        if self.is_ledge_grabbing or self.on_ground:
            return False
        if self.is_dashing or self.is_attacking or self.is_spawning or self.is_dead or self.is_fall_attacking:
            return False
        if self.velocity_y <= 0:  # Must be falling (not jumping up)
            return False
            
        # Must have forward input to grab ledge (prevents accidental grabs)
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        
        # Check if moving toward a ledge
        check_direction = 0
        if right and self.velocity_x > 0:
            check_direction = 1
        elif left and self.velocity_x < 0:
            check_direction = -1
        else:
            return False  # Not moving forward
        
        # Define hand/chest level relative to player position
        hand_y = self.pos_y - 25  # About chest height
        hand_x = self.pos_x + (check_direction * 20)  # Reach ahead
        
        # Check for solid tile at hand level (the ledge)
        if not world_map.is_solid_at_any_layer(hand_x, hand_y):
            return False
            
        # Check that there's empty space above the ledge (clearance)
        clearance_y = hand_y - 35  # Check space above ledge
        if world_map.is_solid_at_any_layer(hand_x, clearance_y):
            return False  # Not enough clearance
            
        # Check that player's current position has empty space (not inside wall)
        if world_map.is_solid_at_any_layer(self.pos_x, self.pos_y - 15):
            return False
            
        # All conditions met - can grab ledge
        return True
    
    def _start_ledge_grab(self, world_map, direction: int):
        """Start ledge grab state."""
        self.is_ledge_grabbing = True
        self.ledge_grab_direction = direction
        
        # Calculate precise ledge position
        hand_y = self.pos_y - 25  # Chest level
        hand_x = self.pos_x + (direction * 20)  # Reach ahead
        
        # Find the exact ledge position
        tile_size = world_map.tile_size * world_map.scale
        ledge_tile_x = int(hand_x // tile_size) * tile_size
        ledge_tile_y = int(hand_y // tile_size) * tile_size
        
        # Position player relative to ledge
        if direction == 1:  # Grabbing right ledge
            self.ledge_grab_x = ledge_tile_x - 18  # Hang slightly left of tile
        else:  # Grabbing left ledge
            self.ledge_grab_x = ledge_tile_x + tile_size + 18  # Hang slightly right of tile
            
        self.ledge_grab_y = ledge_tile_y + 48  # Hang closer to ledge surface (was +25)
        
        # Snap to ledge position
        self.pos_x = self.ledge_grab_x
        self.pos_y = self.ledge_grab_y
        
        # Stop all velocity
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # Set animation state
        self.state = "ledge_grab"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.direction = direction
        
        # Reset jump count (hanging counts as landing)
        self.jump_count = 0
    
    def _handle_ledge_grab_input(self, input_state: dict, dt: float):
        """Handle input while in ledge grab state."""
        jump = input_state.get('jump', False)
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        down = input_state.get('down', False)
        
        # Detect key presses
        prev_jump = self.prev_input_state.get('jump', False)
        prev_down = self.prev_input_state.get('down', False)
        jump_just_pressed = jump and not prev_jump
        down_just_pressed = down and not prev_down
        
        # Climb up with jump/up
        if jump_just_pressed or (input_state.get('up', False) and not self.prev_input_state.get('up', False)):
            self._climb_up_from_ledge()
        # Drop down with down key
        elif down_just_pressed:
            self._drop_from_ledge()
        # Jump off ledge in opposite direction
        elif (left and self.ledge_grab_direction == 1) or (right and self.ledge_grab_direction == -1):
            self._jump_off_ledge()
    
    def _climb_up_from_ledge(self):
        """Climb up from ledge grab."""
        # Move player on top of the ledge
        self.pos_y = self.ledge_grab_y - 40  # Move up onto the platform
        
        # Player is now on ground after climbing
        self.on_ground = True
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # End ledge grab (but don't let it override our ground state)
        self.is_ledge_grabbing = False
        
        # Set proper idle state since we're on ground
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        
        # Prevent immediate re-grab
        self.can_ledge_grab = False
        self.ledge_grab_timer = 0.5  # Cooldown before can grab again
    
    def _drop_from_ledge(self):
        """Drop down from ledge grab."""
        # Give slight downward velocity to ensure drop
        self.velocity_y = 50.0
        
        # End ledge grab
        self._end_ledge_grab()
        
        # Allow immediate grab again (might want to grab lower ledge)
        self.can_ledge_grab = True
    
    def _jump_off_ledge(self):
        """Jump off ledge in opposite direction."""
        # Jump velocity
        self.velocity_y = -self.jump_speed * 0.8  # Slightly weaker than normal jump
        self.velocity_x = -self.ledge_grab_direction * self.move_speed * 1.2  # Push away from wall
        
        # Set jump count to 1 (used first jump)
        self.jump_count = 1
        
        # End ledge grab
        self._end_ledge_grab()
        
        # Prevent immediate re-grab
        self.can_ledge_grab = False
        self.ledge_grab_timer = 0.3  # Short cooldown
    
    def _end_ledge_grab(self):
        """End ledge grab state."""
        self.is_ledge_grabbing = False
        self.on_ground = False  # In air after ledge grab
        
        # Force transition to appropriate movement state
        if self.velocity_y > 0:
            self.state = "fall"
        elif self.velocity_y < 0:
            self.state = "jump"
        else:
            self.state = "idle"
            
        # Reset animation frame
        self.current_frame = 0
        self.frame_timer = 0.0
        
    def _check_wall_collision(self, world_map, side: str = 'both') -> int:
        """
        Check if player can grab wall on specified side.
        Returns: -1 for left wall, 1 for right wall, 0 for no wall
        """
        # Check both sides or specific side
        sides_to_check = []
        if side == 'both':
            sides_to_check = ['left', 'right']
        else:
            sides_to_check = [side]
        
        for check_side in sides_to_check:
            # Define check position based on side
            check_x = self.pos_x + (-12 if check_side == 'left' else 12)
            
            # Check multiple points along player's height
            check_points = [
                self.pos_y - 30,  # Upper body
                self.pos_y - 15,  # Middle body  
                self.pos_y - 5    # Lower body
            ]
            
            # If any point hits a solid tile, we found a wall
            for check_y in check_points:
                if world_map.is_solid_at_any_layer(check_x, check_y):
                    return -1 if check_side == 'left' else 1
                    
        return 0  # No wall found
    
    def _detect_wall_grab(self, world_map, input_state: dict) -> int:
        """
        Detect if player should grab a wall.
        Returns: -1 for left wall, 1 for right wall, 0 for no grab
        """
        # Only check for wall grab if conditions are met
        if not self.can_wall_grab:
            return 0
        if self.is_wall_holding or self.is_ledge_grabbing or self.on_ground:
            return 0
        if self.is_dashing or self.is_attacking or self.is_spawning or self.is_dead or self.is_fall_attacking:
            return 0
        
        # Must be moving downward or at minimal upward velocity (not at jump peak)
        if self.velocity_y < -200:  # Too high up velocity
            return 0
            
        # Must have forward input toward the wall
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        
        # Check direction of movement
        wall_side = 0
        if right and self.velocity_x > 0:
            # Moving right, check for right wall
            wall_side = self._check_wall_collision(world_map, 'right')
        elif left and self.velocity_x < 0:
            # Moving left, check for left wall
            wall_side = self._check_wall_collision(world_map, 'left')
        
        return wall_side
    
    def _start_wall_hold(self, wall_side: int):
        """Start wall hold state."""
        self.is_wall_holding = True
        self.wall_side = wall_side
        self.wall_hold_timer = 0.0
        
        # Stop all velocity when grabbing wall
        self.velocity_x = 0.0
        self.velocity_y = 0.0  # Stop upward momentum completely
        
        # Set animation state
        self.state = "wall_hold"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.direction = wall_side  # Face the wall
        
        # Reset jump count (wall grab acts like landing)
        self.jump_count = 0
        
        # Only print debug message once when starting
        if not hasattr(self, '_last_wall_grab_debug') or self._last_wall_grab_debug != wall_side:
            self._last_wall_grab_debug = wall_side
    
    def _handle_wall_hold_input(self, input_state: dict, dt: float):
        """Handle input while in wall hold state."""
        jump = input_state.get('jump', False)
        left = input_state.get('left', False)
        right = input_state.get('right', False)
        down = input_state.get('down', False)
        
        # Detect key presses
        prev_jump = self.prev_input_state.get('jump', False)
        prev_down = self.prev_input_state.get('down', False)
        jump_just_pressed = jump and not prev_jump
        down_just_pressed = down and not prev_down
        
        # Wall jump with jump key
        if jump_just_pressed:
            # Determine wall jump direction based on input
            if (left and self.wall_side == 1) or (right and self.wall_side == -1):
                # Pressing away from wall - 45° jump away
                self._wall_jump('away')
            elif (right and self.wall_side == 1) or (left and self.wall_side == -1):
                # Pressing toward wall - push out then back toward wall
                self._wall_jump('toward')
            else:
                # No horizontal input - small push away
                self._wall_jump('neutral')
        # Start wall slide with down key
        elif down_just_pressed:
            self._start_wall_slide()
        # Release wall if not holding toward it
        elif not ((left and self.wall_side == -1) or (right and self.wall_side == 1)):
            self._end_wall_hold()
    
    def _wall_jump(self, direction: str):
        """Perform wall jump in specified direction."""
        # Set wall jump timer
        self.wall_jump_timer = self.wall_jump_duration
        
        if direction == 'away':
            # 45° jump away from wall
            self.velocity_x = -self.wall_side * self.wall_jump_speed_x
            self.velocity_y = -self.wall_jump_speed_y
        elif direction == 'toward':
            # Push out, propel up, move back toward wall
            self.velocity_x = -self.wall_side * (self.wall_jump_speed_x * 0.5)
            self.velocity_y = -self.wall_jump_speed_y * 1.1
        else:  # neutral
            # Small push away
            self.velocity_x = -self.wall_side * (self.wall_jump_speed_x * 0.3)
            self.velocity_y = -self.wall_jump_speed_y * 0.9
        
        # Set jump count to 1 (used first jump)
        self.jump_count = 1
        
        # End wall hold
        self._end_wall_hold()
        
        # Prevent immediate re-grab
        self.can_wall_grab = False
        self.wall_grab_cooldown = self.wall_grab_cooldown_duration
    
    def _start_wall_slide(self):
        """Start wall sliding."""
        self.state = "wall_transition"  # Transition animation
        self.current_frame = 0
        self.frame_timer = 0.0
    
    def _update_wall_slide(self, dt: float):
        """Update wall sliding physics."""
        # Only apply sliding physics if in sliding states, not during wall_hold grace period
        if self.state in ["wall_transition", "wall_slide"]:
            # Apply wall slide gravity
            if self.velocity_y < self.wall_slide_max_speed:
                self.velocity_y += self.wall_slide_speed * dt
                if self.velocity_y > self.wall_slide_max_speed:
                    self.velocity_y = self.wall_slide_max_speed
        # During wall_hold state, maintain zero velocity (grace period)
        elif self.state == "wall_hold":
            self.velocity_y = 0.0
    
    def _end_wall_hold(self):
        """End wall hold state."""
        self.is_wall_holding = False
        self.wall_side = 0
        self.on_ground = False  # In air after wall hold
        
        # Reset debug tracking
        if hasattr(self, '_last_wall_grab_debug'):
            self._last_wall_grab_debug = None
        
        # Transition to appropriate movement state
        if self.velocity_y > 0:
            self.state = "fall"
        elif self.velocity_y < 0:
            self.state = "jump"
        else:
            self.state = "fall"  # Default to fall when leaving wall
            
        # Reset animation frame
        self.current_frame = 0
        self.frame_timer = 0.0
        
    def _update_wall_hold_state(self, dt: float):
        """Update wall hold animation state based on timer and conditions."""
        # Update wall hold timer
        self.wall_hold_timer += dt
        
        # Wall hold state machine
        if self.state == "wall_hold":
            # After grace period, start sliding
            if self.wall_hold_timer > self.wall_hold_grace_time:
                self.state = "wall_transition"
                self.current_frame = 0
                self.frame_timer = 0.0
        elif self.state == "wall_transition":
            # Check if transition animation is complete
            transition_animation = self.animation_loader.get_animation('wall_transition')
            if transition_animation and self.current_frame >= len(transition_animation['surfaces_right']) - 1:
                self.state = "wall_slide"
                self.current_frame = 0
                self.frame_timer = 0.0
        elif self.state == "wall_slide":
            # Continue sliding until released or stopped
            pass
        elif self.state == "wall_slide_stop":
            # Check if stop animation is complete, then hold
            stop_animation = self.animation_loader.get_animation('wall_slide_stop')
            if stop_animation and self.current_frame >= len(stop_animation['surfaces_right']) - 1:
                self.state = "wall_hold"
                self.current_frame = 0
                self.frame_timer = 0.0
            
    def _apply_physics(self, dt: float):
        """Apply gravity and basic physics."""
        if self.is_fall_attacking:
            # Apply enhanced gravity during fall attack for faster descent
            self.velocity_y += self.gravity * self.fall_attack_speed_multiplier * dt
        else:
            # Normal gravity
            self.velocity_y += self.gravity * dt
        
    def _handle_collisions(self, world_map, dt: float):
        """Handle collision detection and response with the world."""
        # Skip collision handling if ledge grabbing (position is locked)
        if self.is_ledge_grabbing:
            return
            
        # Check wall hold conditions if wall holding
        if self.is_wall_holding:
            # Check if still touching wall
            wall_still_exists = self._check_wall_collision(world_map, 'left' if self.wall_side == -1 else 'right')
            if wall_still_exists == 0:
                # Wall ended, release hold
                self._end_wall_hold()
                return
                
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
                self.jump_count = 0  # Reset jump count when landing
                # End wall hold if touching ground
                if self.is_wall_holding:
                    self._end_wall_hold()
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
                    self.jump_count = 0  # Reset jump count when landing
                    # End wall hold if touching ground
                    if self.is_wall_holding:
                        self._end_wall_hold()
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
            self.jump_count = 0  # Reset jump count when landing
        else:
            self.on_ground = False
            
        # Apply horizontal movement
        self.pos_x += self.velocity_x * (1/60.0)
        
    def _update_animation(self, dt: float):
        """Update animation state and frame."""
        # Handle special states that should not be overridden
        # Note: 'roll' intentionally NOT in special_states so animation can revert naturally after timing ends
        special_states = ["spawn", "hit", "death", "ledge_grab", "wall_hold", "wall_transition", "wall_slide", "wall_slide_stop"]
        
        # For spawning state
        if self.is_spawning:
            if self.state != "spawn":
                self.state = "spawn"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For death state  
        elif self.is_dead:
            if self.state != "death":
                self.state = "death"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For roll state (transient; not locked like other special states)
        elif self.is_rolling:
            if self.state != "roll":
                self.state = "roll"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For fall attack state (transient; not locked like other special states)
        elif self.is_fall_attacking:
            if self.state != "fall_attack":
                self.state = "fall_attack"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For slam attack state (transient; not locked like other special states)
        elif self.is_slam_attacking:
            if self.state != "slam_attack":
                self.state = "slam_attack"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For ledge grab state
        elif self.is_ledge_grabbing:
            if self.state != "ledge_grab":
                self.state = "ledge_grab"
                self.current_frame = 0
                self.frame_timer = 0.0
        # For wall hold state
        elif self.is_wall_holding:
            self._update_wall_hold_state(dt)
        # For hit state (during invulnerability after taking damage)
        elif self.is_invulnerable and not self.is_spawning and self.health > 0:
            if self.state != "hit":
                self.state = "hit"
                self.current_frame = 0
                self.frame_timer = 0.0
        # Normal state logic (only if not in special states)
        elif self.state not in special_states:
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
                        # For special animations that should complete once
                        if self.state in ["attack1", "attack2", "dash", "spawn", "hit", "death", "roll", "fall_attack"]:
                            if self.current_frame >= len(frames) - 1:
                                # Animation completed
                                self.current_frame = len(frames) - 1
                                
                                # Handle special animation completions
                                if self.state == "spawn":
                                    self.is_spawning = False
                                    self.is_invulnerable = False  # End spawn invulnerability
                                elif self.state == "hit":
                                    # Hit animation complete, but invulnerability may continue
                                    pass  # Let invulnerability timer handle state change
                                elif self.state == "death":
                                    # Death animation complete - stay in death state
                                    pass
                                elif self.state == "roll":
                                    # Roll animation complete - let timer handle state change
                                    pass
                                elif self.state == "fall_attack":
                                    # Fall attack animation complete - let timer handle state change
                                    pass
                            else:
                                self.current_frame += 1
                        else:
                            # Looping animations
                            self.current_frame = (self.current_frame + 1) % len(frames)
                    elif direction == "reverse":
                        self.current_frame = (self.current_frame - 1) % len(frames)
                    else:  # pingpong or other directions - default to forward for now
                        # For special animations that should complete once
                        if self.state in ["attack1", "attack2", "dash", "spawn", "hit", "death", "roll", "fall_attack"]:
                            if self.current_frame >= len(frames) - 1:
                                # Animation completed
                                self.current_frame = len(frames) - 1
                                
                                # Handle special animation completions
                                if self.state == "spawn":
                                    self.is_spawning = False
                                    self.is_invulnerable = False  # End spawn invulnerability
                                elif self.state == "hit":
                                    # Hit animation complete, but invulnerability may continue
                                    pass  # Let invulnerability timer handle state change
                                elif self.state == "death":
                                    # Death animation complete - stay in death state
                                    pass
                                elif self.state == "roll":
                                    # Roll animation complete - let timer handle state change
                                    pass
                                elif self.state == "fall_attack":
                                    # Fall attack animation complete - let timer handle state change
                                    pass
                            else:
                                self.current_frame += 1
                        else:
                            # Looping animations
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
                # If player was in hit state, transition back to normal state
                if self.state == "hit" and not self.is_dead:
                    # Reset to idle so normal animation logic can take over
                    self.state = "idle"
                    self.current_frame = 0
                    self.frame_timer = 0.0
        
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
        
        if self.health <= 0:
            self._trigger_death()
        else:
            self._trigger_hit()
        
        return True  # Damage was applied
    
    def _trigger_hit(self):
        """Handle player taking non-fatal damage."""
        self.is_invulnerable = True
        self.invulnerability_timer = 0.0
        self.state = "hit"
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
    
    def respawn(self):
        """Request respawn (to be handled by game class)."""
        self.respawn_requested = True
