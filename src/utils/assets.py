"""Asset loading utilities for the game."""
import os
import sys
from typing import List, Tuple

import pygame

from .spritesheet import SpriteSheet

# Animation data imports
try:
    from ..animations.player.walk_selection import SHEET as SELECTED_SHEET, FRAMES as SELECTED_FRAMES
    try:
        from ..animations.player.walk_selection import TRIMMED as WALK_TRIMMED, PIVOTS as WALK_PIVOTS
    except Exception:
        WALK_TRIMMED, WALK_PIVOTS = None, None
except Exception:
    SELECTED_SHEET = None
    SELECTED_FRAMES = []
    WALK_TRIMMED, WALK_PIVOTS = None, None

try:
    from ..animations.player.idle_selection import SHEET as IDLE_SHEET, FRAMES as IDLE_FRAMES
    try:
        from ..animations.player.idle_selection import TRIMMED as IDLE_TRIMMED, PIVOTS as IDLE_PIVOTS
    except Exception:
        IDLE_TRIMMED, IDLE_PIVOTS = None, None
except Exception:
    IDLE_SHEET = None
    IDLE_FRAMES = []
    IDLE_TRIMMED, IDLE_PIVOTS = None, None

# Prefer 'jump_selection' (new export name); fallback to older 'fall_selection'
try:
    from ..animations.player.jump_selection import SHEET as JUMP_SHEET, FRAMES as JUMP_FRAMES
    try:
        from ..animations.player.jump_selection import TRIMMED as JUMP_TRIMMED, PIVOTS as JUMP_PIVOTS
    except Exception:
        JUMP_TRIMMED, JUMP_PIVOTS = None, None
except Exception:
    JUMP_SHEET = None
    JUMP_FRAMES = []
    JUMP_TRIMMED, JUMP_PIVOTS = None, None

try:
    from ..animations.player.trans_selection import SHEET as TRANS_SHEET, FRAMES as TRANS_FRAMES
    try:
        from ..animations.player.trans_selection import TRIMMED as TRANS_TRIMMED, PIVOTS as TRANS_PIVOTS
    except Exception:
        TRANS_TRIMMED, TRANS_PIVOTS = None, None
except Exception:
    TRANS_SHEET = None
    TRANS_FRAMES = []
    TRANS_TRIMMED, TRANS_PIVOTS = None, None

try:
    from ..animations.player.fall_selection import SHEET as FALL_SHEET, FRAMES as FALL_FRAMES
    try:
        from ..animations.player.fall_selection import TRIMMED as FALL_TRIMMED, PIVOTS as FALL_PIVOTS
    except Exception:
        FALL_TRIMMED, FALL_PIVOTS = None, None
except Exception:
    FALL_SHEET = None
    FALL_FRAMES = []
    FALL_TRIMMED, FALL_PIVOTS = None, None


def resource_path(relative: str) -> str:
    """Resolve resource paths whether running from source or a bundled exe.

    Accepts paths like 'Assests/foo.png' or os.path.join('Assests','foo.png').
    Normalizes separators for Windows.
    """
    # Get the base path - go up from src/utils to project root
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    
    # If we're in the src/utils directory, go up two levels to project root
    if base_path.endswith(os.path.join('src', 'utils')):
        base_path = os.path.dirname(os.path.dirname(base_path))
    
    return os.path.join(base_path, relative)


