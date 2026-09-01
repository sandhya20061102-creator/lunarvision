import React, { useState } from 'react';
import {
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Download,
  Sliders,
  Maximize2,
  Eye,
  Activity,
  GitCompare
} from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import { registerImages } from '../services/api';
import ImageUploader from '../components/ImageUploader';
import MetricCard from '../components/MetricCard';
import ResultImage from '../components/ResultImage';
import ComparisonSlider from '../components/ComparisonSlider';
import LoadingState from '../components/LoadingState';
import ErrorMessage from '../components/ErrorMessage';
import DownloadButton from '../components/DownloadButton';

export default function RegistrationPage() {
  const {
    sourceFile,
    referenceFile,
    sourcePreview,
    referencePreview,
    setSourceImage,
    setReferenceImage,
    registrationResult,
    setRegistrationResult,
    setActiveTab,
  } = usePipeline();

  const [isLoading, setIsLoading] = useState(false);
  const [detectorChoice, setDetectorChoice] = useState('SIFT');
  const [activeResultView, setActiveResultView] = useState('aligned'); // 'aligned', 'inliers', 'raw_matches', 'overlay', 'slider'

  const handleStartRegistration = async () => {
    if (!sourceFile || !referenceFile) {
      alert('Please upload both Source and Reference lunar images before starting registration.');
      return;
    }

    setIsLoading(true);
    setRegistrationResult(null);

    try {
      const data = await registerImages(sourceFile, referenceFile, detectorChoice);
      setRegistrationResult(data);
    } catch (err) {
      setRegistrationResult({
        status: 'no_match',
        reason: err.message || 'An unexpected error occurred during image registration.',
        details: { step: 'client_call' },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const isSuccess = registrationResult?.status === 'success';
  const isNoMatch = registrationResult?.status === 'no_match';
  const metrics = registrationResult?.metrics;
  const artifacts = registrationResult?.artifacts;

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 text-xs font-semibold mb-2">
            <Layers className="w-3.5 h-3.5" />
            Module 01: Geometric Registration
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Planetary Image Registration
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Align temporal or multi-sensor lunar orbital images to a baseline reference geometry using SIFT/AKAZE keypoints and RANSAC homography.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-lunar-900 border border-lunar-700">
            <span className="text-xs text-slate-400">Detector:</span>
            <select
              value={detectorChoice}
              onChange={(e) => setDetectorChoice(e.target.value)}
              className="bg-transparent text-xs font-semibold text-cyan-400 focus:outline-none cursor-pointer"
            >
              <option value="SIFT" className="bg-lunar-900 text-white">SIFT (High Precision)</option>
              <option value="AKAZE" className="bg-lunar-900 text-white">AKAZE (Fast Binary)</option>
            </select>
          </div>

          <button
            onClick={handleStartRegistration}
            disabled={!sourceFile || !referenceFile || isLoading}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-all hover:scale-[1.02]"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Aligning Imagery...
              </>
            ) : (
              <>
                <Layers className="w-4 h-4" /> Start Registration
              </>
            )}
          </button>
        </div>
      </div>

      {/* Image Upload Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ImageUploader
          title="Secondary / Temporal Image (Source)"
          subtitle="Image to be warped and aligned (e.g. post-event orbital pass)"
          file={sourceFile}
          previewUrl={sourcePreview}
          onImageSelected={setSourceImage}
          onImageRemoved={() => setSourceImage(null)}
          badgeText="Source Frame"
          badgeColor="text-indigo-400 border-indigo-800 bg-indigo-950/60"
        />

        <ImageUploader
          title="Baseline Image (Reference)"
          subtitle="Target coordinate frame and geometry (e.g. pre-event orbital pass)"
          file={referenceFile}
          previewUrl={referencePreview}
          onImageSelected={setReferenceImage}
          onImageRemoved={() => setReferenceImage(null)}
          badgeText="Reference Frame"
          badgeColor="text-cyan-400 border-cyan-800 bg-cyan-950/60"
        />
      </div>

      {/* Loading Radar Scanner */}
      {isLoading && (
        <LoadingState
          title="Computing Homography & Alignment..."
          subtitle="Extracting invariant keypoints and eliminating outliers via RANSAC"
        />
      )}

      {/* No Match or Error Card */}
      {isNoMatch && !isLoading && (
        <ErrorMessage
          title="No Reliable Match Detected"
          reason={registrationResult.reason}
          details={registrationResult.details}
        />
      )}

      {/* Successful Registration View */}
      {isSuccess && !isLoading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Status Alert Banner */}
          <div className="glass-panel p-4 rounded-2xl border border-emerald-500/50 bg-emerald-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-white text-sm sm:text-base">
                  Geometric Alignment Successful
                </h4>
                <p className="text-xs text-slate-300">
                  Computed perspective homography using {registrationResult.detector_used} detector with {metrics.inlier_count} inliers ({metrics.inlier_ratio * 100}% inlier ratio).
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <DownloadButton
                filePath={artifacts?.aligned_image}
                filename={`lunar_aligned_${registrationResult.session_id}.png`}
                label="Download Aligned Image"
                size="sm"
              />
              <button
                onClick={() => setActiveTab('change_detection')}
                className="px-3.5 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md"
              >
                <span>Proceed to Change Detection</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Scientific Metrics Grid */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Quantitative Alignment Metrics
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="RMSE (Root Mean Square Error)"
                value={metrics.rmse}
                unit="px intensity"
                description="Pixel-wise alignment discrepancy across valid overlapping mask"
                colorScheme={metrics.rmse < 15 ? 'emerald' : metrics.rmse < 35 ? 'cyan' : 'amber'}
              />

              <MetricCard
                title="RANSAC Inliers"
                value={metrics.inlier_count}
                unit={`/ ${metrics.total_good_matches}`}
                description="Geometrically consistent point correspondences verified by RANSAC"
                colorScheme="cyan"
              />

              <MetricCard
                title="Inlier Ratio"
                value={`${(metrics.inlier_ratio * 100).toFixed(1)}%`}
                description="Percentage of reliable matches surviving outlier rejection"
                colorScheme={metrics.inlier_ratio > 0.6 ? 'emerald' : 'cyan'}
              />

              <MetricCard
                title="Registration Confidence"
                value={`${metrics.registration_confidence_percentage}%`}
                progress={metrics.registration_confidence_percentage}
                description="Synthesized score from match volume, inlier ratio, and RMSE"
                colorScheme={metrics.registration_confidence_score > 0.8 ? 'emerald' : 'cyan'}
              />
            </div>
          </div>

          {/* Multi-Tab Result Visualizer */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                Visual Correspondence Artifacts
              </h3>

              {/* View Selector Tabs */}
              <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-lunar-900 border border-lunar-700">
                <button
                  onClick={() => setActiveResultView('aligned')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeResultView === 'aligned'
                      ? 'bg-cyan-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Aligned Image
                </button>
                <button
                  onClick={() => setActiveResultView('slider')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeResultView === 'slider'
                      ? 'bg-cyan-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Split Slider
                </button>
                <button
                  onClick={() => setActiveResultView('inliers')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeResultView === 'inliers'
                      ? 'bg-cyan-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  RANSAC Inliers
                </button>
                <button
                  onClick={() => setActiveResultView('raw_matches')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeResultView === 'raw_matches'
                      ? 'bg-cyan-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  All Matches
                </button>
                <button
                  onClick={() => setActiveResultView('overlay')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeResultView === 'overlay'
                      ? 'bg-cyan-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  50/50 Blend
                </button>
              </div>
            </div>

            {/* Active View Container */}
            {activeResultView === 'slider' ? (
              <ComparisonSlider
                beforeImage={artifacts?.reference_image}
                afterImage={artifacts?.aligned_image}
                beforeLabel="Reference Frame (Baseline)"
                afterLabel="Warped Source Frame (Aligned)"
              />
            ) : activeResultView === 'aligned' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultImage
                  title="Original Reference Baseline"
                  subtitle="Target coordinate system"
                  imagePath={artifacts?.reference_image}
                  badgeText="Target Frame"
                />
                <ResultImage
                  title="Registered & Aligned Source"
                  subtitle="Warped via computed Homography"
                  imagePath={artifacts?.aligned_image}
                  badgeText="Warped Output"
                  badgeColor="bg-emerald-950 text-emerald-400 border-emerald-800"
                />
              </div>
            ) : activeResultView === 'inliers' ? (
              <ResultImage
                title="RANSAC Filtered Inlier Correspondences"
                subtitle={`Showing verified geometric inliers (${metrics.inlier_count} matches)`}
                imagePath={artifacts?.inlier_matches}
                badgeText="Inliers Only"
                badgeColor="bg-cyan-950 text-cyan-400 border-cyan-800"
              />
            ) : activeResultView === 'raw_matches' ? (
              <ResultImage
                title="Raw Feature Matches (Lowe's Ratio Test)"
                subtitle={`Candidate matches before RANSAC filtering (${metrics.total_good_matches} matches)`}
                imagePath={artifacts?.feature_matches}
                badgeText="All Good Matches"
                badgeColor="bg-indigo-950 text-indigo-400 border-indigo-800"
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultImage
                  title="Alpha-Blended Overlay Comparison"
                  subtitle="50% Reference + 50% Aligned Source transparency blend"
                  imagePath={artifacts?.overlay_comparison}
                  badgeText="Overlay Blend"
                />
                <ResultImage
                  title="Warped Source Geometry"
                  subtitle="Direct perspective aligned output"
                  imagePath={artifacts?.aligned_image}
                  badgeText="Aligned"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
