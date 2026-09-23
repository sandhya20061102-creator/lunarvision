import React, { useState } from 'react';
import {
  Sun,
  Activity,
  Layers,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sliders,
  Play,
  RotateCcw,
  Info,
  Compass,
  Gauge,
  BarChart2,
  LineChart
} from 'lucide-react';
import { analyzeSunAngleRobustness, runSunAngleBatchBenchmark } from '../services/api';
import ImageUploader from '../components/ImageUploader';
import MetricCard from '../components/MetricCard';
import LoadingState from '../components/LoadingState';
import { extractGeoMetadata } from '../utils/geoMetadata';
import { extractPdsMetadata } from '../utils/pdsMetadata';
import FootprintMap from '../components/FootprintMap';

export default function SunAnglePage() {
  const [sourceFile, setSourceFile] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null);
  const [sourcePreview, setSourcePreview] = useState(null);
  const [referencePreview, setReferencePreview] = useState(null);
  const [detectorChoice, setDetectorChoice] = useState('SIFT');
  const [manualAngleInput, setManualAngleInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Footprint metadata (null = not yet loaded or unavailable)
  const [sourceFootprint, setSourceFootprint] = useState(null);
  const [referenceFootprint, setReferenceFootprint] = useState(null);

  // PDS bounding-box metadata (populated when a .lbl or .img label is uploaded)
  const [sourcePdsMeta, setSourcePdsMeta] = useState(null);
  const [referencePdsMeta, setReferencePdsMeta] = useState(null);

  const handleSourceSelected = (file) => {
    setSourceFile(file);
    setSourcePreview(URL.createObjectURL(file));
    setSourceFootprint(null);
    setSourcePdsMeta(null);
    // Try EXIF first, then PDS (for .img/.lbl files)
    extractGeoMetadata(file).then(setSourceFootprint).catch(() => setSourceFootprint(null));
    extractPdsMetadata(file).then(setSourcePdsMeta).catch(() => setSourcePdsMeta(null));
  };

  const handleReferenceSelected = (file) => {
    setReferenceFile(file);
    setReferencePreview(URL.createObjectURL(file));
    setReferenceFootprint(null);
    setReferencePdsMeta(null);
    extractGeoMetadata(file).then(setReferenceFootprint).catch(() => setReferenceFootprint(null));
    extractPdsMetadata(file).then(setReferencePdsMeta).catch(() => setReferencePdsMeta(null));
  };

  const handleClear = () => {
    setSourceFile(null);
    setReferenceFile(null);
    setSourcePreview(null);
    setReferencePreview(null);
    setResult(null);
    setManualAngleInput('');
    setSourceFootprint(null);
    setReferenceFootprint(null);
    setSourcePdsMeta(null);
    setReferencePdsMeta(null);
  };

  // --- Batch Benchmark State ---
  const [batchBaseFile, setBatchBaseFile] = useState(null);
  const [batchBasePreview, setBatchBasePreview] = useState(null);
  const [batchNumPairs, setBatchNumPairs] = useState(18);
  const [batchDetector, setBatchDetector] = useState('SIFT');
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState(null);
  const [batchError, setBatchError] = useState(null);
  const [hoveredPairId, setHoveredPairId] = useState(null);

  const handleBatchSelected = (file) => {
    setBatchBaseFile(file);
    setBatchBasePreview(URL.createObjectURL(file));
    setBatchError(null);
  };

  const handleClearBatch = () => {
    setBatchBaseFile(null);
    setBatchBasePreview(null);
    setBatchResults(null);
    setBatchError(null);
    setHoveredPairId(null);
  };

  const handleRunBatch = async () => {
    if (!batchBaseFile) {
      alert('Please select a baseline lunar image for the benchmark.');
      return;
    }

    const count = Math.min(20, Math.max(15, parseInt(batchNumPairs, 10) || 18));
    setIsBatchLoading(true);
    setBatchResults(null);
    setBatchError(null);

    try {
      const resp = await runSunAngleBatchBenchmark(batchBaseFile, count, batchDetector);
      if (resp?.results) {
        setBatchResults(resp.results);
      } else if (Array.isArray(resp)) {
        setBatchResults(resp);
      } else {
        setBatchError(resp?.reason || 'Batch benchmark returned unexpected format.');
      }
    } catch (err) {
      setBatchError(err.message || 'Failed to execute sun-angle batch benchmark.');
    } finally {
      setIsBatchLoading(false);
    }
  };


  const handleRunAnalysis = async () => {
    if (!sourceFile || !referenceFile) {
      alert('Please upload both Source and Reference lunar images for sun-angle robustness testing.');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const angleVal = manualAngleInput !== '' ? parseFloat(manualAngleInput) : null;
      const data = await analyzeSunAngleRobustness(
        sourceFile,
        referenceFile,
        detectorChoice,
        angleVal
      );
      setResult(data);
    } catch (err) {
      setResult({
        status: 'rejected',
        decision: 'Rejected',
        reason: err.message || 'Error occurred during robustness analysis.',
        details: { error_type: 'execution_failed' },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const metrics = result?.metrics ?? result?.details ?? {};

  // Determine acceptance based on backend status
  const isAccepted = result?.status === 'success';
  const isRejected = result && !isAccepted;

  // Extract metric values with fallbacks
  const confidenceValue = (metrics.confidence_percentage ?? (metrics.confidence_score ? metrics.confidence_score * 100 : 0)).toFixed(1);
  const inlierCount = metrics.inliers ?? 0;
  const inlierRatio = ((metrics.inlier_ratio ?? 0) * 100).toFixed(1);
  const rmseValue = typeof metrics.rmse === 'number' ? metrics.rmse.toFixed(2) : '99.99';
  const goodMatches = metrics.good_matches ?? 0;
  const sourceKP = metrics.source_keypoints ?? 0;
  const referenceKP = metrics.reference_keypoints ?? 0;
  const detectorUsed = result?.detector_used ?? detectorChoice;
  const sunAngleDiff = result?.sun_angle_difference;
  const sunAngleLabel = result?.metadata_label || (result?.is_manual_angle ? 'Manual Input' : 'Metadata');
  const reason = result?.reason || 'Insufficient feature matches survived geometric verification due to severe shadow divergence.';
  const confidencePercentage = (metrics.confidence_percentage ?? (metrics.confidence_score ? metrics.confidence_score * 100 : 0)).toFixed(1);

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* HUD Module Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-800/80 text-amber-400 text-xs font-semibold mb-2">
            <Sun className="w-3.5 h-3.5 animate-pulse" />
            Illumination Invariance Engine
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Sun-Angle Robustness Analysis
          </h2>
          <p className="text-slate-400 text-sm mt-1 max-w-2xl">
            Evaluate computer vision feature stability, inlier preservation, and geometric registration reliability under extreme solar elevation and azimuth illumination disparities.
          </p>
        </div>

        {(sourceFile || referenceFile || result) && (
          <button
            onClick={handleClear}
            className="self-start md:self-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-700 bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 text-xs font-medium transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Inputs
          </button>
        )}
      </div>

      {/* Image Upload Area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ImageUploader
          title="Source Lunar Image"
          subtitle="Primary observation under varying solar incidence"
          file={sourceFile}
          previewUrl={sourcePreview}
          onImageSelected={handleSourceSelected}
          onImageRemoved={() => {
            setSourceFile(null);
            setSourcePreview(null);
          }}
          badgeText="Source"
          badgeColor="text-amber-400 border-amber-800 bg-amber-950/60"
        />

        <ImageUploader
          title="Reference Lunar Image"
          subtitle="Baseline coordinate frame or nadir illumination frame"
          file={referenceFile}
          previewUrl={referencePreview}
          onImageSelected={handleReferenceSelected}
          onImageRemoved={() => {
            setReferenceFile(null);
            setReferencePreview(null);
          }}
          badgeText="Reference"
          badgeColor="text-cyan-400 border-cyan-800 bg-cyan-950/60"
        />
      </div>

      {/* Parameter Controls & Trigger */}
      <div className="hud-panel p-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-4">
          <Sliders className="w-4 h-4 text-amber-400" />
          <span>Analysis Parameters & Illumination Metadata</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 items-end">
          {/* Feature Detector Choice */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Feature Detector Algorithm
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDetectorChoice('SIFT')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all border ${
                  detectorChoice === 'SIFT'
                    ? 'bg-amber-500/20 border-amber-400 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                SIFT (Scale-Invariant)
              </button>
              <button
                type="button"
                onClick={() => setDetectorChoice('AKAZE')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all border ${
                  detectorChoice === 'AKAZE'
                    ? 'bg-amber-500/20 border-amber-400 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                AKAZE (Non-Linear)
              </button>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              SIFT excels at multi-scale gradients; AKAZE preserves non-linear boundary contours across shadows.
            </p>
          </div>

          {/* Optional Sun-Angle Difference Input */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider flex items-center justify-between">
              <span>Sun-Angle Difference (Δθ)</span>
              <span className="text-slate-500 font-normal">Optional</span>
            </label>
            <div className="relative">
              <input
                type="number"
                min="0"
                max="90"
                step="0.1"
                value={manualAngleInput}
                onChange={(e) => setManualAngleInput(e.target.value)}
                placeholder="e.g. 24.5 (or read from metadata)"
                className="w-full bg-slate-900/80 border border-slate-700/80 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400/80 focus:ring-1 focus:ring-amber-400/40"
              />
              <span className="absolute right-3 top-2 text-xs text-slate-500">deg</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Leave blank to automatically extract solar angles from PDS/EXIF image metadata.
            </p>
          </div>

          {/* Action Button */}
          <div>
            <button
              onClick={handleRunAnalysis}
              disabled={isLoading || !sourceFile || !referenceFile}
              className={`w-full py-2.5 px-6 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg ${
                isLoading || !sourceFile || !referenceFile
                  ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                  : 'bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white border border-amber-300/40 shadow-[0_0_20px_rgba(245,158,11,0.4)] cursor-pointer active:scale-[0.99]'
              }`}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Computing Correspondences...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Sun-Angle Analysis</span>
                </>
              )}
            </button>
            <p className="text-[11px] text-slate-500 mt-1 text-center">
              Requires both source and reference images.
            </p>
          </div>
        </div>
      </div>

      {/* Loading Overlay State */}
      {isLoading && (
        <LoadingState
          message="Analyzing feature robustness across illumination geometry..."
          currentStep="Extracting solar angles and executing RANSAC correspondence matching..."
        />
      )}

      {/* Results Section */}
      {result && !isLoading && (
        <div className="space-y-6">
          {/* Decision Outcome Banner */}
          <div
            className={`hud-panel p-6 border ${
              isAccepted
                ? 'border-emerald-500/40 bg-emerald-950/20'
                : 'border-rose-500/40 bg-rose-950/20'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                {isAccepted ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs uppercase font-bold tracking-widest px-2.5 py-0.5 rounded-full border ${
                        isAccepted
                          ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                          : 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                      }`}
                    >
                      {isAccepted ? 'Registration Accepted' : 'Registration Rejected'}
                    </span>
                    {result.detector_used && (
                      <span className="text-xs text-slate-400 font-mono">
                        via {result.detector_used}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1">
                    {isAccepted
                      ? 'Features Robust to Illumination Disparity'
                      : 'Severe Shadow Displacement or Insufficient Inliers'}
                  </h3>
                  <p className="text-xs text-slate-300 mt-0.5">
                    {isAccepted
                      ? `Geometric correspondence verified with confidence ${(result.confidence_percentage ?? (result.confidence_score ? result.confidence_score * 100 : 0)).toFixed(1)}%.`
                      : result.reason || 'Insufficient feature matches survived geometric verification due to severe shadow divergence.'}
                  </p>
                </div>
              </div>

              {/* Sun Angle Badge */}
              <div className="flex sm:flex-col items-center sm:items-end justify-between border-t sm:border-t-0 border-slate-700/50 pt-2 sm:pt-0">
                <span className="text-[11px] text-slate-400 uppercase tracking-wider">
                  Solar Difference
                </span>
                <span className="text-xl font-mono font-extrabold text-amber-300">
                  {typeof result.sun_angle_difference === 'number'
                    ? `${result.sun_angle_difference.toFixed(1)}°`
                    : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-400 max-w-[180px] text-right truncate">
                  {result.metadata_label || (result.is_manual_angle ? 'Manual Input' : 'Metadata')}
                </span>
              </div>
            </div>
          </div>

          {/* Core Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Confidence Score"
              value={`${(result.confidence_percentage ?? (result.confidence_score ? result.confidence_score * 100 : 0)).toFixed(1)}`}
              unit="%"
              description="Geometric & feature correspondence quality"
              icon={Gauge}
              progress={result.confidence_percentage ?? (result.confidence_score ? result.confidence_score * 100 : 0)}
              colorScheme={isAccepted ? 'emerald' : 'amber'}
            />

            <MetricCard
              title="Inliers / Ratio"
              value={`${result.inliers ?? 0}`}
              unit={`/ ${((result.inlier_ratio ?? 0) * 100).toFixed(1)}%`}
              description="RANSAC surviving keypoint pairs"
              icon={Layers}
              colorScheme="cyan"
            />

            <MetricCard
              title="Geometric RMSE"
              value={typeof result.rmse === 'number' ? result.rmse.toFixed(2) : '99.99'}
              unit="px"
              description="Root Mean Square Error of aligned features"
              icon={Activity}
              colorScheme={typeof result.rmse === 'number' && result.rmse < 5 ? 'emerald' : 'amber'}
            />

            <MetricCard
              title="Good Matches"
              value={`${result.good_matches ?? 0}`}
              unit={`kps: ${result.source_keypoints ?? 0}/${result.reference_keypoints ?? 0}`}
              description="Descriptor distance ratio test pass"
              icon={Sparkles}
              colorScheme="indigo"
            />
          </div>

          {/* Scientific Illumination Interpretation Panel */}
          <div className="hud-panel p-6">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-3">
              <Info className="w-4 h-4 text-cyan-400" />
              <span>Solar Illumination & Topographic Shadow Insights</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-amber-400" />
                  Angular Geometry
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Sun-angle disparity: <span className="text-amber-300 font-mono font-semibold">{result.sun_angle_difference ?? 0}°</span>. Disparities above 35° typically introduce significant crater rim shadow elongations that shift apparent feature centroid positions.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  Algorithm Performance
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Detector used: <span className="text-cyan-300 font-semibold">{result.detector_used || detectorChoice}</span>. Found {result.source_keypoints ?? 0} source keypoints and {result.reference_keypoints ?? 0} reference keypoints, yielding {result.inliers ?? 0} valid inliers.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Registration Integrity
                </div>
                <p className="text-slate-300 leading-relaxed">
                  {isAccepted
                    ? 'The homography matrix maintained sub-pixel alignment stability despite illumination changes, confirming robust registration.'
                    : 'The pair exceeded tolerance bounds. High shadow distortion caused matching ambiguity; consider applying histogram normalization or AKAZE diffusion.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* FOOTPRINT MAP (shown when at least one image is uploaded)                 */}
      {/* ========================================================================= */}
      {(sourceFile || referenceFile) && (
        <FootprintMap
          metadataA={sourceFootprint}
          metadataB={referenceFootprint}
          pdsMetaA={sourcePdsMeta}
          pdsMetaB={referencePdsMeta}
          fileA={sourceFile}
          fileB={referenceFile}
          labelA="Source Image"
          labelB="Reference Image"
        />
      )}

      {/* ========================================================================= */}
      {/* SECTION 2: SUN-ANGLE ROBUSTNESS BENCHMARK (BATCH TESTING)                */}
      {/* ========================================================================= */}

      <div className="border-t border-slate-800/80 pt-10 space-y-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-950/80 border border-teal-800/80 text-teal-400 text-xs font-semibold mb-2">
              <BarChart2 className="w-3.5 h-3.5" />
              Multi-Pair Benchmark Extension
            </div>
            <h3 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
              Sun-Angle Robustness Benchmark
            </h3>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              Simulate progressive solar angle sweeps against a baseline lunar frame to chart registration confidence degradation boundaries.
            </p>
          </div>

          {(batchBaseFile || batchResults) && (
            <button
              onClick={handleClearBatch}
              className="self-start md:self-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-700 bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 text-xs font-medium transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Benchmark
            </button>
          )}
        </div>

        {/* Batch Input Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Baseline Lunar Image Upload */}
          <div className="lg:col-span-6">
            <ImageUploader
              title="Baseline Lunar Image"
              subtitle="Reference observation used to generate multi-angle lighting benchmark pairs"
              file={batchBaseFile}
              previewUrl={batchBasePreview}
              onImageSelected={handleBatchSelected}
              onImageRemoved={() => {
                setBatchBaseFile(null);
                setBatchBasePreview(null);
              }}
              badgeText="Baseline Required"
              badgeColor="text-teal-400 border-teal-800 bg-teal-950/60"
            />
          </div>

          {/* Benchmark Parameters Panel */}
          <div className="lg:col-span-6 hud-panel p-6 space-y-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Sliders className="w-4 h-4 text-teal-400" />
              <span>Benchmark Execution Parameters</span>
            </div>

            {/* Number of Pairs (15 to 20, default 18) */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Evaluation Pairs Count
                </label>
                <span className="text-xs font-mono text-teal-400 font-bold">{batchNumPairs} Pairs</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="15"
                  max="20"
                  step="1"
                  value={batchNumPairs}
                  onChange={(e) => setBatchNumPairs(parseInt(e.target.value, 10))}
                  className="w-full accent-teal-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                />
                <input
                  type="number"
                  min="15"
                  max="20"
                  value={batchNumPairs}
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10);
                    setBatchNumPairs(isNaN(v) ? 18 : Math.min(20, Math.max(15, v)));
                  }}
                  className="w-16 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white text-center font-mono focus:border-teal-400 focus:outline-none"
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Supported range: 15 to 20 synthetic/empirical solar illumination angle increments.
              </p>
            </div>

            {/* Detector Selection for Batch */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
                Benchmark Feature Detector
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setBatchDetector('SIFT')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all border ${
                    batchDetector === 'SIFT'
                      ? 'bg-teal-500/20 border-teal-400 text-teal-300 shadow-[0_0_12px_rgba(20,184,166,0.3)]'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  SIFT (Scale-Invariant)
                </button>
                <button
                  type="button"
                  onClick={() => setBatchDetector('AKAZE')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all border ${
                    batchDetector === 'AKAZE'
                      ? 'bg-teal-500/20 border-teal-400 text-teal-300 shadow-[0_0_12px_rgba(20,184,166,0.3)]'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  AKAZE (Non-Linear)
                </button>
              </div>
            </div>

            {/* Run Button */}
            <div className="pt-2">
              <button
                onClick={handleRunBatch}
                disabled={isBatchLoading || !batchBaseFile}
                className={`w-full py-3 px-6 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg ${
                  isBatchLoading || !batchBaseFile
                    ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                    : 'bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-400 hover:to-cyan-500 text-white border border-teal-300/40 shadow-[0_0_20px_rgba(20,184,166,0.4)] cursor-pointer active:scale-[0.99]'
                }`}
              >
                {isBatchLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Executing Batch Benchmark ({batchNumPairs} Pairs)...</span>
                  </>
                ) : (
                  <>
                    <BarChart2 className="w-4 h-4" />
                    <span>Run Multi-Pair Benchmark</span>
                  </>
                )}
              </button>
              <p className="text-[11px] text-slate-500 mt-1 text-center">
                Iterates registration pipeline across all simulated illumination incidence angles.
              </p>
            </div>
          </div>
        </div>

        {/* Batch Error Message */}
        {batchError && (
          <div className="hud-panel p-4 border border-rose-500/40 bg-rose-950/20 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <div className="text-xs text-rose-200">{batchError}</div>
          </div>
        )}

        {/* Batch Loading Indicator */}
        {isBatchLoading && (
          <LoadingState
            message={`Evaluating ${batchNumPairs} lunar pairs across 0° to 85° sun-angle difference...`}
            currentStep="Simulating illumination shifts, extracting feature descriptors, and running RANSAC alignment..."
          />
        )}

        {/* Batch Results: Chart + Metrics Table */}
        {batchResults && !isBatchLoading && (
          <div className="space-y-6">
            {/* Top Summary Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="hud-panel p-4 border border-teal-500/30">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Total Evaluated Pairs</div>
                <div className="text-2xl font-bold font-mono text-teal-300 mt-1">{batchResults.length}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Span: 0° to ~85° sun elevation</div>
              </div>

              <div className="hud-panel p-4 border border-emerald-500/30">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Accepted Pairs</div>
                <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                  {batchResults.filter((p) => p.decision === 'Accepted').length}{' '}
                  <span className="text-xs font-normal text-slate-400">
                    ({((batchResults.filter((p) => p.decision === 'Accepted').length / batchResults.length) * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">Confidence threshold ≥ 20%</div>
              </div>

              <div className="hud-panel p-4 border border-amber-500/30">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Detector Tested</div>
                <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{batchDetector}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Feature correspondence pipeline</div>
              </div>
            </div>

            {/* Visual Scatter / Line Chart: Confidence vs Sun-Angle Difference */}
            <div className="hud-panel p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <LineChart className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                    Confidence vs Sun-Angle Difference
                  </h4>
                </div>
                <div className="flex items-center gap-4 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
                    Accepted
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block"></span>
                    Rejected
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 border-t border-dashed border-amber-400/80 inline-block"></span>
                    20% Threshold
                  </span>
                </div>
              </div>

              {/* Chart SVG Canvas */}
              <div className="w-full overflow-x-auto">
                <div className="min-w-[640px] bg-slate-950/60 rounded-lg p-3 border border-slate-800/80">
                  <svg viewBox="0 0 640 240" className="w-full h-auto">
                    {/* Horizontal Grid lines and Y Labels */}
                    {[0, 20, 40, 60, 80, 100].map((val) => {
                      const yPos = 25 + (1 - val / 100) * 175;
                      return (
                        <g key={`y-${val}`}>
                          <line
                            x1={50}
                            y1={yPos}
                            x2={610}
                            y2={yPos}
                            stroke={val === 20 ? 'rgba(245, 158, 11, 0.4)' : 'rgba(100, 116, 139, 0.15)'}
                            strokeDasharray={val === 20 ? '4 3' : undefined}
                            strokeWidth="1"
                          />
                          <text
                            x={42}
                            y={yPos + 3}
                            fill="#64748b"
                            fontSize="10"
                            fontFamily="monospace"
                            textAnchor="end"
                          >
                            {val}%
                          </text>
                        </g>
                      );
                    })}

                    {/* Vertical Grid lines and X Labels */}
                    {[0, 15, 30, 45, 60, 75, 90].map((deg) => {
                      const xPos = 50 + (deg / 90) * 560;
                      return (
                        <g key={`x-${deg}`}>
                          <line
                            x1={xPos}
                            y1={25}
                            x2={xPos}
                            y2={200}
                            stroke="rgba(100, 116, 139, 0.15)"
                            strokeWidth="1"
                          />
                          <text
                            x={xPos}
                            y={216}
                            fill="#64748b"
                            fontSize="10"
                            fontFamily="monospace"
                            textAnchor="middle"
                          >
                            {deg}°
                          </text>
                        </g>
                      );
                    })}

                    {/* Axis Labels */}
                    <text
                      x={320}
                      y={234}
                      fill="#94a3b8"
                      fontSize="11"
                      fontWeight="600"
                      textAnchor="middle"
                    >
                      Sun-Angle Difference (Δθ in Degrees)
                    </text>
                    <text
                      transform="rotate(-90 14 120)"
                      x="14"
                      y={120}
                      fill="#94a3b8"
                      fontSize="11"
                      fontWeight="600"
                      textAnchor="middle"
                    >
                      Confidence (%)
                    </text>

                    {/* Polyline Curve */}
                    {(() => {
                      const sorted = [...batchResults].sort(
                        (a, b) => (a.sun_angle_difference ?? 0) - (b.sun_angle_difference ?? 0)
                      );
                      const points = sorted
                        .map((p) => {
                          const conf = p.confidence_percentage ?? (p.confidence_score ? p.confidence_score * 100 : 0);
                          const x = 50 + (Math.max(0, Math.min(90, p.sun_angle_difference ?? 0)) / 90) * 560;
                          const y = 25 + (1 - Math.max(0, Math.min(100, conf)) / 100) * 175;
                          return `${x},${y}`;
                        })
                        .join(' ');
                      return (
                        <polyline
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          opacity="0.85"
                          points={points}
                        />
                      );
                    })()}

                    {/* Data Points */}
                    {batchResults.map((p) => {
                      const conf = p.confidence_percentage ?? (p.confidence_score ? p.confidence_score * 100 : 0);
                      const cx = 50 + (Math.max(0, Math.min(90, p.sun_angle_difference ?? 0)) / 90) * 560;
                      const cy = 25 + (1 - Math.max(0, Math.min(100, conf)) / 100) * 175;
                      const isAcc = p.decision === 'Accepted';
                      const isHovered = hoveredPairId === p.pair_id;

                      return (
                        <g
                          key={`pt-${p.pair_id}`}
                          className="cursor-pointer"
                          onMouseEnter={() => setHoveredPairId(p.pair_id)}
                          onMouseLeave={() => setHoveredPairId(null)}
                        >
                          {isHovered && (
                            <circle
                              cx={cx}
                              cy={cy}
                              r="10"
                              fill={isAcc ? 'rgba(52, 211, 153, 0.25)' : 'rgba(251, 113, 133, 0.25)'}
                              stroke={isAcc ? '#34d399' : '#fb7185'}
                              strokeWidth="1.5"
                            />
                          )}
                          <circle
                            cx={cx}
                            cy={cy}
                            r={isHovered ? '6' : '4.5'}
                            fill={isAcc ? '#10b981' : '#f43f5e'}
                            stroke="#020617"
                            strokeWidth="2"
                          />
                        </g>
                      );
                    })}
                  </svg>
                </div>
              </div>

              {/* Hover Indicator Card */}
              {hoveredPairId !== null && (
                (() => {
                  const hp = batchResults.find((p) => p.pair_id === hoveredPairId);
                  if (!hp) return null;
                  const conf = hp.confidence_percentage ?? (hp.confidence_score ? hp.confidence_score * 100 : 0);
                  const isAcc = hp.decision === 'Accepted';
                  return (
                    <div className="text-xs p-2.5 rounded-lg bg-slate-900 border border-slate-700 flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono text-cyan-300 font-bold">Pair #{hp.pair_id}</span>
                      <span className="text-slate-300">Angle: <span className="font-mono text-amber-300">{hp.sun_angle_difference?.toFixed(1)}°</span></span>
                      <span className="text-slate-300">Confidence: <span className="font-mono text-emerald-300">{conf.toFixed(1)}%</span></span>
                      <span className="text-slate-300">Inliers: <span className="font-mono text-white">{hp.inliers ?? 0}</span> ({((hp.inlier_ratio ?? 0) * 100).toFixed(1)}%)</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${isAcc ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                        {hp.decision}
                      </span>
                    </div>
                  );
                })()
              )}
            </div>

            {/* Compact Table */}
            <div className="hud-panel p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-400" />
                  <span>Batch Pair Evaluation Results</span>
                </h4>
                <span className="text-xs text-slate-400 font-mono">
                  {batchResults.length} pairs recorded
                </span>
              </div>

              <div className="overflow-x-auto max-h-96 border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs text-slate-300 font-mono">
                  <thead className="bg-slate-900/90 text-[11px] text-slate-400 uppercase tracking-wider sticky top-0 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Pair</th>
                      <th className="py-2.5 px-3">Sun-Angle Difference</th>
                      <th className="py-2.5 px-3">Confidence %</th>
                      <th className="py-2.5 px-3">Inliers</th>
                      <th className="py-2.5 px-3">Inlier Ratio</th>
                      <th className="py-2.5 px-3">RMSE</th>
                      <th className="py-2.5 px-3">Decision</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                    {batchResults.map((item) => {
                      const isAcc = item.decision === 'Accepted';
                      const conf = item.confidence_percentage ?? (item.confidence_score ? item.confidence_score * 100 : 0);
                      const isHovered = hoveredPairId === item.pair_id;

                      return (
                        <tr
                          key={`row-${item.pair_id}`}
                          className={`transition-colors cursor-pointer ${
                            isHovered
                              ? 'bg-teal-950/30'
                              : isAcc
                              ? 'hover:bg-slate-900/60'
                              : 'hover:bg-rose-950/10'
                          }`}
                          onMouseEnter={() => setHoveredPairId(item.pair_id)}
                          onMouseLeave={() => setHoveredPairId(null)}
                        >
                          <td className="py-2 px-3 font-semibold text-cyan-300">
                            #{item.pair_id}
                          </td>
                          <td className="py-2 px-3 text-amber-300 font-bold">
                            {typeof item.sun_angle_difference === 'number'
                              ? `${item.sun_angle_difference.toFixed(1)}°`
                              : 'N/A'}
                          </td>
                          <td className="py-2 px-3">
                            <span
                              className={`font-bold ${
                                conf >= 20 ? 'text-emerald-400' : 'text-rose-400'
                              }`}
                            >
                              {conf.toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-2 px-3 text-white">
                            {item.inliers ?? 0}
                          </td>
                          <td className="py-2 px-3 text-slate-300">
                            {typeof item.inlier_ratio === 'number'
                              ? `${(item.inlier_ratio * 100).toFixed(1)}%`
                              : '0.0%'}
                          </td>
                          <td className="py-2 px-3 text-slate-400">
                            {typeof item.rmse === 'number' && item.rmse < 90
                              ? `${item.rmse.toFixed(2)} px`
                              : '99.99 px'}
                          </td>
                          <td className="py-2 px-3">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                                isAcc
                                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                                  : 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                              }`}
                            >
                              {isAcc ? (
                                <>
                                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                  Accepted
                                </>
                              ) : (
                                <>
                                  <XCircle className="w-3 h-3 text-rose-400" />
                                  Rejected
                                </>
                              )}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
