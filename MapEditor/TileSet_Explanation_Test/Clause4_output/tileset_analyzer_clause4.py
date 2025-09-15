import json, os, math
from collections import deque, defaultdict
from statistics import mean
from PIL import Image

"""
Comprehensive Tileset Analysis for Clause 4
- Analyzes 24x24 grid of 16x16 pixel tiles (576 total)
- Identifies non-blank tiles and classifies as solid/platform/decoration
- Generates detailed semantic descriptions for each tile type
- Incorporates manual overrides from example JSON
- Targets ~294 non-blank tile entries
"""

# Configuration
TILE_SIZE = 16
COLS = 24
ROWS = 24
TOTAL_TILES = COLS * ROWS  # 576

# Adaptive thresholds for tile detection
MAIN_THRESHOLDS = [1.0, 0.6, 0.3, 0.15]
ULTRA_FAINT_THRESHOLD = 0.05
TARGET_TILE_COUNT = 294
TARGET_RANGE = 20  # +/- range around target

# Classification thresholds
SOLID_MIN_PCT = 65.0
SOLID_SECONDARY_MIN_PCT = 55.0
PLATFORM_TOP_FOCUS = 0.75
PLATFORM_BOTTOM_MAX = 0.35

# File paths
ROOT = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT, 'Clause4_output')
IMAGE_PATH = os.path.join(ROOT, 'Caves_Full_Tileset.png')
EXAMPLE_JSON_PATH = os.path.join(ROOT, 'tileset_JSon_Example.json')
OUTPUT_JSON = os.path.join(OUTPUT_DIR, 'tileset_comprehensive_analysis.json')
DEBUG_OUTPUT = os.path.join(OUTPUT_DIR, 'analysis_debug_data.json')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Verify tileset image exists
if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(f"Tileset image not found: {IMAGE_PATH}")

print(f"Loading tileset image: {IMAGE_PATH}")
im = Image.open(IMAGE_PATH).convert('RGBA')
W, H = im.size

# Validate image dimensions
expected_w, expected_h = COLS * TILE_SIZE, ROWS * TILE_SIZE
if W != expected_w or H != expected_h:
    raise ValueError(f"Image dimensions {W}x{H} don't match expected {expected_w}x{expected_h}")

print(f"Image validated: {W}x{H} pixels ({COLS}x{ROWS} tiles)")

