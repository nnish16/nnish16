#!/usr/bin/env python3
"""Custom snake animation: a visible snake with head + body traverses the
contribution grid eating all cells except those forming NISHANT.
"""
import json, os, sys, urllib.request

COLS, ROWS, CELL, GAP, RAD = 52, 7, 11, 3, 2
BG = "#0d1117"
EMPTY = "#161b22"
LV = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
LOOP, EAT, HOLD = 18, 10, 4  # longer eat = slower visible snake

FONT = {
    'N': [[1,1,0,0,1,1],[1,1,1,0,1,1],[1,1,1,1,1,1],[1,1,0,1,1,1],
          [1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1]],
    'I': [[1,1,1,1,1,1],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],
          [0,0,1,1,0,0],[0,0,1,1,0,0],[1,1,1,1,1,1]],
    'S': [[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,0,0],[0,1,1,1,1,0],
          [0,0,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]],
    'H': [[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,1,1,1,1],
          [1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1]],
    'A': [[0,0,1,1,0,0],[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,1,1,1,1],
          [1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1]],
    'T': [[1,1,1,1,1,1],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],
          [0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0]],
}

def text_mask(text):
    mask = [[False]*COLS for _ in range(ROWS)]
    lw, g = 6, 1
    total = len(text)*lw + (len(text)-1)*g
    off = (COLS - total) // 2
    for i, ch in enumerate(text):
        bc = off + i*(lw+g)
        for r in range(ROWS):
            for c in range(lw):
                gc = bc + c
                if 0 <= gc < COLS and FONT[ch][r][c]:
                    mask[r][gc] = True
    return mask

