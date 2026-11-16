"""Smoked-oak textures for the plank header and the framed logo.
Writes assets/img/tex-oak-bar.webp (header boards, 2x), tex-oak-frame-h.webp / -v.webp (frame planks).
Run: python3 tools/frame_textures.py   (numpy + pillow)."""
import numpy as np
from PIL import Image, ImageFilter
import os
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img')
C_DARK = np.array([0x2A, 0x1C, 0x13]); C_MID = np.array([0x4A, 0x33, 0x23]); C_LIGHT = np.array([0x6E, 0x4E, 0x34])

def periodic_noise(W, rng, kmax=24, decay=1.1):
    x = np.arange(W) / W; n = np.zeros(W)
    for k in range(1, kmax + 1):
        n += rng.normal() / k ** decay * np.sin(2 * np.pi * k * x + rng.uniform(0, 6.283))
    return n / (np.abs(n).max() + 1e-9)

def board(W, H, rng, tone=0.0, ray_density=1.0, contrast=1.0):
    """one plank face, grain running along x, periodic in x"""
    y = np.arange(H)[:, None] / H; x = np.arange(W)[None, :]
    warp = periodic_noise(W, rng, 10)[None, :] * 0.35 + periodic_noise(W, rng, 30, 0.8)[None, :] * 0.04
    # long grain lines (latewood) with uneven spacing and gentle wander along the board
    yy = np.arange(H)
    yn = np.cumsum(np.abs(rng.normal(1.0, 0.55, H))); yn = yn / yn[-1]          # uneven ring spacing
    nl = rng.uniform(7, 11) * (H / 44) ** 0.5
    warp2 = (periodic_noise(W, rng, 6)[None, :] * 0.5 + periodic_noise(W, rng, 18, 0.9)[None, :] * 0.12) * (0.4 + 0.6 * np.sin(np.pi * y))
    phase = (yn[:, None] * nl + warp2 * 1.2) % 1.0
    late = np.exp(-((phase - 0.5) / 0.07) ** 2)                                  # thin dark latewood bands
    soft = np.exp(-((phase - 0.5) / 0.22) ** 2)
    f = rng.normal(size=(H, W))
    f = np.array(Image.fromarray(((f - f.min()) / (f.max() - f.min()) * 255).astype(np.uint8)).resize((W // 30, H)).resize((W, H), Image.BICUBIC)) / 255.0
    f2 = rng.normal(size=(H // 2 + 1, W // 6))
    f2 = np.array(Image.fromarray(((f2 - f2.min()) / (f2.max() - f2.min()) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) / 255.0
    v = 0.56 + tone + contrast * (-0.20 * late - 0.07 * soft + 0.14 * (f - 0.5) + 0.12 * (f2 - 0.5))
    # oak ray flecks: short, lighter, elongated
    rays = np.zeros((H, W))
    for _ in range(int(W * H / 2600 * ray_density)):
        cx, cy = rng.integers(0, W), rng.integers(0, H); L = rng.integers(6, 26); t = max(1, int(rng.integers(1, 3)))
        rays[cy:cy + t, max(0, cx - L):cx + L] += rng.uniform(.05, .13)
    rays = np.array(Image.fromarray((np.clip(rays, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))) / 255.0
    v = np.clip(v + rays, 0, 1)
    rgb = np.where(v[..., None] < .5, C_DARK + (C_MID - C_DARK) * (v[..., None] / .5), C_MID + (C_LIGHT - C_MID) * ((v[..., None] - .5) / .5))
    # satin sheen: soft horizontal highlight band + edge bevel (lighter top arris, darker bottom)
    sheen = 1 + 0.10 * np.exp(-((y - 0.32) / 0.16) ** 2)
    bevel = 1 + 0.16 * np.exp(-(y / 0.035)) - 0.30 * np.exp(-((1 - y) / 0.05))
    rgb = rgb * sheen[..., None] * bevel[..., None]
    return np.clip(rgb, 0, 255)

def save(arr, name, q=82):
    p = os.path.join(OUT, name); Image.fromarray(arr.astype(np.uint8)).save(p, 'WEBP', quality=q, method=6); print(name, os.path.getsize(p))

def main():
    rng = np.random.default_rng(7)
    # header bar: 3 boards of 64px (2x) + 4px gaps, 2400 wide, staggered butt joints
    W, bh, gap = 2400, 66, 3; rows = []
    for i, tone in enumerate([-.02, -.07, -.04]):
        b = board(W, bh, rng, tone)
        j = [700, 1650, 1150][i]
        b[:, j - 1:j + 1] = b[:, j - 1:j + 1] * 0.35; b[:, j + 1:j + 3] *= 1.08
        rows.append(b); rows.append(np.tile(np.array([0x15, 0x0D, 0x08]), (gap, W, 1)))
    save(np.vstack(rows[:-1]), 'tex-oak-bar.webp', 78)
    # frame plank: 1400 x 44, slightly richer (walnut-leaning) with a strong satin band
    fp = board(1400, 44, np.random.default_rng(21), 0.03, 1.6, 1.9)
    save(fp, 'tex-oak-frame-h.webp', 85)
    fv = board(1400, 44, np.random.default_rng(33), 0.0, 1.6, 1.9)
    save(np.transpose(fv, (1, 0, 2))[:, ::-1], 'tex-oak-frame-v.webp', 85)

if __name__ == '__main__':
    main()
