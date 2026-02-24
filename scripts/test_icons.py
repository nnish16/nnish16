import urllib.request
import re

url = "https://skillicons.dev/icons?i=ts,swift,py,js,java,cpp,html,css,go,react,nodejs,vite,mongodb,postgres,docker,git,rust,bash&theme=dark&perline=9"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    svg_data = response.read().decode('utf-8')

pattern = r'(<g transform="translate\([^)]+\)">\s*<svg.*?</svg>\s*</g>)'
icons = re.findall(pattern, svg_data, re.DOTALL)
print(f"Total icons found: {len(icons)}")
