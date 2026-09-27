"""
Step 2 - Physically-Based Illumination Renderer
================================================
Renders the synthetic height-map under different sun angles using:
  1. Lambertian shading  : intensity = max(0, dot(normal, sun_direction))
  2. Ray-marched cast shadows : for each pixel, step along the sun direction
     and check whether any uphill point blocks the sun ray.  This produces
     physically correct crater-interior blackouts at low sun elevation,
     unlike a simple brightness gradient.

Outputs (in <out_dir>/renders/):
  elev{EL}_az{AZ}_scale{S}.png   -- uint8 grayscale rendered image
  render_index.json               -- metadata for every rendered image

Sun-angle grid (defaults):
  elevations : 70, 50, 30, 15, 5  degrees
  azimuths   : 45, 135            degrees  (NE / NW illumination)
  scales     : 1.0 (full res), 0.5 (half res, simulates coarser sensor)

Usage
-----
  python backend/scripts/render_illumination.py
         [--terrain outputs/terrain]
         [--out     outputs/renders]
         [--elevations 70 50 30 15 5]
         [--azimuths 45 135]
         [--scales 1.0 0.5]
         [--shadow-step 1.5]
"""

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import terrain helpers so we can regenerate if needed
from backend.scripts.generate_synthetic_terrain import (
    generate_base_terrain, add_craters, compute_normals, save_terrain
)


# ---------------------------------------------------------------------------
# Sun direction helper
# ---------------------------------------------------------------------------

def sun_direction(elevation_deg: float, azimuth_deg: float) -> np.ndarray:
    """
    Convert (elevation, azimuth) angles to a unit 3-D sun direction vector.

    Convention (matching surface normal space):
      X = East,  Y = North,  Z = Up
      Azimuth 0 = North, 90 = East (clockwise).
    """
    el = math.radians(elevation_deg)
    az = math.radians(azimuth_deg)
    sx = math.sin(az) * math.cos(el)
    sy = math.cos(az) * math.cos(el)
    sz = math.sin(el)
    return np.array([sx, sy, sz], dtype=np.float32)


# ---------------------------------------------------------------------------
# Shadow computation
# ---------------------------------------------------------------------------

