# 🎯 Animation System Quick Start Guide

**Get up and running with the Darkvania Animation System in 5 minutes**

---

## 🚀 Quick Setup

### 1. Basic Player Setup (30 seconds)

```python
from src.animations import PlayerAnimationLoader

# Initialize player animations
player_loader = PlayerAnimationLoader("Assests/SwordMaster/SwordMaster.json", scale=2)

# Load animations
if player_loader.load_player_animations():
    print("✓ Player animations loaded successfully!")
else:
    print("✗ Failed to load player animations")

# Your player is ready!
```

### 2. Basic Enemy Setup (30 seconds)

```python
from src.animations.enemy_animation_loader import AssassinAnimationLoader

# Initialize assassin animations
assassin_loader = AssassinAnimationLoader("Assests/enemies/assassin/Assassin.json", scale=2)

# Load animations
if assassin_loader.load_assassin_animations():
    print("✓ Assassin animations loaded successfully!")
else:
    print("✗ Failed to load assassin animations")

# Your enemy is ready!
```

### 3. Simple Animation Playback (1 minute)

```python
class SimpleAnimatedSprite:
    def __init__(self, loader, x, y):
        self.loader = loader
        self.x = x
        self.y = y
        self.current_animation = "idle"
        self.current_frame = 0
        self.frame_timer = 0.0
        self.facing_right = True
    
    def update(self, dt):
        # Update animation timing
        duration = self.loader.get_frame_duration(self.current_animation, self.current_frame)
        self.frame_timer += dt
        
        if self.frame_timer >= duration:
            self.frame_timer = 0.0
            frame_count = self.loader.get_frame_count(self.current_animation)
            self.current_frame = (self.current_frame + 1) % frame_count
    
    def render(self, screen, camera_x=0, camera_y=0):
        # Get current frame surface
        surface = self.loader.get_frame_surface(
            self.current_animation, self.current_frame, self.facing_right
        )
        
        if surface:
            # Get pivot for positioning
            pivot = self.loader.get_frame_pivot(
                self.current_animation, self.current_frame, self.facing_right
            )
            
            if pivot:
                render_x = self.x - camera_x - pivot[0]
                render_y = self.y - camera_y - pivot[1]
                screen.blit(surface, (render_x, render_y))
    
    def play_animation(self, animation_name):
        if self.loader.has_animation(animation_name):
            if self.current_animation != animation_name:
                self.current_animation = animation_name
                self.current_frame = 0
                self.frame_timer = 0.0

# Usage
player_sprite = SimpleAnimatedSprite(player_loader, 100, 200)
player_sprite.play_animation("walk")
```

### 4. Ready-to-Use Template (2 minutes)

```python
import pygame
from src.animations import PlayerAnimationLoader

class QuickStartPlayer:
    def __init__(self, x, y):
        # Initialize animation system
        self.animation_loader = PlayerAnimationLoader("Assests/SwordMaster/SwordMaster.json", scale=2)
        self.animation_loader.load_player_animations()
        
        # Position and state
        self.x = x
        self.y = y
        self.facing_right = True
        
        # Animation state
        self.state = "idle"
        self.frame = 0
        self.timer = 0.0
        
        # Input tracking
        self.keys = pygame.key.get_pressed()
    
    def update(self, dt):
        # Update input
        self.keys = pygame.key.get_pressed()
        
        # Simple state machine
        old_state = self.state
        
        if self.keys[pygame.K_LEFT] or self.keys[pygame.K_RIGHT]:
            self.state = "walk"
            self.facing_right = self.keys[pygame.K_RIGHT]
        elif self.keys[pygame.K_SPACE]:
            self.state = "attack1"
        else:
            self.state = "idle"
        
        # Reset animation if state changed
        if old_state != self.state:
            self.frame = 0
            self.timer = 0.0
        
        # Update animation frame
        duration = self.animation_loader.get_frame_duration(self.state, self.frame)
        self.timer += dt
        
        if self.timer >= duration:
            self.timer = 0.0
            frame_count = self.animation_loader.get_frame_count(self.state)
            self.frame = (self.frame + 1) % frame_count
    
    def render(self, screen, camera_x=0, camera_y=0):
        surface = self.animation_loader.get_frame_surface(self.state, self.frame, self.facing_right)
        if surface:
            pivot = self.animation_loader.get_frame_pivot(self.state, self.frame, self.facing_right)
            if pivot:
                screen.blit(surface, (self.x - camera_x - pivot[0], self.y - camera_y - pivot[1]))

# Usage in your game loop
player = QuickStartPlayer(400, 300)

# In your main loop:
# player.update(delta_time)
# player.render(screen)
```

---

## 🎨 Aseprite Quick Setup

### 1. Create Your Sprite (2 minutes)

1. **Open Aseprite**
2. **Create New Sprite**: File → New
3. **Set Size**: 32x32 or 64x64 pixels
4. **Draw your character frames**

### 2. Add Animation Tags (1 minute)

1. **Open Timeline**: View → Timeline
2. **Create Tag**: Right-click frame range → "New Tag"
3. **Name your animations**:
   - "Idle" (frames 0-3)
   - "Walk" (frames 4-11)
   - "Attack 1" (frames 12-15)

### 3. Add Pivot Point (30 seconds)

1. **Create Slice**: Slice Tool (U)
2. **Name it "Pivot"**
3. **Position at character's feet center**

### 4. Export (30 seconds)

1. **File → Export Sprite Sheet**
2. **Select "JSON (Array)" format**
3. **Include both JSON and PNG**
4. **Save to your Assets folder**

