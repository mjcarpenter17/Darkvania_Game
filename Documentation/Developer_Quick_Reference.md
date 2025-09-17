# 🛠️ Developer Quick Reference - Darkvania Game

**Quick Start Guide for New Developers**

---

## 🚀 Immediate Setup

```bash
# Clone and setup
git clone https://github.com/mjcarpenter17/Darkvania_Game.git
cd Darkvania_Game

# Environment setup (Windows)
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the game
python main.py
```

---

## 📁 Critical Files Overview

### Core Game Logic
```
src/game/
├── player.py      # Player character (607 lines) - Movement, combat, health
├── enemy.py       # Enemy AI system (420+ lines) - Assassin AI with 4-phase behavior
├── interactables.py # Interactive objects (300+ lines) - Chest system, E key interaction
├── collectible.py # Collectible items (200+ lines) - Bandage health items
└── game.py        # Main coordinator (600+ lines) - System integration
```

### Engine Systems
```
src/engine/
├── world.py       # Tile-based world with collision detection + object spawning
└── camera.py      # Follow camera with smooth tracking
```

### Animation Framework
```
src/animations/
├── base_animation_loader.py         # Core animation framework (326 lines)
├── entity_animation_loader.py      # Entity-specific loaders (177 lines) 
├── interactable_animation_loader.py # Interactable loaders (315 lines)
└── player/                          # Player-specific animations

src/utils/
└── aseprite_loader.py              # Aseprite JSON parsing (186 lines)
```

---

## 🎮 System Quick Reference

### Player System (`src/game/player.py`)
```python
# Key Properties
health: int = 2                    # Player HP
is_attacking: bool                 # Combat state
is_invulnerable: bool             # Damage protection
state: str                        # Animation state

# Key Methods
take_damage(damage: int)          # Apply damage with hit animation
_trigger_hit()                    # Non-fatal damage reaction
_trigger_death()                  # Death animation and state
respawn()                         # Request level restart
```

### Enemy AI (`src/game/enemy.py`)
```python
# AI State Machine
ai_state: str                     # "patrol", "idle", "hit", "death"
health: int = 2                   # Enemy HP
move_speed: float = 80.0          # Patrol speed

# Key Methods
take_damage(damage: int)          # Player attack handling
_update_patrol_ai(dt, world_map)  # Movement and edge detection
_trigger_death()                  # Death sequence
```

### Animation System (`src/utils/aseprite_loader.py`)
```python
# Key Features
animations: Dict                  # Loaded animation data
pivot_point: Tuple               # Sprite pivot for flipping

# Key Methods
load()                           # Load from Aseprite JSON
get_animation(name: str)         # Get animation data
get_frame_surface(frame)         # Extract frame surface from spritesheet
```

### Interactable System (`src/game/interactables.py`)
```python
# Base Interactable Class
x, y: int                        # World position
active: bool                     # Can interact
interactable: bool              # Interaction enabled

# Key Methods
is_player_nearby(player_x, player_y) # Proximity detection (64px range)
interact(player) -> bool         # Handle E key interaction
update(dt: float)               # Animation and state updates
render(screen, camera_x, camera_y) # Draw with camera offset

# Chest System
state: str                      # "closed", "opening", "opened"
current_animation: str          # Animation name ("idle", "opening", "used")
waiting_for_used_transition: bool # Timer-based state management
```

### Collectible System (`src/game/collectible.py`)
```python
# BandageCollectible Class
floating_height: float = 32.0   # Pixels above ground
floating_timer: float          # Sine wave animation
health_value: int = 25         # Health restoration amount

# Key Methods
update(dt: float)              # Floating animation update
check_collision(player) -> bool # Player pickup detection
apply_effect(player)           # Health restoration
```

---

## 🔧 Common Tasks

### Adding New Animations
1. **Export from Aseprite**: JSON + PNG format with 0-based frameTags
2. **Update animation loader**: Add animation name mapping
3. **Integrate with game object**: Update state machine
4. **Test frame bounds**: Verify frame count matches expected length

### Creating New Enemy Types
1. **Inherit from Enemy**: `class NewEnemy(Enemy):`
2. **Override AI methods**: `_update_patrol_ai()`, `_update_idle_ai()`
3. **Configure animations**: Update animation mapping
4. **Add to game spawning**: Update `game.py` enemy creation

### Adding New Interactables
1. **Inherit from Interactable**: `class NewObject(Interactable):`
2. **Define animation states**: Create loader with state mapping
3. **Implement interaction logic**: Override `interact()` method
4. **Add to world spawning**: Update `world.py` object detection
5. **Add to map editor**: Include object type with unique color

### Creating New Collectibles
1. **Inherit from appropriate base**: Use collectible patterns
2. **Define floating behavior**: Override `update()` for animation
3. **Implement effect**: Override `apply_effect()` for player impact
4. **Add spawn detection**: Update world object parsing

### Modifying Player Abilities
1. **Add properties**: New state variables in `__init__()`
2. **Update input handling**: Modify `_handle_input()`
3. **Add animations**: Include in animation state machine
4. **Update UI**: Modify health/status display

---

## 🎯 Key Game Values

### Combat Balance
```python
# Player
PLAYER_HEALTH = 2                # Total HP
PLAYER_DAMAGE = 1               # Damage per attack
INVULNERABILITY_TIME = 1.0      # Seconds after taking damage

# Enemy  
ENEMY_HEALTH = 2                # Assassin HP
ENEMY_DAMAGE = 1               # Damage to player
HIT_STUN_TIME = 0.3            # Seconds stunned when hit
```

