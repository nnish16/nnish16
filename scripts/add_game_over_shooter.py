#!/usr/bin/env python3
"""
Post-process shooter.gif:
  1. Extend canvas by HUD_H pixels at the top (hearts, score, level)
  2. Score counter animates 0→total across the original game frames
  3. Append an authentic STAGE CLEAR end screen

Usage:
    python scripts/add_game_over_shooter.py [input.gif] [output.gif] [--stats stats.json]
    Defaults: shooter.gif -> shooter.gif (in-place), no stats (zeros)
"""
import sys, json, random, math
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Palette (from actual shooter.gif analysis)
# ---------------------------------------------------------------------------
BG_COLOR   = (13, 17, 23)       # #0d1117  — space background
SHIP_BLUE  = (68, 147, 248)     # #4493f8  — player ship / HUD accent
GREEN_HI   = (87, 242, 135)     # #57f287  — bright green
GREEN_MID  = (57, 211, 83)      # #39d353
GREEN_DIM  = (38, 166, 65)      # #26a641
GOLD       = (255, 213, 0)      # arcade yellow-gold
RED_FULL   = (255, 50, 50)      # full-life heart
RED_EMPTY  = (80, 20, 20)       # empty heart outline
WHITE      = (255, 255, 255)

# HUD strip dimensions
HUD_H      = 34                  # pixels above the game

