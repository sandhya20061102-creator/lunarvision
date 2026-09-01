"""
Lunar Image Preprocessing Service
Handles image ingestion, arbitrary resolution handling with memory safety,
16-bit/8-bit grayscale normalization, and Contrast Limited Adaptive Histogram Equalization (CLAHE).
"""

from typing import Tuple, Dict, Optional, Union
import cv2
import numpy as np


class PreprocessingService:
    """
    Service responsible for loading, standardizing, and enhancing real lunar imagery.
    Supports optical, terrain mapping, and infrared grayscale/color imagery.
    """

    def __init__(
        self,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
        max_dimension: int = 4096
    ):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.max_dimension = max_dimension
        self._clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def parse_pds_img(self, file_bytes: bytes) -> Optional[np.ndarray]:
        """
        Parses scientific planetary PDS3/PDS4/VICAR .IMG format files.
        Extracts ASCII label header parameters (LINES, LINE_SAMPLES, SAMPLE_BITS, SAMPLE_TYPE, ^IMAGE)
        and decodes raw binary pixel data into a normalized BGR NumPy array.
        """
        try:
            # Decode up to first 64KB as ASCII/latin-1 to parse label text
            header_chunk = file_bytes[:65536].decode("latin-1", errors="ignore")
            
            import re
            lines_match = re.search(r'\bLINES\s*=\s*(\d+)', header_chunk, re.IGNORECASE)
            samples_match = re.search(r'\b(?:LINE_SAMPLES|SAMPLES)\s*=\s*(\d+)', header_chunk, re.IGNORECASE)
            
            if not lines_match or not samples_match:
                return None
                
            lines = int(lines_match.group(1))
            samples = int(samples_match.group(1))
            
            if lines <= 0 or samples <= 0 or lines * samples > 100000000:
                return None

            # Determine sample bits & data type
            bits_match = re.search(r'\bSAMPLE_BITS\s*=\s*(\d+)', header_chunk, re.IGNORECASE)
            sample_bits = int(bits_match.group(1)) if bits_match else 8

            type_match = re.search(r'\bSAMPLE_TYPE\s*=\s*([A-Za-z0-9_"]+)', header_chunk, re.IGNORECASE)
            sample_type = type_match.group(1).replace('"', '').upper() if type_match else ""

            # Determine numpy dtype based on endianness and bits
            is_big_endian = any(k in sample_type for k in ["MSB", "SUN", "MAC"])
            is_float = any(k in sample_type for k in ["REAL", "FLOAT"])
            is_signed = "SIGNED" in sample_type and "UNSIGNED" not in sample_type

            if sample_bits == 8:
                dtype = np.uint8
            elif sample_bits == 16:
                if is_big_endian:
                    dtype = np.dtype(">i2") if is_signed else np.dtype(">u2")
                else:
                    dtype = np.dtype("<i2") if is_signed else np.dtype("<u2")
            elif sample_bits == 32:
                if is_float:
                    dtype = np.dtype(">f4") if is_big_endian else np.dtype("<f4")
                else:
                    if is_big_endian:
                        dtype = np.dtype(">i4") if is_signed else np.dtype(">u4")
                    else:
                        dtype = np.dtype("<i4") if is_signed else np.dtype("<u4")
            elif sample_bits == 64 and is_float:
                dtype = np.dtype(">f8") if is_big_endian else np.dtype("<f8")
            else:
                dtype = np.uint8

            bytes_per_sample = dtype.itemsize

            # Determine binary data offset
            rec_bytes_match = re.search(r'\bRECORD_BYTES\s*=\s*(\d+)', header_chunk, re.IGNORECASE)
            record_bytes = int(rec_bytes_match.group(1)) if rec_bytes_match else 0

            image_ptr_match = re.search(r'\^IMAGE\s*=\s*(\d+)', header_chunk, re.IGNORECASE)
            lbl_recs_match = re.search(r'\bLABEL_RECORDS\s*=\s*(\d+)', header_chunk, re.IGNORECASE)

            offset = 0
            if image_ptr_match and record_bytes > 0:
                rec_num = int(image_ptr_match.group(1))
                offset = max(0, (rec_num - 1) * record_bytes)
            elif lbl_recs_match and record_bytes > 0:
                rec_num = int(lbl_recs_match.group(1))
                offset = rec_num * record_bytes
            else:
                # Search for END label marker
                end_match = re.search(r'\bEND\b', header_chunk)
                if end_match:
                    end_pos = end_match.end()
                    if record_bytes > 0:
                        offset = ((end_pos // record_bytes) + 1) * record_bytes
                    else:
                        offset = end_pos
                        # Align to line boundary if possible
                        expected_data_len = lines * samples * bytes_per_sample
                        if len(file_bytes) - expected_data_len > 0:
                            offset = len(file_bytes) - expected_data_len

            expected_bytes = lines * samples * bytes_per_sample
            if len(file_bytes) < offset + expected_bytes:
                # If offset extends past buffer, try reading from back of buffer
                offset = max(0, len(file_bytes) - expected_bytes)

            raw_arr = np.frombuffer(file_bytes[offset:offset + expected_bytes], dtype=dtype)
            if len(raw_arr) < lines * samples:
                return None

            img_matrix = raw_arr[:lines * samples].reshape((lines, samples)).astype(np.float32)

            # Robust percentile normalization to preserve high dynamic range crater details
            p_min, p_max = np.percentile(img_matrix, (0.5, 99.5))
            if p_max - p_min > 1e-5:
                norm_img = np.clip((img_matrix - p_min) / (p_max - p_min) * 255.0, 0, 255).astype(np.uint8)
            else:
                norm_img = cv2.normalize(img_matrix, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

            bgr = cv2.cvtColor(norm_img, cv2.COLOR_GRAY2BGR)
            return bgr
        except Exception:
            return None

    def parse_raw_binary_img(self, file_bytes: bytes) -> Optional[np.ndarray]:
        """
        Fallback parser for unheadered raw binary raster matrices (.IMG).
        Attempts square or standard aspect ratio pixel reconstruction.
        """
        try:
            total_bytes = len(file_bytes)
            if total_bytes == 0:
                return None

            for dtype in [np.uint8, np.uint16, np.float32]:
                elem_size = dtype().itemsize
                num_elems = total_bytes // elem_size
                if num_elems < 64:
                    continue

                side = int(np.sqrt(num_elems))
                if side * side == num_elems:
                    arr = np.frombuffer(file_bytes[:side*side*elem_size], dtype=dtype).astype(np.float32)
                    arr = arr.reshape((side, side))
                    norm = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    return cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
            return None
        except Exception:
            return None

    def load_image_from_bytes(self, file_bytes: bytes, filename: Optional[str] = None) -> np.ndarray:
        """
        Safely decodes image bytes into a BGR NumPy array.
        Automatically detects file type and supports:
        1. Standard web & scientific images (JPEG, JPG, PNG, TIFF, BMP) via OpenCV & PIL.
        2. Planetary PDS3/PDS4/VICAR .IMG format files.
        3. Raw binary raster .IMG files.
        """
        if not file_bytes:
            raise ValueError("Empty image byte buffer provided.")

        image = None
        is_img_extension = filename and filename.lower().endswith(".img")

        # If extension is .IMG or file starts with PDS text, try PDS parser first
        if is_img_extension or file_bytes[:100].startswith(b"PDS_VERSION_ID") or b"RECORD_BYTES" in file_bytes[:512]:
            image = self.parse_pds_img(file_bytes)

        # Try standard OpenCV decoding
        if image is None:
            np_arr = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
            if image is None:
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Fallback to PIL / ImageIO
        if image is None:
            try:
                from PIL import Image
                import io
                pil_img = Image.open(io.BytesIO(file_bytes))
                image = np.array(pil_img)
                if len(image.shape) == 2:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                elif len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                elif len(image.shape) == 3 and image.shape[2] == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            except Exception:
                image = None

        # Fallback to PDS parser or Raw binary parser
        if image is None:
            image = self.parse_pds_img(file_bytes)
        if image is None and is_img_extension:
            image = self.parse_raw_binary_img(file_bytes)

        if image is None:
            raise ValueError(
                "Failed to decode image file. Ensure file is a valid web image (PNG, JPG, TIFF, BMP) "
                "or a valid scientific lunar .IMG (PDS3/PDS4/VICAR) format dataset."
            )

        # Convert 16-bit or float images to 8-bit uint8
        if image.dtype == np.uint16:
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        elif image.dtype == np.float32 or image.dtype == np.float64:
            image = np.clip(image * 255.0 if image.max() <= 1.0 else image, 0, 255).astype(np.uint8)

        # Ensure 3-channel BGR representation for uniform downstream pipeline
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # Memory Safety: Downscale if image exceeds max dimension while preserving aspect ratio
        h, w = image.shape[:2]
        if max(h, w) > self.max_dimension:
            scale = self.max_dimension / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return image

    def load_image_from_path(self, file_path: str) -> np.ndarray:
        """
        Loads an image from local disk with memory safety.
        """
        with open(file_path, "rb") as f:
            return self.load_image_from_bytes(f.read(), filename=file_path)

    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Converts 3-channel BGR/RGB images to single-channel uint8 grayscale.
        """
        if image is None or image.size == 0:
            raise ValueError("Cannot convert an empty image to grayscale.")

        if len(image.shape) == 2:
            return image.copy()
        elif len(image.shape) == 3:
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            elif image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 1:
                return image[:, :, 0].copy()

        raise ValueError(f"Unsupported image shape for grayscale conversion: {image.shape}")

    def normalize_intensity(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Min-max normalizes grayscale image to full [0, 255] dynamic range (uint8).
        """
        if gray_image is None or gray_image.size == 0:
            raise ValueError("Empty image provided for normalization.")

        min_val, max_val = float(np.min(gray_image)), float(np.max(gray_image))
        if max_val - min_val < 1e-5:
            return np.zeros_like(gray_image, dtype=np.uint8)

        normalized = cv2.normalize(
            gray_image,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8U
        )
        return normalized

    def apply_clahe(
        self,
        gray_image: np.ndarray,
        clip_limit: Optional[float] = None,
        tile_grid_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """
        Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
        to accentuate subtle crater rims and shadowed topography on the lunar surface.
        """
        if gray_image is None or gray_image.size == 0:
            raise ValueError("Empty image provided for CLAHE enhancement.")

        if gray_image.dtype != np.uint8:
            gray_image = self.normalize_intensity(gray_image)

        if clip_limit is not None or tile_grid_size is not None:
            c_limit = clip_limit if clip_limit is not None else self.clip_limit
            t_size = tile_grid_size if tile_grid_size is not None else self.tile_grid_size
            clahe = cv2.createCLAHE(clipLimit=c_limit, tileGridSize=t_size)
            return clahe.apply(gray_image)

        return self._clahe.apply(gray_image)

    def preprocess_pipeline(self, image_input: Union[bytes, np.ndarray, str]) -> Dict[str, np.ndarray]:
        """
        Executes end-to-end preprocessing pipeline on input:
        1. Decode/load color image with memory safety bounds.
        2. Convert to grayscale.
        3. Normalize intensity range.
        4. Apply CLAHE enhancement.
        """
        if isinstance(image_input, bytes):
            color_img = self.load_image_from_bytes(image_input)
        elif isinstance(image_input, str):
            color_img = self.load_image_from_path(image_input)
        elif isinstance(image_input, np.ndarray):
            color_img = image_input.copy()
            if len(color_img.shape) == 2:
                color_img = cv2.cvtColor(color_img, cv2.COLOR_GRAY2BGR)
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        gray = self.convert_to_grayscale(color_img)
        normalized = self.normalize_intensity(gray)
        enhanced = self.apply_clahe(normalized)

        return {
            "original_color": color_img,
            "gray": gray,
            "normalized": normalized,
            "enhanced": enhanced,
        }
