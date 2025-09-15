import json, os, math
from collections import defaultdict
from statistics import mean
from PIL import Image

# Configuration
TILE_SIZE = 16
COLS = 24
ROWS = 24
MIN_OCCUPANCY_PCT = 1.0   # minimum % (0-100) non-transparent pixels to consider tile non-blank
PLATFORM_TOP_FOCUS_THRESHOLD = 0.78  # fraction of pixels in top half
PLATFORM_BOTTOM_MAX = 0.30           # fraction of pixels in bottom half
SOLID_MIN_PCT = 70.0                 # occupancy >= this => solid
SOLID_SECONDARY_MIN_PCT = 60.0       # fallback occupancy threshold if distribution uniform

ROOT = os.path.dirname(__file__)
IMAGE_PATH = os.path.join(ROOT, 'Caves_Full_Tileset.png')
OUTPUT_JSON = os.path.join(ROOT, 'tileset_full_analysis.json')

if not os.path.exists(IMAGE_PATH):
    raise SystemExit(f"Tileset image not found: {IMAGE_PATH}")

im = Image.open(IMAGE_PATH).convert('RGBA')
W, H = im.size
assert W == COLS * TILE_SIZE and H == ROWS * TILE_SIZE, (
    f"Unexpected image size {W}x{H}; expected {COLS*TILE_SIZE}x{ROWS*TILE_SIZE}")

# Data structures
raw_tiles = {}
classification = {}

# First pass: occupancy + basic stats
for row in range(ROWS):
    for col in range(COLS):
        tile_index = row * COLS + col
        box = (col*TILE_SIZE, row*TILE_SIZE, (col+1)*TILE_SIZE, (row+1)*TILE_SIZE)
        tile = im.crop(box)
        # Convert to list so we can slice per row
        pix = list(tile.getdata())
        opaque = [(r,g,b,a) for (r,g,b,a) in pix if a > 0]
        occ = len(opaque)
        occ_pct = occ / (TILE_SIZE*TILE_SIZE) * 100.0
        if occ_pct < MIN_OCCUPANCY_PCT:
            continue  # blank
        # Row occupancy distribution
        rows_occ = []
        for y in range(TILE_SIZE):
            row_slice = pix[y*TILE_SIZE:(y+1)*TILE_SIZE]
            row_pixels = [p for p in row_slice if p[3] > 0]
            rows_occ.append(len(row_pixels))
        top_half = sum(rows_occ[:TILE_SIZE//2])
        bottom_half = sum(rows_occ[TILE_SIZE//2:])
        top_fraction = top_half / max(1,(top_half+bottom_half))
        bottom_fraction = bottom_half / max(1,(top_half+bottom_half))
        avg_r = mean([p[0] for p in opaque]) if opaque else 0
        avg_g = mean([p[1] for p in opaque]) if opaque else 0
        avg_b = mean([p[2] for p in opaque]) if opaque else 0
        avg_hex = f"#{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}"
        raw_tiles[tile_index] = {
            'row': row, 'col': col,
            'occ_pct': occ_pct,
            'top_fraction': top_fraction,
            'bottom_fraction': bottom_fraction,
            'avg_color': (avg_r, avg_g, avg_b),
            'avg_hex': avg_hex,
            'rows_occ': rows_occ,
        }

# Helper to get classification for adjacency
solids = set()
platforms = set()

def classify_tile(info):
    occ = info['occ_pct']
    top_f = info['top_fraction']
    bottom_f = info['bottom_fraction']
    r,g,b = info['avg_color']

    # Platform heuristic
    if occ < SOLID_MIN_PCT and top_f >= PLATFORM_TOP_FOCUS_THRESHOLD and bottom_f <= PLATFORM_BOTTOM_MAX:
        return 'platform'
    # Solid heuristic
    if occ >= SOLID_MIN_PCT:
        return 'solid'
    if occ >= SOLID_SECONDARY_MIN_PCT and abs(top_f - 0.5) < 0.2:
        return 'solid'
    # Decoration by default
    return 'decoration'

for idx, info in raw_tiles.items():
    ttype = classify_tile(info)
    classification[idx] = {'type': ttype}
    if ttype == 'solid':
        solids.add(idx)
    elif ttype == 'platform':
        platforms.add(idx)

# Second pass for edge/corner determination in solids & platforms
solids_map = {(t//COLS, t%COLS): True for t in solids}
platforms_map = {(t//COLS, t%COLS): True for t in platforms}

def neighbor(map_, r,c):
    return map_.get((r,c), False)

output = {}

for idx, meta in raw_tiles.items():
    row = meta['row']; col = meta['col']
    ttype = classification[idx]['type']
    desc = ''
    if ttype == 'solid':
        up = neighbor(solids_map, row-1, col)
        down = neighbor(solids_map, row+1, col)
        left = neighbor(solids_map, row, col-1)
        right = neighbor(solids_map, row, col+1)
        if not up and not left and right and down:
            desc = 'Top left corner solid block'
        elif not up and not right and left and down:
            desc = 'Top right corner solid block'
        elif not down and not left and right and up:
            desc = 'Bottom left corner solid block'
        elif not down and not right and left and up:
            desc = 'Bottom right corner solid block'
        elif not up and left and right and down:
            desc = 'Top edge solid block'
        elif not down and left and right and up:
            desc = 'Bottom edge solid block'
        elif not left and up and down and right:
            desc = 'Left side solid block'
        elif not right and up and down and left:
            desc = 'Right side solid block'
        else:
            desc = 'Middle fill solid block'
    elif ttype == 'platform':
        left = neighbor(platforms_map, row, col-1)
        right = neighbor(platforms_map, row, col+1)
        if not left and right:
            desc = 'Left side platform (one-way)'
        elif left and right:
            desc = 'Middle platform (one-way)'
        elif left and not right:
            desc = 'Right side platform (one-way)'
        else:
            desc = 'Single platform (one-way)'
    else:  # decoration
        r,g,b = meta['avg_color']
        # Rough semantic hints based on dominant color
        if g > r + 10 and g > b + 10:
            if r < 90:
                desc = 'Decoration - mossy vine / foliage segment'
            else:
                desc = 'Decoration - leafy foliage cluster'
        elif r > g + 25 and r > b + 25:
            if g > 100 and b < 80:
                desc = 'Decoration - glowing orange drip (stalactite segment)'
            elif b > 120:
                desc = 'Decoration - glowing pink drip (stalactite segment)'
            else:
                desc = 'Decoration - trunk/root detail'
        elif r < 80 and g < 90 and b < 90:
            desc = 'Decoration - dark rock / shadow fragment'
        else:
            desc = 'Decoration - detailed object piece'
        # Append color hint
        desc += f" (avg {meta['avg_hex']})"
    output[str(idx)] = { 'type': ttype, 'description': desc }

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)

print(f"Generated {len(output)} tile entries -> {OUTPUT_JSON}")
print('Type counts:', sum(1 for v in output.values() if v['type']=='solid'), 'solids,',
      sum(1 for v in output.values() if v['type']=='platform'), 'platforms,',
      sum(1 for v in output.values() if v['type']=='decoration'), 'decorations')