def fetch(user, token):
    q = json.dumps({"query": '{ user(login: "%s") { contributionsCollection { contributionCalendar { weeks { contributionDays { contributionCount weekday } } } } } }' % user})
    try:
        req = urllib.request.Request("https://api.github.com/graphql", q.encode(),
            {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        grid = []
        for w in weeks:
            col = [0]*ROWS
            for d in w["contributionDays"]: col[d["weekday"]] = d["contributionCount"]
            grid.append(col)
        if len(grid) > COLS: grid = grid[-COLS:]
        while len(grid) < COLS: grid.insert(0, [0]*ROWS)
        return grid
    except Exception as e:
        print(f"API warning: {e}", file=sys.stderr)
        return None

def to_level(c, mx):
    if c == 0 or mx == 0: return 0
    r = c/mx
    return 1 if r<=0.25 else 2 if r<=0.5 else 3 if r<=0.75 else 4

def generate(out, text="NISHANT", grid=None):
    mask = text_mask(text)

    if grid:
        mx = max(max(w) for w in grid)
        lvl = [[to_level(grid[c][r], mx) for c in range(COLS)] for r in range(ROWS)]
    else:
        import random; random.seed(7)
        lvl = [[random.choice([0,0,1,1,2,3,4]) for _ in range(COLS)] for _ in range(ROWS)]

    # Snake zigzag order
    order = []
    for r in range(ROWS):
        rng = range(COLS) if r % 2 == 0 else range(COLS-1, -1, -1)
        for c in rng: order.append((r, c))
    idx = {pos: i for i, pos in enumerate(order)}
    N = len(order)

    S = CELL + GAP
    pad = 16
    sw, sh = COLS*S + GAP + pad*2, ROWS*S + GAP + pad*2

    def frac(sec): return f"{sec/LOOP:.4f}"
    def cell_center(r, c):
        return pad + c*S + GAP + CELL//2, pad + r*S + GAP + CELL//2

    # Pre-compute ALL snake positions (every cell in zigzag order)
    # Subsample every 2nd for file size balance (still smooth)
    STEP = 2
    sampled = list(range(0, N, STEP))
    if sampled[-1] != N-1:
        sampled.append(N-1)
    n_pts = len(sampled)

    # Build position arrays for the snake head
    # keyTimes MUST span 0.0 to 1.0 for valid SMIL
    head_cx = []
    head_cy = []
    head_kt = []
    for si in sampled:
        r, c = order[si]
        cx, cy = cell_center(r, c)
        head_cx.append(str(cx))
        head_cy.append(str(cy))
        head_kt.append(frac((si / N) * EAT))

    # Add hold position (stay at last point during NISHANT glow)
    last_r, last_c = order[-1]
    last_cx, last_cy = cell_center(last_r, last_c)
    head_cx.append(str(last_cx))
    head_cy.append(str(last_cy))
    head_kt.append(frac(EAT + HOLD))

    # Add reset position (jump back to start for next loop)
    first_r, first_c = order[0]
    first_cx, first_cy = cell_center(first_r, first_c)
    head_cx.append(str(first_cx))
    head_cy.append(str(first_cy))
    head_kt.append("1")

    # Body segments: same path but offset by `lag` positions behind the head
    BODY_SEGMENTS = 8
    BODY_LAG = 3  # positions behind per segment
    BODY_COLORS = ["#39d353", "#31c14a", "#29ae41", "#229c38", "#1a8a2f",
                   "#127826", "#0a661d", "#025414"]
    BODY_SIZES = [CELL//2+2, CELL//2+1, CELL//2+1, CELL//2, CELL//2,
                  CELL//2-1, CELL//2-1, CELL//2-2]
    BODY_OPACITY = ["1", "0.95", "0.9", "0.85", "0.75", "0.65", "0.55", "0.4"]

    def build_body_positions(lag_cells):
        """Build position arrays for a body segment lagging behind head."""
        cx_arr, cy_arr = [], []
        for si in sampled:
            lagged = max(0, si - lag_cells)
            r, c = order[lagged]
            x, y = cell_center(r, c)
            cx_arr.append(str(x))
            cy_arr.append(str(y))
        # Hold position (same as head's last lagged pos)
        lagged = max(0, N - 1 - lag_cells)
        r, c = order[lagged]
        x, y = cell_center(r, c)
        cx_arr.append(str(x))
        cy_arr.append(str(y))
        # Reset position (back to start lagged pos)
        r, c = order[0]
        x, y = cell_center(r, c)
        cx_arr.append(str(x))
        cy_arr.append(str(y))
        return cx_arr, cy_arr

    # --- Start SVG ---
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sw} {sh}">']

    o.append('<defs>')
    o.append('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">')
    o.append('<feGaussianBlur stdDeviation="2.5" result="b"/>')
    o.append('<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    o.append('</filter>')
    o.append('<filter id="glow2" x="-50%" y="-50%" width="200%" height="200%">')
    o.append('<feGaussianBlur stdDeviation="4" result="b"/>')
    o.append('<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    o.append('</filter>')
    o.append('</defs>')

    o.append(f'<rect width="{sw}" height="{sh}" fill="{BG}" rx="6"/>')

    # --- Grid cells ---
    for r in range(ROWS):
        for c in range(COLS):
            x = pad + c*S + GAP
            y = pad + r*S + GAP
            lv = lvl[r][c]

            if mask[r][c]:
                color = LV[max(3, lv)]
                o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="{RAD}" fill="{color}" filter="url(#glow)">')
                o.append(f'<animate attributeName="opacity" '
                         f'values="0.4;0.4;1;1;0.4" '
                         f'keyTimes="0;{frac(EAT)};{frac(EAT+1)};{frac(EAT+HOLD)};1" '
                         f'dur="{LOOP}s" repeatCount="indefinite"/>')
                o.append('</rect>')
            else:
                color = LV[lv] if lv > 0 else EMPTY
                pos = idx[(r, c)]
                # Cell fades exactly when snake head arrives
                fade_at = (pos / N) * EAT
                fade_end = min(fade_at + 0.15, EAT)

                o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="{RAD}" fill="{color}">')
                o.append(f'<animate attributeName="opacity" '
                         f'values="1;1;0;0;1;1" '
                         f'keyTimes="0;{frac(fade_at)};{frac(fade_end)};'
                         f'{frac(EAT+HOLD)};{frac(EAT+HOLD+2)};1" '
                         f'dur="{LOOP}s" repeatCount="indefinite"/>')
                o.append('</rect>')

    # --- Snake body segments (drawn BEFORE head so head is on top) ---
    kt_str = ";".join(head_kt)

    # Visibility: visible during eat, hidden during hold, reappear for reset
    snake_vis = (f'<animate attributeName="opacity" values="1;1;0;0;1" '
                 f'keyTimes="0;{frac(EAT)};{frac(EAT+0.3)};{frac(EAT+HOLD+1)};1" '
                 f'dur="{LOOP}s" repeatCount="indefinite"/>')

    # Draw body from tail to head (so head renders on top)
    for seg in range(BODY_SEGMENTS-1, -1, -1):
        lag = (seg + 1) * BODY_LAG
        bcx, bcy = build_body_positions(lag)
        cx_str = ";".join(bcx)
        cy_str = ";".join(bcy)
        r_size = BODY_SIZES[seg]
        color = BODY_COLORS[seg]
        opac = BODY_OPACITY[seg]

        o.append(f'<circle r="{r_size}" fill="{color}" opacity="{opac}">')
        o.append(f'<animate attributeName="cx" values="{cx_str}" '
                 f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
        o.append(f'<animate attributeName="cy" values="{cy_str}" '
                 f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
        o.append(snake_vis)
        o.append('</circle>')

    # --- Snake head (on top of everything) ---
    cx_str = ";".join(head_cx)
    cy_str = ";".join(head_cy)

    # Head outer glow
    o.append(f'<circle r="{CELL//2+4}" fill="{LV[4]}" opacity="0.3" filter="url(#glow2)">')
    o.append(f'<animate attributeName="cx" values="{cx_str}" '
             f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(f'<animate attributeName="cy" values="{cy_str}" '
             f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(snake_vis)
    o.append('</circle>')

    # Head core
    o.append(f'<circle r="{CELL//2+2}" fill="{LV[4]}" filter="url(#glow)">')
    o.append(f'<animate attributeName="cx" values="{cx_str}" '
             f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(f'<animate attributeName="cy" values="{cy_str}" '
             f'keyTimes="{kt_str}" dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(snake_vis)
    o.append('</circle>')

    o.append('</svg>')

    with open(out, 'w') as f:
        f.write('\n'.join(o))
    print(f"Generated: {out}")

if __name__ == "__main__":
    user = os.environ.get("GITHUB_USER", "nnish16")
    token = os.environ.get("GITHUB_TOKEN", "")
    out = sys.argv[1] if len(sys.argv) > 1 else "snake.svg"
    grid = fetch(user, token) if token else None
    generate(out, "NISHANT", grid)
