"""Generate the procedural timber textures used by the site (assets/img/tex-*.webp).
Run: python3 tools/textures.py   (needs numpy + pillow). Output is committed, so this is optional."""
import numpy as np
from PIL import Image, ImageFilter
import os
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img')

def pnoise(W, rng, kmax=14, decay=1.0, shift=0.0):
    """periodic 1D noise over W samples"""
    x = np.arange(W) / W
    n = np.zeros(W)
    for k in range(1, kmax + 1):
        n += (rng.normal() / k ** decay) * np.sin(2 * np.pi * (k * x) + rng.uniform(0, 2 * np.pi))
    return n / (np.abs(n).max() + 1e-9)

def board(W, h, rng, base, contrast, ring_px):
    y = np.arange(h)[:, None].astype(float)
    xs = np.arange(W)[None, :].astype(float)
    n1 = pnoise(W, rng, 8, 1.7)[None, :]
    n2 = pnoise(W, rng, 30, 0.9)[None, :]
    n3 = pnoise(W, rng, 6, 1.0)[None, :]
    # a slow cathedral/flat-sawn sweep plus wobble
    v = y + h * 0.55 * n1 + 1.6 * n2 + 0.05 * y * n3 * 6
    # knots
    for _ in range(rng.integers(0, 2)):
        kx, ky = rng.uniform(0, W), rng.uniform(h * .2, h * .8)
        dx = (xs - kx); dx = (dx + W / 2) % W - W / 2
        d2 = (dx / 26.0) ** 2 + ((y - ky) / 9.0) ** 2
        v += 14 * np.exp(-d2) * np.sign(y - ky + 1e-3)
    spacing = ring_px * (1 + 0.35 * n3)
    ph = (v / spacing) % 1.0
    lw = (np.floor(v / spacing) * 7.31) % 1.0
    ring = np.exp(-((ph - 0.5) ** 2) / 0.02) * (0.45 + 0.75 * lw)   # dark late-wood lines, varying strength
    fib = rng.normal(0, 1, (h, W))
    k = 41; ker = np.ones(k) / k                           # stretch noise along the grain (x)
    fib = np.real(np.fft.ifft(np.fft.fft(fib, axis=1) * np.fft.fft(np.pad(ker, (0, W - k)))[None, :], axis=1))
    fib = fib / (fib.std() + 1e-9)
    sheen = 0.07 * np.exp(-((y / h - 0.32) ** 2) / 0.03) - 0.04 * (y / h)   # satin-oiled highlight
    shade = 1 - contrast * ring - 0.025 * fib + 0.035 * n2 + sheen
    img = np.clip(base[None, None, :] * shade[..., None], 0, 255)
    # edge bevel
    bev = np.ones(h); bev[:3] = [0.72, 0.85, 0.94]; bev[-3:] = [0.94, 0.85, 0.7]
    return img * bev[:, None, None]

def screw(img, cx, cy, r, ss=4):
    H, W, _ = img.shape
    y0, y1, x0, x1 = int(cy - r - 2), int(cy + r + 3), int(cx - r - 2), int(cx + r + 3)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    d = np.hypot(xx - cx, yy - cy)
    a = np.clip(r - d + 0.5, 0, 1)[..., None]
    # brass head with light from top-left
    lx = (xx - cx) / r; ly = (yy - cy) / r
    lit = np.clip(0.85 - 0.45 * (lx + ly) * 0.5 - 0.25 * (d / r) ** 2, 0.35, 1.2)
    brass = np.array([214, 160, 72])[None, None, :] * lit[..., None]
    # cross recess (pozi-ish)
    slot = ((np.abs(xx - cx) < r * 0.16) | (np.abs(yy - cy) < r * 0.16)) & (d < r * 0.62)
    brass[slot] = brass[slot] * 0.45
    ring = (d > r - 1.3) & (d <= r)
    brass[ring] *= 0.6
    # shadow
    sh = np.clip(1 - np.clip(r + 2 - np.hypot(xx - cx - 1.2, yy - cy - 1.6), 0, 1) * 0.35, 0, 1)[..., None]
    reg = img[y0 % H:y0 % H + (y1 - y0), x0:x1]
    if reg.shape[:2] != a.shape[:2]:
        return
    reg[:] = reg * sh
    reg[:] = reg * (1 - a) + brass * a

