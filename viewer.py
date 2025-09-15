import os
import sys
import json
import re
from typing import List, Tuple, Set

import pygame


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ASSET_PATH = os.path.join(SCRIPT_DIR, "Assests", "Sword Master Sprite Sheet 90x37.png")


def compute_grid(image_w: int, image_h: int, fw: int, fh: int, margin: int, spacing: int) -> Tuple[int, int]:
    # n <= floor((image_w - margin + spacing) / (fw + spacing))
    cols = max(0, (image_w - margin + spacing) // (fw + spacing))
    rows = max(0, (image_h - margin + spacing) // (fh + spacing))
    return int(cols), int(rows)


def rect_for(r: int, c: int, fw: int, fh: int, margin: int, spacing: int) -> pygame.Rect:
    x = margin + c * (fw + spacing)
    y = margin + r * (fh + spacing)
    return pygame.Rect(x, y, fw, fh)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Sprite Sheet Frame Viewer")
    font = pygame.font.SysFont(None, 18)

    # Configurable defaults (you can tweak while running):
    frame_w, frame_h = 90, 37
    margin, spacing = 0, 0

    # Load sprite sheet
    if not os.path.exists(ASSET_PATH):
        print(f"Sprite sheet not found at: {ASSET_PATH}")
        sys.exit(1)
    raw_sheet = pygame.image.load(ASSET_PATH)  # delay convert_alpha() until window is created
    img_w, img_h = raw_sheet.get_width(), raw_sheet.get_height()

    cols, rows = compute_grid(img_w, img_h, frame_w, frame_h, margin, spacing)
    cursor_r, cursor_c = 0, 0

    # Selection state
    selected_order: List[Tuple[int, int]] = []  # order of selection
    selected_set: Set[Tuple[int, int]] = set()

    # Header height reserved for UI text so it doesn't overlap the sheet
    HEADER_H = 110

    # Window size and scale to fit (include header height)
    win_w, win_h = max(1000, img_w), max(600, img_h + HEADER_H)
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    def compute_scale() -> float:
        # Use available height excluding header panel
        avail_w = screen.get_width()
        avail_h = max(50, screen.get_height() - HEADER_H)
        scale = min(avail_w / img_w, avail_h / img_h)
        # Snap to a reasonable integer-ish zoom for crispness when possible
        if scale > 3.0:
            return 4.0
        if scale > 2.0:
            return 3.0
        if scale > 1.5:
            return 2.0
        return max(1.0, scale)

    show_grid = True
    show_help = True
    # Trim / pivot analysis toggle
    analyze_mode = False

    # Viewport scroll (in scaled pixels)
    scroll_x = 0
    scroll_y = 0
    dragging_v = False
    dragging_h = False
    drag_off_y = 0
    drag_off_x = 0

    # Optional auto-exit for smoke tests
    auto_exit = None
    try:
        v = os.environ.get("AUTO_EXIT_SEC")
        if v:
            auto_exit = float(v)
    except Exception:
        auto_exit = None
    elapsed = 0.0

    def toggle_select(r: int, c: int) -> None:
        key = (r, c)
        if key in selected_set:
            selected_set.remove(key)
            # remove first occurrence from order
            for i, rc in enumerate(selected_order):
                if rc == key:
                    selected_order.pop(i)
                    break
        else:
            selected_set.add(key)
            selected_order.append(key)

    def clear_selection() -> None:
        selected_set.clear()
        selected_order.clear()

    def select_row(r: int) -> None:
        for c in range(cols):
            key = (r, c)
            if key not in selected_set:
                selected_set.add(key)
                selected_order.append(key)

    # --- Trimming / pivot analysis cache & helpers ---
    analyze_cache = {}  # key: (r,c,frame_w,frame_h,margin,spacing) -> (trim_rect, (pivot_x,pivot_y), orig_rect)

    def clear_analysis_cache():
        analyze_cache.clear()

    def analyze_frame(r: int, c: int):
        """Compute trimmed non-transparent bounding box and bottom-center pivot for frame (r,c).
        Returns ( (tx,ty,tw,th), (pivot_x, pivot_y), orig_rect ). Coordinates in sheet space.
        pivot_* are relative to trimmed rect (0..tw-1 / 0..th-1).
        """
        key = (r, c, frame_w, frame_h, margin, spacing)
        if key in analyze_cache:
            return analyze_cache[key]
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return None
        orig = rect_for(r, c, frame_w, frame_h, margin, spacing)
        # Guard against out of bounds (should not happen if grid computed correctly)
        if orig.right > img_w or orig.bottom > img_h:
            analyze_cache[key] = None
            return None
        sub = raw_sheet.subsurface(orig).copy().convert_alpha()
        w, h = sub.get_width(), sub.get_height()
        threshold = 16
        min_x, min_y = w, h
        max_x, max_y = -1, -1
        # Pixel scan
        # (For 90x37 this is trivial cost; if larger you could use pygame.surfarray for speed.)
        for yy in range(h):
            for xx in range(w):
                if sub.get_at((xx, yy)).a > threshold:
                    if xx < min_x: min_x = xx
                    if yy < min_y: min_y = yy
                    if xx > max_x: max_x = xx
                    if yy > max_y: max_y = yy
        if max_x == -1:
            # No opaque pixels found; fall back to full frame
            trim = (orig.x, orig.y, orig.w, orig.h)
            pivot_x = orig.w // 2
            pivot_y = orig.h - 1
        else:
            tw = max_x - min_x + 1
            th = max_y - min_y + 1
            trim = (orig.x + min_x, orig.y + min_y, tw, th)
            pivot_x = tw // 2
            pivot_y = th - 1
        result = (trim, (pivot_x, pivot_y), orig)
        analyze_cache[key] = result
        return result

    def clamp_scroll(view_w: int, view_h: int, scale: float) -> None:
        nonlocal scroll_x, scroll_y
        scaled_w, scaled_h = int(img_w * scale), int(img_h * scale)
        max_x = max(0, scaled_w - view_w)
        max_y = max(0, scaled_h - view_h)
        scroll_x = max(0, min(scroll_x, max_x))
        scroll_y = max(0, min(scroll_y, max_y))

    def ensure_cell_visible(r: int, c: int, view_w: int, view_h: int, scale: float) -> None:
        nonlocal scroll_x, scroll_y
        rect = rect_for(r, c, frame_w, frame_h, margin, spacing)
        rx = int(rect.x * scale)
        ry = int(rect.y * scale)
        rw = int(rect.w * scale)
        rh = int(rect.h * scale)
        if rx < scroll_x:
            scroll_x = rx
        elif rx + rw > scroll_x + view_w:
            scroll_x = rx + rw - view_w
        if ry < scroll_y:
            scroll_y = ry
        elif ry + rh > scroll_y + view_h:
            scroll_y = ry + rh - view_h
        clamp_scroll(view_w, view_h, scale)

    # --- Interactive save dialog state ---
    save_mode = False
    save_prompts = [("Animation name", "walk"), ("Folder", "data")]  # order of prompts
    save_index = 0
    save_inputs: List[str] = ["", ""]
    current_text = ""

    def sanitize_name(name: str) -> str:
        name = name.strip().replace(" ", "_")
        name = re.sub(r"[^A-Za-z0-9_]", "", name)
        return name or "anim"

    def begin_save_dialog():
        nonlocal save_mode, save_index, save_inputs, current_text
        if not selected_order:
            print("No frames selected; nothing to save.")
            return
        save_mode = True
        save_index = 0
        save_inputs = ["", ""]
        current_text = ""
        pygame.key.start_text_input()

    def cancel_save():
        nonlocal save_mode, save_index, current_text
        save_mode = False
        save_index = 0
        current_text = ""
        pygame.key.stop_text_input()

    def commit_current_input():
        nonlocal save_mode, save_index, current_text
        label, default_val = save_prompts[save_index]
        val = current_text.strip() if current_text.strip() else default_val
        save_inputs[save_index] = val
        save_index += 1
        current_text = ""
        if save_index >= len(save_prompts):
            finalize_save()

    def finalize_save():
        nonlocal save_mode
        anim_name_raw = save_inputs[0]
        folder_raw = save_inputs[1]
        anim_name = sanitize_name(anim_name_raw)
        folder = folder_raw.strip() or "data"
        target_dir = os.path.join(SCRIPT_DIR, folder)
        os.makedirs(target_dir, exist_ok=True)

        total = len(selected_order)
        rects = []
        trimmed_list = []  # (x,y,w,h, ox, oy)
        pivots_list = []   # (px, py)

        # Progress feedback renderer (header line)
        def render_progress(i: int, n: int):
            msg = f"Analyzing frame {i}/{n}..."
            # Draw into header area
            header_rect = pygame.Rect(0, 0, screen.get_width(), HEADER_H)
            pygame.draw.rect(screen, (25, 28, 36), header_rect)
            pygame.draw.line(screen, (60, 70, 90), (0, HEADER_H - 1), (screen.get_width(), HEADER_H - 1))
            surf = font.render(msg, True, (230, 230, 235))
            screen.blit(surf, (8, 6))
            pygame.display.flip()
            pygame.event.pump()

        for idx, (r, c) in enumerate(selected_order, start=1):
            render_progress(idx, total)
            rect = rect_for(r, c, frame_w, frame_h, margin, spacing)
            # Original rect entry (always present)
            entry = {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h, "row": r, "col": c}
            # Analyze trim & pivot
            res = None
            try:
                res = analyze_frame(r, c)
            except Exception:
                res = None
            if res is None:
                # Fallback to original
                tx, ty, tw, th = rect.x, rect.y, rect.w, rect.h
                pvx, pvy = rect.w // 2, rect.h - 1
                ox, oy = 0, 0
            else:
                (tx, ty, tw, th), (pvx, pvy), orig_rect = res
                ox, oy = tx - orig_rect.x, ty - orig_rect.y
            entry["trimmed"] = {"x": tx, "y": ty, "w": tw, "h": th}
            entry["offset"] = {"x": ox, "y": oy}
            entry["pivot"] = {"x": pvx, "y": pvy}
            rects.append(entry)
            trimmed_list.append((tx, ty, tw, th, ox, oy))
            pivots_list.append((pvx, pvy))

        meta = {
            "animation": anim_name,
            "sheet": os.path.relpath(ASSET_PATH, SCRIPT_DIR).replace("\\", "/"),
            "frame_size": [frame_w, frame_h],
            "margin": margin,
            "spacing": spacing,
            "rows": rows,
            "cols": cols,
            "order": "selection-order",
            "frames": rects,
        }
        json_filename = f"{anim_name}_selection.json"
        py_filename = f"{anim_name}_selection.py"
        json_path = os.path.join(target_dir, json_filename)
        py_path = os.path.join(target_dir, py_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        with open(py_path, "w", encoding="utf-8") as f:
            f.write("# Auto-generated by viewer.py\n")
            f.write(f"ANIMATION = '{anim_name}'\n")
            f.write(f"SHEET = '{meta['sheet']}'\n")
            f.write(f"FRAME_SIZE = ({frame_w}, {frame_h})\n")
            f.write(f"MARGIN = {margin}\n")
            f.write(f"SPACING = {spacing}\n")
            f.write("FRAMES = [\n")
            for rinfo in rects:
                f.write(f"    ({rinfo['x']}, {rinfo['y']}, {rinfo['w']}, {rinfo['h']}),\n")
            f.write("]\n")
            f.write("TRIMMED = [\n")
            for (tx, ty, tw, th, ox, oy) in trimmed_list:
                f.write(f"    ({tx}, {ty}, {tw}, {th}, {ox}, {oy}),\n")
            f.write("]\n")
            f.write("PIVOTS = [\n")
            for (px, py) in pivots_list:
                f.write(f"    ({px}, {py}),\n")
            f.write("]\n")
        print(f"Saved animation '{anim_name}' to: {json_path} and {py_path}")
        save_mode = False
        pygame.key.stop_text_input()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not save_mode:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_g:
                    show_grid = not show_grid

                elif event.key == pygame.K_LEFT:
                    cursor_c = max(0, cursor_c - 1)
                elif event.key == pygame.K_RIGHT:
                    cursor_c = min(max(0, cols - 1), cursor_c + 1)
                elif event.key == pygame.K_UP:
                    cursor_r = max(0, cursor_r - 1)
                elif event.key == pygame.K_DOWN:
                    cursor_r = min(max(0, rows - 1), cursor_r + 1)

                # Keep the cursor cell visible when navigating
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                    view_w = screen.get_width()
                    view_h = max(50, screen.get_height() - HEADER_H)
                    ensure_cell_visible(cursor_r, cursor_c, view_w, view_h, compute_scale())

                elif event.key == pygame.K_t:
                    analyze_mode = not analyze_mode
                elif event.key == pygame.K_SPACE:
                    toggle_select(cursor_r, cursor_c)
                elif event.key == pygame.K_c:
                    clear_selection()
                elif event.key == pygame.K_s:
                    begin_save_dialog()
                elif event.key == pygame.K_r:
                    select_row(cursor_r)

                # Adjust frame/grid params if needed
                elif event.key == pygame.K_LEFTBRACKET:  # [ decrease spacing
                    spacing = max(0, spacing - 1)
                    cols, rows = compute_grid(img_w, img_h, frame_w, frame_h, margin, spacing)
                    clear_analysis_cache()
                elif event.key == pygame.K_RIGHTBRACKET:  # ] increase spacing
                    spacing += 1
                    cols, rows = compute_grid(img_w, img_h, frame_w, frame_h, margin, spacing)
                    clear_analysis_cache()
                elif event.key == pygame.K_SEMICOLON:  # ; decrease margin
                    margin = max(0, margin - 1)
                    cols, rows = compute_grid(img_w, img_h, frame_w, frame_h, margin, spacing)
                    clear_analysis_cache()
                elif event.key == pygame.K_QUOTE:  # ' increase margin
                    margin += 1
                    cols, rows = compute_grid(img_w, img_h, frame_w, frame_h, margin, spacing)
                    clear_analysis_cache()
            elif save_mode:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        cancel_save()
                    elif event.key == pygame.K_RETURN:
                        commit_current_input()
                    elif event.key == pygame.K_BACKSPACE:
                        current_text = current_text[:-1]
                elif event.type == pygame.TEXTINPUT:
                    # Append typed text (filter nothing; sanitization on save)
                    current_text += event.text

            # Scrolling and scrollbar interactions when not in save-mode
            if not save_mode:
                if event.type == pygame.MOUSEWHEEL:
                    mods = pygame.key.get_mods()
                    view_w = screen.get_width()
                    view_h = max(50, screen.get_height() - HEADER_H)
                    scale_now = compute_scale()
                    if mods & pygame.KMOD_SHIFT:
                        scroll_x -= event.y * 50
                    else:
                        scroll_y -= event.y * 70
                        scroll_x -= event.x * 50
                    clamp_scroll(view_w, view_h, scale_now)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    view_rect = pygame.Rect(0, HEADER_H, screen.get_width(), max(0, screen.get_height() - HEADER_H))
                    scale_now = compute_scale()
                    scaled_w, scaled_h = int(img_w * scale_now), int(img_h * scale_now)
                    need_v = scaled_h > view_rect.h
                    need_h = scaled_w > view_rect.w
                    v_track = pygame.Rect(view_rect.right - 10, view_rect.y, 8, view_rect.h)
                    h_track = pygame.Rect(view_rect.x, view_rect.bottom - 10, view_rect.w, 8)
                    if need_v:
                        thumb_h = max(20, int(v_track.h * (view_rect.h / scaled_h)))
                        max_y = v_track.h - thumb_h
                        ty = v_track.y + (0 if max_y <= 0 else int((scroll_y / (scaled_h - view_rect.h)) * max_y))
                        v_thumb = pygame.Rect(v_track.x, ty, v_track.w, thumb_h)
                        if v_thumb.collidepoint(mx, my):
                            dragging_v = True
                            drag_off_y = my - v_thumb.y
                        elif v_track.collidepoint(mx, my):
                            if my < v_thumb.y:
                                scroll_y = max(0, scroll_y - int(view_rect.h * 0.9))
                            elif my > v_thumb.bottom:
                                scroll_y = min(scaled_h - view_rect.h, scroll_y + int(view_rect.h * 0.9))
                    if need_h:
                        thumb_w = max(20, int(h_track.w * (view_rect.w / scaled_w)))
                        max_x = h_track.w - thumb_w
                        tx = h_track.x + (0 if max_x <= 0 else int((scroll_x / (scaled_w - view_rect.w)) * max_x))
                        h_thumb = pygame.Rect(tx, h_track.y, thumb_w, h_track.h)
                        if h_thumb.collidepoint(mx, my):
                            dragging_h = True
                            drag_off_x = mx - h_thumb.x
                        elif h_track.collidepoint(mx, my):
                            if mx < h_thumb.x:
                                scroll_x = max(0, scroll_x - int(view_rect.w * 0.9))
                            elif mx > h_thumb.right:
                                scroll_x = min(scaled_w - view_rect.w, scroll_x + int(view_rect.w * 0.9))
                    clamp_scroll(view_rect.w, view_rect.h, scale_now)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_v = False
                    dragging_h = False
                elif event.type == pygame.MOUSEMOTION and (dragging_v or dragging_h):
                    mx, my = event.pos
                    view_rect = pygame.Rect(0, HEADER_H, screen.get_width(), max(0, screen.get_height() - HEADER_H))
                    scale_now = compute_scale()
                    scaled_w, scaled_h = int(img_w * scale_now), int(img_h * scale_now)
                    if dragging_v:
                        v_track = pygame.Rect(view_rect.right - 10, view_rect.y, 8, view_rect.h)
                        thumb_h = max(20, int(v_track.h * (view_rect.h / scaled_h)))
                        max_y = max(1, v_track.h - thumb_h)
                        rel = my - drag_off_y - v_track.y
                        rel = max(0, min(rel, max_y))
                        ratio = rel / max_y
                        scroll_y = int(ratio * (scaled_h - view_rect.h))
                    if dragging_h:
                        h_track = pygame.Rect(view_rect.x, view_rect.bottom - 10, view_rect.w, 8)
                        thumb_w = max(20, int(h_track.w * (view_rect.w / scaled_w)))
                        max_x = max(1, h_track.w - thumb_w)
                        rel = mx - drag_off_x - h_track.x
                        rel = max(0, min(rel, max_x))
                        ratio = rel / max_x
                        scroll_x = int(ratio * (scaled_w - view_rect.w))
                    clamp_scroll(view_rect.w, view_rect.h, scale_now)

        screen.fill((18, 20, 26))
        # Header panel
        header_rect = pygame.Rect(0, 0, screen.get_width(), HEADER_H)
        pygame.draw.rect(screen, (25, 28, 36), header_rect)
        pygame.draw.line(screen, (60, 70, 90), (0, HEADER_H - 1), (screen.get_width(), HEADER_H - 1))

        scale = compute_scale()
        # Ensure we have a display-ready surface now
        sheet = raw_sheet.convert_alpha()
        scaled_w, scaled_h = int(img_w * scale), int(img_h * scale)
        scaled = pygame.transform.smoothscale(sheet, (scaled_w, scaled_h)) if scale != 1.0 else sheet

        # Define viewport below header and blit only the visible portion
        view_rect = pygame.Rect(0, HEADER_H, screen.get_width(), max(0, screen.get_height() - HEADER_H))
        clamp_scroll(view_rect.w, view_rect.h, scale)
        src = pygame.Rect(scroll_x, scroll_y, view_rect.w, view_rect.h)
        src.w = max(0, min(src.w, scaled_w - src.x))
        src.h = max(0, min(src.h, scaled_h - src.y))
        if src.w > 0 and src.h > 0:
            screen.blit(scaled, view_rect.topleft, src)

        # Grid overlay
        if show_grid and cols > 0 and rows > 0:
            grid_color = (80, 100, 160)
            for r in range(rows):
                for c in range(cols):
                    rect = rect_for(r, c, frame_w, frame_h, margin, spacing)
                    rx = int(rect.x * scale) - scroll_x
                    ry = int(rect.y * scale) - scroll_y + HEADER_H
                    rw = int(rect.w * scale)
                    rh = int(rect.h * scale)
                    cell = pygame.Rect(rx, ry, rw, rh)
                    if cell.colliderect(view_rect):
                        pygame.draw.rect(screen, grid_color, cell, 1)

        # Draw selected cells
        for (r, c) in selected_set:
            rect = rect_for(r, c, frame_w, frame_h, margin, spacing)
            rx = int(rect.x * scale) - scroll_x
            ry = int(rect.y * scale) - scroll_y + HEADER_H
            rw = int(rect.w * scale)
            rh = int(rect.h * scale)
            cell = pygame.Rect(rx, ry, rw, rh)
            if cell.colliderect(view_rect):
                pygame.draw.rect(screen, (60, 200, 120), cell, 2)

        # Draw cursor highlight
        if cols > 0 and rows > 0:
            rect = rect_for(cursor_r, cursor_c, frame_w, frame_h, margin, spacing)
            rx = int(rect.x * scale) - scroll_x
            ry = int(rect.y * scale) - scroll_y + HEADER_H
            rw = int(rect.w * scale)
            rh = int(rect.h * scale)
            cell = pygame.Rect(rx, ry, rw, rh)
            if cell.colliderect(view_rect):
                pygame.draw.rect(screen, (240, 220, 60), cell, 3)

        # Analysis overlay: trimmed bounding box + pivot cross
        analyze_info_line = None
        if analyze_mode:
            res = analyze_frame(cursor_r, cursor_c)
            if res:
                (tx, ty, tw, th), (pvx, pvy), orig_rect = res
                tr_rx = int(tx * scale) - scroll_x
                tr_ry = int(ty * scale) - scroll_y + HEADER_H
                tr_rw = int(tw * scale)
                tr_rh = int(th * scale)
                trimmed_rect_vp = pygame.Rect(tr_rx, tr_ry, tr_rw, tr_rh)
                if trimmed_rect_vp.colliderect(view_rect):
                    pygame.draw.rect(screen, (50, 210, 255), trimmed_rect_vp, 2)
                # Pivot in sheet coords
                pv_sheet_x = tx + pvx
                pv_sheet_y = ty + pvy
                pv_rx = int(pv_sheet_x * scale) - scroll_x
                pv_ry = int(pv_sheet_y * scale) - scroll_y + HEADER_H
                pygame.draw.line(screen, (255, 80, 180), (pv_rx - 4, pv_ry), (pv_rx + 4, pv_ry), 2)
                pygame.draw.line(screen, (255, 80, 180), (pv_rx, pv_ry - 4), (pv_rx, pv_ry + 4), 2)
                analyze_info_line = (
                    f"Orig: ({orig_rect.x},{orig_rect.y},{orig_rect.w},{orig_rect.h})  "
                    f"Trim: ({tx},{ty},{tw},{th})  Pivot: ({pvx},{pvy})"
                )

        # HUD text
        info_lines = [
            f"Sheet: {os.path.basename(ASSET_PATH)}  {img_w}x{img_h}",
            f"Frame: {frame_w}x{frame_h}  margin:{margin} spacing:{spacing}  grid: {rows}x{cols}",
            f"Cursor: r={cursor_r} c={cursor_c}  selected:{len(selected_order)}",
        ]
        if show_help and not save_mode:
            info_lines += [
                "Arrows move  Space select  R row-select  C clear",
                "Mouse wheel scroll (Shift=horizontal), drag scrollbars",
                "T trim-analyze  S save  G grid  H help  [ ] spacing  ; ' margin  Esc quit",
            ]
        if save_mode:
            label, default_val = save_prompts[save_index]
            preview = []
            for i, (lab, defv) in enumerate(save_prompts):
                if i < save_index:
                    preview.append(f"{lab}: {save_inputs[i]}")
                elif i == save_index:
                    cur = current_text or f"[{defv}]"
                    preview.append(f"{lab}: {cur}")
                else:
                    preview.append(f"{lab}: ...")
            info_lines += ["Saving (Enter=OK Esc=cancel)"] + preview

        if analyze_mode and analyze_info_line:
            info_lines.append(analyze_info_line)

        y = 6
        for line in info_lines:
            surf = font.render(line, True, (230, 230, 235))
            screen.blit(surf, (8, y))
            y += surf.get_height() + 2

        # Draw scrollbars if content exceeds viewport
        need_v = scaled_h > view_rect.h
        need_h = scaled_w > view_rect.w
        if need_v:
            v_track = pygame.Rect(view_rect.right - 10, view_rect.y, 8, view_rect.h)
            pygame.draw.rect(screen, (40, 45, 60), v_track)
            thumb_h = max(20, int(v_track.h * (view_rect.h / scaled_h)))
            max_y = v_track.h - thumb_h
            ty = v_track.y + (0 if max_y <= 0 else int((scroll_y / (scaled_h - view_rect.h)) * max_y))
            v_thumb = pygame.Rect(v_track.x, ty, v_track.w, thumb_h)
            pygame.draw.rect(screen, (120, 130, 160), v_thumb)
        if need_h:
            h_track = pygame.Rect(view_rect.x, view_rect.bottom - 10, view_rect.w, 8)
            pygame.draw.rect(screen, (40, 45, 60), h_track)
            thumb_w = max(20, int(h_track.w * (view_rect.w / scaled_w)))
            max_x = h_track.w - thumb_w
            tx = h_track.x + (0 if max_x <= 0 else int((scroll_x / (scaled_w - view_rect.w)) * max_x))
            h_thumb = pygame.Rect(tx, h_track.y, thumb_w, h_track.h)
            pygame.draw.rect(screen, (120, 130, 160), h_thumb)

        pygame.display.flip()
        dt = clock.tick(60) / 1000.0
        if auto_exit is not None:
            elapsed += dt
            if elapsed >= auto_exit:
                running = False

    pygame.quit()


if __name__ == "__main__":
    main()
