import React from 'react';
import {
  UploadCloud,
  SlidersHorizontal,
  Sparkles,
  GitCompare,
  Layers,
  Activity,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  BookOpen
} from 'lucide-react';

export default function HowItWorksPage() {
  const pipelineSteps = [
    {
      step: 1,
      title: 'Planetary Image Ingestion & Memory Safety',
      badge: 'Step 01: Ingestion',
      icon: UploadCloud,
      color: 'from-blue-500/20 to-cyan-500/20',
      border: 'border-blue-500/30',
      iconColor: 'text-blue-400',
      summary: 'Safe memory loading and dynamic range normalization for orbital rasters.',
      details: [
        'Decodes 8-bit, 16-bit, and multi-channel TIFF/PNG/JPG frames without loss.',
        'Normalizes dynamic range to standard 8-bit uint8 intensity space.',
        'Applies memory-safe bounding (downscaling if >4096px) to prevent Out-Of-Memory exceptions on gigapixel planetary scans.',
      ],
      math: 'I_{norm}(x, y) = \\frac{I(x, y) - I_{min}}{I_{max} - I_{min}} \\times 255'
    },
    {
      step: 2,
      title: 'Illumination Normalization (CLAHE)',
      badge: 'Step 02: Enhancement',
      icon: SlidersHorizontal,
      color: 'from-cyan-500/20 to-teal-500/20',
      border: 'border-cyan-500/30',
      iconColor: 'text-cyan-400',
      summary: 'Equalizes steep solar elevation shadows across lunar crater topography.',
      details: [
        'Partitions the image into contextual tiles (8×8 grid).',
        'Computes local histograms and clips contrast at limit (2.0) to prevent amplifying regolith noise.',
        'Bilinearly interpolates tile boundaries to remove artificial grid artifacts.',
      ],
      math: '\\text{CLAHE}(I) = \\text{BilinearInterp}(\\text{ClippedHist}(I_{tile}))'
    },
    {
      step: 3,
      title: 'Scale-Invariant Feature Detection (SIFT / AKAZE)',
      badge: 'Step 03: Keypoints',
      icon: Sparkles,
      color: 'from-indigo-500/20 to-purple-500/20',
      border: 'border-indigo-500/30',
      iconColor: 'text-indigo-400',
      summary: 'Detects scale- and rotation-invariant keypoints along crater rims and peaks.',
      details: [
        'Primary Detector: SIFT constructs Difference-of-Gaussians (DoG) pyramid to find stable extrema.',
        'Computes 128-dimensional orientation-assigned gradient descriptor vectors.',
        'Automatic Fallback: If SIFT keypoints < 12, activates accelerated Accelerated-KAZE (AKAZE) binary detector.',
      ],
      math: 'D(x, y, \\sigma) = (G(x, y, k\\sigma) - G(x, y, \\sigma)) * I(x, y)'
    },
    {
      step: 4,
      title: 'Descriptor Matching & Lowe’s Ratio Test',
      badge: 'Step 04: Correspondence',
      icon: GitCompare,
      color: 'from-sky-500/20 to-blue-500/20',
      border: 'border-sky-500/30',
      iconColor: 'text-sky-400',
      summary: 'Prunes ambiguous correspondences using nearest-neighbor distance ratios.',
      details: [
        'Executes Brute-Force Matcher (BFMatcher) with L2 norm for SIFT or Hamming norm for AKAZE.',
        'Finds the 2 nearest neighbors (k=2) for each source descriptor in reference space.',
        'Applies Lowe’s Ratio Test: Keeps match only if d_1 < 0.75 × d_2, discarding ambiguous duplicate terrain patterns.',
      ],
      math: '\\text{Accept if } \\|D_{src} - D_{ref,1}\\| < 0.75 \\times \\|D_{src} - D_{ref,2}\\|'
    },
    {
      step: 5,
      title: 'RANSAC Geometric Outlier Rejection',
      badge: 'Step 05: Filtering',
      icon: Layers,
      color: 'from-violet-500/20 to-purple-500/20',
      border: 'border-violet-500/30',
      iconColor: 'text-violet-400',
      summary: 'Isolates true geometric inliers and eliminates false matches.',
      details: [
        'Randomly samples 4-point subsets to compute candidate perspective transformations.',
        'Measures reprojection error across all matches with 3.5px tolerance threshold.',
        'Discards all geometric outliers; validates that inlier count ≥ 4 and homography determinant is non-degenerate.',
      ],
      math: '\\text{Inlier if } \\|p_{ref} - H p_{src}\\| < \\tau_{\\text{reproj}}'
    },
    {
      step: 6,
      title: 'Perspective Homography Warping',
      badge: 'Step 06: Registration',
      icon: Layers,
      color: 'from-purple-500/20 to-pink-500/20',
      border: 'border-purple-500/30',
      iconColor: 'text-purple-400',
      summary: 'Transforms source frame into baseline reference coordinate space.',
      details: [
        'Computes 3×3 projective Homography matrix H relating source 2D coordinates to reference.',
        'Executes bilinear perspective warping cv2.warpPerspective.',
        'Generates binary validity mask of overlapping pixels to prevent boundary edge errors.',
      ],
      math: '\\begin{bmatrix} x\' \\\\ y\' \\\\ 1 \\end{bmatrix} \\sim \\begin{bmatrix} h_{11} & h_{12} & h_{13} \\\\ h_{21} & h_{22} & h_{23} \\\\ h_{31} & h_{32} & h_{33} \\end{bmatrix} \\begin{bmatrix} x \\\\ y \\\\ 1 \\end{bmatrix}'
    },
    {
      step: 7,
      title: 'Quantitative Alignment & Accuracy Evaluation',
      badge: 'Step 07: Metrics',
      icon: Activity,
      color: 'from-amber-500/20 to-orange-500/20',
      border: 'border-amber-500/30',
      iconColor: 'text-amber-400',
      summary: 'Computes objective quality scores to prevent false registrations.',
      details: [
        'Masked RMSE: Computes Root Mean Square Error strictly over valid overlapping pixels.',
        'Inlier Ratio: Ratio of confirmed RANSAC correspondences to candidate matches.',
        'Registration Confidence Score: Weighted multi-factor metric (Match count, Inlier ratio, RMSE).',
      ],
      math: '\\text{RMSE} = \\sqrt{ \\frac{1}{N} \\sum_{(x,y) \\in \\text{Mask}} (I_{ref}(x,y) - I_{aln}(x,y))^2 }'
    },
    {
      step: 8,
      title: 'SSIM & Temporal Anomaly Segmentation',
      badge: 'Step 08: Change Detection',
      icon: Cpu,
      color: 'from-emerald-500/20 to-green-500/20',
      border: 'border-emerald-500/30',
      iconColor: 'text-emerald-400',
      summary: 'Isolates structural deltas and categorizes candidate surface alterations.',
      details: [
        'Computes Structural Similarity Index (SSIM) dissimilarity and absolute pixel differencing.',
        'Applies morphological opening (salt noise removal) and closing (crater rim bridging).',
        'Extracts connected component contours; assigns explainable heuristic labels based on circularity, aspect ratio, and mean delta.',
      ],
      math: '\\text{SSIM}(x, y) = \\frac{(2\\mu_x\\mu_y + c_1)(2\\sigma_{xy} + c_2)}{(\\mu_x^2 + \\mu_y^2 + c_1)(\\sigma_x^2 + \\sigma_y^2 + c_2)}'
    }
  ];

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Header Info */}
      <div className="glass-panel p-6 sm:p-10 rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-lunar-900/90 via-lunar-950 to-lunar-900/80">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 text-xs font-semibold mb-3">
          <BookOpen className="w-3.5 h-3.5" />
          Technical Transparency & Pipeline Explainability
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          How LunarVision Works: Computer Vision Pipeline
        </h2>
        <p className="mt-2 text-sm sm:text-base text-slate-300 max-w-3xl leading-relaxed">
          LunarVision is built on mathematical and geometric principles of computer vision. Every algorithmic step is explainable, transparent, and auditable—avoiding unverified "black box" claims.
        </p>
      </div>

      {/* 8 Step Cards */}
      <div className="space-y-6">
        {pipelineSteps.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.step}
              className={`glass-panel p-6 rounded-2xl border ${item.border} bg-lunar-900/40 transition-all hover:border-cyan-500/50`}
            >
              <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2.5 rounded-xl bg-gradient-to-br ${item.color} ${item.iconColor}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                        {item.badge}
                      </span>
                      <h3 className="text-base sm:text-lg font-bold text-white">
                        {item.title}
                      </h3>
                    </div>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-300 font-medium mb-3">
                    {item.summary}
                  </p>

                  <ul className="space-y-1.5 text-xs text-slate-400 list-disc list-inside">
                    {item.details.map((detail, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Mathematical Formulation Card */}
                <div className="lg:w-80 flex-shrink-0 p-4 rounded-xl bg-black/60 border border-lunar-800 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block mb-2">
                      Mathematical Formulation
                    </span>
                    <div className="p-2.5 rounded bg-lunar-950/80 border border-lunar-800/80 font-mono text-[11px] text-cyan-300 overflow-x-auto leading-tight">
                      <code>{item.math}</code>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Implemented in OpenCV / NumPy</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
