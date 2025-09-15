import json, os, math
from collections import deque, defaultdict
from statistics import mean
from PIL import Image

"""
Enhanced tileset analysis & semantic labeling for Gemini 2.5.
- Attempts to reach target ~294 non-blank tiles by adaptive thresholding.
- Adds semantic grouping for large tree (canopy / trunk / roots).
- Detects vines / moss, drips (orange & pink), roots, foliage clusters.
- Integrates manual overrides from provided example JSON & text notes.
- Produces: tileset_detailed_descriptions.json in a specified output folder.
"""

# Configuration
TILE_SIZE = 16
COLS = 24
ROWS = 24
ADAPTIVE_THRESHOLDS = [1.0, 0.6, 0.3, 0.15, 0.08]  # % opaque pixel thresholds tried until count >= MIN_TARGET
ULTRA_FAINT_THRESHOLD = 0.05  # additional pass to force-include ultra faint tiles user requested
MIN_TARGET = 290
MAX_TARGET = 310
PLATFORM_TOP_FOCUS_THRESHOLD = 0.78
PLATFORM_BOTTOM_MAX = 0.30
SOLID_MIN_PCT = 70.0
SOLID_SECONDARY_MIN_PCT = 60.0

# File Paths
ROOT = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT, 'Gemini_2.5_output')
IMAGE_PATH = os.path.join(ROOT, 'Caves_Full_Tileset.png') # Image is in the same directory
EXAMPLE_JSON = os.path.join(ROOT, 'tileset_JSon_Example.json')
OUTPUT_JSON = os.path.join(OUTPUT_DIR, 'tileset_detailed_descriptions.json')
RAW_DEBUG_JSON = os.path.join(OUTPUT_DIR, 'tileset_raw_metrics.json')

