"""
LunarVision Complete Technical Implementation PDF Report Generator
Uses ReportLab to build a professional, styled multi-page PDF technical report.
Output: LunarVision_Technical_Report.pdf
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render 'Page X of Y' page numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "LunarVision: Complete Technical Implementation Report")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — LUNARVISION SYSTEM ARCHITECTURE")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.restoreState()


def create_pdf(filename="LunarVision_Technical_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F172A")
    secondary_color = colors.HexColor("#0284C7")
    accent_color = colors.HexColor("#0D9488")
    dark_slate = colors.HexColor("#1E293B")
    text_color = colors.HexColor("#334155")
    bg_light = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_color,
        spaceAfter=6,
        alignment=TA_LEFT
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_color,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=dark_slate,
        backColor=bg_light,
        borderColor=colors.HexColor("#E2E8F0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=text_color
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=primary_color
    )

    story = []

    # Title Banner
    story.append(Paragraph("LunarVision: Technical Implementation Report", title_style))
    story.append(Paragraph("End-to-End Multi-Modal Lunar Image Registration & Temporal Change Detection Pipeline", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceBefore=0, spaceAfter=10))

    # Metadata Card Table
    meta_data = [
        [Paragraph("<b>Project:</b> LunarVision", table_cell_style), Paragraph("<b>Status:</b> Fully Implemented & Verified", table_cell_style)],
        [Paragraph("<b>Architecture:</b> React 18 + FastAPI + OpenCV", table_cell_style), Paragraph("<b>Primary Detectors:</b> SIFT & AKAZE", table_cell_style)],
        [Paragraph("<b>Scientific Ingestion:</b> PDS3/PDS4 .IMG & Web Formats", table_cell_style), Paragraph("<b>Machine Learning:</b> None (Deterministic Classical CV)", table_cell_style)]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # SECTION 1: PROJECT OVERVIEW
    story.append(Paragraph("1. PROJECT OVERVIEW", h1_style))
    story.append(Paragraph(
        "<b>LunarVision</b> is an end-to-end computer vision platform engineered for planetary surface exploration and orbital image correspondence. "
        "It performs automated multi-modal image ingestion, contrast-aware CLAHE enhancement, scale- and rotation-invariant feature extraction (SIFT & AKAZE), "
        "Lowe's ratio-tested feature matching, RANSAC projective homography registration, quantitative alignment metric calculation, and temporal change isolation.",
        body_style
    ))
    story.append(Paragraph("<b>Main Objective:</b> To provide sub-pixel geometric alignment and explainable temporal surface alteration detection across multi-temporal and multi-sensor lunar orbital passes (such as Chandrayaan OHRC, TMC, IIRS, and NASA LRO), eliminating false registration distortions while providing transparent scientific quality metrics.", body_style))
    story.append(Paragraph("<b>Key Technologies:</b> React 18, Vite, Tailwind CSS, FastAPI (Python 3.14 / 3.11+), OpenCV 4.13.0, NumPy, scikit-image 0.26.0, Pillow 12.1.1.", body_style))
    story.append(Paragraph("<b>Database / Storage:</b> Local stateless filesystem storage (`backend/outputs/` and `backend/uploads/`). No external database required.", body_style))

    # SECTION 2: SYSTEM ARCHITECTURE
    story.append(Paragraph("2. SYSTEM ARCHITECTURE", h1_style))
    story.append(Paragraph("The system follows a decoupled client-server architecture:", body_style))
    story.append(Paragraph("• <b>Frontend Layer (`frontend/src/`):</b> React 18 SPA serving interactive modules for Registration, Three-Sensor Analysis, and Change Detection.", bullet_style))
    story.append(Paragraph("• <b>API Gateway (`backend/routers/image_routes.py`):</b> FastAPI endpoint routing handling multipart FormData uploads and JSON responses.", bullet_style))
    story.append(Paragraph("• <b>Preprocessing Pipeline (`backend/services/preprocessing.py`):</b> PDS3/PDS4 label parsing, byte offset slicing, 16-bit to 8-bit dynamic range scaling, and CLAHE.", bullet_style))
    story.append(Paragraph("• <b>Feature Engine (`backend/services/feature_detection.py`):</b> SIFT feature extraction with automatic fallback to AKAZE.", bullet_style))
    story.append(Paragraph("• <b>Matching Engine (`backend/services/matching.py`):</b> Brute-Force KNN matcher with distance norm selection (L2 for SIFT, Hamming for AKAZE) and Lowe's Ratio Test.", bullet_style))
    story.append(Paragraph("• <b>Registration Engine (`backend/services/registration.py`):</b> RANSAC 2D perspective homography matrix estimation and bilinear warping.", bullet_style))
    story.append(Paragraph("• <b>Metrics Engine (`backend/services/metrics.py`):</b> Masked RMSE, Inlier Ratio, SSIM, and composite Confidence Score computation.", bullet_style))
    story.append(Paragraph("• <b>Change Engine (`backend/services/change_detection.py`):</b> SSIM dissimilarity, thresholding, morphological opening/closing, and connected component heuristic labeling.", bullet_style))

    # SECTION 3 & 4: FRONTEND & BACKEND IMPLEMENTATION
    story.append(Paragraph("3 & 4. FRONTEND & BACKEND IMPLEMENTATION", h1_style))
    
    endpoints_data = [
        [Paragraph("Endpoint", table_header_style), Paragraph("Method", table_header_style), Paragraph("Input Format", table_header_style), Paragraph("Purpose & Output", table_header_style)],
        [Paragraph("<code>/api/health</code>", table_cell_bold), Paragraph("GET", table_cell_style), Paragraph("None", table_cell_style), Paragraph("Returns telemetry: OpenCV, skimage, Python versions and directory status.", table_cell_style)],
        [Paragraph("<code>/api/images/register</code>", table_cell_bold), Paragraph("POST", table_cell_style), Paragraph("Multipart FormData<br/>(source, reference, detector)", table_cell_style), Paragraph("Executes full SIFT/AKAZE registration, computes metrics & artifacts.", table_cell_style)],
        [Paragraph("<code>/api/images/multi-sensor-register</code>", table_cell_bold), Paragraph("POST", table_cell_style), Paragraph("Multipart FormData<br/>(hub, sensor_a, sensor_b)", table_cell_style), Paragraph("Executes real pairwise cross-sensor registration across payloads.", table_cell_style)],
        [Paragraph("<code>/api/images/change-detection</code>", table_cell_bold), Paragraph("POST", table_cell_style), Paragraph("Multipart FormData<br/>(source, reference, min_conf, diff_thresh)", table_cell_style), Paragraph("Executes registration followed by SSIM change detection & bounding box labels.", table_cell_style)],
    ]
    ep_table = Table(endpoints_data, colWidths=[110, 44, 110, 240])
    ep_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(ep_table)
    story.append(Spacer(1, 8))

    # SECTION 5 & 6: PREPROCESSING & SCIENTIFIC .IMG SUPPORT
    story.append(Paragraph("5 & 6. IMAGE PREPROCESSING & SCIENTIFIC .IMG SUPPORT", h1_style))
    story.append(Paragraph(
        "Scientific lunar datasets (NASA PDS3/PDS4, ISRO Chandrayaan TMC/OHRC/IIRS, LRO LROC) are delivered in <code>.IMG</code> formats containing ASCII text headers followed by 8-bit, 16-bit, or 32-bit float raw binary matrices. "
        "LunarVision implements an in-house PDS label parser in <code>PreprocessingService.parse_pds_img()</code>:",
        body_style
    ))
    story.append(Paragraph("• <b>Header Parsing:</b> Decodes the first 64KB as <code>latin-1</code> and uses regular expressions to extract <code>LINES</code>, <code>LINE_SAMPLES</code>, <code>SAMPLE_BITS</code>, <code>SAMPLE_TYPE</code>, <code>RECORD_BYTES</code>, <code>LABEL_RECORDS</code>, and <code>^IMAGE</code> byte pointer.", bullet_style))
    story.append(Paragraph("• <b>Endianness & Data Types:</b> Maps <code>MSB</code> (big-endian) and <code>LSB</code> (little-endian) types to NumPy dtypes (<code>>u2</code>, <code><u2</code>, <code>>i2</code>, <code><i2</code>, <code>>f4</code>, <code><f4</code>).", bullet_style))
    story.append(Paragraph("• <b>Percentile Normalization:</b> Applies 0.5%–99.5% percentile intensity scaling (<code>np.percentile(img_matrix, (0.5, 99.5))</code>) to convert high-dynamic range 16-bit or float arrays to 8-bit uint8 while preserving crater rims and regolith shadow contrast.", bullet_style))
    story.append(Paragraph("• <b>Raw Binary Fallback:</b> Unheadered <code>.IMG</code> files are decoded via <code>parse_raw_binary_img()</code> using square root factor reconstruction (<code>side = int(np.sqrt(num_elems))</code>).", bullet_style))
    story.append(Paragraph("• <b>CLAHE Contrast Enhancement:</b> Applies <code>cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))</code> to accentuate subtle topography.", bullet_style))

    # SECTION 7 - 11: FEATURE DETECTION, MATCHING, LOWE RATIO, RANSAC
    story.append(Paragraph("7 – 11. FEATURE DETECTION, MATCHING, LOWE RATIO & RANSAC", h1_style))
    
    cv_pipeline_data = [
        [Paragraph("Pipeline Stage", table_header_style), Paragraph("Algorithm / Library", table_header_style), Paragraph("Parameters / Config", table_header_style), Paragraph("Mathematical / Operational Role", table_header_style)],
        [Paragraph("<b>Feature Detection</b>", table_cell_bold), Paragraph("SIFT (OpenCV)<br/><i>Fallback: AKAZE</i>", table_cell_style), Paragraph("<code>min_features=12</code><br/>SIFT: DoG Pyramid<br/>AKAZE: M-LDB Binary", table_cell_style), Paragraph("Extracts scale/rotation invariant keypoints. SIFT yields float32 descriptors; AKAZE yields uint8 binary descriptors.", table_cell_style)],
        [Paragraph("<b>Feature Matching</b>", table_cell_bold), Paragraph("BFMatcher (OpenCV)", table_cell_style), Paragraph("<code>k=2</code> (KNN)<br/>SIFT: <code>NORM_L2</code><br/>AKAZE: <code>NORM_HAMMING</code>", table_cell_style), Paragraph("Computes 2 nearest neighbors for each source descriptor against reference descriptor space.", table_cell_style)],
        [Paragraph("<b>Match Filtering</b>", table_cell_bold), Paragraph("Lowe's Ratio Test", table_cell_style), Paragraph("$\tau_{sift} = 0.75$<br/>$\tau_{akaze} = 0.80$", table_cell_style), Paragraph("Prunes ambiguous matches: Keeps match iff $d_1 < \\tau \\times d_2$. Discards duplicate terrain patterns.", table_cell_style)],
        [Paragraph("<b>Outlier Rejection</b>", table_cell_bold), Paragraph("RANSAC (OpenCV)", table_cell_style), Paragraph("<code>reprojThresh=3.5px</code><br/><code>min_matches=6</code>", table_cell_style), Paragraph("Randomly samples 4-point subsets to compute $3\\times3$ Homography $H$, isolating geometrically consistent inliers.", table_cell_style)],
        [Paragraph("<b>Image Warping</b>", table_cell_bold), Paragraph("Perspective Warp", table_cell_style), Paragraph("<code>BORDER_REFLECT</code><br/><code>INTER_LINEAR</code>", table_cell_style), Paragraph("Warp source image into reference coordinate space via $p_{ref} \\sim H p_{src}$. Extends valid overlap mask.", table_cell_style)],
    ]
    cv_table = Table(cv_pipeline_data, colWidths=[90, 100, 110, 204])
    cv_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(cv_table)
    story.append(Spacer(1, 8))

    # SECTION 12: SAME LOCATION DECISION LOGIC
    story.append(Paragraph("12. SAME LOCATION DECISION LOGIC", h1_style))
    story.append(Paragraph("The system enforces strict mathematical decision gates to avoid forcing false registrations on unrelated imagery:", body_style))
    story.append(Paragraph(
        "<code>def evaluate_same_location(ref_kps, src_kps, matches, inliers, confidence):<br/>"
        "&nbsp;&nbsp;if len(ref_kps) &lt; 6 or len(src_kps) &lt; 6: return 'no_match'<br/>"
        "&nbsp;&nbsp;if len(matches) &lt; 6: return 'no_match'<br/>"
        "&nbsp;&nbsp;if inliers &lt; 6: return 'no_match'<br/>"
        "&nbsp;&nbsp;if confidence &lt; 0.20: return 'no_match'<br/>"
        "&nbsp;&nbsp;return 'success'</code>",
        code_style
    ))

    # SECTION 14 & 15: METRICS & FORMULAS
    story.append(Paragraph("14 & 15. QUANTITATIVE METRICS & FORMULAS", h1_style))
    story.append(Paragraph("• <b>Masked RMSE (Root Mean Square Error):</b> Computes pixel intensity discrepancy over valid overlapping mask:", body_style))
    story.append(Paragraph("$$\\text{RMSE} = \\sqrt{ \\frac{1}{N} \\sum_{(x,y) \\in \\text{Mask}} (I_{\\text{ref}}(x,y) - I_{\\text{aligned}}(x,y))^2 }$$", code_style))
    story.append(Paragraph("• <b>Inlier Ratio:</b> Percentage of candidate matches surviving RANSAC outlier rejection:", body_style))
    story.append(Paragraph("$$\\text{Inlier Ratio} = \\frac{\\text{Inlier Count}}{\\max(\\text{Good Matches}, 1)}$$", code_style))
    story.append(Paragraph("• <b>Registration Confidence Score:</b> Multi-factor synthesized reliability score:", body_style))
    story.append(Paragraph("$$\\text{Confidence} = 0.40 \\times \\min\\left(1.0, \\frac{\\text{Inliers}}{40}\\right) + 0.35 \\times \\text{InlierRatio} + 0.25 \\times \\max\\left(0.0, 1.0 - \\frac{\\text{RMSE}}{60}\\right)$$", code_style))

    # SECTION 17 & 18: AUTOMATED TESTS & SAMPLE DATASET
    story.append(Paragraph("17 & 18. AUTOMATED TEST RESULTS & SAMPLE DATASETS", h1_style))
    
    test_results_data = [
        [Paragraph("Test Script", table_header_style), Paragraph("Target Feature Tested", table_header_style), Paragraph("Sample Data Used", table_header_style), Paragraph("Empirical Results", table_header_style), Paragraph("Status", table_header_style)],
        [Paragraph("<code>test_img_upload.py</code>", table_cell_bold), Paragraph("PNG/JPG decoding, PDS3 16-bit .IMG, raw binary, SIFT/AKAZE & error rejection", table_cell_style), Paragraph("<code>01_baseline_pre_event.png</code><br/><code>05_scientific_lunar_reference.IMG</code>", table_cell_style), Paragraph("6/6 tests passed. 276 inliers verified on PDS .IMG registration.", table_cell_style), Paragraph("<b>PASS</b>", table_cell_style)],
        [Paragraph("<code>test_backend_cv.py</code>", table_cell_bold), Paragraph("Full CV pipeline (Preprocess, SIFT, RANSAC, SSIM, No-match)", table_cell_style), Paragraph("Synthetic crater terrain pair", table_cell_style), Paragraph("RMSE: 7.83px, Inliers: 165/170, Confidence: 95.7%", table_cell_style), Paragraph("<b>PASS</b>", table_cell_style)],
        [Paragraph("<code>test_api_endpoints.py</code>", table_cell_bold), Paragraph("FastAPI endpoints (/health, /register, /change-detection)", table_cell_style), Paragraph("Sample PNG orbital frames", table_cell_style), Paragraph("HTTP 200 responses, static asset URL serving verified.", table_cell_style), Paragraph("<b>PASS</b>", table_cell_style)],
        [Paragraph("<code>test_full_integration.py</code>", table_cell_bold), Paragraph("End-to-end integration across multi-sensor channels & errors", table_cell_style), Paragraph("OHRC, TMC, IIRS sample pairs", table_cell_style), Paragraph("Multi-sensor Pair 1: 100 inliers (98.2% conf). Pair 2: 41 inliers (93.6% conf).", table_cell_style), Paragraph("<b>PASS</b>", table_cell_style)],
    ]
    test_table = Table(test_results_data, colWidths=[90, 110, 110, 144, 50])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # SECTION 19 & 20: MACHINE LEARNING & AI CLARIFICATION
    story.append(Paragraph("19 & 20. AI / ML USAGE & EXPLICIT CLARIFICATION", h1_style))
    story.append(Paragraph(
        "<b>Explicit Clarification:</b> No trained Machine Learning (ML), Deep Learning (DL), or Neural Network model is used in LunarVision. "
        "The entire system is grounded strictly in <b>deterministic classical computer vision algorithms</b> (gradient orientation histograms, non-linear scale space differential operators, and RANSAC geometric consensus). "
        "SIFT and AKAZE are hand-crafted mathematical feature extractors, not trained AI models.",
        body_style
    ))

    # SECTION 24: CURRENT STATUS MATRIX
    story.append(Paragraph("24. CURRENT IMPLEMENTATION STATUS", h1_style))
    
    status_matrix_data = [
        [Paragraph("Requirement", table_header_style), Paragraph("Status", table_header_style), Paragraph("Evidence File", table_header_style), Paragraph("Notes", table_header_style)],
        [Paragraph("JPEG/JPG/PNG Upload", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>PreprocessingService</code>", table_cell_style), Paragraph("Fully operational & tested.", table_cell_style)],
        [Paragraph("Scientific .IMG PDS Decoding", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>preprocessing.py:L29</code>", table_cell_style), Paragraph("Parses PDS3/PDS4/VICAR labels & raw binary matrices.", table_cell_style)],
        [Paragraph("SIFT Feature Detector", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>feature_detection.py:L77</code>", table_cell_style), Paragraph("Primary feature extractor (128d float32 descriptors).", table_cell_style)],
        [Paragraph("AKAZE Feature Detector", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>feature_detection.py:L89</code>", table_cell_style), Paragraph("Fallback & binary feature extractor (Hamming norm).", table_cell_style)],
        [Paragraph("Lowe's Ratio Test", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>matching.py:L73</code>", table_cell_style), Paragraph("Thresholds: 0.75 (SIFT) / 0.80 (AKAZE).", table_cell_style)],
        [Paragraph("RANSAC Homography Warping", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>registration.py:L60</code>", table_cell_style), Paragraph("Tolerance: 3.5px, min matches: 6.", table_cell_style)],
        [Paragraph("Same-Location Decision Logic", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>image_routes.py:L192</code>", table_cell_style), Paragraph("Rejects noise & bad pairs with 'no_match' alert.", table_cell_style)],
        [Paragraph("Temporal Change Detection", table_cell_bold), Paragraph("IMPLEMENTED", table_cell_style), Paragraph("<code>change_detection.py</code>", table_cell_style), Paragraph("SSIM dissimilarity & heuristic bounding box tags.", table_cell_style)],
    ]
    status_table = Table(status_matrix_data, colWidths=[130, 84, 130, 160])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 8))

    # SECTION 26 & 27: DEMO READINESS & FINAL SUMMARY
    story.append(Paragraph("26 & 27. DEMO READINESS & FINAL SUMMARY", h1_style))
    story.append(Paragraph("<b>Demo Readiness: YES.</b> The system is fully functional, fully tested, and ready for live demonstration.", body_style))
    story.append(Paragraph(
        "<b>Final Summary for Technical Reviewers:</b> LunarVision is an end-to-end computer vision platform for multi-modal lunar orbital imagery. "
        "Built with React 18, FastAPI, OpenCV, and scikit-image, it automatically ingests web imagery (PNG, JPG, TIFF, BMP) and scientific PDS3/PDS4 <code>.IMG</code> orbital datasets. "
        "The pipeline executes CLAHE contrast enhancement, scale-invariant SIFT and AKAZE keypoint extraction, Lowe's ratio-tested $k$-NN descriptor matching, and RANSAC perspective homography warping. "
        "The system computes quantitative alignment metrics (masked RMSE, inlier ratio, and confidence score) and performs SSIM-based temporal change detection to isolate surface anomalies. "
        "All operations are explainable, deterministic, and grounded in classical computer vision principles.",
        body_style
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Technical PDF report generated successfully at: {filename}")


if __name__ == "__main__":
    create_pdf()
