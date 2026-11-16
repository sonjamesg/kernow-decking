"""Render the hero's perspective deck (boards receding toward the sea, with a glass + steel balustrade).
Output: assets/img/hero-deck-perspective-cornwall.webp (RGBA). Optional: output is committed."""
import numpy as np, os
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(__file__); OUT = os.path.join(D, '..', 'assets', 'img')
S = 2                       # supersample
W, H, TOP = 1920 * S, 520 * S, 110 * S   # TOP = headroom for the balustrade
tex = Image.open(os.path.join(OUT, 'tex-hero-deck-boards.webp')).convert('RGB')
# tile texture into a big plane: width = 2.6 tiles, depth = 3 tiles
tw, th = tex.size
plane = Image.new('RGB', (int(tw * 2.6), th * 3))
for i in range(3):
    for j in range(3):
        plane.paste(tex, (j * tw, i * th))
PW, PH = plane.size

def coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

far_l, far_r = W * 0.06, W * 0.94
near_l, near_r = -W * 0.9, W * 1.9
dst = [(far_l, TOP), (far_r, TOP), (near_r, H), (near_l, H)]
src = [(0, 0), (PW, 0), (PW, PH), (0, PH)]
deck = plane.transform((W, H), Image.PERSPECTIVE, coeffs(dst, src), Image.BICUBIC)
mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(dst, fill=255)
a = np.array(deck).astype(float)
yy, xx = np.mgrid[0:H, 0:W].astype(float)
t = np.clip((yy - TOP) / (H - TOP), 0, 1)          # 0 far, 1 near
# atmospheric warm haze far away, darker near the viewer, sunset sheen toward the sun (x≈0.62)
sun_x = W * 0.62
sheen = np.exp(-((xx - sun_x) / (W * 0.18)) ** 2) * (1 - t) ** 1.5
haze = (1 - t) ** 3
a = a * (0.62 + 0.38 * (1 - t) ** 0.6)[..., None]
a = a * (1 - 0.25 * haze[..., None]) + np.array([250, 196, 120]) * (0.25 * haze)[..., None]
a = a + np.array([255, 190, 110]) * (0.35 * sheen)[..., None]
# side vignette
vig = 1 - 0.35 * (np.abs(xx - W / 2) / (W / 2)) ** 2
a = np.clip(a * vig[..., None], 0, 255)
img = Image.fromarray(a.astype(np.uint8)).convert('RGBA'); img.putalpha(mask)
# fascia board along the far edge
d = ImageDraw.Draw(img, 'RGBA')
d.polygon([(far_l, TOP), (far_r, TOP), (far_r, TOP + 7 * S), (far_l, TOP + 7 * S)], fill=(92, 56, 30, 255))
# balustrade along far edge: glass panels between steel posts + timber handrail
posts = np.linspace(far_l + 10 * S, far_r - 10 * S, 13)
rail_top = TOP - 74 * S
for i in range(len(posts) - 1):
    x0, x1 = posts[i] + 5 * S, posts[i + 1] - 5 * S
    d.rectangle([x0, rail_top + 8 * S, x1, TOP - 2 * S], fill=(190, 220, 240, 46))
    d.line([(x0 + 12 * S, rail_top + 16 * S), (x0 + 40 * S, TOP - 10 * S)], fill=(255, 255, 255, 40), width=3 * S)
for x in posts:
    d.rectangle([x - 4 * S, rail_top, x + 4 * S, TOP], fill=(48, 58, 70, 255))
    d.rectangle([x - 4 * S, rail_top, x - 1 * S, TOP], fill=(140, 150, 162, 255))
d.rectangle([far_l, rail_top - 6 * S, far_r, rail_top + 4 * S], fill=(112, 70, 38, 255))
d.rectangle([far_l, rail_top - 6 * S, far_r, rail_top - 3 * S], fill=(196, 140, 86, 255))
img = img.resize((W // S, H // S), Image.LANCZOS)
img.save(os.path.join(OUT, 'hero-deck-perspective-cornwall.webp'), 'WEBP', quality=70, method=6)
# small version for phones (crop centre; CSS keeps the far edge aligned)
print(img.size, os.path.getsize(os.path.join(OUT, 'hero-deck-perspective-cornwall.webp')) // 1024, 'KB')
