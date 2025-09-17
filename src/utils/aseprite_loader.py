"""Aseprite animation loader for parsing JSON animation data."""
import json
import os
from typing import Dict, List, Tuple, Optional, Any
import pygame


class AsepriteFrame:
    """Represents a single frame from Aseprite data."""
    
    def __init__(self, name: str, frame_data: Dict[str, Any]):
        self.name = name
        self.x = frame_data["frame"]["x"]
        self.y = frame_data["frame"]["y"]
        self.width = frame_data["frame"]["w"]
        self.height = frame_data["frame"]["h"]
        self.duration = frame_data.get("duration", 100)  # Default 100ms
        
        # Trimming info (for accurate positioning)
        self.trimmed = frame_data.get("trimmed", False)
        if self.trimmed:
            sprite_source = frame_data.get("spriteSourceSize", {})
            self.trim_x = sprite_source.get("x", 0)
            self.trim_y = sprite_source.get("y", 0)
            
            source_size = frame_data.get("sourceSize", {})
            self.original_width = source_size.get("w", self.width)
            self.original_height = source_size.get("h", self.height)
        else:
            self.trim_x = 0
            self.trim_y = 0
            self.original_width = self.width
            self.original_height = self.height


class AsepriteAnimation:
    """Represents an animation sequence from Aseprite frameTags."""
    
    def __init__(self, name: str, from_frame: int, to_frame: int, direction: str = "forward"):
        self.name = name
        self.from_frame = from_frame
        self.to_frame = to_frame
        self.direction = direction
        self.frames: List[AsepriteFrame] = []
        
    def add_frame(self, frame: AsepriteFrame):
        """Add a frame to this animation."""
        self.frames.append(frame)
        
    def get_frame_count(self) -> int:
        """Get total number of frames in this animation."""
        return len(self.frames)
        
    def get_total_duration(self) -> float:
        """Get total duration of animation in seconds."""
        return sum(frame.duration for frame in self.frames) / 1000.0


class AsepriteLoader:
    """Loads and parses Aseprite JSON animation data."""
    
    def __init__(self, json_path: str, image_path: str = None, scale: int = 2):
        self.json_path = json_path
        self.scale = scale
        
        # Auto-detect image path if not provided
        if image_path is None:
            base_path = os.path.splitext(json_path)[0]
            self.image_path = base_path + ".png"
        else:
            self.image_path = image_path
            
        self.sprite_sheet: Optional[pygame.Surface] = None
        self.frames: Dict[str, AsepriteFrame] = {}
        self.animations: Dict[str, AsepriteAnimation] = {}
        self.pivot_point: Tuple[int, int] = (0, 0)  # Default pivot
        
        # Frame name to index mapping (for frameTag references)
        self.frame_index_map: Dict[int, str] = {}
        
    def load(self) -> bool:
        """Load and parse the Aseprite JSON file."""
        try:
            # Load JSON data
            with open(self.json_path, 'r') as f:
                data = json.load(f)
                
            # Load sprite sheet image
            if os.path.exists(self.image_path):
                self.sprite_sheet = pygame.image.load(self.image_path).convert_alpha()
            else:
                print(f"Warning: Sprite sheet not found at {self.image_path}")
                return False
                
            # Parse frames
            self._parse_frames(data.get("frames", {}))
            
            # Parse animations from frameTags
            self._parse_animations(data.get("meta", {}).get("frameTags", []))
            
            # Parse pivot point from slices
            self._parse_pivot(data.get("meta", {}).get("slices", []))
            
            print(f"Loaded {len(self.frames)} frames and {len(self.animations)} animations")
            return True
            
        except Exception as e:
            print(f"Error loading Aseprite data: {e}")
            return False
            
    def _parse_frames(self, frames_data: Dict[str, Any]):
        """Parse frame data from JSON."""
        # Create frame index mapping based on order in JSON
        frame_names = list(frames_data.keys())
        for index, name in enumerate(frame_names):
            self.frame_index_map[index] = name  # Use 0-based indexing to match frameTags
            
        # Parse each frame
        for name, frame_data in frames_data.items():
            self.frames[name] = AsepriteFrame(name, frame_data)
            
    def _parse_animations(self, frame_tags: List[Dict[str, Any]]):
        """Parse animation data from frameTags."""
        for tag in frame_tags:
            name = tag["name"]
            from_frame = tag["from"]
            to_frame = tag["to"]
            direction = tag.get("direction", "forward")
            
            animation = AsepriteAnimation(name, from_frame, to_frame, direction)
            
            # Add frames to animation based on frame indices
            for frame_index in range(from_frame, to_frame + 1):
                if frame_index in self.frame_index_map:
                    frame_name = self.frame_index_map[frame_index]
                    if frame_name in self.frames:
                        animation.add_frame(self.frames[frame_name])
                        
            self.animations[name] = animation
            
    def _parse_pivot(self, slices_data: List[Dict[str, Any]]):
        """Parse pivot point from slice data."""
        for slice_info in slices_data:
            if slice_info.get("name") == "Pivot":
                keys = slice_info.get("keys", [])
                if keys:
                    # Use first key frame for pivot
                    key = keys[0]
                    bounds = key.get("bounds", {})
                    pivot = key.get("pivot", {})
                    
                    # Calculate world pivot as bounds + pivot offset
                    pivot_x = bounds.get("x", 0) + pivot.get("x", 0)
                    pivot_y = bounds.get("y", 0) + pivot.get("y", 0)
                    self.pivot_point = (pivot_x, pivot_y)
                    print(f"Found pivot point at ({pivot_x}, {pivot_y})")
                    break
                    
    def get_animation(self, name: str) -> Optional[AsepriteAnimation]:
        """Get an animation by name."""
        return self.animations.get(name)
        
    def get_frame_surface(self, frame: AsepriteFrame) -> pygame.Surface:
        """Extract a frame surface from the sprite sheet."""
        if not self.sprite_sheet:
            return pygame.Surface((frame.width, frame.height))
            
        # Extract frame from sprite sheet
        frame_surface = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        frame_rect = pygame.Rect(frame.x, frame.y, frame.width, frame.height)
        frame_surface.blit(self.sprite_sheet, (0, 0), frame_rect)
        
        # Scale if needed
        if self.scale != 1:
            scaled_size = (frame.width * self.scale, frame.height * self.scale)
            frame_surface = pygame.transform.scale(frame_surface, scaled_size)
            
        return frame_surface
        
    def get_scaled_pivot(self) -> Tuple[int, int]:
        """Get the pivot point scaled for current scale factor."""
        return (self.pivot_point[0] * self.scale, self.pivot_point[1] * self.scale)
        
    def list_animations(self) -> List[str]:
        """Get list of all available animation names."""
        return list(self.animations.keys())