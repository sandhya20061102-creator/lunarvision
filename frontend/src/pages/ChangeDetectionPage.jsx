import React, { useState } from 'react';
import {
  Cpu,
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
  Layers,
  Info,
  ShieldAlert,
  Compass
} from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import { detectTemporalChanges } from '../services/api';
import ImageUploader from '../components/ImageUploader';
import MetricCard from '../components/MetricCard';
import ResultImage from '../components/ResultImage';
import ComparisonSlider from '../components/ComparisonSlider';
import LoadingState from '../components/LoadingState';
import ErrorMessage from '../components/ErrorMessage';
import DownloadButton from '../components/DownloadButton';

export default function ChangeDetectionPage() {
  const {
    sourceFile,
    referenceFile,
    sourcePreview,
    referencePreview,
    setSourceImage,
    setReferenceImage,
    changeDetectionResult,
    setChangeDetectionResult,
    setActiveTab,
  } = usePipeline();

  const [isLoading, setIsLoading] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.35);
  const [diffThreshold, setDiffThreshold] = useState(35);
  const [activeView, setActiveView] = useState('heatmap'); // 'heatmap', 'annotated', 'mask', 'aligned', 'slider'

  const handleStartChangeDetection = async () => {
    if (!sourceFile || !referenceFile) {
      alert('Please upload both Earlier (Source) and Later (Reference) lunar images.');
      return;
    }

    setIsLoading(true);
    setChangeDetectionResult(null);

    try {
      const data = await detectTemporalChanges(
        sourceFile,
        referenceFile,
        minConfidence,
        diffThreshold
      );
      setChangeDetectionResult(data);
    } catch (err) {
      setChangeDetectionResult({
        status: 'no_match',
        reason: err.message || 'An unexpected error occurred during temporal change detection.',
        details: { step: 'client_call' },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const isSuccess = changeDetectionResult?.status === 'success';
  const isNoMatch = changeDetectionResult?.status === 'no_match';
  const regMetrics = changeDetectionResult?.registration_metrics;
  const changeMetrics = changeDetectionResult?.change_metrics;
  const regions = changeDetectionResult?.detected_regions || [];
  const artifacts = changeDetectionResult?.artifacts;

  const getLabelColor = (label) => {
    switch (label) {
      case 'Possible crater-like change':
        return 'bg-amber-950/80 text-amber-400 border-amber-800';
      case 'Potential surface change':
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-800';
      case 'Possible illumination artifact':
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-800';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-semibold mb-2">
            <Cpu className="w-3.5 h-3.5" />
            Module 03: Temporal Change Detection
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Temporal Surface Change Analysis
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Detect crater formations, boulder displacement, and surface reflectance disturbances across temporal lunar orbital passes.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-lunar-900 border border-lunar-700 text-xs">
            <span className="text-slate-400">Min Conf:</span>
            <span className="font-mono text-cyan-400">{Math.round(minConfidence * 100)}%</span>
          </div>

          <button
            onClick={handleStartChangeDetection}
            disabled={!sourceFile || !referenceFile || isLoading}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-emerald-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-all hover:scale-[1.02]"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Detecting Anomalies...
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" /> Detect Potential Changes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Mandatory Scientific Disclaimer Banner */}
      <div className="glass-panel p-4 rounded-2xl border border-cyan-500/30 bg-cyan-950/20 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <span className="font-bold text-cyan-300 block mb-0.5">Scientific Transparency Protocol:</span>
          Detected regions represent automated computer vision potential changes and are not scientifically confirmed discoveries. Heuristic labels provide morphological cues and require expert validation against solar azimuth data.
        </div>
      </div>

      {/* Image Upload Area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ImageUploader
          title="Earlier Image (Source T0)"
          subtitle="Pre-event baseline lunar orbital frame"
          file={sourceFile}
          previewUrl={sourcePreview}
          onImageSelected={setSourceImage}
          onImageRemoved={() => setSourceImage(null)}
          badgeText="Earlier Pass"
          badgeColor="text-indigo-400 border-indigo-800 bg-indigo-950/60"
        />

        <ImageUploader
          title="Later Image (Reference T1)"
          subtitle="Post-event target lunar orbital frame"
          file={referenceFile}
          previewUrl={referencePreview}
          onImageSelected={setReferenceImage}
          onImageRemoved={() => setReferenceImage(null)}
          badgeText="Later Pass"
          badgeColor="text-emerald-400 border-emerald-800 bg-emerald-950/60"
        />
      </div>

      {/* Loading State */}
      {isLoading && (
        <LoadingState
          title="Running Temporal Change Detection..."
          subtitle="Normalizing illumination, calculating SSIM dissimilarity, and segmenting morphological candidates"
          steps={[
            'Aligning temporal coordinate frames with RANSAC...',
            'Normalizing solar illumination variations via CLAHE...',
            'Computing Structural Similarity Index (SSIM) map...',
            'Executing morphological opening & closing filters...',
            'Classifying candidate regions with explainable heuristics...',
          ]}
        />
      )}

      {/* No Match / Error Message */}
      {isNoMatch && !isLoading && (
        <ErrorMessage
          title="Change Detection Blocked: Insufficient Alignment"
          reason={changeDetectionResult.reason}
          details={changeDetectionResult.details}
          recommendations={[
            'Ensure the temporal image pair covers the same lunar coordinates.',
            'Change detection strictly requires high-confidence geometric registration to prevent false difference artifacts.',
            'Try adjusting illumination or checking for high feature density crater regions.',
          ]}
        />
      )}

      {/* Successful Change Detection Output */}
      {isSuccess && !isLoading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Status & Summary Bar */}
          <div className="glass-panel p-4 rounded-2xl border border-emerald-500/50 bg-emerald-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-white text-sm sm:text-base">
                  Change Detection Completed ({regions.length} Candidate Regions)
                </h4>
                <p className="text-xs text-slate-300">
                  Global SSIM Similarity: <span className="font-mono text-cyan-300 font-bold">{changeMetrics.mean_ssim}</span> • Alignment Confidence: <span className="font-mono text-emerald-300 font-bold">{regMetrics.registration_confidence_percentage}%</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <DownloadButton
                filePath={artifacts?.change_heatmap}
                filename={`lunar_heatmap_${changeDetectionResult.session_id}.png`}
                label="Save Heatmap"
                size="sm"
              />
              <button
                onClick={() => setActiveTab('results')}
                className="px-3.5 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-md"
              >
                <span>View Full Results Summary</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Metrics Row */}
          <div>
            <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Temporal Comparison Metrics
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="SSIM Structural Similarity"
                value={changeMetrics.mean_ssim}
                description="Structural preservation between registered temporal passes (1.0 = identical)"
                colorScheme={changeMetrics.mean_ssim > 0.85 ? 'emerald' : 'amber'}
              />

              <MetricCard
                title="Candidate Regions Detected"
                value={regions.length}
                unit="anomalies"
                description="Connected components exceeding area and intensity delta thresholds"
                colorScheme="cyan"
              />

              <MetricCard
                title="Pre-Registration RMSE"
                value={regMetrics.rmse}
                unit="px intensity"
                description="Geometric alignment error before differencing"
                colorScheme="emerald"
              />

              <MetricCard
                title="Alignment Confidence"
                value={`${regMetrics.registration_confidence_percentage}%`}
                progress={regMetrics.registration_confidence_percentage}
                description="Quality baseline ensuring valid change isolation"
                colorScheme="cyan"
              />
            </div>
          </div>

          {/* Multi-Tab Visualizer */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Eye className="w-4 h-4 text-emerald-400" />
                Visual Change Overlays & Masks
              </h3>

              {/* View Switcher */}
              <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-lunar-900 border border-lunar-700">
                <button
                  onClick={() => setActiveView('heatmap')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeView === 'heatmap'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Change Heatmap
                </button>
                <button
                  onClick={() => setActiveView('annotated')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeView === 'annotated'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Labeled Bounding Boxes
                </button>
                <button
                  onClick={() => setActiveView('mask')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeView === 'mask'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Binary Change Mask
                </button>
                <button
                  onClick={() => setActiveView('slider')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeView === 'slider'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Split Slider
                </button>
              </div>
            </div>

            {/* Active View Display */}
            {activeView === 'slider' ? (
              <ComparisonSlider
                beforeImage={artifacts?.reference_image}
                afterImage={artifacts?.change_heatmap}
                beforeLabel="Reference Frame (Baseline)"
                afterLabel="Change Heatmap Overlay (JET)"
              />
            ) : activeView === 'heatmap' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultImage
                  title="False-Color Temporal Change Heatmap"
                  subtitle="JET colormap overlay accentuating intensity & SSIM variance"
                  imagePath={artifacts?.change_heatmap}
                  badgeText="Heatmap Overlay"
                  badgeColor="bg-emerald-950 text-emerald-400 border-emerald-800"
                />
                <ResultImage
                  title="Baseline Reference Pass (T1)"
                  subtitle="Post-event reference image"
                  imagePath={artifacts?.reference_image}
                  badgeText="Reference T1"
                />
              </div>
            ) : activeView === 'annotated' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultImage
                  title="Annotated Candidates with Heuristic Labels"
                  subtitle="Bounding boxes colored by morphological heuristic class"
                  imagePath={artifacts?.annotated_visualization}
                  badgeText="Annotated Boxes"
                  badgeColor="bg-cyan-950 text-cyan-400 border-cyan-800"
                />
                <ResultImage
                  title="Binary Change Mask"
                  subtitle="Morphologically cleaned candidate segments"
                  imagePath={artifacts?.change_mask}
                  badgeText="Binary Mask"
                />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultImage
                  title="Binary Change Mask"
                  subtitle="Segmented threshold regions post-opening/closing"
                  imagePath={artifacts?.change_mask}
                  badgeText="Binary Mask"
                />
                <ResultImage
                  title="Warped Earlier Image (T0)"
                  subtitle="Aligned source frame"
                  imagePath={artifacts?.aligned_image}
                  badgeText="Warped T0"
                />
              </div>
            )}
          </div>

          {/* Detected Candidate Regions Table */}
          <div className="glass-panel p-5 sm:p-6 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-white text-base">
                  Detected Candidate Surface Alterations ({regions.length})
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Morphological characterization and explainable heuristic classification
                </p>
              </div>
            </div>

            {regions.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No statistically significant anomalies detected above threshold.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-lunar-800 text-slate-400 uppercase font-mono text-[10px]">
                      <th className="pb-3 px-2">ID</th>
                      <th className="pb-3 px-2">Heuristic Classification</th>
                      <th className="pb-3 px-2">Area (px)</th>
                      <th className="pb-3 px-2">Circularity</th>
                      <th className="pb-3 px-2">Aspect Ratio</th>
                      <th className="pb-3 px-2">Bounding Box [X, Y, W, H]</th>
                      <th className="pb-3 px-2">Scientific Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lunar-800/60 font-mono text-slate-300">
                    {regions.map((reg) => (
                      <tr key={reg.region_id} className="hover:bg-lunar-900/40 transition-colors">
                        <td className="py-3 px-2 font-bold text-cyan-400">#{reg.region_id}</td>
                        <td className="py-3 px-2">
                          <span className={`px-2 py-0.5 rounded-full border text-[11px] font-sans font-semibold ${getLabelColor(reg.label)}`}>
                            {reg.label}
                          </span>
                        </td>
                        <td className="py-3 px-2">{reg.area_pixels}</td>
                        <td className="py-3 px-2">{reg.circularity}</td>
                        <td className="py-3 px-2">{reg.aspect_ratio}</td>
                        <td className="py-3 px-2 text-slate-400">
                          [{reg.bounding_box.x}, {reg.bounding_box.y}, {reg.bounding_box.width}, {reg.bounding_box.height}]
                        </td>
                        <td className="py-3 px-2 text-slate-400 font-sans text-[11px]">
                          Unconfirmed Candidate
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
