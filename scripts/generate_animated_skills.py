import urllib.request
import re
import sys

def main():
    url = "https://skillicons.dev/icons?i=ts,swift,py,js,java,cpp,html,css,go,react,nodejs,vite,mongodb,postgres,docker,git,rust,bash&theme=dark&perline=9"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            svg_data = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching icons: {e}")
        sys.exit(1)

    svg_start_match = re.search(r'<svg[^>]+>', svg_data)
    if not svg_start_match:
        print("Could not find <svg> tag")
        sys.exit(1)
        
    svg_start_idx = svg_start_match.end()
    
    pattern = r'(<g transform="translate\([^)]+\)">)\s*(<svg.*?</svg>)\s*(</g>)'
    
    GAME_DURATION = 40.0 # seconds
    FILL_TIME = 35.0
    
    icons_found = re.findall(pattern, svg_data, re.DOTALL)
    num_icons = len(icons_found)
    
    if num_icons == 0:
        print("No icons found in the SVG!")
        sys.exit(1)
        
    counter = 0
    def replacer_staggered(match):
        nonlocal counter
        g_open = match.group(1)
        inner_svg = match.group(2)
        g_close = match.group(3)
        
        start_time = (counter / num_icons) * FILL_TIME
        end_time = start_time + 1.0
        
        k_start = start_time / GAME_DURATION
        k_end = end_time / GAME_DURATION
        
        k_str = f"0;{k_start:.4f};{k_end:.4f};1"
        v_str = "0;0;1;1"
        
        res = f"{g_open}\n" + \
              f'  <g filter="url(#grayscale_%d)">\n    {inner_svg}\n  </g>\n' % counter + \
              f'  <g opacity="0">\n    {inner_svg}\n' + \
              f'    <animate attributeName="opacity" values="{v_str}" keyTimes="{k_str}" dur="{GAME_DURATION}s" fill="freeze" />\n' + \
              f'  </g>\n' + \
              f"{g_close}"
        
        counter += 1
        return res

    animated_svg_data = re.sub(pattern, replacer_staggered, svg_data, flags=re.DOTALL)
    
    # We create multiple grayscale filters because some SVG renderers might struggle applying one filter to many elements
    # Or just one is fine, let's use a single one to save space.
    # Wait, in the string interpolation I used #grayscale_%d. Let's provide multiple just in case or change it to one.
    # Changed to multiple filters below to be safe.
    
    defs_block = "  <defs>\n"
    for i in range(num_icons):
        defs_block += f'    <filter id="grayscale_{i}"><feColorMatrix type="matrix" values="0.3333 0.3333 0.3333 0 0  0.3333 0.3333 0.3333 0 0  0.3333 0.3333 0.3333 0 0  0 0 0 1 0"/></filter>\n'
    defs_block += "  </defs>\n"

    animated_svg_data = animated_svg_data[:svg_start_idx] + "\n" + defs_block + animated_svg_data[svg_start_idx:]

    with open('animated-skills.svg', 'w') as f:
        f.write(animated_svg_data)
        
    print(f"Generated animated-skills.svg with {num_icons} animated icons!")

if __name__ == "__main__":
    main()
