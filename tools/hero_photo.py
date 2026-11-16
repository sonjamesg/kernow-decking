"""Make the homepage hero + Open Graph images from James's photo.
Usage: python3 tools/hero_photo.py /path/to/photo.jpg   (then run tools/build.py)
Outputs assets/img/decking-cornwall-newquay-sea-view-deck-{768,1280,1920}.webp / -{1280,1920}.jpg
and assets/img/kernow-decking-cornwall-og.jpg (1200x630)."""
import sys, os
from PIL import Image, ImageFilter, ImageEnhance
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'img')
NAME = 'decking-cornwall-newquay-sea-view-deck'
src = Image.open(sys.argv[1]).convert('RGB')
w, h = src.size
for W in (768, 1280, 1920):
    H = round(h * W / w)
    im = src.resize((W, H), Image.LANCZOS)
    if W > w:  # upscaled: a light unsharp mask keeps edges crisp
        im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    im.save(os.path.join(OUT, f'{NAME}-{W}.webp'), 'WEBP', quality=80, method=6)
    if W >= 1280:
        im.save(os.path.join(OUT, f'{NAME}-{W}.jpg'), 'JPEG', quality=80, optimize=True, progressive=True)
# Open Graph 1200x630 (centre crop)
r = 1200 / 630
cw, ch = (w, round(w / r)) if w / h < r else (round(h * r), h)
x, y = (w - cw) // 2, (h - ch) // 2
og = src.crop((x, y, x + cw, y + ch)).resize((1200, 630), Image.LANCZOS)
og.save(os.path.join(OUT, 'kernow-decking-cornwall-og.jpg'), 'JPEG', quality=84, optimize=True, progressive=True)
print('hero images written', src.size)
