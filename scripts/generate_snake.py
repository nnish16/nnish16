#!/usr/bin/env python3
"""Custom snake animation: sweeps contribution grid, revealing NISHANT.
Generates an animated SVG using SMIL animations with cyber-violet palette.
"""
import json, os, sys, urllib.request

# --- Grid config (matches GitHub contribution graph) ---
COLS, ROWS, CELL, GAP, RAD = 52, 7, 11, 3, 2

# --- Cyber-violet palette ---
BG = "#0d1117"
EMPTY = "#161b22"
LV = ["#161b22", "#570a57", "#702963", "#a91079", "#f72585"]

# --- Animation timing (seconds) ---
LOOP, EAT, HOLD = 16, 8, 4  # total, eat phase, hold phase

# --- Thick block font (6 wide × 7 tall, 2px-wide strokes) ---
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
    """Build 7×52 boolean mask for thick block text centered on grid."""
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
    """Fetch contribution calendar via GitHub GraphQL API."""
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
            for d in w["contributionDays"]:
                col[d["weekday"]] = d["contributionCount"]
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
    return 1 if r <= 0.25 else 2 if r <= 0.5 else 3 if r <= 0.75 else 4

def generate(out, text="NISHANT", grid=None):
    mask = text_mask(text)

    # Build level grid
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

    # SVG dimensions
    S = CELL + GAP
    pad = 16
    sw, sh = COLS*S + GAP + pad*2, ROWS*S + GAP + pad*2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sw} {sh}">']

    # Glow filter
    o.append('<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">')
    o.append('<feGaussianBlur stdDeviation="2" result="b"/>')
    o.append('<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    o.append('</filter></defs>')

    # Background
    o.append(f'<rect width="{sw}" height="{sh}" fill="{BG}" rx="6"/>')

    # Fraction helpers
    def frac(sec): return f"{sec/LOOP:.4f}"

    # Draw cells
    for r in range(ROWS):
        for c in range(COLS):
            x = pad + c*S + GAP
            y = pad + r*S + GAP
            lv = lvl[r][c]

            if mask[r][c]:
                # NISHANT cell — stays visible, pulses when revealed
                color = LV[max(3, lv)]
                o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="{RAD}" fill="{color}" filter="url(#glow)">')
                o.append(f'<animate attributeName="opacity" '
                         f'values="0.5;0.5;1;1;0.5" '
                         f'keyTimes="0;{frac(EAT)};{frac(EAT+1)};{frac(EAT+HOLD)};1" '
                         f'dur="{LOOP}s" repeatCount="indefinite"/>')
                o.append('</rect>')
            else:
                # Eaten cell — fades out as snake passes
                color = LV[lv] if lv > 0 else EMPTY
                pos = idx[(r, c)]
                fade_start = (pos / N) * EAT
                fade_end = min(fade_start + 0.3, EAT)

                o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="{RAD}" fill="{color}">')
                o.append(f'<animate attributeName="opacity" '
                         f'values="1;1;0;0;1;1" '
                         f'keyTimes="0;{frac(fade_start)};{frac(fade_end)};'
                         f'{frac(EAT+HOLD)};{frac(EAT+HOLD+2)};1" '
                         f'dur="{LOOP}s" repeatCount="indefinite"/>')
                o.append('</rect>')

    # Snake head — moves along zigzag path
    # Build path as SVG polyline points (subsample every 4th cell for efficiency)
    step = 4
    path_pts = []
    path_times = []
    for i in range(0, N, step):
        r, c = order[i]
        px = pad + c*S + GAP + CELL//2
        py = pad + r*S + GAP + CELL//2
        path_pts.append(f"{px},{py}")
        path_times.append(frac((i/N)*EAT))
    # Add final point
    r, c = order[-1]
    path_pts.append(f"{pad + c*S + GAP + CELL//2},{pad + r*S + GAP + CELL//2}")
    path_times.append(frac(EAT))

    cx_vals = ";".join(str(pad + order[min(i,N-1)][1]*S + GAP + CELL//2)
                       for i in range(0, N, step)) + f";{pad + order[-1][1]*S + GAP + CELL//2}"
    cy_vals = ";".join(str(pad + order[min(i,N-1)][0]*S + GAP + CELL//2)
                       for i in range(0, N, step)) + f";{pad + order[-1][0]*S + GAP + CELL//2}"
    kt = ";".join(path_times)

    o.append(f'<circle r="{CELL//2+1}" fill="{LV[4]}" filter="url(#glow)">')
    o.append(f'<animate attributeName="cx" values="{cx_vals}" keyTimes="{kt}" '
             f'dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(f'<animate attributeName="cy" values="{cy_vals}" keyTimes="{kt}" '
             f'dur="{LOOP}s" repeatCount="indefinite"/>')
    o.append(f'<animate attributeName="opacity" values="1;1;0;0;1" '
             f'keyTimes="0;{frac(EAT)};{frac(EAT+0.5)};{frac(EAT+HOLD+1)};1" '
             f'dur="{LOOP}s" repeatCount="indefinite"/>')
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
