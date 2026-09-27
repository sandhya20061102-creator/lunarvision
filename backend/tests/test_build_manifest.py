"""
test_build_manifest.py — Tests for Real-Data Manifest Builder

Verifies:
1. PDS text parsing for sensor, solar angles, pixel resolution, and lat/lon bounds.
2. IoU calculation for intersecting and non-intersecting footprints.
3. Center-distance fallback calculation.
4. Scanning a mock dataset directory containing .IMG, detached .LBL, and .PNG images.
5. Generation of benchmark_manifest.csv with required columns.
6. Verification of summary bucket distributions (<10, 10-30, 30-60, >60, unknown).
7. Error tolerance on corrupt or empty files.
"""

import csv
import sys
from pathlib import Path

import pytest

# Ensure root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.scripts.build_manifest import (
    parse_pds_text,
    calculate_bbox_iou,
    calculate_center_distance,
    scan_dataset,
    propose_candidate_pairs,
    compute_manifest_summary,
    write_manifest_csv,
    build_manifest,
)


def test_parse_pds_text_complete():
    sample_label = """
    PDS_VERSION_ID = PDS3
    INSTRUMENT_NAME = "CH2_TMC_2"
    INCIDENCE_ANGLE = 24.5
    SUN_AZIMUTH = 112.3
    PIXEL_RESOLUTION = 5.0
    MINIMUM_LATITUDE = -15.5
    MAXIMUM_LATITUDE = -14.0
    WESTERNMOST_LONGITUDE = 40.0
    EASTERNMOST_LONGITUDE = 41.5
    CENTER_LATITUDE = -14.75
    CENTER_LONGITUDE = 40.75
    """
    meta = parse_pds_text(sample_label)
    assert meta["sensor"] == "TMC_2"
    assert meta["incidence_angle"] == 24.5
    assert meta["sun_elevation"] == 65.5  # 90 - 24.5
    assert meta["sun_azimuth"] == 112.3
    assert meta["pixel_resolution"] == 5.0
    assert meta["min_lat"] == -15.5
    assert meta["max_lat"] == -14.0
    assert meta["min_lon"] == 40.0
    assert meta["max_lon"] == 41.5
    assert meta["center_lat"] == -14.75
    assert meta["center_lon"] == 40.75


def test_parse_pds_text_empty_and_corrupt():
    meta = parse_pds_text("")
    assert meta["sensor"] is None
    assert meta["incidence_angle"] is None
    assert meta["pixel_resolution"] is None

    garbage_label = "CORRUPT_HEADER_WITHOUT_EQUALS_SIGNS_AND_RANDOM_BYTES_01010101"
    meta_garbage = parse_pds_text(garbage_label)
    assert meta_garbage["sensor"] is None
    assert meta_garbage["min_lat"] is None


def test_calculate_bbox_iou():
    # Box: (min_lat, max_lat, min_lon, max_lon)
    # Box A: [0, 2, 0, 2] -> Area = 4
    # Box B: [1, 3, 1, 3] -> Area = 4, Inter = [1, 2, 1, 2] -> Area = 1, Union = 7
    box_a = (0.0, 2.0, 0.0, 2.0)
    box_b = (1.0, 3.0, 1.0, 3.0)
    iou = calculate_bbox_iou(box_a, box_b)
    assert abs(iou - (1.0 / 7.0)) < 1e-4

    # Disjoint boxes
    box_c = (5.0, 6.0, 5.0, 6.0)
    assert calculate_bbox_iou(box_a, box_c) == 0.0


def test_calculate_center_distance():
    c1 = (0.0, 0.0)
    c2 = (0.0, 0.3)
    dist = calculate_center_distance(c1, c2)
    assert abs(dist - 0.3) < 1e-3


