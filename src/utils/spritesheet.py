"""SpriteSheet utilities for loading and slicing sprite animations."""
from __future__ import annotations

from typing import List, Sequence, Tuple
import pygame


class SpriteSheet:
    """Helper to slice frames from a sprite sheet image.

    Typical usage:
        sheet = SpriteSheet(pygame.image.load(path).convert_alpha())
        frames = sheet.slice_grid(frame_width, frame_height, rows, cols, margin=0, spacing=0)
    Or provide explicit rects to extract specific frames.
    """

    def __init__(self, image: pygame.Surface):
        self.image = image

    def get_image(self, rect: pygame.Rect | Tuple[int, int, int, int]) -> pygame.Surface:
        """Extract a single frame from the sprite sheet."""
        rect = pygame.Rect(rect)
        frame = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        frame.blit(self.image, (0, 0), rect)
        return frame

    def image_at(self, rect: pygame.Rect | Tuple[int, int, int, int]) -> pygame.Surface:
        """Legacy method name for backwards compatibility."""
        return self.get_image(rect)

    def images_at(self, rects: Sequence[pygame.Rect | Tuple[int, int, int, int]]) -> List[pygame.Surface]:
        """Extract multiple frames from the sprite sheet."""
        return [self.get_image(r) for r in rects]

    def slice_grid(
        self,
        frame_width: int,
        frame_height: int,
        rows: int,
        cols: int,
        *,
        margin: int = 0,
        spacing: int = 0,
        row_order: str = "row-major",
    ) -> List[pygame.Surface]:
        """Slice a uniform grid of frames.

        row_order: 'row-major' or 'col-major' controls returned order.
        """
        rects: List[pygame.Rect] = []
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (frame_width + spacing)
                y = margin + r * (frame_height + spacing)
                rects.append(pygame.Rect(x, y, frame_width, frame_height))

        if row_order == "col-major":
            # transpose order
            reordered: List[pygame.Rect] = []
            grid = [rects[r * cols : (r + 1) * cols] for r in range(rows)]
            for c in range(cols):
                for r in range(rows):
                    reordered.append(grid[r][c])
            rects = reordered

        return self.images_at(rects)