def deck(W, nboards, bh, gap, palette, contrast, ring_px, seed, screws=True, joist=300, gapcol=(26, 17, 10), joint=0.45, joints=True):
    rng = np.random.default_rng(seed)
    H = nboards * bh
    img = np.zeros((H, W, 3))
    img[:] = gapcol
    for i in range(nboards):
        base = np.array(palette[rng.integers(len(palette))], float) * rng.uniform(0.93, 1.06)
        b = board(W, bh - gap, rng, base, contrast, ring_px * rng.uniform(.8, 1.25))
        # butt joint
        if joints and rng.random() < 0.6:
            jx = int(rng.integers(1, W // joist)) * joist + joist // 2
            b[:, jx - 1:jx + 1] *= joint
        img[i * bh + gap // 2: i * bh + gap // 2 + bh - gap] = b
    if screws:
        for i in range(nboards):
            for jx in range(joist // 2, W, joist):
                for fy in (0.3, 0.7):
                    screw(img, jx + (i % 2) * 2, i * bh + gap // 2 + (bh - gap) * fy, max(3.2, bh * 0.045))
    return Image.fromarray(img.astype(np.uint8), 'RGB')

# "cedar" = smoked oak, "hardwood" = dark walnut (names kept so CSS/filenames stay stable)
cedar = [(122, 86, 56), (112, 78, 51), (130, 93, 62), (104, 73, 48), (118, 84, 57)]
hardwood = [(74, 51, 35), (82, 57, 39), (66, 46, 32), (78, 54, 37), (70, 49, 34)]
limed = [(232, 222, 206), (226, 214, 196), (236, 228, 214), (222, 210, 192)]
navy = [(18, 44, 72), (14, 38, 64), (22, 50, 80), (16, 41, 69)]

def save(im, name, q=62):
    im.save(os.path.join(OUT, name), 'WEBP', quality=q, method=6)
    print(name, im.size, os.path.getsize(os.path.join(OUT, name)) // 1024, 'KB')

save(deck(1200, 8, 96, 4, cedar, 0.13, 3.6, 1, screws=False, gapcol=(20, 13, 8), joint=0.7), 'tex-cedar-deck-boards.webp')
save(deck(1200, 8, 96, 4, hardwood, 0.2, 3.4, 2, screws=False, gapcol=(12, 8, 5), joint=0.72), 'tex-hardwood-deck-boards.webp')
save(deck(1200, 8, 96, 4, limed, 0.06, 7, 3, screws=False, gapcol=(196, 182, 160), joint=0.82), 'tex-limed-deck-boards.webp', 58)
save(deck(1200, 8, 96, 5, navy, 0.18, 6, 4, screws=False, gapcol=(4, 18, 33), joint=0.7), 'tex-navy-painted-boards.webp', 58)
# hero: boards running away from the viewer (rotated)
hero = deck(1200, 12, 100, 6, cedar, 0.13, 3.6, 7, joist=400, screws=False, gapcol=(16, 10, 6)).rotate(90, expand=True)
save(hero, 'tex-hero-deck-boards.webp', 64)

# single-board surfaces (no gaps, joints or screws) for cards, steps, tags and the form
def plain(palette, contrast, ring_px, seed, q=60):
    rng = np.random.default_rng(seed)
    base = np.array(palette[0], float)
    b = board(1200, 400, rng, base, contrast, ring_px)
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8), 'RGB')
save(plain(cedar, 0.13, 3.6, 11), 'tex-cedar-plank.webp')
save(plain(limed, 0.06, 7, 12), 'tex-limed-plank.webp', 58)
save(plain(hardwood, 0.2, 3.4, 13), 'tex-hardwood-plank.webp')