def compute_shadow_mask(terrain: np.ndarray, sun_dir: np.ndarray,
                        step_size: float = 1.5) -> np.ndarray:
    """
    Ray-march cast shadows across the height-map.

    For every pixel (x, y):
      Walk backward along the projected sun ray in 2-D map space.
      At each step, check whether the terrain height at the walked position
      exceeds the interpolated ray height.  If yes -> pixel is in shadow.

    Parameters
    ----------
    terrain   : float32 (H, W)  in [0, 1]
    sun_dir   : float32 (3,)    unit vector [sx, sy, sz]
    step_size : marching step in pixels

    Returns
    -------
    shadow : float32 (H, W)  0 = fully shadowed, 1 = lit
    """
    H, W = terrain.shape
    sx, sy, sz = float(sun_dir[0]), float(sun_dir[1]), float(sun_dir[2])

    if sz <= 1e-6:
        # Sun at or below horizon: entire terrain in shadow
        return np.zeros((H, W), dtype=np.float32)

    # Horizontal speed per unit height gain
    # dx/dz and dy/dz when moving *toward* the sun
    dx_dh = sx / sz
    dy_dh = sy / sz

    shadow = np.zeros((H, W), dtype=np.float32)
    max_dim = max(H, W)
    max_steps = int(max_dim / step_size) + 1

    # Build a float32 copy for fast bilinear lookup
    t = terrain.astype(np.float32)

    for step in range(1, max_steps + 1):
        dist = step * step_size
        # Shift in pixel coordinates as we walk *away* from the sun
        px_offset = -dx_dh * dist   # x shift (cols)
        py_offset = -dy_dh * dist   # y shift (rows)
        # Height of the ray above the origin pixel at this distance
        h_ray_gain = dist * (sz / math.sqrt(sx**2 + sy**2 + sz**2 + 1e-12)) * (1.0 / (math.sqrt(sx**2 + sy**2 + 1e-12) or 1e-9))

        # For each pixel (row r, col c), the shadowing position is (r + py_offset, c + px_offset)
        # Build sampling grid
        r_coords = np.arange(H, dtype=np.float32)
        c_coords = np.arange(W, dtype=np.float32)
        cc, rr = np.meshgrid(c_coords, r_coords)

        sample_r = rr + py_offset
        sample_c = cc + px_offset

        # Bilinear interpolation of terrain at (sample_r, sample_c)
        # Out-of-bounds -> treat as 0 height (no shadow from outside terrain)
        valid = (
            (sample_r >= 0) & (sample_r < H - 1) &
            (sample_c >= 0) & (sample_c < W - 1)
        )

        sr = np.clip(sample_r, 0, H - 1)
        sc = np.clip(sample_c, 0, W - 1)
        sr0 = sr.astype(np.int32)
        sc0 = sc.astype(np.int32)
        sr1 = np.clip(sr0 + 1, 0, H - 1)
        sc1 = np.clip(sc0 + 1, 0, W - 1)
        fr = sr - sr0
        fc = sc - sc0

        neighbour_h = (
            t[sr0, sc0] * (1 - fr) * (1 - fc) +
            t[sr0, sc1] * (1 - fr) * fc +
            t[sr1, sc0] * fr * (1 - fr) +
            t[sr1, sc1] * fr * fc
        )

        # Ray height at the sampled position
        ray_h = t + h_ray_gain   # origin pixel terrain + ray gain

        # Pixel is in shadow if the neighbour terrain is HIGHER than the ray
        newly_shadowed = valid & (neighbour_h > ray_h)
        shadow[newly_shadowed] = 1.0

    return 1.0 - shadow   # 1 = lit, 0 = shadow


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render(terrain: np.ndarray, normals: np.ndarray,
           elevation_deg: float, azimuth_deg: float,
           output_size: int, shadow_step: float = 1.5) -> np.ndarray:
    """
    Render terrain as a uint8 grayscale image at the given sun angle.

    Steps:
      1. Lambertian shading from surface normals
      2. Cast shadow mask via ray-marching
      3. Combine: shaded_pixel = shade * shadow_factor
      4. Rescale output to `output_size` x `output_size`
      5. Stretch to full uint8 range

    Returns uint8 (output_size, output_size) grayscale image.
    """
    sun = sun_direction(elevation_deg, azimuth_deg)

    # Lambertian shading
    shade = np.tensordot(normals, sun, axes=([2], [0])).astype(np.float32)
    shade = np.clip(shade, 0.0, 1.0)

    # Ambient term so fully-shadowed regions aren't pure black (more realistic)
    ambient = 0.08
    shade = ambient + (1.0 - ambient) * shade

    # Cast shadows
    shadow = compute_shadow_mask(terrain, sun, step_size=shadow_step)
    rendered = shade * shadow

    # Rescale to output_size
    H, W = terrain.shape
    if output_size != H or output_size != W:
        rendered = cv2.resize(rendered, (output_size, output_size),
                              interpolation=cv2.INTER_AREA)

    # Stretch to [0, 255]
    r_min, r_max = rendered.min(), rendered.max()
    if r_max - r_min > 1e-7:
        rendered = (rendered - r_min) / (r_max - r_min)
    out = (rendered * 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------
# Batch render
# ---------------------------------------------------------------------------

def batch_render(terrain: np.ndarray, normals: np.ndarray,
                 elevations, azimuths, scales,
                 out_dir: Path, shadow_step: float,
                 base_size: int) -> list:
    """
    Render all (elevation, azimuth, scale) combinations.
    Returns list of metadata dicts.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []

    total = len(elevations) * len(azimuths) * len(scales)
    done = 0
    for el in elevations:
        for az in azimuths:
            for sc in scales:
                output_size = max(32, int(base_size * sc))
                img = render(terrain, normals, el, az,
                             output_size=output_size,
                             shadow_step=shadow_step)
                fname = f"elev{el:03.0f}_az{az:03.0f}_scale{sc:.2f}.png"
                fpath = out_dir / fname
                cv2.imwrite(str(fpath), img)

                meta = {
                    "filename": fname,
                    "path": str(fpath),
                    "elevation_deg": el,
                    "azimuth_deg": az,
                    "scale_factor": sc,
                    "output_size": output_size,
                }
                index.append(meta)
                done += 1
                print(f"  [{done:3d}/{total}]  elev={el:5.1f}  az={az:5.1f}  "
                      f"scale={sc:.2f}  size={output_size}px  -> {fname}")

    # Save index
    with open(out_dir / "render_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"\n[render]  {len(index)} images saved to {out_dir}")
    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Physically-based shadow renderer for synthetic lunar terrain."
    )
    parser.add_argument("--terrain", type=str, default="outputs/terrain",
                        help="Directory containing heightmap.npy and normals.npy")
    parser.add_argument("--out", type=str, default="outputs/renders")
    parser.add_argument("--elevations", type=float, nargs="+",
                        default=[70.0, 50.0, 30.0, 15.0, 5.0])
    parser.add_argument("--azimuths", type=float, nargs="+",
                        default=[45.0, 135.0])
    parser.add_argument("--scales", type=float, nargs="+",
                        default=[1.0, 0.5])
    parser.add_argument("--shadow-step", type=float, default=1.5,
                        help="Ray-march step size in pixels (smaller=accurate, slower)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--craters", type=int, default=22)
    parser.add_argument("--size", type=int, default=1024,
                        help="Terrain size if generating fresh (ignored if .npy present)")
    args = parser.parse_args()

    terrain_dir = ROOT / args.terrain
    out_dir = ROOT / args.out

    # Load or generate terrain
    hm_path = terrain_dir / "heightmap.npy"
    nm_path = terrain_dir / "normals.npy"

    if hm_path.exists() and nm_path.exists():
        print(f"[render]  loading terrain from {terrain_dir}")
        terrain = np.load(str(hm_path))
        normals = np.load(str(nm_path))
    else:
        print(f"[render]  terrain not found at {terrain_dir}, generating ...")
        rng = np.random.RandomState(args.seed)
        terrain = generate_base_terrain(args.size, args.size, seed=args.seed)
        terrain = add_craters(terrain, rng, n_craters=args.craters)
        terrain -= terrain.min()
        terrain /= (terrain.max() + 1e-9)
        normals = compute_normals(terrain)
        save_terrain(terrain, normals, terrain_dir)

    base_size = terrain.shape[0]
    print(f"[render]  terrain {terrain.shape}  "
          f"elevations={args.elevations}  azimuths={args.azimuths}  scales={args.scales}")

    batch_render(terrain, normals,
                 elevations=args.elevations,
                 azimuths=args.azimuths,
                 scales=args.scales,
                 out_dir=out_dir,
                 shadow_step=args.shadow_step,
                 base_size=base_size)


if __name__ == "__main__":
    main()