---

## 🔧 Common Patterns

### Animation State Machine

```python
class AnimationStateMachine:
    def __init__(self, loader):
        self.loader = loader
        self.state = "idle"
        self.frame = 0
        self.timer = 0.0
        
        # State transitions
        self.transitions = {
            "idle": {"walk", "attack1", "jump"},
            "walk": {"idle", "attack1", "jump"},
            "attack1": {"idle"},
            "jump": {"fall", "idle"},
            "fall": {"idle"}
        }
    
    def can_transition(self, new_state):
        return new_state in self.transitions.get(self.state, set())
    
    def change_state(self, new_state):
        if self.can_transition(new_state):
            self.state = new_state
            self.frame = 0
            self.timer = 0.0
            return True
        return False
```

### Multi-Entity Manager

```python
class AnimationManager:
    def __init__(self):
        self.loaders = {}
    
    def load_player(self):
        self.loaders['player'] = PlayerAnimationLoader("Assests/SwordMaster/SwordMaster.json", scale=2)
        return self.loaders['player'].load_player_animations()
    
    def load_enemy(self, enemy_type):
        from src.animations.enemy_animation_loader import create_enemy_loader
        path = f"Assests/enemies/{enemy_type}/{enemy_type.title()}.json"
        self.loaders[enemy_type] = create_enemy_loader(enemy_type, path, scale=2)
        return getattr(self.loaders[enemy_type], f'load_{enemy_type}_animations')()
    
    def get_loader(self, entity_type):
        return self.loaders.get(entity_type)

# Usage
anim_manager = AnimationManager()
anim_manager.load_player()
anim_manager.load_enemy('assassin')
```

### Factory Pattern for Entities

```python
def create_animated_entity(entity_type, entity_subtype, x, y, scale=2):
    """Factory to create any animated entity."""
    
    # Define paths
    paths = {
        'player': "Assests/SwordMaster/SwordMaster.json",
        'assassin': "Assests/enemies/assassin/Assassin.json",
        'chest': "Assests/interactables/chest/Chest.json"
    }
    
    # Create appropriate loader
    if entity_type == 'player':
        loader = PlayerAnimationLoader(paths['player'], scale)
        loader.load_player_animations()
    elif entity_type == 'enemy':
        from src.animations.enemy_animation_loader import create_enemy_loader
        loader = create_enemy_loader(entity_subtype, paths[entity_subtype], scale)
        getattr(loader, f'load_{entity_subtype}_animations')()
    
    # Create entity with loader
    return SimpleAnimatedSprite(loader, x, y)
```

---

## 🎯 Essential Commands

### Check Animation Status

```python
# Check what animations are available
print(f"Available animations: {loader.list_animations()}")

# Check if specific animation exists
if loader.has_animation('attack2'):
    print("Character has second attack!")

# Get animation info
info = loader.get_player_info()  # or get_entity_info()
print(f"Loaded {info['total_animations']} animations")
```

### Debug Animation Loading

```python
# Enable debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Load with debug info
loader = PlayerAnimationLoader("path/to/sprite.json", scale=2)
success = loader.load_player_animations()

if success:
    print("✓ All animations loaded")
else:
    print("✗ Some animations failed")
    missing = loader.get_entity_info()['missing_animations']
    print(f"Missing: {missing}")
```

### Performance Check

```python
import time

# Time the loading
start = time.time()
loader = PlayerAnimationLoader("Assests/SwordMaster/SwordMaster.json", scale=2)
loader.load_player_animations()
load_time = time.time() - start

print(f"Loading took {load_time:.3f} seconds")

# Check memory usage
info = loader.get_player_info()
print(f"Loaded {info['total_animations']} animations at {info['scale']}x scale")
```

---

## 🚨 Quick Troubleshooting

### Problem: "Animation not loading"
```python
# Check file paths
import os
json_path = "Assests/SwordMaster/SwordMaster.json"
png_path = "Assests/SwordMaster/SwordMaster.png"

print(f"JSON exists: {os.path.exists(json_path)}")
print(f"PNG exists: {os.path.exists(png_path)}")

# Check available animations
loader = PlayerAnimationLoader(json_path)
loader.load()
print(f"Aseprite animations: {loader.aseprite_loader.list_animations()}")
```

### Problem: "Wrong animation playing"
```python
# Check animation mappings
print("Current mappings:")
for game_name, aseprite_name in PlayerAnimationLoader.PLAYER_ANIMATIONS.items():
    print(f"  {game_name} -> {aseprite_name}")

# Check what's actually loaded
print(f"Loaded animations: {loader.list_animations()}")
```

### Problem: "Character positioned wrong"
```python
# Check pivot point
info = loader.get_player_info()
print(f"Pivot point: {info['pivot_point']}")

# Manually set pivot if needed
loader.pivot_point = (32, 60)  # Custom pivot
```

---

## 📚 Next Steps

1. **Read the Full Documentation**: [ANIMATION_SYSTEM_DOCUMENTATION.md](ANIMATION_SYSTEM_DOCUMENTATION.md)
2. **Check API Reference**: [ANIMATION_SYSTEM_API_REFERENCE.md](ANIMATION_SYSTEM_API_REFERENCE.md)
3. **Study Example Implementation**: Look at `src/game/player.py` and `src/game/enemy.py`
4. **Create Your Own Entity Type**: Follow the patterns in existing loaders

---

**🎉 Congratulations! You now have a working animation system. Start creating amazing animated characters for your game!**

*Need help? Check the troubleshooting section or refer to the comprehensive documentation.*