def extract_tile_data(tile_index):
    """Extract comprehensive data for a single tile"""
    row, col = divmod(tile_index, COLS)
    box = (col * TILE_SIZE, row * TILE_SIZE, (col + 1) * TILE_SIZE, (row + 1) * TILE_SIZE)
    tile = im.crop(box)
    pixels = list(tile.getdata())
    
    # Count opaque pixels
    opaque_pixels = [p for p in pixels if p[3] > 0]
    total_pixels = TILE_SIZE * TILE_SIZE
    occupancy_pct = (len(opaque_pixels) / total_pixels) * 100.0
    
    if not opaque_pixels:
        return None
    
    # Row-by-row occupancy analysis
    row_occupancies = []
    for y in range(TILE_SIZE):
        row_pixels = pixels[y * TILE_SIZE:(y + 1) * TILE_SIZE]
        opaque_count = sum(1 for p in row_pixels if p[3] > 0)
        row_occupancies.append(opaque_count)
    
    # Vertical distribution analysis
    top_half = sum(row_occupancies[:TILE_SIZE // 2])
    bottom_half = sum(row_occupancies[TILE_SIZE // 2:])
    total_opaque = top_half + bottom_half
    
    if total_opaque > 0:
        top_fraction = top_half / total_opaque
        bottom_fraction = bottom_half / total_opaque
    else:
        top_fraction = bottom_fraction = 0
    
    # Color analysis
    avg_r = mean(p[0] for p in opaque_pixels)
    avg_g = mean(p[1] for p in opaque_pixels)
    avg_b = mean(p[2] for p in opaque_pixels)
    avg_hex = f"#{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}"
    
    return {
        'index': tile_index,
        'row': row,
        'col': col,
        'occupancy_pct': occupancy_pct,
        'opaque_count': len(opaque_pixels),
        'top_fraction': top_fraction,
        'bottom_fraction': bottom_fraction,
        'avg_color': (avg_r, avg_g, avg_b),
        'avg_hex': avg_hex,
        'row_occupancies': row_occupancies,
        'vertical_span': sum(1 for count in row_occupancies if count > 0)
    }

# Phase 1: Adaptive tile detection
print("Phase 1: Detecting non-blank tiles...")
detected_tiles = {}
selected_threshold = None

for threshold in MAIN_THRESHOLDS:
    tiles_at_threshold = {}
    
    for tile_idx in range(TOTAL_TILES):
        tile_data = extract_tile_data(tile_idx)
        if tile_data and tile_data['occupancy_pct'] >= threshold:
            tiles_at_threshold[tile_idx] = tile_data
    
    tile_count = len(tiles_at_threshold)
    print(f"  Threshold {threshold}%: {tile_count} tiles")
    
    # Check if we're in target range
    if TARGET_TILE_COUNT - TARGET_RANGE <= tile_count <= TARGET_TILE_COUNT + TARGET_RANGE:
        detected_tiles = tiles_at_threshold
        selected_threshold = threshold
        print(f"  ✓ Selected threshold: {threshold}% ({tile_count} tiles)")
        break
    
    # Keep best attempt
    if not detected_tiles or abs(tile_count - TARGET_TILE_COUNT) < abs(len(detected_tiles) - TARGET_TILE_COUNT):
        detected_tiles = tiles_at_threshold
        selected_threshold = threshold

# Phase 2: Ultra-faint tile inclusion
print("Phase 2: Including ultra-faint tiles...")
faint_tiles_added = 0

for tile_idx in range(TOTAL_TILES):
    if tile_idx in detected_tiles:
        continue
    
    tile_data = extract_tile_data(tile_idx)
    if tile_data and 0 < tile_data['occupancy_pct'] <= ULTRA_FAINT_THRESHOLD:
        tile_data['ultra_faint'] = True
        detected_tiles[tile_idx] = tile_data
        faint_tiles_added += 1

print(f"  Added {faint_tiles_added} ultra-faint tiles")
print(f"  Total tiles detected: {len(detected_tiles)}")

# Phase 3: Tile classification
print("Phase 3: Classifying tiles...")
classifications = {}
solid_tiles = set()
platform_tiles = set()
decoration_tiles = set()

for tile_idx, tile_data in detected_tiles.items():
    occ = tile_data['occupancy_pct']
    top_frac = tile_data['top_fraction']
    bottom_frac = tile_data['bottom_fraction']
    
    # Classification logic
    if tile_data.get('ultra_faint'):
        tile_type = 'decoration'
    elif occ >= SOLID_MIN_PCT:
        tile_type = 'solid'
    elif occ >= SOLID_SECONDARY_MIN_PCT and abs(top_frac - 0.5) < 0.2:
        tile_type = 'solid'
    elif (occ < SOLID_MIN_PCT and 
          top_frac >= PLATFORM_TOP_FOCUS and 
          bottom_frac <= PLATFORM_BOTTOM_MAX and 
          occ > 10):
        tile_type = 'platform'
    else:
        tile_type = 'decoration'
    
    classifications[tile_idx] = tile_type
    
    if tile_type == 'solid':
        solid_tiles.add(tile_idx)
    elif tile_type == 'platform':
        platform_tiles.add(tile_idx)
    else:
        decoration_tiles.add(tile_idx)

print(f"  Solid: {len(solid_tiles)}, Platform: {len(platform_tiles)}, Decoration: {len(decoration_tiles)}")

# Phase 4: Neighbor analysis for solid/platform descriptions
print("Phase 4: Analyzing spatial relationships...")
solid_neighbors = {}
platform_neighbors = {}

for tile_idx in solid_tiles:
    row, col = divmod(tile_idx, COLS)
    neighbors = {
        'up': (row - 1, col) if row > 0 else None,
        'down': (row + 1, col) if row < ROWS - 1 else None,
        'left': (row, col - 1) if col > 0 else None,
        'right': (row, col + 1) if col < COLS - 1 else None
    }
    
    solid_neighbors[tile_idx] = {}
    for direction, pos in neighbors.items():
        if pos:
            neighbor_idx = pos[0] * COLS + pos[1]
            solid_neighbors[tile_idx][direction] = neighbor_idx in solid_tiles
        else:
            solid_neighbors[tile_idx][direction] = False

for tile_idx in platform_tiles:
    row, col = divmod(tile_idx, COLS)
    platform_neighbors[tile_idx] = {
        'left': ((row, col - 1) if col > 0 else None),
        'right': ((row, col + 1) if col < COLS - 1 else None)
    }
    
    for direction, pos in platform_neighbors[tile_idx].items():
        if pos:
            neighbor_idx = pos[0] * COLS + pos[1]
            platform_neighbors[tile_idx][direction] = neighbor_idx in platform_tiles
        else:
            platform_neighbors[tile_idx][direction] = False

# Phase 5: Connected component analysis for decorations
print("Phase 5: Analyzing decoration clusters...")
visited_decorations = set()
decoration_clusters = []

for tile_idx in decoration_tiles:
    if tile_idx in visited_decorations:
        continue
    
    # BFS to find connected component
    cluster = set()
    queue = deque([tile_idx])
    cluster.add(tile_idx)
    visited_decorations.add(tile_idx)
    
    min_row = max_row = divmod(tile_idx, COLS)[0]
    min_col = max_col = divmod(tile_idx, COLS)[1]
    
    while queue:
        current = queue.popleft()
        curr_row, curr_col = divmod(current, COLS)
        
        min_row, max_row = min(min_row, curr_row), max(max_row, curr_row)
        min_col, max_col = min(min_col, curr_col), max(max_col, curr_col)
        
        # Check 4-connected neighbors
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = curr_row + dr, curr_col + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                neighbor_idx = nr * COLS + nc
                if (neighbor_idx in decoration_tiles and 
                    neighbor_idx not in visited_decorations):
                    cluster.add(neighbor_idx)
                    queue.append(neighbor_idx)
                    visited_decorations.add(neighbor_idx)
    
    bbox = (min_row, min_col, max_row, max_col)
    decoration_clusters.append((cluster, bbox))

# Find largest cluster (likely the tree)
largest_cluster = max(decoration_clusters, key=lambda x: len(x[0])) if decoration_clusters else (set(), (0, 0, 0, 0))
tree_cluster, tree_bbox = largest_cluster
tree_height = tree_bbox[2] - tree_bbox[0] + 1
tree_width = tree_bbox[3] - tree_bbox[1] + 1

print(f"  Found {len(decoration_clusters)} decoration clusters")
print(f"  Largest cluster: {len(tree_cluster)} tiles (likely tree)")

# Phase 6: Generate descriptions
print("Phase 6: Generating tile descriptions...")
final_output = {}

for tile_idx, tile_data in detected_tiles.items():
    tile_type = classifications[tile_idx]
    description = ""
    
    if tile_type == 'solid':
        # Solid block descriptions based on neighbors
        neighbors = solid_neighbors[tile_idx]
        up, down, left, right = neighbors['up'], neighbors['down'], neighbors['left'], neighbors['right']
        
        if not up and not left and right and down:
            description = "Top left corner solid block"
        elif not up and not right and left and down:
            description = "Top right corner solid block"
        elif not down and not left and right and up:
            description = "Bottom left corner solid block"
        elif not down and not right and left and up:
            description = "Bottom right corner solid block"
        elif not up and left and right and down:
            description = "Top edge solid block"
        elif not down and left and right and up:
            description = "Bottom edge solid block"
        elif not left and up and down and right:
            description = "Left side solid block"
        elif not right and up and down and left:
            description = "Right side solid block"
        else:
            description = "Middle fill solid block"
    
    elif tile_type == 'platform':
        # Platform descriptions based on neighbors
        neighbors = platform_neighbors[tile_idx]
        left, right = neighbors['left'], neighbors['right']
        
        if not left and right:
            description = "Left side platform (one-way)"
        elif left and right:
            description = "Middle platform (one-way)"
        elif left and not right:
            description = "Right side platform (one-way)"
        else:
            description = "Single platform (one-way)"
    
    else:  # decoration
        # Detailed decoration descriptions
        r, g, b = tile_data['avg_color']
        occ = tile_data['occupancy_pct']
        ultra_faint = tile_data.get('ultra_faint', False)
        
        if ultra_faint:
            description = "Decoration - ultra faint fragment"
        elif tile_idx in tree_cluster:
            # Tree part descriptions
            rel_row = (tile_data['row'] - tree_bbox[0]) / max(1, tree_height)
            rel_col = (tile_data['col'] - tree_bbox[1]) / max(1, tree_width)
            
            if rel_row < 0.4 and g > r and g > b:
                # Upper canopy
                horiz = "left" if rel_col < 0.33 else "right" if rel_col > 0.66 else "center"
                vert = "top" if rel_row < 0.2 else "upper"
                description = f"Decoration - large tree canopy ({vert}-{horiz} section)"
            elif rel_row < 0.7:
                # Middle tree area
                if g > r + 15:
                    description = "Decoration - inner canopy foliage cluster"
                else:
                    description = "Decoration - tree trunk segment"
            elif rel_row < 0.9:
                description = "Decoration - lower trunk segment"
            else:
                description = "Decoration - tree root or base segment"
        else:
            # Other decorations
            is_foliage = g > r + 8 and g > b + 8
            is_orange_drip = r > g + 25 and r > b + 25 and g > 60 and occ < 60
            is_pink_drip = r > 150 and b > 150 and g < 140 and occ < 60
            is_dark_rock = r < 80 and g < 90 and b < 90
            is_vertical = tile_data['vertical_span'] >= 10
            is_sparse = occ < 40
            
            if is_orange_drip:
                description = "Decoration - glowing orange drip (stalactite piece)"
            elif is_pink_drip:
                description = "Decoration - glowing pink drip (stalactite piece)"
            elif is_foliage and is_vertical and is_sparse:
                description = "Decoration - hanging vine or moss strand"
            elif is_foliage and tile_data['top_fraction'] > 0.6:
                description = "Decoration - mossy overhang edge"
            elif is_foliage:
                density = "dense" if occ > 60 else "sparse"
                description = f"Decoration - {density} foliage cluster"
            elif is_dark_rock:
                description = "Decoration - dark rock or shadow fragment"
            elif is_vertical:
                description = "Decoration - vertical structural element"
            else:
                description = "Decoration - miscellaneous object fragment"
        
        # Add color information for decorations
        description += f" (avg {tile_data['avg_hex']})"
    
    final_output[str(tile_idx)] = {
        "type": tile_type,
        "description": description
    }

# Phase 7: Apply manual overrides from example JSON
print("Phase 7: Applying manual overrides...")
manual_overrides_applied = 0

if os.path.exists(EXAMPLE_JSON_PATH):
    try:
        with open(EXAMPLE_JSON_PATH, 'r', encoding='utf-8') as f:
            example_data = json.load(f)
        
        for tile_key, tile_info in example_data.items():
            if tile_key in final_output:
                final_output[tile_key].update(tile_info)
                manual_overrides_applied += 1
            else:
                # Include even if not detected by automatic analysis
                final_output[tile_key] = tile_info
                manual_overrides_applied += 1
        
        print(f"  Applied {manual_overrides_applied} manual overrides")
    except Exception as e:
        print(f"  Warning: Could not load example JSON: {e}")

# Sort output by tile index
sorted_output = dict(sorted(final_output.items(), key=lambda x: int(x[0])))

# Phase 8: Save results
print("Phase 8: Saving results...")

with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(sorted_output, f, indent=4, ensure_ascii=False)

# Save debug data
debug_data = {
    'analysis_summary': {
        'total_tiles_analyzed': TOTAL_TILES,
        'non_blank_tiles_found': len(detected_tiles),
        'selected_threshold': selected_threshold,
        'ultra_faint_threshold': ULTRA_FAINT_THRESHOLD,
        'faint_tiles_added': faint_tiles_added,
        'final_tile_count': len(sorted_output)
    },
    'type_distribution': {
        'solid': len(solid_tiles),
        'platform': len(platform_tiles), 
        'decoration': len(decoration_tiles)
    },
    'tree_analysis': {
        'tree_cluster_size': len(tree_cluster),
        'tree_bbox': tree_bbox,
        'tree_dimensions': f"{tree_width}x{tree_height}"
    },
    'decoration_clusters': len(decoration_clusters)
}

with open(DEBUG_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(debug_data, f, indent=2)

# Final summary
print(f"\n=== ANALYSIS COMPLETE ===")
print(f"Total tiles processed: {TOTAL_TILES}")
print(f"Non-blank tiles found: {len(sorted_output)}")
print(f"Target was ~{TARGET_TILE_COUNT} tiles")
print(f"Threshold used: {selected_threshold}% + ultra-faint at {ULTRA_FAINT_THRESHOLD}%")
print(f"\nType distribution:")
print(f"  Solid blocks: {len(solid_tiles)}")
print(f"  Platforms: {len(platform_tiles)}")  
print(f"  Decorations: {len(decoration_tiles)}")
print(f"\nOutput files:")
print(f"  Main JSON: {OUTPUT_JSON}")
print(f"  Debug data: {DEBUG_OUTPUT}")
print(f"\nManual overrides applied: {manual_overrides_applied}")
