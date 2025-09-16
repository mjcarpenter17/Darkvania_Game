# 🎬 Darkvania Animation System Documentation

**Complete Guide to the Modular Animation System**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Aseprite Integration](#aseprite-integration)
4. [Animation Loading Process](#animation-loading-process)
5. [Entity-Specific Loaders](#entity-specific-loaders)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Extending the System](#extending-the-system)

---

## 🔍 System Overview

The Darkvania Animation System is a modular, entity-specific animation framework built around **Aseprite** integration. It provides a robust, maintainable way to manage animations for different game entities while preventing cross-contamination between entity types.

### Key Features
- **Modular Design**: Each entity type has its own dedicated animation loader
- **Aseprite Integration**: Direct support for Aseprite JSON/PNG exports
- **Robust Fallbacks**: Multiple fallback mechanisms prevent crashes
- **Type Safety**: Clear separation prevents animation conflicts
- **Extensible**: Easy to add new entity types and animations
- **Performance Optimized**: Efficient loading and caching

### Entity Types Supported
- **Player**: Main character with complex movement and combat abilities
- **Enemies**: Various enemy types (Assassin, Archer, Wasp, etc.)
- **Interactables**: Objects the player can interact with (Chests, Doors, etc.)
- **NPCs**: Non-player characters for dialogue and story

---

## 🏗️ Architecture

The system is built with a three-tier architecture:

```
BaseAnimationLoader (Core Aseprite functionality)
    ↓
EntityAnimationLoader (Entity-specific features)
    ↓
Specific Loaders (PlayerAnimationLoader, EnemyAnimationLoader, etc.)
```

### Class Hierarchy

```python
BaseAnimationLoader
├── EntityAnimationLoader
    ├── PlayerAnimationLoader
    ├── EnemyAnimationLoader
    │   ├── AssassinAnimationLoader
    │   ├── ArcherAnimationLoader
    │   └── WaspAnimationLoader
    ├── InteractableAnimationLoader
    │   ├── ChestAnimationLoader
    │   ├── DoorAnimationLoader
    │   ├── CollectibleAnimationLoader
    │   └── SwitchAnimationLoader
    └── NPCAnimationLoader
        ├── DialogueNPCLoader
        ├── ShopNPCLoader
        ├── QuestNPCLoader
        └── AmbientNPCLoader
```

### Core Components

#### BaseAnimationLoader
- **Purpose**: Core Aseprite integration and frame management
- **Features**: JSON parsing, frame extraction, scaling, pivot handling
- **Methods**: `load()`, `_load_animation()`, `get_frame_surface()`, etc.

#### EntityAnimationLoader  
- **Purpose**: Entity-specific animation management
- **Features**: Required animations, fallback chains, validation
- **Methods**: `load_animations()`, `validate_animations()`, `_ensure_required_animations()`

#### Specific Loaders
- **Purpose**: Define animation mappings and entity-specific behavior
- **Features**: Animation name mappings, entity-specific fallbacks
- **Methods**: `load_[entity]_animations()`, entity-specific helpers

---

## 🎨 Aseprite Integration

The system is built around **Aseprite**, a professional pixel art tool that exports animation data in JSON format.

### Aseprite Workflow

1. **Create Sprite in Aseprite**
   - Design your character/object frames
   - Organize frames into animation sequences
   - Set frame durations for each frame

2. **Create Animation Tags**
   - Use Aseprite's "Tags" feature to define animations
   - Tag names become animation names in the system
   - Example tags: "Idle", "Walk", "Attack 1", "Death"

3. **Add Pivot Point (Optional)**
   - Create a "Slice" named "Pivot" to define the sprite's pivot point
   - This becomes the anchor point for positioning and rotation
   - If no pivot is defined, system uses default bottom-center

4. **Export Animation Data**
   - Export as "JSON (Array)" format
   - Include both JSON and PNG files
   - Place files in appropriate asset directories

### File Structure Example
```
Assests/
├── SwordMaster/
│   ├── SwordMaster.json    # Animation data
│   └── SwordMaster.png     # Sprite sheet
├── enemies/
│   └── assassin/
│       ├── Assassin.json
│       └── Assassin.png
└── interactables/
    └── chest/
        ├── Chest.json
        └── Chest.png
```

### JSON Format Structure

```json
{
  "frames": {
    "SwordMaster0.png": {
      "frame": {"x": 0, "y": 0, "w": 90, "h": 37},
      "duration": 100,
      "trimmed": false,
      "spriteSourceSize": {"x": 0, "y": 0, "w": 90, "h": 37},
      "sourceSize": {"w": 90, "h": 37}
    }
  },
  "meta": {
    "frameTags": [
      {
        "name": "Idle",
        "from": 0,
        "to": 8,
        "direction": "forward"
      }
    ],
    "slices": [
      {
        "name": "Pivot",
        "keys": [{"bounds": {"x": 0, "y": 0}, "pivot": {"x": 27, "y": 33}}]
      }
    ]
  }
}
```

---

## ⚙️ Animation Loading Process

Understanding how animations are loaded helps debug issues and optimize performance.

### Loading Steps

1. **Initialization**
   ```python
   loader = PlayerAnimationLoader("path/to/sprite.json", scale=2)
   ```

2. **File Loading**
   - JSON file is loaded and parsed
   - PNG sprite sheet is loaded into memory
   - Error handling for missing files

3. **Frame Parsing**
   - Individual frames are extracted from sprite sheet
   - Frame metadata (position, size, duration) is processed
   - Pivot points are calculated

4. **Animation Creation**
   - Frame tags are processed into animation sequences
   - Animations are converted to game format
   - Both left and right-facing versions are created

5. **Validation**
   - Required animations are checked
   - Fallback chains are applied for missing animations
   - System validates all essential animations exist

### Data Conversion

The system converts Aseprite data into an optimized game format:

```python
# Aseprite Format (simplified)
{
  "name": "Idle",
  "frames": [AsepriteFrame, AsepriteFrame, ...]
}

# Game Format
{
  "idle": {
    "surfaces_right": [pygame.Surface, ...],
    "surfaces_left": [pygame.Surface, ...],
    "pivots_right": [(x, y), ...],
    "pivots_left": [(x, y), ...],
    "durations": [0.1, 0.15, ...],
    "direction": "forward",
    "frame_count": 9
  }
}
```

### Scaling and Optimization

- **Automatic Scaling**: Frames are scaled by the specified factor
- **Flip Generation**: Left-facing sprites are automatically generated
- **Pivot Adjustment**: Pivot points are adjusted for scaling and flipping
- **Memory Efficiency**: Surfaces are created once and reused

---

## 🎭 Entity-Specific Loaders

Each entity type has its own dedicated loader with specific features.

### PlayerAnimationLoader

**Purpose**: Manages all player character animations including movement, combat, and abilities.

**Animation Categories**:
- **Basic Movement**: idle, walk, jump, fall, trans, dash
- **Combat**: attack1, attack2, roll, fall_attack, slam_attack  
- **Health States**: spawn, hit, death
- **Advanced Movement**: ledge_grab, wall_hold, wall_transition, wall_slide, wall_slide_stop

**Usage Example**:
```python
from src.animations import PlayerAnimationLoader

# Initialize player animations
player_loader = PlayerAnimationLoader("Assests/SwordMaster/SwordMaster.json", scale=2)
success = player_loader.load_player_animations()

if success:
    # Get specific animation
    idle_anim = player_loader.get_animation('idle')
    
    # Check capabilities
    has_combat = player_loader.has_combat_abilities()
    has_wall = player_loader.has_wall_abilities()
    
    # Get animation info
    info = player_loader.get_player_info()
```

**Fallback Chains**:
```python
FALLBACK_CHAINS = {
    'walk': ['idle'],
    'attack2': ['attack1'],
    'roll': ['dash', 'walk'],
    'wall_slide': ['wall_transition', 'fall', 'idle']
}
```

### EnemyAnimationLoader

**Purpose**: Base class for all enemy animations with enemy-specific fallbacks.

**Assassin Enemy**:
- **Animations**: idle, run, jump, fall, attack1, attack2, hit, death
- **AI Integration**: Animations match AI state machine
- **Combat Focus**: Multiple attack animations for variety

**Usage Example**:
```python
from src.animations.enemy_animation_loader import AssassinAnimationLoader

# Initialize assassin animations
assassin_loader = AssassinAnimationLoader("Assests/enemies/assassin/Assassin.json", scale=2)
success = assassin_loader.load_assassin_animations()

# Get AI-relevant animations
ai_anims = assassin_loader.get_ai_animations()
has_advanced = assassin_loader.has_advanced_attacks()
```

### InteractableAnimationLoader

**Purpose**: Manages animations for interactive objects in the game world.

**Chest Animations**:
- **States**: closed, opening, open, highlight
- **Interaction Flow**: closed → opening → open
- **Visual Feedback**: highlight when player nearby

**Usage Example**:
```python
from src.animations.interactable_animation_loader import ChestAnimationLoader

# Initialize chest animations
chest_loader = ChestAnimationLoader("Assests/interactables/chest/Chest.json", scale=2)
success = chest_loader.load_chest_animations()

# Check capabilities
has_opening = chest_loader.has_opening_animation()
```

### NPCAnimationLoader

**Purpose**: Manages animations for non-player characters.

**Dialogue NPC**:
- **Social Animations**: idle, talk, listen, greet, goodbye
- **Expressions**: nod, shake_head, think
- **Conversation Support**: Smooth dialogue interactions

**Usage Example**:
```python
from src.animations.npc_animation_loader import DialogueNPCLoader

# Initialize NPC animations
npc_loader = DialogueNPCLoader("Assests/npcs/villager/Villager.json", scale=2)
success = npc_loader.load_dialogue_animations()

# Get conversation animations
conv_anims = npc_loader.get_conversation_animations()
has_expressions = npc_loader.has_expression_animations()
```

---

## 📝 Usage Examples

### Basic Entity Setup

```python
# Player Setup
from src.animations import PlayerAnimationLoader

class Player:
    def __init__(self, x, y, scale=2):
        self.pos_x = x
        self.pos_y = y
        
        # Load animations
        json_path = "Assests/SwordMaster/SwordMaster.json"
        self.animation_loader = PlayerAnimationLoader(json_path, scale)
        
        if not self.animation_loader.load_player_animations():
            print("Warning: Player animations failed to load")
            
        # Animation state
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.facing_right = True
```

### Animation Playback

```python
def update_animation(self, dt):
    """Update animation frame based on time."""
    # Get frame duration for current frame
    duration = self.animation_loader.get_frame_duration(self.state, self.current_frame)
    
    self.frame_timer += dt
    
    if self.frame_timer >= duration:
        self.frame_timer = 0.0
        frame_count = self.animation_loader.get_frame_count(self.state)
        
        # Advance frame
        self.current_frame = (self.current_frame + 1) % frame_count

def render(self, screen, camera_x, camera_y):
    """Render the entity with current animation frame."""
    # Get current frame surface
    surface = self.animation_loader.get_frame_surface(
        self.state, self.current_frame, self.facing_right
    )
    
    if surface:
        # Get pivot point for proper positioning
        pivot = self.animation_loader.get_frame_pivot(
            self.state, self.current_frame, self.facing_right
        )
        
        if pivot:
            # Calculate render position using pivot
            render_x = self.pos_x - camera_x - pivot[0]
            render_y = self.pos_y - camera_y - pivot[1]
            screen.blit(surface, (render_x, render_y))
```

### Factory Pattern Usage

```python
# Enemy Factory
from src.animations.enemy_animation_loader import create_enemy_loader

def create_enemy(enemy_type, x, y, scale=2):
    """Factory function to create enemies with appropriate animations."""
    
    # Determine JSON path based on enemy type
    json_paths = {
        'assassin': "Assests/enemies/assassin/Assassin.json",
        'archer': "Assests/enemies/archer/Archer.json",
        'wasp': "Assests/enemies/wasp/Wasp.json"
    }
    
    json_path = json_paths.get(enemy_type)
    if not json_path:
        raise ValueError(f"Unknown enemy type: {enemy_type}")
    
    # Create appropriate loader
    loader = create_enemy_loader(enemy_type, json_path, scale)
    
    # Load animations based on enemy type
    if enemy_type == 'assassin':
        success = loader.load_assassin_animations()
    elif enemy_type == 'archer':
        success = loader.load_archer_animations()
    elif enemy_type == 'wasp':
        success = loader.load_wasp_animations()
    
    return loader if success else None
```

### Animation State Management

```python
def change_state(self, new_state):
    """Change animation state with validation."""
    if self.animation_loader.has_animation(new_state):
        if self.state != new_state:
            self.state = new_state
            self.current_frame = 0
            self.frame_timer = 0.0
    else:
        print(f"Warning: Animation '{new_state}' not available")
        
def play_one_shot_animation(self, animation_name, callback=None):
    """Play an animation once and optionally call callback when done."""
    if self.animation_loader.has_animation(animation_name):
        self.temp_state = animation_name
        self.temp_frame = 0
        self.temp_callback = callback
        self.playing_temp_animation = True
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Animation Not Loading
**Symptoms**: Animation appears as placeholder or missing
**Causes**:
- Incorrect file path
- Missing JSON or PNG file
- Animation name mismatch

**Solutions**:
```python
# Check if files exist
import os
json_path = "Assests/SwordMaster/SwordMaster.json"
png_path = "Assests/SwordMaster/SwordMaster.png"

if not os.path.exists(json_path):
    print(f"JSON file missing: {json_path}")
if not os.path.exists(png_path):
    print(f"PNG file missing: {png_path}")

# Check animation availability
loader = PlayerAnimationLoader(json_path)
loader.load_player_animations()
print(f"Available animations: {loader.list_animations()}")
```

#### 2. Incorrect Animation Names
**Symptoms**: Specific animations not loading, fallbacks being used
**Causes**: Mismatch between code expectations and Aseprite tag names

**Solutions**:
```python
# Debug animation mappings
class DebugPlayerLoader(PlayerAnimationLoader):
    def _load_animation(self, state_name, aseprite_name):
        print(f"Loading: {state_name} -> {aseprite_name}")
        success = super()._load_animation(state_name, aseprite_name)
        if not success:
            available = self.aseprite_loader.list_animations()
            print(f"Available in Aseprite: {available}")
        return success
```

#### 3. Pivot Point Issues
**Symptoms**: Sprite appears offset or positioned incorrectly
**Causes**: Missing or incorrect pivot point in Aseprite

**Solutions**:
```python
# Check pivot point
loader = PlayerAnimationLoader(json_path)
loader.load_player_animations()
print(f"Pivot point: {loader.pivot_point}")

# Manual pivot override if needed
loader.pivot_point = (custom_x, custom_y)
```

#### 4. Performance Issues
**Symptoms**: Game runs slowly during animation loading
**Causes**: Large sprite sheets, excessive scaling, frequent reloading

**Solutions**:
```python
# Profile loading time
import time

start_time = time.time()
loader = PlayerAnimationLoader(json_path, scale=2)
success = loader.load_player_animations()
load_time = time.time() - start_time

print(f"Loading took {load_time:.3f} seconds")

# Use appropriate scaling
# Scale=1 for pixel-perfect, Scale=2 for most games, Scale=4+ for large displays
loader = PlayerAnimationLoader(json_path, scale=2)  # Good balance
```

### Debug Output Interpretation

```python
# Successful loading output
"""
Found pivot point at (27, 33)
Loaded 153 frames and 28 animations
Found pivot point at (54, 66)
Loaded animation 'idle' with 9 frames
Loaded animation 'walk' with 8 frames
...
Player: Loaded 19/19 animations
Player animation system loaded successfully:
  - 19 animations loaded
  - Pivot point: (54, 66)
  - Scale: 2x
Player: All required animations present
  - All required animations validated ✓
"""

# Problem indicators
"""
Warning: Animation 'attack3' not found in Aseprite data
Player: Failed to load animation 'attack3' -> 'Attack 3'
Player: Using 'attack1' as fallback for 'attack3'
Player: Missing required animations: ['critical_animation']
"""
```

---

## 💡 Best Practices

### 1. Animation Organization

**Aseprite Tags Naming**:
- Use consistent naming conventions
- Avoid spaces if possible (use underscores)
- Group related animations with prefixes
- Examples: "Idle", "Walk", "Attack_1", "Attack_2"

**File Organization**:
```
Assests/
├── player/           # Player sprites
├── enemies/          # Enemy sprites by type
│   ├── assassin/
│   ├── archer/
│   └── wasp/
├── interactables/    # Interactive objects
│   ├── chests/
│   └── doors/
└── npcs/            # Non-player characters
    ├── villagers/
    └── merchants/
```

### 2. Performance Optimization

**Efficient Loading**:
```python
# Load animations once, reuse loader instance
class PlayerManager:
    def __init__(self):
        self.animation_loader = PlayerAnimationLoader(json_path, scale=2)
        self.animation_loader.load_player_animations()
    
    def create_player(self, x, y):
        # Reuse the same loader for multiple player instances
        player = Player(x, y)
        player.animation_loader = self.animation_loader
        return player
```

**Memory Management**:
```python
# Use appropriate scaling
scale = 1    # Pixel-perfect, minimal memory
scale = 2    # Good balance for most games
scale = 4    # High resolution displays only

# Consider animation complexity
# Simple objects: fewer frames, longer durations
# Complex characters: more frames, shorter durations
```

### 3. Error Handling

**Graceful Degradation**:
```python
def safe_animation_load(json_path, scale=2):
    """Load animations with comprehensive error handling."""
    try:
        loader = PlayerAnimationLoader(json_path, scale)
        if loader.load_player_animations():
            if loader.validate_animations():
                return loader
            else:
                print("Warning: Some required animations missing")
                return loader  # Still usable with fallbacks
        else:
            print("Error: Failed to load any animations")
            return None
    except Exception as e:
        print(f"Critical error loading animations: {e}")
        return None
```

**Fallback Strategies**:
```python
# Define comprehensive fallback chains
FALLBACK_CHAINS = {
    'special_attack': ['attack2', 'attack1', 'idle'],
    'hurt': ['hit', 'idle'],
    'victory': ['idle'],
    'confused': ['think', 'idle']
}
```

### 4. Testing and Validation

**Animation Testing**:
```python
def test_all_animations(loader):
    """Test that all animations can be played."""
    for anim_name in loader.list_animations():
        frame_count = loader.get_frame_count(anim_name)
        print(f"Testing {anim_name}: {frame_count} frames")
        
        for frame_idx in range(frame_count):
            surface = loader.get_frame_surface(anim_name, frame_idx, True)
            pivot = loader.get_frame_pivot(anim_name, frame_idx, True)
            duration = loader.get_frame_duration(anim_name, frame_idx)
            
            assert surface is not None, f"Frame {frame_idx} missing"
            assert pivot is not None, f"Pivot {frame_idx} missing"
            assert duration > 0, f"Invalid duration {frame_idx}"
        
        print(f"  ✓ {anim_name} validated")
```

---

## 🚀 Extending the System

### Adding New Entity Types

1. **Create New Loader Class**:
```python
from src.animations.entity_animation_loader import EntityAnimationLoader

class VehicleAnimationLoader(EntityAnimationLoader):
    """Animation loader for vehicles."""
    
    VEHICLE_ANIMATIONS = {
        'idle': 'Idle',
        'moving': 'Moving',
        'turning': 'Turning',
        'damaged': 'Damaged'
    }
    
    REQUIRED_ANIMATIONS = ['idle', 'moving']
    
    def __init__(self, json_path, scale=2):
        super().__init__(json_path, scale, entity_type="Vehicle")
        self.set_required_animations(self.REQUIRED_ANIMATIONS)
        
    def load_vehicle_animations(self):
        return self.load_animations(self.VEHICLE_ANIMATIONS)
```

2. **Update Main Module**:
```python
# Add to src/animations/__init__.py
from .vehicle_animation_loader import VehicleAnimationLoader

__all__ = [
    # ... existing exports
    'VehicleAnimationLoader'
]
```

### Adding New Animation Features

1. **Extended Animation Data**:
```python
class AdvancedAnimationLoader(BaseAnimationLoader):
    def _load_animation(self, state_name, aseprite_name):
        # Call parent method
        success = super()._load_animation(state_name, aseprite_name)
        
        if success:
            # Add custom features
            anim_data = self.animations[state_name]
            anim_data['loop_count'] = self._get_loop_count(aseprite_name)
            anim_data['sound_events'] = self._get_sound_events(aseprite_name)
            anim_data['effect_triggers'] = self._get_effect_triggers(aseprite_name)
        
        return success
```

2. **Custom Animation Behaviors**:
```python
class SmartAnimationLoader(EntityAnimationLoader):
    def get_contextual_animation(self, base_state, context):
        """Get animation based on context."""
        # Try context-specific version first
        contextual_name = f"{base_state}_{context}"
        if self.has_animation(contextual_name):
            return self.get_animation(contextual_name)
        
        # Fall back to base animation
        return self.get_animation(base_state)
```

### Performance Enhancements

1. **Animation Caching**:
```python
class CachedAnimationLoader(BaseAnimationLoader):
    def __init__(self, json_path, scale=2):
        super().__init__(json_path, scale)
        self._surface_cache = {}
        
    def get_frame_surface(self, animation_name, frame_index, facing_right):
        # Create cache key
        cache_key = (animation_name, frame_index, facing_right)
        
        if cache_key not in self._surface_cache:
            surface = super().get_frame_surface(animation_name, frame_index, facing_right)
            self._surface_cache[cache_key] = surface
            
        return self._surface_cache[cache_key]
```

2. **Lazy Loading**:
```python
class LazyAnimationLoader(EntityAnimationLoader):
    def load_animations(self, animation_mappings):
        # Store mappings but don't load until needed
        self._pending_animations = animation_mappings
        return True
        
    def get_animation(self, name):
        if name not in self.animations and name in self._pending_animations:
            # Load animation on demand
            aseprite_name = self._pending_animations[name]
            self._load_animation(name, aseprite_name)
            
        return super().get_animation(name)
```

---

## 📊 System Performance Metrics

### Typical Loading Times
- **Player** (19 animations, 153 frames): ~0.1-0.3 seconds
- **Assassin Enemy** (8 animations, 63 frames): ~0.05-0.15 seconds
- **Simple Interactable** (3 animations, 10 frames): ~0.01-0.05 seconds

### Memory Usage
- **Per Frame** (32x32, scale=2): ~8KB
- **Player Complete** (153 frames): ~1.2MB
- **Enemy Complete** (63 frames): ~0.5MB

### Optimization Targets
- **Loading Time**: < 0.5 seconds per entity
- **Memory Usage**: < 10MB total for all animations
- **Frame Rate Impact**: < 1ms per entity render

---

## 🔗 Related Documentation

- [Game Progress Status Report](Game_Progress_Status_Report.md) - Overall game development status
- [Developer Quick Reference](Developer_Quick_Reference.md) - Quick development guide
- [COMPREHENSIVE_DEVELOPMENT_TASKLIST](COMPREHENSIVE_DEVELOPMENT_TASKLIST.md) - Development roadmap

---

*This documentation covers the complete Darkvania Animation System. For questions or issues, refer to the troubleshooting section or check the related documentation files.*