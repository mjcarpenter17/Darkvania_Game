# Animation Files Restructuring

The animation files have been successfully reorganized into a more structured directory layout.

## What Changed

### Before
```
data/
├── walk_selection.py
├── walk_selection.json
├── idle_selection.py
├── idle_selection.json
├── jump_selection.py
├── jump_selection.json
├── trans_selection.py
├── trans_selection.json
├── fall_selection.py
├── fall_selection.json
├── __init__.py
└── __pycache__/
```

### After
```
src/
└── animations/
    ├── __init__.py
    └── player/
        ├── __init__.py
        ├── walk_selection.py
        ├── walk_selection.json
        ├── idle_selection.py
        ├── idle_selection.json
        ├── jump_selection.py
        ├── jump_selection.json
        ├── trans_selection.py
        ├── trans_selection.json
        ├── fall_selection.py
        ├── fall_selection.json
        └── __pycache__/
```

## Files Moved

✅ **Moved to `src\animations\player\`:**
- `walk_selection.py` and `walk_selection.json`
- `idle_selection.py` and `idle_selection.json`
- `jump_selection.py` and `jump_selection.json`
- `trans_selection.py` and `trans_selection.json`
- `fall_selection.py` and `fall_selection.json`
- `__init__.py`

✅ **Updated Imports:**
- All imports in `src\utils\assets.py` updated from `data.` to `..animations.player.`
- Relative imports ensure proper module loading within the src package structure

✅ **Preserved Functionality:**
- All animation data remains accessible
- Game functionality unchanged
- Exception handling for missing animations maintained

## Benefits

1. **Better Organization**: Animation files are now grouped logically under `src\animations\player\`
2. **Scalability**: Easy to add other animation categories (enemies, effects, etc.)
3. **Consistency**: Animation data is now part of the main source structure
4. **Modularity**: Clear separation between player animations and other data

## Data Directory Status

The original `data\` directory now only contains:
- `Backup\` - Preserved backup files
- `Old_Animations\` - Preserved old animation files

These can be kept for reference or removed if no longer needed.

## Testing

✅ Game tested and loads successfully with new file structure
✅ All animation imports working correctly
✅ Player animations functional

## Critical Animation Implementation Lessons (Chest System)

### Frame Index Mapping Bug (CRITICAL)
**Issue**: Aseprite loader used 1-based indexing while frameTags use 0-based indexing
- **Symptom**: Animations loading with 0 frames, causing fallback rendering
- **Location**: `src/utils/aseprite_loader.py` - `_parse_frames()` method
- **Fix**: Changed `self.frame_index_map[index + 1] = name` to `self.frame_index_map[index] = name`
- **Impact**: Essential for any new Aseprite-based animations

### Animation Frame Bounds Logic (CRITICAL)
**Issue**: Frame increment happened before bounds checking
- **Symptom**: "Frame index X out of range" errors, gold square fallbacks
- **Location**: Animation update loops in entity classes
- **Fix**: Check `if self.current_frame + 1 >= frame_count` before incrementing
- **Pattern**: 
```python
# WRONG - causes out-of-bounds
self.current_frame += 1
if self.current_frame >= frame_count:
    # handle completion

# CORRECT - prevents out-of-bounds  
if self.current_frame + 1 >= frame_count:
    # handle completion
else:
    self.current_frame += 1
```

### Pivot Point Handling
**Issue**: Default pivot overrides can mask proper Aseprite pivot data
- **Symptom**: Sprites positioned incorrectly, appearing "in ground"
- **Solution**: Check if pivot exists in JSON before applying defaults
- **Best Practice**: Always include pivot slices in Aseprite exports

### Animation State Transitions
**Key Learning**: Multi-state animations need careful transition management
- **Implementation**: Use timer-based delays for natural feeling transitions
- **Example**: Chest opening → 2-second pause → used state
- **Code Pattern**: `waiting_for_transition` flag + `transition_timer`

### Debugging Animation Issues
**Essential Debug Points**:
1. Frame count vs. frame index bounds
2. Animation name mapping (check `animations.keys()`)
3. Surface retrieval success (`surface is not None`)
4. Pivot point application
5. State transition timing

### Animation File Requirements Checklist
For new Aseprite animations:
- ✅ Use 0-based frame indices in frameTags
- ✅ Include pivot point slice if positioning matters
- ✅ Test frame count matches expected animation length
- ✅ Verify all required animations present in JSON
- ✅ Check frame duration values for proper timing
