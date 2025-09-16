# 🔧 Animation System API Reference

**Complete API Documentation for the Darkvania Animation System**

---

## 📋 Table of Contents

1. [BaseAnimationLoader](#baseanimationloader)
2. [EntityAnimationLoader](#entityanimationloader)
3. [PlayerAnimationLoader](#playeranimationloader)
4. [EnemyAnimationLoader](#enemyanimationloader)
5. [InteractableAnimationLoader](#interactableanimationloader)
6. [NPCAnimationLoader](#npcanimationloader)
7. [Factory Functions](#factory-functions)
8. [Data Structures](#data-structures)
9. [Constants and Enums](#constants-and-enums)

---

## 🏗️ BaseAnimationLoader

Core animation loading functionality with Aseprite integration.

### Constructor

```python
BaseAnimationLoader(json_path: str, scale: int = 2)
```

**Parameters**:
- `json_path` (str): Path to Aseprite JSON file
- `scale` (int): Scaling factor for animation frames (default: 2)

**Raises**:
- `FileNotFoundError`: If JSON or PNG file doesn't exist
- `ValueError`: If scale is not positive

### Core Methods

#### `load() -> bool`
Load the Aseprite animation data.

**Returns**: `bool` - True if successful, False otherwise

**Example**:
```python
loader = BaseAnimationLoader("path/to/sprite.json", scale=2)
if loader.load():
    print("Animation data loaded successfully")
```

#### `get_animation(name: str) -> Dict[str, Any] | None`
Get animation data by name.

**Parameters**:
- `name` (str): Animation name

**Returns**: Animation dictionary or None if not found

**Example**:
```python
idle_anim = loader.get_animation('idle')
if idle_anim:
    frame_count = idle_anim['frame_count']
    surfaces = idle_anim['surfaces_right']
```

#### `has_animation(name: str) -> bool`
Check if animation exists.

**Parameters**:
- `name` (str): Animation name to check

**Returns**: `bool` - True if animation exists

#### `list_animations() -> List[str]`
Get list of all available animations.

**Returns**: List of animation names

#### `get_frame_surface(animation_name: str, frame_index: int, facing_right: bool = True) -> pygame.Surface | None`
Get specific animation frame surface.

**Parameters**:
- `animation_name` (str): Name of animation
- `frame_index` (int): Frame index (0-based)
- `facing_right` (bool): Direction facing (default: True)

**Returns**: Pygame surface or None if not found

#### `get_frame_pivot(animation_name: str, frame_index: int, facing_right: bool = True) -> Tuple[int, int] | None`
Get pivot point for specific frame.

**Parameters**:
- `animation_name` (str): Name of animation
- `frame_index` (int): Frame index (0-based)  
- `facing_right` (bool): Direction facing (default: True)

**Returns**: (x, y) pivot coordinates or None

#### `get_frame_duration(animation_name: str, frame_index: int) -> float`
Get duration of specific frame in seconds.

**Parameters**:
- `animation_name` (str): Name of animation
- `frame_index` (int): Frame index (0-based)

**Returns**: Duration in seconds

#### `get_frame_count(animation_name: str) -> int`
Get total frame count for animation.

**Parameters**:
- `animation_name` (str): Name of animation

**Returns**: Number of frames (0 if animation not found)

### Properties

#### `pivot_point: Tuple[int, int] | None`
The base pivot point from Aseprite data.

#### `animations: Dict[str, Dict[str, Any]]`
Dictionary containing all loaded animation data.

#### `aseprite_loader: AsepriteLoader`
The underlying Aseprite loader instance.

### Protected Methods

#### `_load_animation(state_name: str, aseprite_name: str) -> bool`
Load a specific animation from Aseprite data.

**Parameters**:
- `state_name` (str): Game state name
- `aseprite_name` (str): Aseprite animation tag name

**Returns**: `bool` - True if successful

---

## 🎭 EntityAnimationLoader

Base class for entity-specific animation management.

### Constructor

```python
EntityAnimationLoader(json_path: str, scale: int = 2, entity_type: str = "Entity")
```

**Parameters**:
- `json_path` (str): Path to Aseprite JSON file
- `scale` (int): Scaling factor (default: 2)
- `entity_type` (str): Type of entity for logging (default: "Entity")

### Core Methods

#### `load_animations(animation_mappings: Dict[str, str]) -> bool`
Load animations using entity-specific mappings.

**Parameters**:
- `animation_mappings` (Dict[str, str]): Mapping of game states to Aseprite names

**Returns**: `bool` - True if successful

**Example**:
```python
mappings = {
    'idle': 'Idle',
    'walk': 'Walk',
    'attack': 'Attack'
}
success = loader.load_animations(mappings)
```

#### `validate_animations() -> bool`
Validate that all required animations are present.

**Returns**: `bool` - True if all required animations exist

#### `set_required_animations(required: List[str]) -> None`
Set the list of required animations for this entity.

**Parameters**:
- `required` (List[str]): List of required animation names

#### `add_fallback_chain(animation: str, fallbacks: List[str]) -> None`
Add fallback chain for an animation.

**Parameters**:
- `animation` (str): Animation name
- `fallbacks` (List[str]): List of fallback animations in order

**Example**:
```python
loader.add_fallback_chain('special_attack', ['attack2', 'attack1', 'idle'])
```

#### `get_entity_info() -> Dict[str, Any]`
Get comprehensive information about the entity's animations.

**Returns**: Dictionary with entity information

### Protected Methods

#### `_ensure_required_animations() -> None`
Ensure required animations exist using fallback chains.

#### `_apply_fallback_chain(animation_name: str) -> bool`
Apply fallback chain for missing animation.

**Parameters**:
- `animation_name` (str): Missing animation name

**Returns**: `bool` - True if fallback applied successfully

---

## 🎮 PlayerAnimationLoader

Specialized loader for player character animations.

### Constructor

```python
PlayerAnimationLoader(json_path: str, scale: int = 2)
```

### Constants

```python
PLAYER_ANIMATIONS = {
    'idle': 'Idle',
    'walk': 'Walk',
    'jump': 'Jump',
    'fall': 'Fall',
    'trans': 'trans',
    'attack1': 'Attack 1',
    'attack2': 'Attack 2',
    'roll': 'Roll',
    'hit': 'Hit',
    'death': 'Death',
    'spawn': 'Spawn',
    'dash': 'Dash',
    'fall_attack': 'Fall Attack',
    'slam_attack': 'Slam Attack',
    'ledge_grab': 'Ledge Grab',
    'wall_hold': 'Wall Hold',
    'wall_transition': 'Wall transition',
    'wall_slide': 'Wall Slide',
    'wall_slide_stop': 'Wall Slide Stop',
    'wall_jump': 'Wall Jump',
    'wall_climb': 'Wall Climb',
    'wall_run': 'Wall Run',
    'slide': 'Slide',
    'crouch': 'Crouch',
    'crouch_walk': 'Crouch Walk'
}

REQUIRED_ANIMATIONS = ['idle', 'walk', 'jump', 'fall', 'attack1', 'hit', 'death']

FALLBACK_CHAINS = {
    'walk': ['idle'],
    'attack2': ['attack1'],
    'roll': ['dash', 'walk'],
    'fall_attack': ['attack1'],
    'slam_attack': ['attack1'],
    'wall_slide': ['wall_transition', 'fall', 'idle'],
    'wall_slide_stop': ['wall_slide', 'idle'],
    'wall_jump': ['jump'],
    'wall_climb': ['wall_hold', 'idle'],
    'wall_run': ['wall_hold', 'walk'],
    'slide': ['crouch', 'idle'],
    'crouch_walk': ['crouch', 'walk']
}
```

### Methods

#### `load_player_animations() -> bool`
Load all player animations with validation.

**Returns**: `bool` - True if successful

#### `has_combat_abilities() -> bool`
Check if player has combat animation capabilities.

**Returns**: `bool` - True if combat animations available

#### `has_wall_abilities() -> bool`
Check if player has wall interaction capabilities.

**Returns**: `bool` - True if wall animations available

#### `has_advanced_movement() -> bool`
Check if player has advanced movement capabilities.

**Returns**: `bool` - True if advanced animations available

#### `get_player_info() -> Dict[str, Any]`
Get comprehensive player animation information.

**Returns**: Dictionary with player-specific information

**Example Return**:
```python
{
    'entity_type': 'Player',
    'total_animations': 19,
    'required_animations': 7,
    'has_combat': True,
    'has_wall_abilities': True,
    'has_advanced_movement': True,
    'pivot_point': (54, 66),
    'scale': 2
}
```

---

## 👹 EnemyAnimationLoader

Base loader for enemy animations with multiple enemy type support.

### AssassinAnimationLoader

#### Constructor

```python
AssassinAnimationLoader(json_path: str, scale: int = 2)
```

#### Constants

```python
ASSASSIN_ANIMATIONS = {
    'idle': 'Idle',
    'run': 'Run',
    'jump': 'Jump',
    'fall': 'Fall',
    'attack1': 'Attack 1',
    'attack2': 'Attack 2',
    'hit': 'Hit',
    'death': 'Death',
    'stealth': 'Stealth'
}

REQUIRED_ANIMATIONS = ['idle', 'run', 'attack1', 'hit', 'death']

FALLBACK_CHAINS = {
    'run': ['idle'],
    'attack2': ['attack1'],
    'stealth': ['idle'],
    'jump': ['idle'],
    'fall': ['idle']
}
```

#### Methods

#### `load_assassin_animations() -> bool`
Load assassin-specific animations.

#### `has_stealth_abilities() -> bool`
Check if assassin has stealth capabilities.

#### `has_advanced_attacks() -> bool`
Check if assassin has multiple attack animations.

#### `get_ai_animations() -> Dict[str, str]`
Get animations relevant for AI state machine.

### Factory Function

#### `create_enemy_loader(enemy_type: str, json_path: str, scale: int = 2) -> EnemyAnimationLoader`
Create appropriate enemy loader based on type.

**Parameters**:
- `enemy_type` (str): Type of enemy ('assassin', 'archer', 'wasp')
- `json_path` (str): Path to animation JSON
- `scale` (int): Scaling factor

**Returns**: Appropriate enemy loader instance

**Example**:
```python
assassin_loader = create_enemy_loader('assassin', 'path/to/assassin.json', scale=2)
archer_loader = create_enemy_loader('archer', 'path/to/archer.json', scale=2)
```

---

## 📦 InteractableAnimationLoader

Loader for interactive objects in the game world.

### ChestAnimationLoader

#### Constructor

```python
ChestAnimationLoader(json_path: str, scale: int = 2)
```

#### Constants

```python
CHEST_ANIMATIONS = {
    'closed': 'Closed',
    'opening': 'Opening',
    'open': 'Open',
    'highlight': 'Highlight'
}

REQUIRED_ANIMATIONS = ['closed', 'opening', 'open']

FALLBACK_CHAINS = {
    'highlight': ['closed'],
    'opening': ['open', 'closed']
}
```

#### Methods

#### `load_chest_animations() -> bool`
Load chest-specific animations.

#### `has_opening_animation() -> bool`
Check if chest has opening animation sequence.

#### `has_highlight_effect() -> bool`
Check if chest has highlight when player nearby.

### DoorAnimationLoader

#### Constants

```python
DOOR_ANIMATIONS = {
    'closed': 'Closed',
    'opening': 'Opening',
    'open': 'Open',
    'closing': 'Closing',
    'locked': 'Locked'
}
```

### Factory Function

#### `create_interactable_loader(object_type: str, json_path: str, scale: int = 2) -> InteractableAnimationLoader`
Create appropriate interactable loader.

**Parameters**:
- `object_type` (str): Type of object ('chest', 'door', 'collectible', 'switch')
- `json_path` (str): Path to animation JSON
- `scale` (int): Scaling factor

---

## 👥 NPCAnimationLoader

Loader for non-player character animations.

### DialogueNPCLoader

#### Constructor

```python
DialogueNPCLoader(json_path: str, scale: int = 2)
```

#### Constants

```python
DIALOGUE_ANIMATIONS = {
    'idle': 'Idle',
    'talk': 'Talk',
    'listen': 'Listen',
    'greet': 'Greet',
    'goodbye': 'Goodbye',
    'nod': 'Nod',
    'shake_head': 'Shake Head',
    'think': 'Think'
}

REQUIRED_ANIMATIONS = ['idle', 'talk']

FALLBACK_CHAINS = {
    'greet': ['talk', 'idle'],
    'goodbye': ['talk', 'idle'],
    'nod': ['idle'],
    'shake_head': ['idle'],
    'think': ['idle']
}
```

#### Methods

#### `load_dialogue_animations() -> bool`
Load dialogue NPC animations.

#### `has_expression_animations() -> bool`
Check if NPC has facial expression animations.

#### `get_conversation_animations() -> List[str]`
Get animations suitable for conversation.

### Factory Function

#### `create_npc_loader(npc_type: str, json_path: str, scale: int = 2) -> NPCAnimationLoader`
Create appropriate NPC loader.

---

## 🏭 Factory Functions

Global factory functions for creating animation loaders.

### `create_player_loader(json_path: str, scale: int = 2) -> PlayerAnimationLoader`
Create player animation loader.

### `create_enemy_loader(enemy_type: str, json_path: str, scale: int = 2) -> EnemyAnimationLoader`
Create enemy animation loader based on type.

### `create_interactable_loader(object_type: str, json_path: str, scale: int = 2) -> InteractableAnimationLoader`
Create interactable object loader.

### `create_npc_loader(npc_type: str, json_path: str, scale: int = 2) -> NPCAnimationLoader`
Create NPC animation loader.

---

## 📊 Data Structures

### Animation Data Structure

```python
AnimationData = {
    'surfaces_right': List[pygame.Surface],    # Right-facing frames
    'surfaces_left': List[pygame.Surface],     # Left-facing frames
    'pivots_right': List[Tuple[int, int]],     # Right-facing pivots
    'pivots_left': List[Tuple[int, int]],      # Left-facing pivots
    'durations': List[float],                  # Frame durations in seconds
    'direction': str,                          # Animation direction ('forward', 'reverse', 'pingpong')
    'frame_count': int                         # Total number of frames
}
```

### Entity Info Structure

```python
EntityInfo = {
    'entity_type': str,                        # Type of entity
    'total_animations': int,                   # Number of loaded animations
    'required_animations': int,                # Number of required animations
    'animations_loaded': List[str],            # List of loaded animation names
    'missing_animations': List[str],           # List of missing required animations
    'fallbacks_applied': List[str],            # List of animations using fallbacks
    'pivot_point': Tuple[int, int] | None,     # Base pivot point
    'scale': int,                              # Scaling factor
    'has_capabilities': Dict[str, bool]        # Entity-specific capabilities
}
```

### Aseprite Frame Data

```python
AsepriteFrame = {
    'x': int,                                  # X position in sprite sheet
    'y': int,                                  # Y position in sprite sheet
    'w': int,                                  # Frame width
    'h': int,                                  # Frame height
    'duration': int                            # Frame duration in milliseconds
}
```

---

## 🔢 Constants and Enums

### Animation Directions

```python
class AnimationDirection:
    FORWARD = "forward"                        # Play frames in order
    REVERSE = "reverse"                        # Play frames in reverse
    PINGPONG = "pingpong"                      # Play forward then reverse
```

### Entity Types

```python
class EntityType:
    PLAYER = "Player"
    ENEMY = "Enemy"
    INTERACTABLE = "Interactable" 
    NPC = "NPC"
```

### Enemy Types

```python
class EnemyType:
    ASSASSIN = "assassin"
    ARCHER = "archer"
    WASP = "wasp"
```

### Interactable Types

```python
class InteractableType:
    CHEST = "chest"
    DOOR = "door"
    COLLECTIBLE = "collectible"
    SWITCH = "switch"
```

### NPC Types

```python
class NPCType:
    DIALOGUE = "dialogue"
    SHOP = "shop"
    QUEST = "quest"
    AMBIENT = "ambient"
```

### Default Values

```python
DEFAULT_SCALE = 2
DEFAULT_FRAME_DURATION = 0.1               # 100ms per frame
DEFAULT_PIVOT = (0, 0)                     # Bottom-left if no pivot found
MAX_FALLBACK_DEPTH = 5                     # Maximum fallback chain length
```

---

## 🔍 Error Codes and Exceptions

### Custom Exceptions

```python
class AnimationError(Exception):
    """Base exception for animation system errors."""
    pass

class AnimationLoadError(AnimationError):
    """Raised when animation loading fails."""
    pass

class AnimationValidationError(AnimationError):
    """Raised when animation validation fails."""
    pass

class MissingAnimationError(AnimationError):
    """Raised when required animation is missing."""
    pass
```

### Error Codes

```python
class ErrorCode:
    SUCCESS = 0
    FILE_NOT_FOUND = 1
    INVALID_JSON = 2
    MISSING_SPRITESHEET = 3
    INVALID_ANIMATION_DATA = 4
    MISSING_REQUIRED_ANIMATION = 5
    FALLBACK_CHAIN_EXHAUSTED = 6
    INVALID_SCALE_FACTOR = 7
```

---

## 📈 Performance Metrics

### Timing Benchmarks

```python
class PerformanceTargets:
    MAX_LOAD_TIME = 0.5                       # Maximum load time in seconds
    MAX_FRAME_ACCESS_TIME = 0.001             # Maximum frame access time
    MAX_MEMORY_PER_ENTITY = 10 * 1024 * 1024  # 10MB maximum per entity
    TARGET_FPS_IMPACT = 1                     # Maximum 1ms per entity render
```

### Memory Usage Estimates

```python
class MemoryEstimates:
    BYTES_PER_PIXEL = 4                       # RGBA format
    TYPICAL_FRAME_SIZE = 32 * 32 * 4         # 32x32 RGBA frame
    SCALE_MEMORY_MULTIPLIER = lambda scale: scale ** 2
    
    @staticmethod
    def estimate_animation_memory(frame_count: int, frame_size: int, scale: int) -> int:
        """Estimate memory usage for animation."""
        base_size = frame_count * frame_size * 2  # Right and left facing
        return base_size * (scale ** 2)
```

---

*This API reference provides complete documentation for all public interfaces in the Darkvania Animation System. Use this as a comprehensive guide for development and integration.*