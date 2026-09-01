"""
Generates realistic synthetic lunar surface image pairs for testing
LunarVision Image Registration, Temporal Change Detection, and No-Match Rejection.
"""

from pathlib import Path
import cv2
import numpy as np


def generate_lunar_terrain(width=512, height=512, seed=42, craters=None):
    """
    Generates a realistic lunar regolith texture with craters and directional solar illumination.
    """
    np.random.seed(seed)
    # 1. Base lunar regolith noise
    base = np.random.normal(128, 18, (height, width)).astype(np.float32)
    base = cv2.GaussianBlur(base, (15, 15), 4.0)

    # 2. Add subtle fine micro-texture
    micro = np.random.normal(0, 6, (height, width)).astype(np.float32)
    micro = cv2.GaussianBlur(micro, (5, 5), 1.0)
    surface = base + micro

    if craters is None:
        craters = [
            (160, 170, 42, -60, 45),  # (cx, cy, radius, depth_shadow, rim_highlight)
            (360, 280, 55, -75, 55),
            (260, 390, 32, -48, 38),
            (390, 130, 26, -40, 30),
            (110, 360, 38, -55, 42),
            (280, 230, 20, -32, 25),
            (190, 80, 18, -28, 22),
            (440, 420, 24, -36, 28),
        ]

    for cx, cy, r, depth, rim in craters:
        y, x = np.ogrid[:height, :width]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

        # Directional solar illumination from top-left (-x, -y)
        sun_dir = ((x - cx) + (y - cy)) / float(max(r, 1))

        # Crater depression with shadow gradient
        crater_mask = dist <= r
        if np.any(crater_mask):
            surface[crater_mask] += depth * (1.0 - (dist[crater_mask] / r) ** 1.5) + (sun_dir[crater_mask] * 20.0)

        # Raised crater rim
        rim_mask = (dist > (r - 5)) & (dist <= (r + 5))
        if np.any(rim_mask):
            rim_factor = 1.0 - (np.abs(dist[rim_mask] - r) / 5.0)
            surface[rim_mask] += rim * rim_factor * (1.0 - sun_dir[rim_mask] * 0.4)

    # Normalize to full 8-bit dynamic range
    surface = np.clip(surface, 0, 255)
    norm_surface = cv2.normalize(surface, None, 15, 240, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    bgr = cv2.cvtColor(norm_surface, cv2.COLOR_GRAY2BGR)
    return bgr


def save_as_pds_img(filepath: Path, img_bgr: np.ndarray):
    """
    Saves an image NumPy array as a standard PDS3 16-bit .IMG scientific dataset.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if len(img_bgr.shape) == 3 else img_bgr
    h, w = gray.shape[:2]
    gray_16 = (gray.astype(np.uint16) * 256)

    record_bytes = 512
    label_records = 2
    header_str = (
        f"PDS_VERSION_ID = PDS3\n"
        f"RECORD_TYPE = FIXED_LENGTH\n"
        f"RECORD_BYTES = {record_bytes}\n"
        f"LABEL_RECORDS = {label_records}\n"
        f"^IMAGE = {label_records + 1}\n"
        f"OBJECT = IMAGE\n"
        f"  LINES = {h}\n"
        f"  LINE_SAMPLES = {w}\n"
        f"  SAMPLE_BITS = 16\n"
        f"  SAMPLE_TYPE = LSB_UNSIGNED_INTEGER\n"
        f"END_OBJECT = IMAGE\n"
        f"END\n"
    )
    header_bytes = header_str.encode("latin-1")
    padded_header = header_bytes + b" " * (record_bytes * label_records - len(header_bytes))

    with open(filepath, "wb") as f:
        f.write(padded_header)
        f.write(gray_16.tobytes())


def create_sample_dataset():
    sample_dir = Path(__file__).resolve().parent / "backend" / "sample_data"
    sample_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating sample lunar test imagery into {sample_dir}...")

    # 1. Baseline Image (Pre-event Reference Pass)
    baseline_img = generate_lunar_terrain(512, 512, seed=101)
    p1 = sample_dir / "01_baseline_pre_event.png"
    cv2.imwrite(str(p1), baseline_img)
    print(f"[OK] Generated: {p1.name} (Baseline Reference Frame)")

    # 2. Temporal Pass with Geometric Transformation (For Testing Image Registration)
    # Apply 3.5 deg rotation + 8px shift
    M = cv2.getRotationMatrix2D((256, 256), angle=3.5, scale=1.0)
    M[0, 2] += 8.0
    M[1, 2] += -6.0
    reg_test_img = cv2.warpAffine(baseline_img, M, (512, 512), borderMode=cv2.BORDER_REFLECT)
    p2 = sample_dir / "02_temporal_rotated_shifted.png"
    cv2.imwrite(str(p2), reg_test_img)
    print(f"[OK] Generated: {p2.name} (Rotated & Translated for Registration Testing)")

    # 3. Temporal Pass with a Fresh Impact Crater (For Testing Change Detection)
    # Start with transformed baseline, add fresh impact crater at (230, 220) with dark shadow and bright ejecta
    change_test_img = reg_test_img.copy()
    # Dark crater depression
    cv2.circle(change_test_img, (230, 220), 22, (25, 25, 25), -1)
    # Bright crater rim
    cv2.circle(change_test_img, (230, 220), 25, (235, 235, 235), 3)
    # Ejecta rays
    cv2.line(change_test_img, (230, 195), (230, 175), (210, 210, 210), 2)
    cv2.line(change_test_img, (255, 220), (280, 220), (200, 200, 200), 2)
    cv2.line(change_test_img, (210, 240), (190, 260), (205, 205, 205), 2)
    cv2.GaussianBlur(change_test_img, (3, 3), 0.8, dst=change_test_img)

    p3 = sample_dir / "03_temporal_new_impact_crater.png"
    cv2.imwrite(str(p3), change_test_img)
    print(f"[OK] Generated: {p3.name} (Fresh Impact Crater for Change Detection Testing)")

    # 4. Completely Unrelated Lunar Terrain (For Testing No-Match Rejection)
    unrelated_img = generate_lunar_terrain(512, 512, seed=999, craters=[
        (200, 200, 70, -80, 60),
        (400, 380, 40, -50, 40),
        (100, 400, 30, -40, 30),
    ])
    p4 = sample_dir / "04_unrelated_lunar_terrain.png"
    cv2.imwrite(str(p4), unrelated_img)
    print(f"[OK] Generated: {p4.name} (Dissimilar Terrain for No-Match Rejection Testing)")

    # 5. Scientific Lunar .IMG Files (PDS3 16-Bit Format)
    p5_ref = sample_dir / "05_scientific_lunar_reference.IMG"
    save_as_pds_img(p5_ref, baseline_img)
    print(f"[OK] Generated: {p5_ref.name} (Scientific Lunar Baseline .IMG Data)")

    p6_src = sample_dir / "06_scientific_lunar_transformed.IMG"
    save_as_pds_img(p6_src, reg_test_img)
    print(f"[OK] Generated: {p6_src.name} (Scientific Lunar Transformed .IMG Data)")

    print("All sample datasets generated successfully!")


if __name__ == "__main__":
    create_sample_dataset()