### Movement Speeds
```python
PLAYER_MOVE_SPEED = 160.0       # Horizontal movement (px/s)
PLAYER_JUMP_SPEED = 700.0       # Jump velocity (px/s)
GRAVITY = 1400.0                # Falling acceleration (px/s²)

ENEMY_MOVE_SPEED = 80.0         # Patrol speed (px/s)
```

### Animation Timings
```python
SPAWN_DURATION = 1.0            # Spawn animation + invulnerability
HIT_ANIMATION_DURATION = 0.2    # Hit reaction time
DEATH_ANIMATION_DURATION = 0.8  # Death sequence time
```

---

## 🐛 Common Issues & Solutions

### Animation Not Playing
- **Check**: Animation name in Aseprite JSON
- **Verify**: State machine transition logic
- **Debug**: Print current animation state

### Collision Detection Problems
- **Check**: Attack box timing with animation frames
- **Verify**: Collision layer in world map
- **Debug**: Enable collision visualization

### Enemy AI Stuck
- **Check**: Edge detection lookahead distance
- **Verify**: Wall collision detection
- **Debug**: Print AI state transitions

### Performance Issues
- **Check**: Enemy count (reverse iteration for removal)
- **Verify**: Animation frame caching
- **Debug**: Profile frame rate and timing

---

## � CRITICAL Animation Issues & Fixes

### Frame Index Mapping Bug (CRITICAL)
**Issue**: Aseprite loader used 1-based indexing while frameTags use 0-based
```python
# WRONG - causes animations to load with 0 frames
self.frame_index_map[index + 1] = name

# CORRECT - proper 0-based mapping
self.frame_index_map[index] = name
```
**Location**: `src/utils/aseprite_loader.py` - `_parse_frames()` method
**Symptom**: Animations show 0 frames, fallback colored rectangles appear

### Animation Frame Bounds Bug (CRITICAL)
**Issue**: Frame increment before bounds checking causes out-of-range errors
```python
# WRONG - causes "Frame index X out of range" errors
self.current_frame += 1
if self.current_frame >= frame_count:
    handle_completion()

# CORRECT - check bounds before incrementing
if self.current_frame + 1 >= frame_count:
    handle_completion()
else:
    self.current_frame += 1
```
**Symptom**: Gold/colored squares instead of sprites, console errors

### Pivot Point Override Issue
**Issue**: Default pivots can mask proper Aseprite pivot data
```python
# Check if pivot exists in JSON before applying defaults
if self.pivot_point == (0, 0):
    # Only then apply calculated default
    self.pivot_point = (calculated_default_x, calculated_default_y)
```
**Symptom**: Sprites positioned incorrectly, appearing "in ground"

---

## �📋 Testing Checklist

### Player Systems
- [ ] Movement in all directions
- [ ] Jump and fall physics  
- [ ] Attack combo (Slash 1 → Slash 2)
- [ ] Health loss and recovery
- [ ] Death and respawn cycle
- [ ] Spawn animation and protection

### Enemy Systems
- [ ] Patrol movement with edge detection
- [ ] Wall collision and direction change
- [ ] Random idle periods
- [ ] Hit reactions and invulnerability
- [ ] Death animation and removal
- [ ] Multiple enemy management

### Interactable Systems
- [ ] Chest spawns with proper idle animation
- [ ] E key interaction within 64px range  
- [ ] Opening animation plays completely
- [ ] 2-second delay before "used" state
- [ ] Collectibles float and restore health
- [ ] Map editor chest object placement

### Integration
- [ ] Player attacks hit enemies
- [ ] Enemy collisions damage player  
- [ ] UI updates in real-time
- [ ] Level restart preserves all systems
- [ ] Camera follows player smoothly

---

## 💡 Development Tips

### Code Organization
- **Keep state machines simple**: Clear transitions, minimal nesting
- **Use composition**: Separate movement, combat, and animation concerns
- **Document timing values**: Game feel depends on precise timing

### Animation Integration
- **State priority**: Special states (spawn/hit/death) override movement
- **Frame timing**: Use Aseprite's duration data for smooth playback
- **Pivot points**: Critical for proper sprite flipping

### AI Development
- **Start simple**: Basic movement, then add complexity
- **Test edge cases**: Platform edges, wall corners, multiple enemies
- **Balance carefully**: Player should feel challenged but fair

### Performance
- **Profile early**: Monitor frame rate during development
- **Optimize collision**: Only check when necessary
- **Manage memory**: Clean up removed objects

---

## 📞 Getting Help

### Documentation
- **`Documentation/`**: Comprehensive system documentation
- **Code comments**: Inline explanations for complex logic
- **Commit history**: Development progression and reasoning

### Testing Tools
- **`python main.py`**: Full game testing
- **`python viewer.py`**: Animation frame inspection
- **Debug mode**: Collision visualization in game

### Common Workflows
1. **Feature addition**: Document → Implement → Test → Integrate
2. **Bug fixing**: Reproduce → Debug → Fix → Test → Validate
3. **Optimization**: Profile → Identify → Optimize → Verify

---

*This quick reference covers 90% of common development tasks. For detailed implementation guidance, see the full documentation in `Documentation/Game_Progress_Status_Report.md`.*