if not os.path.exists(IMAGE_PATH):
    raise SystemExit(f"Tileset image not found: {IMAGE_PATH}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

im = Image.open(IMAGE_PATH).convert('RGBA')
W, H = im.size
assert W == COLS * TILE_SIZE and H == ROWS * TILE_SIZE, (
    f"Unexpected image size {W}x{H}; expected {COLS*TILE_SIZE}x{ROWS*TILE_SIZE}")

# --- Analysis Logic ---

# Try adaptive thresholds to reach desired tile count
raw_tiles = {}
selected_threshold = None

for thresh in ADAPTIVE_THRESHOLDS:
    raw_tiles_tmp = {}
    for row in range(ROWS):
        for col in range(COLS):
            tile_index = row * COLS + col
            box = (col*TILE_SIZE, row*TILE_SIZE, (col+1)*TILE_SIZE, (row+1)*TILE_SIZE)
            tile = im.crop(box)
            pix = list(tile.getdata())
            opaque = [(r,g,b,a) for (r,g,b,a) in pix if a > 0]
            occ = len(opaque)
            occ_pct = occ / (TILE_SIZE*TILE_SIZE) * 100.0
            if occ_pct < thresh:
                continue
            rows_occ = []
            for y in range(TILE_SIZE):
                row_slice = pix[y*TILE_SIZE:(y+1)*TILE_SIZE]
                rows_occ.append(sum(1 for p in row_slice if p[3] > 0))
            top_half = sum(rows_occ[:TILE_SIZE//2])
            bottom_half = sum(rows_occ[TILE_SIZE//2:])
            total_pixels = top_half + bottom_half or 1
            top_fraction = top_half / total_pixels
            bottom_fraction = bottom_half / total_pixels
            avg_r = mean([p[0] for p in opaque]) if opaque else 0
            avg_g = mean([p[1] for p in opaque]) if opaque else 0
            avg_b = mean([p[2] for p in opaque]) if opaque else 0
            avg_hex = f"#{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}"
            raw_tiles_tmp[tile_index] = {
                'row': row, 'col': col,
                'occ_pct': occ_pct,
                'top_fraction': top_fraction,
                'bottom_fraction': bottom_fraction,
                'avg_color': (avg_r, avg_g, avg_b),
                'avg_hex': avg_hex,
                'rows_occ': rows_occ,
            }
    if MIN_TARGET <= len(raw_tiles_tmp) <= MAX_TARGET:
        raw_tiles = raw_tiles_tmp
        selected_threshold = thresh
        break
    if not raw_tiles or abs(len(raw_tiles_tmp)-MIN_TARGET) < abs(len(raw_tiles)-MIN_TARGET):
        raw_tiles = raw_tiles_tmp
        selected_threshold = thresh

# After initial pass, optionally include ultra-faint tiles not yet captured (force include)
if ULTRA_FAINT_THRESHOLD:
    for row in range(ROWS):
        for col in range(COLS):
            tile_index = row * COLS + col
            if tile_index in raw_tiles:
                continue
            box = (col*TILE_SIZE, row*TILE_SIZE, (col+1)*TILE_SIZE, (row+1)*TILE_SIZE)
            tile = im.crop(box)
            pix = list(tile.getdata())
            opaque = [(r,g,b,a) for (r,g,b,a) in pix if a > 0]
            occ = len(opaque)
            occ_pct = occ / (TILE_SIZE*TILE_SIZE) * 100.0
            if 0 < occ_pct <= ULTRA_FAINT_THRESHOLD:
                rows_occ = []
                for y in range(TILE_SIZE):
                    row_slice = pix[y*TILE_SIZE:(y+1)*TILE_SIZE]
                    rows_occ.append(sum(1 for p in row_slice if p[3] > 0))
                top_half = sum(rows_occ[:TILE_SIZE//2])
                bottom_half = sum(rows_occ[TILE_SIZE//2:])
                total_pixels = top_half + bottom_half or 1
                top_fraction = top_half / total_pixels
                bottom_fraction = bottom_half / total_pixels
                if opaque:
                    avg_r = mean([p[0] for p in opaque]); avg_g = mean([p[1] for p in opaque]); avg_b = mean([p[2] for p in opaque])
                else:
                    avg_r = avg_g = avg_b = 0
                avg_hex = f"#{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}"
                raw_tiles[tile_index] = {
                    'row': row, 'col': col, 'occ_pct': occ_pct,
                    'top_fraction': top_fraction, 'bottom_fraction': bottom_fraction,
                    'avg_color': (avg_r, avg_g, avg_b), 'avg_hex': avg_hex, 'rows_occ': rows_occ,
                    'ultra_faint': True
                }

# Classification
classification = {}
solids = set(); platforms = set(); decorations = set()

for idx, info in raw_tiles.items():
    occ = info['occ_pct']
    top_f = info['top_fraction']
    bottom_f = info['bottom_fraction']

    ttype = 'decoration'
    if info.get('ultra_faint'):
        ttype = 'decoration'
    elif occ >= SOLID_MIN_PCT:
        ttype = 'solid'
    elif occ >= SOLID_SECONDARY_MIN_PCT and abs(top_f - 0.5) < 0.2:
        ttype = 'solid'
    elif occ < SOLID_MIN_PCT and top_f >= PLATFORM_TOP_FOCUS_THRESHOLD and bottom_f <= PLATFORM_BOTTOM_MAX and occ > 8:
        ttype = 'platform'

    classification[idx] = ttype
    if ttype == 'solid': solids.add(idx)
    elif ttype == 'platform': platforms.add(idx)
    else: decorations.add(idx)

# Build neighbor maps
solids_map = {(t//COLS, t%COLS): True for t in solids}
platforms_map = {(t//COLS, t%COLS): True for t in platforms}
def has(map_, r,c): return map_.get((r,c), False)

# Connected components for decoration clusters (identify large tree cluster)
visited = set()
clusters = []
for t in decorations:
    if t in visited: continue
    q = deque([t]); comp = set([t]); visited.add(t)
    min_r, min_c, max_r, max_c = t//COLS, t%COLS, t//COLS, t%COLS
    while q:
        cur = q.popleft()
        r, c = cur//COLS, cur%COLS
        min_r, max_r = min(min_r, r), max(max_r, r)
        min_c, max_c = min(min_c, c), max(max_c, c)
        for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr,nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS:
                nid = nr*COLS+nc
                if nid in decorations and nid not in visited:
                    visited.add(nid); comp.add(nid); q.append(nid)
    clusters.append((comp, (min_r,min_c,max_r,max_c)))

largest_cluster = max(clusters, key=lambda x: len(x[0])) if clusters else (set(), (0,0,0,0))
TREE_CLUSTER = largest_cluster[0]
tr_min_r,tr_min_c,tr_max_r,tr_max_c = largest_cluster[1]
height = max(1, tr_max_r - tr_min_r + 1)
width = max(1, tr_max_c - tr_min_c + 1)

# Generate descriptions
output = {}
for idx, info in raw_tiles.items():
    ttype = classification[idx]
    row, col = info['row'], info['col']
    desc = ''
    if ttype == 'solid':
        up, down, left, right = has(solids_map, row-1, col), has(solids_map, row+1, col), has(solids_map, row, col-1), has(solids_map, row, col+1)
        if not up and not left: desc = 'Top left corner solid block'
        elif not up and not right: desc = 'Top right corner solid block'
        elif not down and not left: desc = 'Bottom left corner solid block'
        elif not down and not right: desc = 'Bottom right corner solid block'
        elif not up: desc = 'Top edge solid block'
        elif not down: desc = 'Bottom edge solid block'
        elif not left: desc = 'Left side solid block'
        elif not right: desc = 'Right side solid block'
        else: desc = 'Middle fill solid block'
    elif ttype == 'platform':
        left, right = has(platforms_map, row, col-1), has(platforms_map, row, col+1)
        if not left and right: desc = 'Left side platform (one-way)'
        elif left and right: desc = 'Middle platform (one-way)'
        elif left and not right: desc = 'Right side platform (one-way)'
        else: desc = 'Single platform (one-way)'
    else: # Decoration semantic enrichment
        r,g,b = info['avg_color']
        occ = info['occ_pct']
        ultra_faint = info.get('ultra_faint')

        def canopy_quadrant(rel_r, rel_c):
            vertical = 'top' if rel_r < 0.2 else 'upper'
            horiz = 'left' if rel_c < 0.33 else 'right' if rel_c > 0.66 else 'center'
            return f'{vertical} {horiz} canopy'

        if idx in TREE_CLUSTER and occ > 2:
            rel_r, rel_c = (row - tr_min_r) / height, (col - tr_min_c) / width
            if rel_r < 0.45 and g >= r and g >= b: desc = f'Decoration - large tree {canopy_quadrant(rel_r, rel_c)} section'
            elif rel_r < 0.75: desc = 'Decoration - inner canopy foliage or branch'
            elif rel_r < 0.9: desc = 'Decoration - lower trunk segment'
            else: desc = 'Decoration - spreading root or base segment'
        else:
            foliage_like = g > r + 8 and g > b + 8
            pink_drip = r > 150 and b > 150 and g < 140 and occ < 60
            orange_drip = r > g + 25 and r > b + 25 and g > 60 and occ < 60
            dark_rock = r < 80 and g < 90 and b < 90
            vertical_span = sum(1 for v in info['rows_occ'] if v > 0)
            top_heavy = sum(info['rows_occ'][:3]) > sum(info['rows_occ'][3:])

            if ultra_faint: desc = 'Decoration - ultra faint fragment'
            elif orange_drip: desc = 'Decoration - glowing orange drip (stalactite piece)'
            elif pink_drip: desc = 'Decoration - glowing pink drip (stalactite piece)'
            elif foliage_like and vertical_span <= 6: desc = 'Decoration - thin hanging vine or moss strand'
            elif foliage_like and top_heavy: desc = 'Decoration - mossy overhang edge'
            elif foliage_like: desc = 'Decoration - sparse foliage cluster'
            elif dark_rock: desc = 'Decoration - dark rock or shadow fragment'
            else: desc = 'Decoration - detailed object micro-fragment'
        desc += f" (avg {info['avg_hex']})"

    output[str(idx)] = {'type': ttype, 'description': desc}

# Manual overrides
manual_overrides = {}
if os.path.exists(EXAMPLE_JSON):
    try:
        with open(EXAMPLE_JSON, 'r', encoding='utf-8') as f:
            manual_overrides.update(json.load(f))
    except Exception as e:
        print(f'Warning: failed to apply example overrides: {e}')

user_requests = {
    3:  { 'type': 'solid', 'description': 'Bottom edge solid block (ceiling)' },
    4:  { 'type': 'solid', 'description': 'Bottom edge solid block (ceiling)' },
    5:  { 'type': 'solid', 'description': 'Bottom edge solid block (ceiling)' },
    7:  { 'type': 'solid', 'description': 'Top edge solid block (floor)' },
    8:  { 'type': 'solid', 'description': 'Top edge solid block (floor)' },
    9:  { 'type': 'solid', 'description': 'Top edge solid block (floor)' },
    11: { 'type': 'decoration', 'description': 'Decoration - grass tuft (left)' },
    12: { 'type': 'decoration', 'description': 'Decoration - grass tuft (center)' },
    13: { 'type': 'decoration', 'description': 'Decoration - grass tuft (right)' },
    25: { 'type': 'decoration', 'description': 'Decoration - corner grass (left edge, descending)' },
    26: { 'type': 'decoration', 'description': 'Decoration - grass tuft' },
    27: { 'type': 'decoration', 'description': 'Decoration - grass tuft' },
    28: { 'type': 'decoration', 'description': 'Decoration - grass tuft' },
}
for k, v in user_requests.items():
    manual_overrides[str(k)] = v

for k,v in manual_overrides.items():
    output[k] = v

# Final sort and save
sorted_output = {k: output[k] for k in sorted(output, key=lambda x:int(x))}

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(sorted_output, f, indent=4)

with open(RAW_DEBUG_JSON, 'w', encoding='utf-8') as f:
    json.dump(raw_tiles, f, indent=2)

print(f"Adaptive threshold chosen: {selected_threshold}% (plus ultra-faint pass at {ULTRA_FAINT_THRESHOLD}%)")
print(f"Generated {len(sorted_output)} tile entries -> {OUTPUT_JSON}")
counts = defaultdict(int)
for v in sorted_output.values():
    counts[v['type']] += 1
print('Type counts:', dict(counts))
