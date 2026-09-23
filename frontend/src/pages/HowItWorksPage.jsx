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
      color: 'from-indigo-500/20 to-cyan-500/20',
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
      color: 'from-violet-500/20 to-cyan-500/20',
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
      color: 'from-cyan-500/20 to-pink-500/20',
      border: 'border-cyan-500/30',
      iconColor: 'text-cyan-400',
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

      {/* Alternating Zigzag 8-Step Pipeline Cards with Revolving Orbital Accent */}
      <div className="space-y-8 relative">
        {/* Central dashed orbital timeline line on large screens */}
        <div className="hidden lg:block absolute left-1/2 top-4 bottom-4 w-0.5 border-l-2 border-dashed border-cyan-500/20 -translate-x-1/2 pointer-events-none"></div>

        {pipelineSteps.map((item, index) => {
          const Icon = item.icon;
          const isEven = index % 2 === 1;

          return (
            <div
              key={item.step}
              className={`flex flex-col lg:flex-row items-center gap-6 ${
                isEven ? 'lg:flex-row-reverse' : ''
              }`}
            >
              {/* Step Content Card */}
              <div className="w-full lg:w-[calc(50%-2rem)] glass-panel p-6 sm:p-7 rounded-3xl border border-lunar-700/70 hover:border-cyan-500/50 bg-lunar-900/50 transition-all duration-300 hover:shadow-xl hover:shadow-cyan-950/40 relative overflow-hidden group">
                {/* Subtle orbital glow in corner */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/15 transition-all pointer-events-none"></div>

                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2.5 rounded-xl bg-gradient-to-br ${item.color} ${item.iconColor} border border-cyan-500/30 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                      {item.badge}
                    </span>
                    <h3 className="text-base sm:text-lg font-bold text-white group-hover:text-cyan-200 transition-colors">
                      {item.title}
                    </h3>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-slate-300 font-medium mb-3 leading-relaxed">
                  {item.summary}
                </p>

                <ul className="space-y-1.5 text-xs text-slate-400 list-disc list-inside mb-4">
                  {item.details.map((detail, idx) => (
                    <li key={idx} className="leading-relaxed">
                      {detail}
                    </li>
                  ))}
                </ul>

                {/* Mathematical Formulation Sub-box */}
                <div className="p-3 rounded-xl bg-black/60 border border-lunar-800">
                  <div className="flex items-center justify-between text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                    <span>Mathematical Formulation</span>
                    <span className="text-emerald-400 flex items-center gap-1 font-normal">
                      <CheckCircle2 className="w-3 h-3" /> Verified
                    </span>
                  </div>
                  <div className="p-2 rounded-lg bg-lunar-950 border border-lunar-800/80 font-mono text-[11px] text-cyan-300 overflow-x-auto leading-tight">
                    <code>{item.math}</code>
                  </div>
                </div>
              </div>

              {/* Central Orbital Node Badge */}
              <div className="hidden lg:flex w-16 h-16 rounded-full bg-lunar-950 border-2 border-cyan-500/40 items-center justify-center relative flex-shrink-0 shadow-lg shadow-cyan-500/20 group">
                <span className="font-mono text-xs font-bold text-cyan-400">
                  {item.step < 10 ? `0${item.step}` : item.step}
                </span>
                {/* Revolving Planetary Satellite Indicator */}
                <div className="absolute inset-0 rounded-full animate-revolve pointer-events-none">
                  <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 shadow-md shadow-cyan-400/80 block -ml-1 -mt-1"></span>
                </div>
              </div>

              {/* Empty Spacer on large screens for zigzag symmetry */}
              <div className="hidden lg:block w-[calc(50%-2rem)]"></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
