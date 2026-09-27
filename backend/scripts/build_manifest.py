"""
build_manifest.py — Real-Data Manifest Builder for LunarVision

Scans an input dataset directory containing lunar orbital imagery (.IMG, .LBL, .QUB,
.TIF, .PNG, .JPG, etc.), extracts PDS labels and spatial metadata, proposes candidate
registration pairs based on bounding box IoU (> 0) or center distance proximity,
and generates/updates the benchmark manifest CSV.
"""

import os
import re
import csv
import math
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("build_manifest")

# Recognized extensions for planetary and scientific raster images
SUPPORTED_EXTENSIONS = {
    ".img", ".lbl", ".qub", ".tif", ".tiff",
    ".png", ".jpg", ".jpeg", ".jp2", ".dat"
}


def parse_pds_text(text: str) -> Dict[str, Any]:
    """
    Parses key PDS label attributes from a text string (from .LBL or embedded header).
    Safely extracts sensor, illumination angles, spatial resolution, and coordinates.
    Never raises an exception; missing values are set to None.
    """
    metadata: Dict[str, Any] = {
        "sensor": None,
        "incidence_angle": None,
        "sun_elevation": None,
        "sun_azimuth": None,
        "pixel_resolution": None,
        "min_lat": None,
        "max_lat": None,
        "min_lon": None,
        "max_lon": None,
        "center_lat": None,
        "center_lon": None,
    }

    if not text:
        return metadata

    try:
        # 1. Sensor / Instrument
        sensor_match = re.search(
            r'\b(?:INSTRUMENT_NAME|INSTRUMENT_ID|SENSOR_NAME|SENSOR|INSTRUMENT_HOST_NAME|DETECTOR_ID)\s*=\s*["\']?([^"\';\r\n]+)',
            text,
            re.IGNORECASE
        )
        if sensor_match:
            raw_sensor = sensor_match.group(1).strip()
            # Clean common prefixes/suffixes
            raw_sensor = re.sub(r'^(CH2_|CH1_|LRO_)', '', raw_sensor, flags=re.IGNORECASE)
            metadata["sensor"] = raw_sensor

        # 2. Solar Incidence Angle
        inc_match = re.search(
            r'\b(?:INCIDENCE_ANGLE|SOLAR_INCIDENCE_ANGLE|CENTER_INCIDENCE_ANGLE)\s*=\s*([0-9.]+)',
            text,
            re.IGNORECASE
        )
        if inc_match:
            try:
                metadata["incidence_angle"] = float(inc_match.group(1))
            except ValueError:
                pass

        # 3. Sun Elevation Angle
        elev_match = re.search(
            r'\b(?:SUN_ELEVATION|SOLAR_ELEVATION|SOLAR_ALTITUDE|CENTER_SUN_ELEVATION)\s*=\s*([0-9.]+)',
            text,
            re.IGNORECASE
        )
        if elev_match:
            try:
                metadata["sun_elevation"] = float(elev_match.group(1))
            except ValueError:
                pass

        # Cross-calculate incidence / elevation if one is missing (incidence ~ 90 - elevation)
        if metadata["incidence_angle"] is None and metadata["sun_elevation"] is not None:
            metadata["incidence_angle"] = round(max(0.0, 90.0 - metadata["sun_elevation"]), 2)
        elif metadata["sun_elevation"] is None and metadata["incidence_angle"] is not None:
            metadata["sun_elevation"] = round(max(0.0, 90.0 - metadata["incidence_angle"]), 2)

        # 4. Sun Azimuth Angle
        az_match = re.search(
            r'\b(?:SUN_AZIMUTH|SOLAR_AZIMUTH|SUB_SOLAR_AZIMUTH|CENTER_SUN_AZIMUTH)\s*=\s*([0-9.]+)',
            text,
            re.IGNORECASE
        )
        if az_match:
            try:
                metadata["sun_azimuth"] = float(az_match.group(1))
            except ValueError:
                pass

        # 5. Pixel Resolution / Map Scale (m/px)
        res_match = re.search(
            r'\b(?:MAP_SCALE|PIXEL_RESOLUTION|SPATIAL_RESOLUTION|SAMPLING_PARAMETER|RESOLUTION|HORIZONTAL_PIXEL_SCALE|LINE_RESOLUTION)\s*=\s*([0-9.]+)',
            text,
            re.IGNORECASE
        )
        if res_match:
            try:
                metadata["pixel_resolution"] = float(res_match.group(1))
            except ValueError:
                pass

        # 6. Latitude bounding box
        min_lat_m = re.search(r'\b(?:MINIMUM_LATITUDE|MIN_LATITUDE|MIN_LAT)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        max_lat_m = re.search(r'\b(?:MAXIMUM_LATITUDE|MAX_LATITUDE|MAX_LAT)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        if min_lat_m and max_lat_m:
            try:
                metadata["min_lat"] = float(min_lat_m.group(1))
                metadata["max_lat"] = float(max_lat_m.group(1))
            except ValueError:
                pass

        # 7. Longitude bounding box
        min_lon_m = re.search(r'\b(?:WESTERNMOST_LONGITUDE|MIN_LONGITUDE|MIN_LON)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        max_lon_m = re.search(r'\b(?:EASTERNMOST_LONGITUDE|MAX_LONGITUDE|MAX_LON)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        if min_lon_m and max_lon_m:
            try:
                metadata["min_lon"] = float(min_lon_m.group(1))
                metadata["max_lon"] = float(max_lon_m.group(1))
            except ValueError:
                pass

        # 8. Center coordinates
        c_lat_m = re.search(r'\b(?:CENTER_LATITUDE|SUB_SPACECRAFT_LATITUDE|SUB_SOLAR_LATITUDE)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        c_lon_m = re.search(r'\b(?:CENTER_LONGITUDE|SUB_SPACECRAFT_LONGITUDE|SUB_SOLAR_LONGITUDE)\s*=\s*([-0-9.]+)', text, re.IGNORECASE)
        if c_lat_m and c_lon_m:
            try:
                metadata["center_lat"] = float(c_lat_m.group(1))
                metadata["center_lon"] = float(c_lon_m.group(1))
            except ValueError:
                pass
        elif metadata["min_lat"] is not None and metadata["max_lat"] is not None:
            metadata["center_lat"] = round((metadata["min_lat"] + metadata["max_lat"]) / 2.0, 4)
            if metadata["min_lon"] is not None and metadata["max_lon"] is not None:
                metadata["center_lon"] = round((metadata["min_lon"] + metadata["max_lon"]) / 2.0, 4)

    except Exception as e:
        logger.debug(f"Error parsing PDS label text: {e}")

    return metadata


def extract_metadata_from_file(file_path: Path) -> Dict[str, Any]:
    """
    Extracts PDS metadata from a file or its corresponding detached .LBL file.
    Reads up to 128KB of text to handle large PDS label blocks.
    Never crashes; returns defaults with None for missing fields.
    """
    text = ""
    # Check for detached .lbl file first if file is not already .lbl
    if file_path.suffix.lower() != ".lbl":
        lbl_candidate = file_path.with_suffix(".LBL")
        if not lbl_candidate.exists():
            lbl_candidate = file_path.with_suffix(".lbl")
        if lbl_candidate.exists():
            try:
                with open(lbl_candidate, "r", encoding="latin-1", errors="ignore") as f:
                    text = f.read(131072)
            except Exception:
                text = ""

    # If no detached label or empty, read directly from the target file header
    if not text:
        try:
            with open(file_path, "rb") as f:
                header_bytes = f.read(131072)
            text = header_bytes.decode("latin-1", errors="ignore")
        except Exception as e:
            logger.debug(f"Could not read header from {file_path}: {e}")
            text = ""

    meta = parse_pds_text(text)
    meta["file_path"] = str(file_path)
    meta["filename"] = file_path.name
    return meta


def calculate_bbox_iou(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float]
) -> float:
    """
    Computes Intersection over Union (IoU) for two (min_lat, max_lat, min_lon, max_lon) boxes.
    Returns a float in [0.0, 1.0].
    """
    min_lat_a, max_lat_a, min_lon_a, max_lon_a = box_a
    min_lat_b, max_lat_b, min_lon_b, max_lon_b = box_b

    inter_min_lat = max(min_lat_a, min_lat_b)
    inter_max_lat = min(max_lat_a, max_lat_b)
    inter_min_lon = max(min_lon_a, min_lon_b)
    inter_max_lon = min(max_lon_a, max_lon_b)

    if inter_max_lat <= inter_min_lat or inter_max_lon <= inter_min_lon:
        return 0.0

    inter_area = (inter_max_lat - inter_min_lat) * (inter_max_lon - inter_min_lon)
    area_a = (max_lat_a - min_lat_a) * (max_lon_a - min_lon_a)
    area_b = (max_lat_b - min_lat_b) * (max_lon_b - min_lon_b)
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def calculate_center_distance(
    c1: Tuple[float, float],
    c2: Tuple[float, float]
) -> float:
    """
    Approximates angular Euclidean distance between two (lat, lon) centers in degrees.
    """
    lat1, lon1 = c1
    lat2, lon2 = c2
    mean_lat_rad = math.radians((lat1 + lat2) / 2.0)
    d_lat = lat1 - lat2
    d_lon = (lon1 - lon2) * math.cos(mean_lat_rad)
    return math.sqrt(d_lat ** 2 + d_lon ** 2)


def scan_dataset(
    dataset_dir: Path
) -> List[Dict[str, Any]]:
    """
    Scans a dataset directory recursively for lunar imagery and parses PDS metadata.
    Avoids duplicate entries if both .IMG and .LBL exist for the same base name.
    """
    if not dataset_dir.exists() or not dataset_dir.is_dir():
        logger.warning(f"Dataset directory does not exist or is not a directory: {dataset_dir}")
        return []

    all_files = list(dataset_dir.rglob("*"))
    image_entries: List[Dict[str, Any]] = []

    # Map stems to avoid treating detached .lbl as a separate image
    image_files: List[Path] = []
    lbl_files: Dict[str, Path] = {}

    for f in all_files:
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            if ext == ".lbl":
                lbl_files[f.stem.lower()] = f
            else:
                image_files.append(f)

    # If there are standalone .lbl files without a matching raster image, keep them
    for stem, lbl_path in lbl_files.items():
        if not any(img.stem.lower() == stem for img in image_files):
            image_files.append(lbl_path)

    # Parse metadata for all discovered images
    for img_path in sorted(image_files):
        meta = extract_metadata_from_file(img_path)
        image_entries.append(meta)

    return image_entries


def propose_candidate_pairs(
    images: List[Dict[str, Any]],
    base_dir: Optional[Path] = None,
    max_center_distance_deg: float = 0.5,
    allow_fallback_all: bool = False
) -> List[Dict[str, Any]]:
    """
    Proposes candidate pairs from a list of image metadata dicts.
    Pairs are matched if:
    1. Both have bounding boxes and IoU > 0.
    2. Missing bounding boxes, but center distance <= max_center_distance_deg.
    3. Fallback: if allow_fallback_all is True and no coordinates are found across the set.
    """
    candidate_pairs: List[Dict[str, Any]] = []
    n = len(images)
    pair_counter = 1

    for i in range(n):
        for j in range(i + 1, n):
            img_a = images[i]
            img_b = images[j]

            path_a = Path(img_a["file_path"])
            path_b = Path(img_b["file_path"])

            # Resolve paths relative to base_dir if possible
            if base_dir:
                try:
                    rel_a = path_a.relative_to(base_dir).as_posix()
                except ValueError:
                    rel_a = path_a.name
                try:
                    rel_b = path_b.relative_to(base_dir).as_posix()
                except ValueError:
                    rel_b = path_b.name
            else:
                rel_a = path_a.as_posix()
                rel_b = path_b.as_posix()

            bbox_a = (img_a.get("min_lat"), img_a.get("max_lat"), img_a.get("min_lon"), img_a.get("max_lon"))
            bbox_b = (img_b.get("min_lat"), img_b.get("max_lat"), img_b.get("min_lon"), img_b.get("max_lon"))

            has_bbox_a = all(v is not None for v in bbox_a)
            has_bbox_b = all(v is not None for v in bbox_b)

            iou: Optional[float] = None
            is_match_candidate = False

            if has_bbox_a and has_bbox_b:
                iou_val = calculate_bbox_iou(bbox_a, bbox_b)
                if iou_val > 0.0:
                    iou = round(float(iou_val), 4)
                    is_match_candidate = True
            else:
                # Center-distance fallback
                c_a = (img_a.get("center_lat"), img_a.get("center_lon"))
                c_b = (img_b.get("center_lat"), img_b.get("center_lon"))
                if all(v is not None for v in c_a) and all(v is not None for v in c_b):
                    dist = calculate_center_distance(c_a, c_b)
                    if dist <= max_center_distance_deg:
                        is_match_candidate = True
                        iou = None
                elif allow_fallback_all:
                    is_match_candidate = True
                    iou = None

            if not is_match_candidate:
                continue

            # Sensor pair string
            sensor_a = img_a.get("sensor") or "unknown"
            sensor_b = img_b.get("sensor") or "unknown"
            # Sort sensor pair consistently
            s_pair = "_".join(sorted([sensor_a, sensor_b]))

            # Sun angle gap
            sun_angle_gap: Optional[float] = None
            inc_a = img_a.get("incidence_angle")
            inc_b = img_b.get("incidence_angle")
            if inc_a is not None and inc_b is not None:
                sun_angle_gap = round(abs(float(inc_a) - float(inc_b)), 2)

            # Scale ratio
            scale_ratio: Optional[float] = None
            res_a = img_a.get("pixel_resolution")
            res_b = img_b.get("pixel_resolution")
            if res_a is not None and res_b is not None and res_a > 0 and res_b > 0:
                scale_ratio = round(max(float(res_a), float(res_b)) / min(float(res_a), float(res_b)), 2)

            pair_id = f"pair_{pair_counter:03d}"
            pair_counter += 1

            candidate_pairs.append({
                "pair_id": pair_id,
                "source_path": rel_a,
                "reference_path": rel_b,
                "sensor_pair": s_pair,
                "sun_angle_gap": sun_angle_gap if sun_angle_gap is not None else "",
                "scale_ratio": scale_ratio if scale_ratio is not None else "",
                "footprint_iou": iou if iou is not None else "",
                "ground_truth_path": "",
            })

    return candidate_pairs


def compute_manifest_summary(
    images: List[Dict[str, Any]],
    pairs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes statistical counts and bucket distributions for the manifest summary.
    """
    total_images = len(images)
    total_pairs = len(pairs)

    # Sensor pair counts
    sensor_counts: Dict[str, int] = {}
    for p in pairs:
        sp = p.get("sensor_pair") or "unknown_unknown"
        sensor_counts[sp] = sensor_counts.get(sp, 0) + 1

    # Sun angle gap bucket counts
    gap_buckets = {
        "<10": 0,
        "10-30": 0,
        "30-60": 0,
        ">60": 0,
        "unknown": 0,
    }

    for p in pairs:
        gap_val = p.get("sun_angle_gap")
        if gap_val is None or gap_val == "":
            gap_buckets["unknown"] += 1
        else:
            try:
                g = float(gap_val)
                if g < 10.0:
                    gap_buckets["<10"] += 1
                elif 10.0 <= g < 30.0:
                    gap_buckets["10-30"] += 1
                elif 30.0 <= g <= 60.0:
                    gap_buckets["30-60"] += 1
                else:
                    gap_buckets[">60"] += 1
            except ValueError:
                gap_buckets["unknown"] += 1

    return {
        "total_images": total_images,
        "total_pairs": total_pairs,
        "sensor_pair_counts": sensor_counts,
        "sun_angle_gap_buckets": gap_buckets,
    }


def write_manifest_csv(
    pairs: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Writes candidate pairs to the benchmark manifest CSV file.
    Columns: pair_id, source_path, reference_path, sensor_pair, sun_angle_gap, scale_ratio, footprint_iou, ground_truth_path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pair_id",
        "source_path",
        "reference_path",
        "sensor_pair",
        "sun_angle_gap",
        "scale_ratio",
        "footprint_iou",
        "ground_truth_path"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in pairs:
            writer.writerow(p)

    logger.info(f"Wrote {len(pairs)} pairs to manifest at {output_path}")


def print_manifest_summary(summary: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Prints a human-readable manifest summary table to stdout.
    """
    print("\n" + "=" * 65)
    print(" LUNARVISION BENCHMARK MANIFEST SUMMARY")
    print("=" * 65)
    print(f" Total Images Found:    {summary['total_images']}")
    print(f" Total Candidate Pairs: {summary['total_pairs']}")
    if output_path:
        print(f" Manifest Destination:  {output_path}")
    print("-" * 65)

    print(" Candidate Pairs by Sensor Combination:")
    if summary["sensor_pair_counts"]:
        for sp, cnt in sorted(summary["sensor_pair_counts"].items()):
            print(f"   - {sp:<25}: {cnt:>4} pair(s)")
    else:
        print("   (No pairs formed)")

    print("-" * 65)
    print(" Candidate Pairs by Sun-Angle Gap Bucket:")
    for b_name in ["<10", "10-30", "30-60", ">60", "unknown"]:
        cnt = summary["sun_angle_gap_buckets"].get(b_name, 0)
        pct = (cnt / summary["total_pairs"] * 100.0) if summary["total_pairs"] > 0 else 0.0
        print(f"   - {b_name:<10} deg : {cnt:>4} pair(s)  ({pct:>5.1f}%)")
    print("=" * 65 + "\n")


def build_manifest(
    dataset_dir: Path,
    output_csv: Path,
    max_center_dist: float = 0.5,
    allow_fallback_all: bool = False
) -> Dict[str, Any]:
    """
    End-to-end execution of manifest building:
    1. Scans dataset directory.
    2. Parses metadata.
    3. Proposes pairs.
    4. Writes CSV.
    5. Returns summary dict.
    """
    images = scan_dataset(dataset_dir)
    pairs = propose_candidate_pairs(
        images=images,
        base_dir=output_csv.parent,
        max_center_distance_deg=max_center_dist,
        allow_fallback_all=allow_fallback_all
    )
    write_manifest_csv(pairs, output_csv)
    summary = compute_manifest_summary(images, pairs)
    print_manifest_summary(summary, output_path=output_csv)
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Scan real lunar dataset, extract PDS metadata, and build benchmark manifest."
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        required=True,
        help="Path to folder containing real lunar images / PDS labels"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="backend/sample_data/benchmark_manifest.csv",
        help="Output CSV path (default: backend/sample_data/benchmark_manifest.csv)"
    )
    parser.add_argument(
        "--max-center-dist",
        type=float,
        default=0.5,
        help="Max distance in degrees between centers if bounding boxes are missing (default: 0.5)"
    )
    parser.add_argument(
        "--fallback-all",
        action="store_true",
        help="Propose candidate pairs for all combinations if spatial coordinates are unavailable"
    )

    args = parser.parse_args()
    dataset_dir = Path(args.dataset_dir).resolve()
    output_csv = Path(args.output).resolve()

    build_manifest(
        dataset_dir=dataset_dir,
        output_csv=output_csv,
        max_center_dist=args.max_center_dist,
        allow_fallback_all=args.fallback_all
    )


if __name__ == "__main__":
    main()
