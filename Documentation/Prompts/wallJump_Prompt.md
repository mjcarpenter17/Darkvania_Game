# Wall Hold & Wall Jump System Design

We've added the Ledge Hold mechanic, which works great. Next, we want to add Wall Hold mechanics.

## **Design Questions**

- When does the player hold the wall?
- When should they slide down the wall?
- What else should be considered?

## **Animations to Consider**

- **Wall Hold**
- **Wall Transition** (to sliding)
- **Wall Slide**
- **Wall Slide Stop**

## **Wall Sliding Thoughts**

- Originally: Player stays in place while holding the wall, slides only when pressing down.
- New idea:  
    - On jumping onto a wall, player slides down a little (wall slide animation), then stops (wall slide stop animation).
    - Holds wall for ~1 second (wall hold animation), then begins to slide (wall transition animation into wall slide animation).
    - Slides down until reaching the end of the wall or jumping off.
    - Wall jump should feel responsive:
        - Jumping off and pressing away: 45° jump away from wall.
        - Jumping off without input: Small push away.
        - Jumping and pressing toward wall: Push out, propel up, move back toward wall or ledge.

Open to additional thoughts and fine-tuning.

---

## **Key Considerations**

### **Core Wall Hold Conditions**

**When to grab the wall:**
- Player is airborne (not on ground)
- Moving toward a wall (input direction matches wall side)
- Side collision box touches solid wall tile
- Downward or minimal upward velocity (not at jump peak)

**When to release the wall:**
- Player presses jump (wall jump)
- Stops holding direction toward wall
- Reaches ground
- Wall ends (no more solid tiles)

---

### **Wall Sliding Mechanics**

```python
# Suggested physics values
self.wall_slide_speed = 100.0  # Slower than gravity (1400.0)
self.wall_slide_max_speed = 200.0  # Terminal velocity while sliding
self.wall_hold_grace_time = 0.1  # Brief moment before sliding starts
```

**Sliding behavior:**
- Brief pause (grace period) before sliding
- Gradual acceleration to max slide speed
- Faster sliding if not holding toward wall
- Visual dust particles trailing

---

### **Wall Jump System**

```python
# Wall jump should be different from normal jump
self.wall_jump_speed_x = 250.0  # Horizontal push away from wall  
self.wall_jump_speed_y = 600.0  # Slightly less than normal jump
self.wall_jump_duration = 0.3   # Brief period of forced movement
```

**Wall jump mechanics:**
- Launches player away at an angle
- Brief period of reduced/ignored horizontal input
- Resets air abilities (double jump, dash cooldown, etc.)
- Unique animation

---

### **Technical Implementation**

**Collision detection:**
```python
def check_wall_collision(self, world_map, side='left'):
        """Check if player can grab wall on specified side."""
        check_x = self.pos_x + (-8 if side == 'left' else 8)
        # Check multiple points along player's height
        check_points = [
                self.pos_y - 30,  # Upper body
                self.pos_y - 15,  # Middle body  
                self.pos_y - 5    # Lower body
        ]
        return any(world_map.is_solid_at_any_layer(check_x, y) for y in check_points)
```

**State management:**
- Add `wall_hold` state (higher priority than fall/jump)
- Track `wall_side` (-1 for left, 1 for right)  
- Add `is_wall_holding` flag
- Integrate with animation state machine

---

### **Gameplay Balance Factors**

**Optional mechanics:**
- **Stamina system:** Limit wall hold time before forced slide
- **Surface types:** Only certain tiles are climbable
- **Wall jump chains:** Prevent infinite climbing between two walls
- **Cooldown:** Delay before grabbing same wall again

**Integration:**
- **Dashing:** Can dash away, cancels wall hold
- **Attacking:** Disable attacks while wall holding
- **Ledge grab:** Wall hold lower priority than ledge grab

---

### **Visual & Audio Feedback**

**Animations:**
- `wall_hold_start` (grab)
- `wall_slide` (slide)
- `wall_jump` (launch)

**Effects:**
- Dust particles while sliding
- Unique sounds for wall grab vs ledge grab
- Optional screen shake on wall impact

---

### **Suggested Implementation Order**

1. **Basic wall detection** – Identify when player touches wall
2. **Wall hold state** – Stop falling when grabbing wall
3. **Wall sliding** – Controlled descent
4. **Wall jumping** – Launch away from wall
5. **Polish** – Animations, particles, sound effects

