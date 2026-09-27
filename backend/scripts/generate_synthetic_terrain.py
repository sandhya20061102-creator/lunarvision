"""
Step 1 - Synthetic Lunar Terrain and Height-Map Generator
==========================================================
Produces a 1024x1024 (or user-specified) height-map representing realistic
lunar-like terrain:

  * Rolling base via sum of random Gaussian hills (pure NumPy, no extra deps).
  * 15-30 craters: paraboloid depression with raised rim, matching real crater morphology.
  * Surface normals derived analytically from height-map gradients.

Saves to <out_dir>:
  heightmap.npy         -- raw float32 height-map
  heightmap_u16.png     -- 16-bit PNG for visual inspection
  normals.npy           -- (H,W,3) unit surface normals
  preview_hillshade.png -- 8-bit hill-shade preview

Usage
-----
  python backend/scripts/generate_synthetic_terrain.py [--size 1024] [--seed 42]
                                                       [--craters 22]
                                                       [--out outputs/terrain]
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def _gaussian_bump(H, W, cx, cy, sigma, amplitude):
    """Return a 2-D Gaussian bump centred at (cx, cy)."""
    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    return amplitude * np.exp(-d2 / (2.0 * sigma ** 2))


def generate_base_terrain(H, W, seed, n_bumps=120):
    """Rolling base terrain from summed Gaussian bumps. Returns float32 in [0,1]."""
    rng = np.random.RandomState(seed)
    terrain = np.zeros((H, W), dtype=np.float64)
    for _ in range(n_bumps):
        cx = rng.uniform(0, W)
        cy = rng.uniform(0, H)
        sigma = rng.uniform(min(H, W) * 0.03, min(H, W) * 0.15)
        amplitude = rng.uniform(-0.3, 0.3)
        terrain += _gaussian_bump(H, W, cx, cy, sigma, amplitude).astype(np.float64)
    terrain -= terrain.min()
    mx = terrain.max()
    if mx > 1e-9:
        terrain /= mx
    return terrain.astype(np.float32)


def add_craters(terrain, rng, n_craters=22):
    """
    Adds n_craters craters: paraboloid bowl + raised rim.
    Crater profile (radial distance d from crater centre, crater radius r):
      d < r       : depth * (1 - (d/r)^2)  depression
      r < d < 1.45r : Gaussian rim peak
    """
    H, W = terrain.shape
    t = terrain.copy()
    for _ in range(n_craters):
        cx = rng.uniform(W * 0.05, W * 0.95)
        cy = rng.uniform(H * 0.05, H * 0.95)
        r = rng.uniform(min(H, W) * 0.015, min(H, W) * 0.08)
        depth = rng.uniform(0.05, 0.20)
        rim_h = rng.uniform(0.02, 0.06)
        r_rim_peak = r * 1.15
        r_rim_outer = r * 1.45

        x0 = max(0, int(cx - r_rim_outer - 2))
        x1 = min(W, int(cx + r_rim_outer + 2))
        y0 = max(0, int(cy - r_rim_outer - 2))
        y1 = min(H, int(cy + r_rim_outer + 2))

        xs = np.arange(x0, x1, dtype=np.float32)
        ys = np.arange(y0, y1, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)
        dist = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)

        # Depression
        bowl = dist <= r
        t[y0:y1, x0:x1][bowl] -= (depth * (1.0 - (dist / r) ** 2))[bowl]

        # Rim
        rim_mask = (dist > r) & (dist < r_rim_outer)
        rim_sigma = (r_rim_outer - r) / 2.5
        rim_val = rim_h * np.exp(-((dist - r_rim_peak) ** 2) / (2.0 * rim_sigma ** 2 + 1e-9))
        t[y0:y1, x0:x1][rim_mask] += rim_val[rim_mask]

    return t


def compute_normals(terrain, z_scale=80.0):
    """
    Sobel-gradient surface normals.
    Returns float32 (H, W, 3) unit normal vectors [nx, ny, nz].
    """
    dzdx = cv2.Sobel(terrain, cv2.CV_32F, 1, 0, ksize=5) * z_scale
    dzdy = cv2.Sobel(terrain, cv2.CV_32F, 0, 1, ksize=5) * z_scale
    nx = -dzdx
    ny = -dzdy
    nz = np.ones_like(terrain, dtype=np.float32)
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2) + 1e-9
    return np.stack([nx / length, ny / length, nz / length], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def save_terrain(terrain, normals, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(out_dir / "heightmap.npy"), terrain)
    np.save(str(out_dir / "normals.npy"), normals)
    hm_u16 = (terrain * 65535.0).astype(np.uint16)
    cv2.imwrite(str(out_dir / "heightmap_u16.png"), hm_u16)

    # Quick hillshade preview (45-deg sun from north-west)
    sun = np.array([0.577, 0.577, 0.577], dtype=np.float32)
    shade = np.clip(np.tensordot(normals, sun, axes=([2], [0])), 0, 1)
    preview = (shade * 255).astype(np.uint8)
    cv2.imwrite(str(out_dir / "preview_hillshade.png"), preview)

    print(f"[terrain]  saved to {out_dir}")
    print(f"           heightmap : {terrain.shape}  range [{terrain.min():.3f}, {terrain.max():.3f}]")
    print(f"           normals   : {normals.shape}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic lunar height-map and surface normals."
    )
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--craters", type=int, default=22)
    parser.add_argument("--out", type=str, default="outputs/terrain")
    args = parser.parse_args()

    out_dir = ROOT / args.out
    rng = np.random.RandomState(args.seed)

    print(f"[terrain]  generating {args.size}x{args.size}  seed={args.seed}  craters={args.craters}")
    terrain = generate_base_terrain(args.size, args.size, seed=args.seed)
    terrain = add_craters(terrain, rng, n_craters=args.craters)
    terrain -= terrain.min()
    terrain /= (terrain.max() + 1e-9)
    normals = compute_normals(terrain)
    save_terrain(terrain, normals, out_dir)


if __name__ == "__main__":
    main()