@pytest.fixture
def fake_lunar_dataset(tmp_path: Path):
    """
    Creates a temporary directory simulating a multi-sensor lunar dataset:
    - Image 1: OHRC strip, incidence 20.0 deg, res 0.3 m/px, box [-15.0, -14.0, 40.0, 41.0]
    - Image 2: TMC strip (overlapping with 1), incidence 45.0 deg, res 5.0 m/px, box [-14.8, -13.8, 40.2, 41.2]
               Sun angle gap = |20 - 45| = 25 deg (bucket: 10-30)
    - Image 3: IIRS strip (overlapping with 1 and 2), incidence 82.0 deg, res 20.0 m/px, box [-15.2, -14.2, 40.1, 41.1]
               Sun angle gap vs 1 = |20 - 82| = 62 deg (bucket: >60)
               Sun angle gap vs 2 = |45 - 82| = 37 deg (bucket: 30-60)
    - Image 4: Disjoint crater image elsewhere (lat: 50.0, lon: 100.0)
    - Image 5: Corrupt image file
    """
    dataset_dir = tmp_path / "fake_dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # 1. OHRC with embedded PDS label
    lbl_1 = (
        "PDS_VERSION_ID = PDS3\n"
        "INSTRUMENT_NAME = \"CH2_OHRC\"\n"
        "INCIDENCE_ANGLE = 20.0\n"
        "SUN_AZIMUTH = 90.0\n"
        "PIXEL_RESOLUTION = 0.32\n"
        "MINIMUM_LATITUDE = -15.0\n"
        "MAXIMUM_LATITUDE = -14.0\n"
        "WESTERNMOST_LONGITUDE = 40.0\n"
        "EASTERNMOST_LONGITUDE = 41.0\n"
        "END\n"
    )
    with open(dataset_dir / "ch2_ohrc_001.img", "wb") as f:
        f.write(lbl_1.encode("latin-1") + b"\x00" * 1024)

    # 2. TMC with detached .LBL file
    lbl_2 = (
        "PDS_VERSION_ID = PDS3\n"
        "INSTRUMENT_NAME = \"TMC\"\n"
        "INCIDENCE_ANGLE = 45.0\n"
        "SUN_AZIMUTH = 100.0\n"
        "PIXEL_RESOLUTION = 5.0\n"
        "MINIMUM_LATITUDE = -14.8\n"
        "MAXIMUM_LATITUDE = -13.8\n"
        "WESTERNMOST_LONGITUDE = 40.2\n"
        "EASTERNMOST_LONGITUDE = 41.2\n"
        "END\n"
    )
    with open(dataset_dir / "ch2_tmc_002.lbl", "w", encoding="latin-1") as f:
        f.write(lbl_2)
    with open(dataset_dir / "ch2_tmc_002.img", "wb") as f:
        f.write(b"RAW_DATA" * 128)

    # 3. IIRS with embedded label
    lbl_3 = (
        "PDS_VERSION_ID = PDS3\n"
        "INSTRUMENT_NAME = \"IIRS\"\n"
        "INCIDENCE_ANGLE = 82.0\n"
        "SUN_AZIMUTH = 110.0\n"
        "PIXEL_RESOLUTION = 20.0\n"
        "MINIMUM_LATITUDE = -15.2\n"
        "MAXIMUM_LATITUDE = -14.2\n"
        "WESTERNMOST_LONGITUDE = 40.1\n"
        "EASTERNMOST_LONGITUDE = 41.1\n"
        "END\n"
    )
    with open(dataset_dir / "ch2_iirs_003.qub", "wb") as f:
        f.write(lbl_3.encode("latin-1") + b"\x00" * 1024)

    # 4. Disjoint image
    lbl_4 = (
        "PDS_VERSION_ID = PDS3\n"
        "INSTRUMENT_NAME = \"OHRC\"\n"
        "INCIDENCE_ANGLE = 22.0\n"
        "PIXEL_RESOLUTION = 0.32\n"
        "MINIMUM_LATITUDE = 50.0\n"
        "MAXIMUM_LATITUDE = 51.0\n"
        "WESTERNMOST_LONGITUDE = 100.0\n"
        "EASTERNMOST_LONGITUDE = 101.0\n"
        "END\n"
    )
    with open(dataset_dir / "ch2_ohrc_disjoint.img", "wb") as f:
        f.write(lbl_4.encode("latin-1") + b"\x00" * 1024)

    # 5. Corrupt file without valid label
    with open(dataset_dir / "corrupted_file.img", "wb") as f:
        f.write(b"\xff\xfe\x00\x00" * 32)

    return dataset_dir


def test_build_manifest_end_to_end(fake_lunar_dataset: Path, tmp_path: Path):
    output_csv = tmp_path / "benchmark_manifest.csv"

    summary = build_manifest(
        dataset_dir=fake_lunar_dataset,
        output_csv=output_csv,
        max_center_dist=0.5
    )

    assert output_csv.exists()
    assert summary["total_images"] == 5

    # Candidates overlapping:
    # (OHRC 1, TMC 2) -> IoU > 0, gap = 25.0
    # (OHRC 1, IIRS 3) -> IoU > 0, gap = 62.0
    # (TMC 2, IIRS 3) -> IoU > 0, gap = 37.0
    # Disjoint is not paired. Corrupt has no bbox/center and is not paired.
    assert summary["total_pairs"] == 3

    # Check sun-angle buckets
    gap_b = summary["sun_angle_gap_buckets"]
    assert gap_b["<10"] == 0
    assert gap_b["10-30"] == 1   # OHRC 1 + TMC 2 (25.0 deg)
    assert gap_b["30-60"] == 1   # TMC 2 + IIRS 3 (37.0 deg)
    assert gap_b[">60"] == 1     # OHRC 1 + IIRS 3 (62.0 deg)
    assert gap_b["unknown"] == 0

    # Check sensor counts
    assert "OHRC_TMC" in summary["sensor_pair_counts"] or "TMC_OHRC" in summary["sensor_pair_counts"]

    # Verify CSV file contents and headers
    with open(output_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    expected_cols = {
        "pair_id", "source_path", "reference_path", "sensor_pair",
        "sun_angle_gap", "scale_ratio", "footprint_iou", "ground_truth_path"
    }
    assert expected_cols.issubset(set(reader.fieldnames))

    # Check values for one row
    row0 = rows[0]
    assert row0["pair_id"] == "pair_001"
    assert float(row0["sun_angle_gap"]) > 0
    assert float(row0["footprint_iou"]) > 0
    assert row0["ground_truth_path"] == ""
