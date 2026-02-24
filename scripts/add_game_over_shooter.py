#!/usr/bin/env python3
"""
Post-process shooter.gif: append an authentic 8-bit arcade end-game screen
after the shooter finishes clearing all contribution blocks.

The original gh-space-shooter is inspired by Galaga/Space Invaders. When you
clear all enemies in those games the screen shows a victory/stage-complete
celebration — NOT "GAME OVER" (which means you lost your lives).

This script appends frames showing:
  ★ "STAGE CLEAR!" (centred, bright green, large pixel font)
  ★ "YOU WIN!"     (centred, gold/yellow, below)
  ★ Blinking ">>> PLAY AGAIN <<<"  (styled like arcade credit prompts)
  ★ Subtle scanline / CRT shimmer aesthetic

Colors are pulled from the actual game palette:
  BG   #0d1117   Ship #4493f8   Blocks #26a641 #39d353 #57f287

Usage:
    python scripts/add_game_over_shooter.py [input.gif] [output.gif]
    Defaults: shooter.gif -> shooter.gif (in-place)
"""
import sys
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# 5×7 pixel-art font bitmaps (7 rows × 5 cols, 1=lit pixel)
# ---------------------------------------------------------------------------
PIXEL_FONT = {
    '!': [[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,0,0,0],[0,0,1,0,0]],
    '>': [[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],
          [0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0]],
    '<': [[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],
          [0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]],
    ' ': [[0]*5]*7,
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
    'W': [[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,1,0,1],
          [1,0,1,0,1],[1,1,0,1,1],[1,0,0,0,1]],
    'Y': [[1,0,0,0,1],[1,0,0,0,1],[0,1,0,1,0],[0,0,1,0,0],
          [0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    'G': [[0,1,1,1,0],[1,0,0,0,0],[1,0,0,0,0],[1,0,1,1,1],
          [1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    'A': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,1],
          [1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'M': [[1,0,0,0,1],[1,1,0,1,1],[1,0,1,0,1],[1,0,0,0,1],
          [1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'E': [[1,1,1,1,1],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],
          [1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,1]],
    '*': [[0,1,0,1,0],[0,0,1,0,0],[1,1,1,1,1],[0,0,1,0,0],
          [0,1,0,1,0],[0,0,0,0,0],[0,0,0,0,0]],
}

# Game palette (from actual shooter.gif analysis)
BG_COLOR    = (13, 17, 23)         # #0d1117  — space background
SHIP_BLUE   = (68, 147, 248)       # #4493f8  — player ship
GREEN_HI    = (87, 242, 135)       # #57f287  — brightest contribution green
GREEN_MID   = (57, 211, 83)        # #39d353
GREEN_DIM   = (38, 166, 65)        # #26a641
GOLD        = (255, 213, 0)        # classic arcade yellow-gold
WHITE       = (255, 255, 255)
PANEL_DARK  = (13, 17, 23)         # same as BG for seamless look


def draw_pixel_text(draw, text, x, y, color, px=5, gap=1, center_in_width=None):
    """Draw pixel-art text at (x,y). If center_in_width given, auto-center."""
    char_w = 5 * (px + gap)
    char_gap = px + 1
    text_w = len(text) * (char_w + char_gap) - char_gap

    if center_in_width is not None:
        x = (center_in_width - text_w) // 2

    cx = x
    for ch in text:
        bitmap = PIXEL_FONT.get(ch, PIXEL_FONT[' '])
        for row_i, row in enumerate(bitmap):
            for col_i, lit in enumerate(row):
                if lit:
                    rx = cx + col_i * (px + gap)
                    ry = y + row_i * (px + gap)
                    draw.rectangle([rx, ry, rx + px - 1, ry + px - 1], fill=color)
        cx += char_w + char_gap
    return text_w


def px_text_width(text, px=5, gap=1):
    """Return pixel width of text rendered at scale px."""
    char_w = 5 * (px + gap)
    char_gap = px + 1
    return len(text) * (char_w + char_gap) - char_gap


def draw_stars(draw, size, seed=42, count=40):
    """Draw static starfield matching the original game's background stars."""
    import random
    rng = random.Random(seed)
    w, h = size
    for _ in range(count):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        bright = rng.randint(60, 200)
        draw.point([x, y], fill=(bright, bright, bright))


def make_stage_clear_frame(size, alpha=255, show_prompt=True,
                           headline="STAGE CLEAR!", sub="YOU WIN!",
                           prompt=">>> PLAY AGAIN <<<"):
    """
    Render a single RGBA end-game frame in authentic arcade style.
    alpha 0-255 controls overall opacity.
    """
    w, h = size

    # Base: space background + stars
    frame = Image.new('RGBA', (w, h), (*BG_COLOR, alpha))
    draw = ImageDraw.Draw(frame)
    if alpha > 30:
        draw_stars(draw, size)

    if alpha == 0:
        return frame

    a = min(255, alpha)

    # ---- Sizes & layout ----
    # Headline: "STAGE CLEAR!" — large pixel font (px=6)
    hl_px, hl_gap = 6, 1
    hl_char_h = 7 * (hl_px + hl_gap)

    # Sub: "YOU WIN!" — medium (px=5)
    sub_px, sub_gap = 5, 1
    sub_char_h = 7 * (sub_px + sub_gap)

    # Prompt: ">>> PLAY AGAIN <<<" — small (px=3)
    pr_px, pr_gap = 3, 1
    pr_char_h = 7 * (pr_px + pr_gap)

    spacing = 8
    total_h = hl_char_h + spacing + sub_char_h + spacing + pr_char_h
    start_y = (h - total_h) // 2

    # ---- Scanline overlay (subtle CRT effect) ----
    if a > 128:
        for y in range(0, h, 2):
            draw.line([(0, y), (w, y)], fill=(0, 0, 0, 20))

    # ---- Glowing panel behind text (subtle) ----
    pad = 14
    panel_w_est = max(
        px_text_width(headline, hl_px, hl_gap),
        px_text_width(sub, sub_px, sub_gap),
        px_text_width(prompt, pr_px, pr_gap),
    ) + pad * 2
    panel_x = (w - panel_w_est) // 2
    panel_y = start_y - pad
    panel_h_est = total_h + pad * 2

    panel_alpha = min(210, int(220 * a / 255))
    draw.rectangle([panel_x, panel_y, panel_x + panel_w_est, panel_y + panel_h_est],
                   fill=(*PANEL_DARK, panel_alpha))
    # Outer border (green glow)
    border_a = min(255, int(a))
    draw.rectangle([panel_x, panel_y, panel_x + panel_w_est, panel_y + panel_h_est],
                   outline=(*GREEN_MID, border_a), width=2)
    # Inner border
    draw.rectangle([panel_x + 3, panel_y + 3,
                    panel_x + panel_w_est - 3, panel_y + panel_h_est - 3],
                   outline=(*GREEN_DIM, border_a // 2), width=1)

    hl_y   = start_y
    sub_y  = hl_y + hl_char_h + spacing
    pr_y   = sub_y + sub_char_h + spacing

    # ---- Headline: "STAGE CLEAR!" in bright green ----
    draw_pixel_text(draw, headline, 0, hl_y, (*GREEN_HI, a),
                    px=hl_px, gap=hl_gap, center_in_width=w)

    # ---- Sub: "YOU WIN!" in gold ----
    draw_pixel_text(draw, sub, 0, sub_y, (*GOLD, a),
                    px=sub_px, gap=sub_gap, center_in_width=w)

    # ---- Prompt: ">>> PLAY AGAIN <<<" blinking in ship blue ----
    if show_prompt:
        draw_pixel_text(draw, prompt, 0, pr_y, (*SHIP_BLUE, a),
                        px=pr_px, gap=pr_gap, center_in_width=w)

    return frame


def blend_onto_last(base_frame: Image.Image, overlay: Image.Image) -> Image.Image:
    """Alpha-composite overlay onto base, return RGB result."""
    base_rgba = base_frame.convert('RGBA')
    base_rgba.alpha_composite(overlay)
    return base_rgba.convert('RGB')


def add_game_over(input_path: str, output_path: str,
                  frame_delay_ms: int = 50,   # ~20fps for the game-over frames
                  flicker_count: int = 6,
                  solid_count: int = 28,
                  fade_count: int = 10,
                  dark_pause: int = 4):
    """
    Load input GIF → extract frames → append Stage Clear animation → save.
    """
    print(f"Opening {input_path} …")
    src = Image.open(input_path)
    size = src.size

    orig_frames, orig_durations = [], []
    try:
        while True:
            orig_frames.append(src.copy().convert('RGB'))
            orig_durations.append(src.info.get('duration', 20))
            src.seek(src.tell() + 1)
    except EOFError:
        pass

    print(f"  {len(orig_frames)} original frames, size={size}")
    last = orig_frames[-1]

    go_frames, go_durations = [], []

    # ---- Phase 1: CRT power-on flicker ----
    flicker_seq = [0, 160, 40, 210, 90, 255]
    for i in range(flicker_count):
        a = flicker_seq[i % len(flicker_seq)]
        ov = make_stage_clear_frame(size, alpha=a, show_prompt=False)
        go_frames.append(blend_onto_last(last, ov))
        go_durations.append(frame_delay_ms)

    # ---- Phase 2: Solid hold with blinking ">>> PLAY AGAIN <<<" ----
    for i in range(solid_count):
        show_p = (i // 6) % 2 == 0   # blink every 6 frames (~0.3s)
        ov = make_stage_clear_frame(size, alpha=255, show_prompt=show_p)
        go_frames.append(blend_onto_last(last, ov))
        go_durations.append(frame_delay_ms)

    # ---- Phase 3: Fade out ----
    for i in range(fade_count):
        a = int(255 * (1 - (i + 1) / fade_count))
        ov = make_stage_clear_frame(size, alpha=a, show_prompt=False)
        go_frames.append(blend_onto_last(last, ov))
        go_durations.append(frame_delay_ms)

    # ---- Phase 4: Dark pause before loop ----
    dark = Image.new('RGB', size, BG_COLOR)
    for _ in range(dark_pause):
        go_frames.append(dark.copy())
        go_durations.append(frame_delay_ms)

    all_frames    = orig_frames + go_frames
    all_durations = orig_durations + go_durations

    print(f"  Total: {len(all_frames)} frames "
          f"({len(orig_frames)} original + {len(go_frames)} stage-clear)")
    print(f"  Saving to {output_path} …")

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
    return len(go_frames)


if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else 'shooter.gif'
    out = sys.argv[2] if len(sys.argv) > 2 else inp
    add_game_over(inp, out)