# ---------------------------------------------------------------------------
# 5×7 pixel-art font  (7 rows × 5 cols)
# ---------------------------------------------------------------------------
PIXEL_FONT = {
    ' ': [[0]*5]*7,
    '!': [[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,0,0,0],[0,0,1,0,0]],
    '>': [[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],
          [0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0]],
    '<': [[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],
          [0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]],
    '0': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,1,1],[1,0,1,0,1],
          [1,1,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '1': [[0,0,1,0,0],[0,1,1,0,0],[0,0,1,0,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[0,1,1,1,0]],
    '2': [[0,1,1,1,0],[1,0,0,0,1],[0,0,0,0,1],[0,0,0,1,0],
          [0,0,1,0,0],[0,1,0,0,0],[1,1,1,1,1]],
    '3': [[1,1,1,1,0],[0,0,0,0,1],[0,0,0,0,1],[0,1,1,1,0],
          [0,0,0,0,1],[0,0,0,0,1],[1,1,1,1,0]],
    '4': [[0,0,0,1,0],[0,0,1,1,0],[0,1,0,1,0],[1,0,0,1,0],
          [1,1,1,1,1],[0,0,0,1,0],[0,0,0,1,0]],
    '5': [[1,1,1,1,1],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],
          [0,0,0,0,1],[0,0,0,0,1],[1,1,1,1,0]],
    '6': [[0,1,1,1,0],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '7': [[1,1,1,1,1],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    '8': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '9': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,1],
          [0,0,0,0,1],[0,0,0,0,1],[0,1,1,1,0]],
    'A': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,1],
          [1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'C': [[0,1,1,1,1],[1,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0],
          [1,0,0,0,0],[1,0,0,0,0],[0,1,1,1,1]],
    'E': [[1,1,1,1,1],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],
          [1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,1]],
    'G': [[0,1,1,1,0],[1,0,0,0,0],[1,0,0,0,0],[1,0,1,1,1],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    'I': [[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[1,1,1,1,1]],
    'L': [[1,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0],
          [1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,1]],
    'M': [[1,0,0,0,1],[1,1,0,1,1],[1,0,1,0,1],[1,0,0,0,1],
          [1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'N': [[1,0,0,0,1],[1,1,0,0,1],[1,0,1,0,1],[1,0,0,1,1],
          [1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'O': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    'P': [[1,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,0],
          [1,0,0,0,0],[1,0,0,0,0],[1,0,0,0,0]],
    'R': [[1,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,0],
          [1,0,1,0,0],[1,0,0,1,0],[1,0,0,0,1]],
    'S': [[0,1,1,1,1],[1,0,0,0,0],[1,0,0,0,0],[0,1,1,1,0],
          [0,0,0,0,1],[0,0,0,0,1],[1,1,1,1,0]],
    'T': [[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    'U': [[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    'V': [[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],
          [1,0,0,0,1],[0,1,0,1,0],[0,0,1,0,0]],
    'W': [[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,1,0,1],
          [1,0,1,0,1],[1,1,0,1,1],[1,0,0,0,1]],
    'Y': [[1,0,0,0,1],[1,0,0,0,1],[0,1,0,1,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
}

# ---------------------------------------------------------------------------
# Heart bitmap  (5 wide × 4 tall; 1=filled pixel)
# ---------------------------------------------------------------------------
HEART_BITMAP = [
    [0,1,0,1,0],
    [1,1,1,1,1],
    [0,1,1,1,0],
    [0,0,1,0,0],
]


def draw_pixel_text(draw, text, x, y, color, px=2, gap=1,
                    right_align_x=None, center_in_width=None):
    """Render pixel-art text. Supports left / right-aligned / centred modes."""
    char_w  = 5 * (px + gap)
    char_gap = px + 1
    text_w  = len(text) * (char_w + char_gap) - char_gap

    if center_in_width is not None:
        x = (center_in_width - text_w) // 2
    elif right_align_x is not None:
        x = right_align_x - text_w

    cx = x
    for ch in text:
        bm = PIXEL_FONT.get(ch, PIXEL_FONT[' '])
        for ri, row in enumerate(bm):
            for ci, lit in enumerate(row):
                if lit:
                    rx = cx + ci * (px + gap)
                    ry = y  + ri * (px + gap)
                    draw.rectangle([rx, ry, rx+px-1, ry+px-1], fill=color)
        cx += char_w + char_gap
    return text_w


def px_text_w(text, px=2, gap=1):
    char_w   = 5 * (px + gap)
    char_gap = px + 1
    return len(text) * (char_w + char_gap) - char_gap


def draw_heart(draw, x, y, px=3, state='full'):
    """
    Draw one heart at (x,y).
    state: 'full'  = solid red
           'half'  = left half red, right half dim outline
           'empty' = dim outline only
    """
    fill_c   = RED_FULL
    empty_c  = RED_EMPTY
    gap = 1

    for ri, row in enumerate(HEART_BITMAP):
        for ci, lit in enumerate(row):
            if not lit:
                continue
            rx = x + ci * (px + gap)
            ry = y + ri * (px + gap)
            # Determine colour: full / half (left=red, right=dim) / empty
            if state == 'full':
                color = fill_c
            elif state == 'half':
                color = fill_c if ci < 3 else empty_c
            else:
                color = empty_c
            draw.rectangle([rx, ry, rx+px-1, ry+px-1], fill=color)


def heart_pixel_width(px=3, gap=1):
    """Total pixel width of one heart sprite."""
    return 5 * (px + gap)


def draw_hud(draw, canvas_w, score_now, level, lives_halves,
             hud_h=HUD_H, px=3, frame_index=0):
    """
    Draw the 34px HUD strip at y=0..hud_h-1.
      lives_halves  : int 0-10 (10 = 5 full hearts, 0 = 5 empty)
      score_now     : current animated score to display
      level         : int, days active (static)
      px            : pixel size for heart sprites
      frame_index   : used to drive heart blink animation
    """
    # Background strip
    draw.rectangle([0, 0, canvas_w, hud_h - 1], fill=BG_COLOR)
    # Bottom separator line (green glow)
    draw.line([(0, hud_h - 1), (canvas_w, hud_h - 1)], fill=GREEN_DIM, width=1)

    MARGIN = 8
    heart_gap = 3
    heart_w   = heart_pixel_width(px)
    heart_y   = (hud_h - 4 * (px + 1)) // 2  # vertically centred

    # ---- HEARTS (left) — blink when low health ----
    # Blink: toggle visibility every 8 frames when lives_halves <= 4
    # Classic arcade: low-health hearts flicker to warn the player
    low_health   = lives_halves <= 4
    blink_on     = (frame_index // 8) % 2 == 0   # on for 8 frames, off for 8
    # Determine which hearts are affected: the rightmost non-empty ones
    # threshold: first heart from right that is full (would blink)
    hx = MARGIN
    for i in range(5):
        filled_halves = max(0, lives_halves - i * 2)
        if filled_halves >= 2:
            state = 'full'
        elif filled_halves == 1:
            state = 'half'
        else:
            state = 'empty'

        # Blink only the last remaining non-empty heart when health is low
        is_last_heart = (filled_halves > 0 and
                         max(0, lives_halves - (i + 1) * 2) == 0)
        skip = low_health and is_last_heart and not blink_on

        if not skip:
            draw_heart(draw, hx, heart_y, px=px, state=state)
        else:
            # Draw the empty outline in place so the gap is obvious
            draw_heart(draw, hx, heart_y, px=px, state='empty')
        hx += heart_w + heart_gap

    # ---- SCORE (centre) ----
    # Label "SCORE" tiny (px=2)
    label_px = 2
    score_str = f"{score_now:06d}"
    lbl_text  = "SCORE"
    lbl_w = px_text_w(lbl_text, label_px)
    num_w = px_text_w(score_str, label_px)
    block_w = max(lbl_w, num_w)
    cx = (canvas_w - block_w) // 2

    lbl_y = 4
    num_y = lbl_y + 7 * (label_px + 1) + 2
    draw_pixel_text(draw, lbl_text, cx + (block_w - lbl_w) // 2, lbl_y,
                    GREEN_MID, px=label_px)
    draw_pixel_text(draw, score_str, cx + (block_w - num_w) // 2, num_y,
                    GOLD, px=label_px)

    # ---- LEVEL (right) ----
    lv_text = f"LV"
    lv_num  = f"{level:03d}"
    lv_w1 = px_text_w(lv_text, label_px)
    lv_w2 = px_text_w(lv_num, label_px)
    lv_block = max(lv_w1, lv_w2)
    rx = canvas_w - MARGIN - lv_block

    draw_pixel_text(draw, lv_text, rx + (lv_block - lv_w1) // 2, lbl_y,
                    GREEN_MID, px=label_px)
    draw_pixel_text(draw, lv_num, rx + (lv_block - lv_w2) // 2, num_y,
                    SHIP_BLUE, px=label_px)


# ---------------------------------------------------------------------------
# Score animation curve (seeded random walk, feels organic)
# ---------------------------------------------------------------------------
def build_score_curve(n_frames: int, total_score: int, seed: int = 2024) -> list:
    """
    Return a list of ints length n_frames+1 ramps 0 → total_score.

    Strategy: smooth linear base + small random jitter, so the score ticks
    up steadily throughout the whole game and lands on EXACTLY total_score
    at frame n_frames.

    The jitter makes it feel like real scoring events (bursts when enemies
    are hit) without the front-loading plateau bug.
    """
    if n_frames == 0 or total_score == 0:
        return [0] * (n_frames + 1)

    rng     = random.Random(seed)
    scores  = [0.0] * (n_frames + 1)

    # Linear base: each frame gets total_score/n_frames
    base_delta = total_score / n_frames

    # Jitter budget: ± up to 8% of base_delta per frame
    jitter_scale = base_delta * 0.08

    for i in range(1, n_frames + 1):
        jitter = rng.uniform(-jitter_scale, jitter_scale)
        scores[i] = scores[i - 1] + base_delta + jitter

    # Force monotone (no negative ticks) and clamp to [0, total]
    for i in range(1, n_frames + 1):
        scores[i] = max(scores[i - 1], min(float(total_score), scores[i]))

    # Force exact final value
    scores[n_frames] = float(total_score)

    return [round(s) for s in scores]


# ---------------------------------------------------------------------------
# Stage-clear end screen (same aesthetic, uses the new palette constants)
# ---------------------------------------------------------------------------
def make_stage_clear_frame(size, alpha=255, show_prompt=True,
                           score=0,
                           headline="STAGE CLEAR!", sub="YOU WIN!",
                           prompt=">>> PLAY AGAIN <<<"):
    w, h = size
    frame = Image.new('RGBA', (w, h), (*BG_COLOR, alpha))
    draw  = ImageDraw.Draw(frame)

    if alpha == 0:
        return frame
    a = min(255, alpha)

    # ---- Layout ----
    hl_px,  hl_gap  = 6, 1
    sub_px, sub_gap = 5, 1
    pr_px,  pr_gap  = 3, 1
    hl_char_h  = 7 * (hl_px  + hl_gap)
    sub_char_h = 7 * (sub_px + sub_gap)
    pr_char_h  = 7 * (pr_px  + pr_gap)
    spacing = 8
    total_h = hl_char_h + spacing + sub_char_h + spacing + pr_char_h
    start_y = (h - total_h) // 2

    # Scanlines
    if a > 128:
        for y in range(0, h, 2):
            draw.line([(0, y), (w, y)], fill=(0, 0, 0, 18))

    # Panel
    pad = 14
    panel_w = max(
        px_text_w(headline, hl_px, hl_gap),
        px_text_w(sub,      sub_px, sub_gap),
        px_text_w(prompt,   pr_px,  pr_gap),
    ) + pad * 2
    px0 = (w - panel_w) // 2
    py0 = start_y - pad
    ph  = total_h + pad * 2
    pa  = min(210, int(220 * a / 255))
    draw.rectangle([px0, py0, px0 + panel_w, py0 + ph], fill=(*BG_COLOR, pa))
    draw.rectangle([px0, py0, px0 + panel_w, py0 + ph],
                   outline=(*GREEN_MID, a), width=2)
    draw.rectangle([px0+3, py0+3, px0+panel_w-3, py0+ph-3],
                   outline=(*GREEN_DIM, a // 2), width=1)

    hl_y  = start_y
    sub_y = hl_y  + hl_char_h  + spacing
    pr_y  = sub_y + sub_char_h + spacing

    draw_pixel_text(draw, headline, 0, hl_y,  (*GREEN_HI, a),
                    px=hl_px,  gap=hl_gap,  center_in_width=w)
    draw_pixel_text(draw, sub,      0, sub_y, (*GOLD, a),
                    px=sub_px, gap=sub_gap, center_in_width=w)
    if show_prompt:
        draw_pixel_text(draw, prompt, 0, pr_y, (*SHIP_BLUE, a),
                        px=pr_px, gap=pr_gap, center_in_width=w)

    return frame


def blend(base: Image.Image, overlay: Image.Image) -> Image.Image:
    b = base.convert('RGBA')
    b.alpha_composite(overlay)
    return b.convert('RGB')


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------
def add_hud_and_game_over(input_path: str, output_path: str,
                          total_score: int = 0,
                          days_active: int = 1,
                          missed_days: int = 0,
                          frame_delay_ms: int = 50,
                          flicker_count:  int = 6,
                          solid_count:    int = 28,
                          fade_count:     int = 10,
                          dark_pause:     int = 4):

    print(f"Opening {input_path} …")
    src  = Image.open(input_path)
    game_size = src.size          # e.g. (860, 230)
    gw, gh   = game_size
    canvas_w  = gw
    canvas_h  = gh + HUD_H       # extended height

    orig_frames, orig_durations = [], []
    try:
        while True:
            orig_frames.append(src.copy().convert('RGB'))
            orig_durations.append(src.info.get('duration', 20))
            src.seek(src.tell() + 1)
    except EOFError:
        pass

    n_orig = len(orig_frames)
    print(f"  {n_orig} original frames  →  extended canvas {canvas_w}×{canvas_h}")

    # Half-hearts: 10 max (5 full hearts), minus missed_days (capped 0-10)
    lives_halves = max(0, 10 - min(10, missed_days))
    level        = days_active
    score_curve  = build_score_curve(n_orig, total_score)

    # ---- Build extended HUD frames for original game ----
    all_frames, all_durations = [], []

    def make_extended_frame(game_frame: Image.Image, score_now: int,
                             frame_idx: int) -> Image.Image:
        canvas = Image.new('RGB', (canvas_w, canvas_h), BG_COLOR)
        canvas.paste(game_frame, (0, HUD_H))
        draw = ImageDraw.Draw(canvas)
        draw_hud(draw, canvas_w, score_now, level, lives_halves,
                 frame_index=frame_idx)
        return canvas

    for i, gf in enumerate(orig_frames):
        all_frames.append(make_extended_frame(gf, score_curve[i], i))
        all_durations.append(orig_durations[i])

    last_game = orig_frames[-1]
    final_score = total_score

    # ---- STAGE CLEAR end screen ----
    stage_clear_size = (canvas_w, canvas_h)

    def make_sc_with_hud(sc_alpha, show_prompt):
        # Extend the stage-clear overlay to full canvas height
        ov_full = make_stage_clear_frame(
            (canvas_w, gh), alpha=sc_alpha, show_prompt=show_prompt,
            score=final_score)
        canvas = Image.new('RGB', (canvas_w, canvas_h), BG_COLOR)
        canvas.paste(last_game, (0, HUD_H))
        sc_rgba = canvas.convert('RGBA')
        # Paste the game-area overlay at y=HUD_H
        ov_ext = Image.new('RGBA', (canvas_w, canvas_h), (0,0,0,0))
        ov_ext.paste(ov_full, (0, HUD_H))
        sc_rgba.alpha_composite(ov_ext)
        result = sc_rgba.convert('RGB')
        # Draw HUD with locked final score — frame_index continues from game
        draw = ImageDraw.Draw(result)
        draw_hud(draw, canvas_w, final_score, level, lives_halves,
                 frame_index=n_orig + 9999)  # high index = blink always on for stage clear
        return result

    # Flicker in
    flicker_seq = [0, 160, 40, 210, 90, 255]
    for i in range(flicker_count):
        a = flicker_seq[i % len(flicker_seq)]
        all_frames.append(make_sc_with_hud(a, show_prompt=False))
        all_durations.append(frame_delay_ms)

    # Solid hold with blinking prompt
    for i in range(solid_count):
        show_p = (i // 6) % 2 == 0
        all_frames.append(make_sc_with_hud(255, show_prompt=show_p))
        all_durations.append(frame_delay_ms)

    # Fade out
    for i in range(fade_count):
        a = int(255 * (1 - (i + 1) / fade_count))
        all_frames.append(make_sc_with_hud(a, show_prompt=False))
        all_durations.append(frame_delay_ms)

    # Dark pause
    dark = Image.new('RGB', (canvas_w, canvas_h), BG_COLOR)
    for _ in range(dark_pause):
        all_frames.append(dark.copy())
        all_durations.append(frame_delay_ms)

    print(f"  Saving {len(all_frames)} frames to {output_path} …")

    out_frames = [f.convert('P', palette=Image.ADAPTIVE, colors=256)
                  for f in all_frames]
    out_frames[0].save(
        output_path,
        format='GIF',
        save_all=True,
        append_images=out_frames[1:],
        duration=all_durations,
        loop=0,
        optimize=False,
        disposal=2,
    )
    print("  Done! ✅")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('input',         nargs='?', default='shooter.gif')
    ap.add_argument('output',        nargs='?', default=None)
    ap.add_argument('--stats',       default=None,
                    help='Path to stats.json from fetch_github_stats.py')
    args = ap.parse_args()

    out = args.output or args.input   # in-place by default

    total_score  = 0
    days_active  = 1
    missed_days  = 0

    if args.stats:
        try:
            with open(args.stats) as f:
                s = json.load(f)
            total_score = s.get('total_contributions',    0)
            days_active = s.get('days_with_contributions', 1)
            missed_days = s.get('missed_days_last_10',    0)
            print(f"  Stats loaded: score={total_score}  level={days_active}  missed={missed_days}")
        except Exception as e:
            print(f"  Warning: could not load stats — {e}", file=sys.stderr)

    add_hud_and_game_over(
        args.input, out,
        total_score=total_score,
        days_active=days_active,
        missed_days=missed_days,
    )