def load_anim(sheet_path: str,
              frames_rects: List[tuple],
              scale: int,
              trimmed: List[tuple] | None = None,
              pivots: List[tuple] | None = None) -> tuple[List[pygame.Surface], List[pygame.Surface], List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Load animation frames.
    Prefer trimmed rects + pivots if provided; fall back to original rects and bottom-center pivots.
    Returns (right_surfaces, left_surfaces, pivots_right(px,py), pivots_left(px,py)) with pivot in scaled pixels.
    """
    img = pygame.image.load(sheet_path).convert_alpha()
    sheet = SpriteSheet(img)
    use_trim = trimmed is not None and pivots is not None and len(trimmed) == len(frames_rects) and len(pivots) == len(frames_rects)

    right_surfaces: List[pygame.Surface] = []
    left_surfaces: List[pygame.Surface] = []
    piv_right: List[Tuple[int, int]] = []
    piv_left: List[Tuple[int, int]] = []

    for idx, rect in enumerate(frames_rects):
        if use_trim:
            tx, ty, tw, th, ox, oy = trimmed[idx]
            src = pygame.Rect(tx, ty, tw, th)
            px, py = pivots[idx]
            orig_surf = sheet.get_image(src)
            scaled = pygame.transform.scale(orig_surf, (tw * scale, th * scale))
            pivot_x = int(px * scale)
            pivot_y = int(py * scale)
        else:
            src = pygame.Rect(rect)
            orig_surf = sheet.get_image(src)
            scaled = pygame.transform.scale(orig_surf, (src.width * scale, src.height * scale))
            pivot_x = int(src.width * scale / 2)
            pivot_y = int((src.height - 1) * scale)

        right_surfaces.append(scaled)
        left_surfaces.append(pygame.transform.flip(scaled, True, False))
        piv_right.append((pivot_x, pivot_y))
        piv_left.append((scaled.get_width() - pivot_x - 1, pivot_y))

    return right_surfaces, left_surfaces, piv_right, piv_left


class AnimationLoader:
    """Manages loading of all character animations."""
    
    def __init__(self, scale: int = 2):
        self.scale = scale
        self.animations = {}
        
    def load_all_animations(self):
        """Load all character animations with fallbacks."""
        # Load walk animation
        if SELECTED_SHEET and SELECTED_FRAMES:
            try:
                self.animations['walk'] = load_anim(
                    resource_path(SELECTED_SHEET), SELECTED_FRAMES, self.scale, WALK_TRIMMED, WALK_PIVOTS
                )
            except Exception as e:
                print(f"Failed to load walk frames: {e}. Using placeholder.")
                self._create_placeholder_animation('walk')
        else:
            self._create_placeholder_animation('walk')
            
        # Load idle animation
        if IDLE_SHEET and IDLE_FRAMES:
            try:
                self.animations['idle'] = load_anim(
                    resource_path(IDLE_SHEET), IDLE_FRAMES, self.scale, IDLE_TRIMMED, IDLE_PIVOTS
                )
            except Exception as e:
                print(f"Failed to load idle frames: {e}")
                self.animations['idle'] = self.animations['walk']
        else:
            self.animations['idle'] = self.animations['walk']
            
        # Load jump animation
        if JUMP_SHEET and JUMP_FRAMES:
            try:
                self.animations['jump'] = load_anim(
                    resource_path(JUMP_SHEET), JUMP_FRAMES, self.scale, JUMP_TRIMMED, JUMP_PIVOTS
                )
            except Exception as e:
                print(f"Failed to load jump frames: {e}")
                self.animations['jump'] = self.animations['idle']
        else:
            self.animations['jump'] = self.animations['idle']
            
        # Load transition animation
        if TRANS_SHEET and TRANS_FRAMES:
            try:
                self.animations['trans'] = load_anim(
                    resource_path(TRANS_SHEET), TRANS_FRAMES, self.scale, TRANS_TRIMMED, TRANS_PIVOTS
                )
            except Exception as e:
                print(f"Failed to load trans frames: {e}")
                self.animations['trans'] = ([], [], [], [])
        else:
            self.animations['trans'] = ([], [], [], [])
            
        # Load fall animation
        if FALL_SHEET and FALL_FRAMES:
            try:
                self.animations['fall'] = load_anim(
                    resource_path(FALL_SHEET), FALL_FRAMES, self.scale, FALL_TRIMMED, FALL_PIVOTS
                )
            except Exception as e:
                print(f"Failed to load fall frames: {e}")
                self.animations['fall'] = self.animations['jump']
        else:
            self.animations['fall'] = self.animations['jump']
            
    def _create_placeholder_animation(self, name: str):
        """Create a placeholder animation for missing assets."""
        placeholder = pygame.Surface((60, 60), pygame.SRCALPHA)
        placeholder.fill((200, 80, 80))
        right_surfaces = [placeholder]
        left_surfaces = [pygame.transform.flip(placeholder, True, False)]
        piv_right, piv_left = [(30, 59)], [(29, 59)]
        self.animations[name] = (right_surfaces, left_surfaces, piv_right, piv_left)
        
    def get_animation(self, name: str):
        """Get animation data by name."""
        return self.animations.get(name, self.animations['walk'])
