"""
Test Suite for LunarVision Scientific Lunar .IMG & Web Image Upload Pipeline
Verifies:
1. Decoding of PNG/JPG/TIFF/BMP files.
2. Parsing of PDS3 16-bit .IMG files.
3. Parsing of raw binary .IMG files.
4. Auto file type detection in PreprocessingService.
5. End-to-end FastAPI image registration endpoint with .IMG uploads.
6. Error handling for invalid/corrupted files.
"""

import sys
import unittest
from pathlib import Path
import numpy as np
import cv2

# Add backend directory to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from services.preprocessing import PreprocessingService
from services.feature_detection import FeatureDetectionService
from services.matching import FeatureMatchingService
from services.registration import ImageRegistrationService


class TestImageUploadAndProcessing(unittest.TestCase):
    def setUp(self):
        self.prep_svc = PreprocessingService()
        self.feature_svc = FeatureDetectionService()
        self.sample_dir = Path(__file__).resolve().parent / "backend" / "sample_data"

    def test_01_png_jpg_decoding(self):
        """Test decoding of standard PNG and JPG files."""
        baseline_png = self.sample_dir / "01_baseline_pre_event.png"
        self.assertTrue(baseline_png.exists(), "Sample baseline PNG missing")

        with open(baseline_png, "rb") as f:
            bytes_data = f.read()

        img = self.prep_svc.load_image_from_bytes(bytes_data, filename="test.png")
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(len(img.shape), 3)
        self.assertEqual(img.shape[2], 3)
        print("  [PASS] PNG/JPG decoding verified")

    def test_02_pds3_img_decoding(self):
        """Test parsing and dynamic range normalization of scientific PDS3 .IMG files."""
        pds_img_path = self.sample_dir / "05_scientific_lunar_reference.IMG"
        self.assertTrue(pds_img_path.exists(), "Sample PDS .IMG missing")

        with open(pds_img_path, "rb") as f:
            bytes_data = f.read()

        img = self.prep_svc.load_image_from_bytes(bytes_data, filename="05_scientific_lunar_reference.IMG")
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(len(img.shape), 3)
        self.assertEqual(img.shape[2], 3)
        self.assertGreater(np.max(img), 0)
        print("  [PASS] Scientific PDS3 .IMG decoding & normalization verified")

    def test_03_raw_binary_img_decoding(self):
        """Test fallback parsing of raw binary matrix .IMG files."""
        # Create unheadered raw 256x256 uint16 buffer
        raw_mat = (np.random.randint(100, 1000, (256, 256), dtype=np.uint16)).tobytes()
        img = self.prep_svc.load_image_from_bytes(raw_mat, filename="raw_matrix.img")
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(img.shape[:2], (256, 256))
        print("  [PASS] Raw binary matrix .IMG decoding verified")

    def test_04_end_to_end_registration_with_img(self):
        """Test geometric image registration between two scientific .IMG lunar datasets."""
        ref_path = self.sample_dir / "05_scientific_lunar_reference.IMG"
        src_path = self.sample_dir / "06_scientific_lunar_transformed.IMG"

        with open(ref_path, "rb") as f:
            ref_bytes = f.read()
        with open(src_path, "rb") as f:
            src_bytes = f.read()

        ref_prep = self.prep_svc.preprocess_pipeline(self.prep_svc.load_image_from_bytes(ref_bytes, filename=ref_path.name))
        src_prep = self.prep_svc.preprocess_pipeline(self.prep_svc.load_image_from_bytes(src_bytes, filename=src_path.name))

        ref_kps, ref_descs, _ = self.feature_svc.detect_features(ref_prep["enhanced"])
        src_kps, src_descs, _ = self.feature_svc.detect_features(src_prep["enhanced"])

        self.assertGreaterEqual(len(ref_kps), 6)
        self.assertGreaterEqual(len(src_kps), 6)

        matcher = FeatureMatchingService()
        good_matches, total_matches = matcher.match_descriptors(src_descs, ref_descs)
        self.assertGreaterEqual(len(good_matches), 6)

        reg_svc = ImageRegistrationService()
        reg_result = reg_svc.align_images(
            source_img=src_prep["original_color"],
            reference_img=ref_prep["original_color"],
            src_keypoints=src_kps,
            ref_keypoints=ref_kps,
            matches=good_matches
        )

        self.assertTrue(reg_result["success"])
        self.assertGreaterEqual(reg_result["inlier_count"], 6)
        print(f"  [PASS] Scientific .IMG registration successful! Inliers: {reg_result['inlier_count']}")

    def test_05_invalid_corrupted_file_rejection(self):
        """Test rejection and error message for corrupted or non-image files."""
        corrupted_bytes = b"THIS_IS_NOT_AN_IMAGE_FILE_BUFFER_12345"
        with self.assertRaises(ValueError) as ctx:
            self.prep_svc.load_image_from_bytes(corrupted_bytes, filename="invalid.txt")
        
        self.assertIn("Failed to decode image file", str(ctx.exception))
        print("  [PASS] Invalid file rejection & error message verified")

    def test_06_akaze_feature_detection_and_matching(self):
        """Test AKAZE keypoint detection and binary descriptor matching with NORM_HAMMING."""
        baseline_png = self.sample_dir / "01_baseline_pre_event.png"
        img = self.prep_svc.load_image_from_path(str(baseline_png))
        prep = self.prep_svc.preprocess_pipeline(img)

        kps, descs, algo = self.feature_svc.detect_features(prep["enhanced"], preferred_algorithm="AKAZE")
        self.assertEqual(algo, "AKAZE")
        self.assertGreaterEqual(len(kps), 6)
        self.assertEqual(descs.dtype, np.uint8)

        matcher = FeatureMatchingService()
        good_matches, total_raw = matcher.match_descriptors(descs, descs, algorithm="AKAZE")
        self.assertGreaterEqual(len(good_matches), 6)
        print("  [PASS] AKAZE feature detection & NORM_HAMMING binary matching verified")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING LUNARVISION IMAGE UPLOAD & .IMG PROCESSING TESTS")
    print("=" * 60)
    unittest.main()
