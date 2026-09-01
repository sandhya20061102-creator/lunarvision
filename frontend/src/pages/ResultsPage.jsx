import React from 'react';
import {
  BarChart3,
  Download,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Cpu,
  Activity,
  FileJson,
  ArrowRight,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import MetricCard from '../components/MetricCard';
import DownloadButton from '../components/DownloadButton';

export default function ResultsPage() {
  const { registrationResult, changeDetectionResult, setActiveTab } = usePipeline();

  const hasRegistration = registrationResult?.status === 'success';
  const hasChange = changeDetectionResult?.status === 'success';

  const regMetrics = registrationResult?.metrics;
  const changeMetrics = changeDetectionResult?.change_metrics;
  const regions = changeDetectionResult?.detected_regions || [];

  const handleExportJson = () => {
    const reportData = {
      title: 'LunarVision Scientific Pipeline Execution Report',
      timestamp: new Date().toISOString(),
      registration_summary: registrationResult || 'Not executed in this session',
      change_detection_summary: changeDetectionResult || 'Not executed in this session',
    };

    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(reportData, null, 2));
    const a = document.createElement('a');
    a.href = dataStr;
    a.download = `lunarvision_scientific_report_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (!hasRegistration && !hasChange) {
    return (
      <div className="glass-panel p-12 rounded-3xl border border-lunar-700/60 bg-lunar-900/30 text-center max-w-2xl mx-auto my-12 animate-fadeIn">
        <div className="p-4 rounded-2xl bg-lunar-800/80 text-cyan-400 border border-lunar-700 w-fit mx-auto mb-4">
          <BarChart3 className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">No Scientific Results Available Yet</h2>
        <p className="mt-2 text-xs sm:text-sm text-slate-400 leading-relaxed">
          Run an Image Registration or Temporal Change Detection session to generate telemetry metrics, transformation matrices, and visual artifacts.
        </p>

        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={() => setActiveTab('registration')}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-md flex items-center gap-1.5"
          >
            <Layers className="w-3.5 h-3.5" /> Start Registration
          </button>
          <button
            onClick={() => setActiveTab('change_detection')}
            className="px-4 py-2 rounded-xl bg-lunar-900 hover:bg-lunar-800 border border-lunar-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5"
          >
            <Cpu className="w-3.5 h-3.5" /> Start Change Detection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-800 text-amber-400 text-xs font-semibold mb-2">
            <BarChart3 className="w-3.5 h-3.5" />
            Consolidated Results Dashboard
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Scientific Analysis & Export Center
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Review synthesized quantitative alignment metrics, anomaly segmentation statistics, and export all generated visual artifacts.
          </p>
        </div>

        <button
          onClick={handleExportJson}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-amber-500/20 flex items-center gap-2"
        >
          <FileJson className="w-4 h-4" /> Export Scientific JSON Report
        </button>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {hasRegistration && (
          <>
            <MetricCard
              title="Registration RMSE"
              value={regMetrics.rmse}
              unit="px"
              description="Alignment Root Mean Square Error"
              colorScheme="emerald"
            />
            <MetricCard
              title="RANSAC Inliers"
              value={regMetrics.inlier_count}
              unit={`/ ${regMetrics.total_good_matches}`}
              description="Verified geometric point pairs"
              colorScheme="cyan"
            />
            <MetricCard
              title="Registration Confidence"
              value={`${regMetrics.registration_confidence_percentage}%`}
              progress={regMetrics.registration_confidence_percentage}
              description="Algorithmic stability confidence"
              colorScheme="cyan"
            />
          </>
        )}

        {hasChange && (
          <MetricCard
            title="SSIM Structural Score"
            value={changeMetrics.mean_ssim}
            description="Mean SSIM over overlapping frame"
            colorScheme="indigo"
          />
        )}
      </div>

      {/* Artifact Download Hub */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-lunar-700/60 bg-lunar-900/30">
        <h3 className="text-base sm:text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Download className="w-5 h-5 text-cyan-400" />
          Planetary Artifact Export Hub
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Download high-resolution registered imagery, heatmaps, binary masks, and telemetry packages.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Registered Image */}
          {registrationResult?.artifacts?.aligned_image && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                  Registration Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">Warped / Registered Source</h4>
                <p className="text-xs text-slate-400 mt-1">Aligned onto reference coordinate system.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={registrationResult.artifacts.aligned_image}
                  filename="lunar_registered_source.png"
                  label="Download Aligned Frame"
                  size="sm"
                />
              </div>
            </div>
          )}

          {/* Overlay Comparison */}
          {registrationResult?.artifacts?.overlay_comparison && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                  Comparison Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">Alpha-Blended Overlay</h4>
                <p className="text-xs text-slate-400 mt-1">50/50 transparency blend of reference and aligned source.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={registrationResult.artifacts.overlay_comparison}
                  filename="lunar_overlay_blend.png"
                  label="Download Overlay"
                  variant="outline"
                  size="sm"
                />
              </div>
            </div>
          )}

          {/* Inlier Matches */}
          {registrationResult?.artifacts?.inlier_matches && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                  Diagnostics Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">RANSAC Inlier Matches</h4>
                <p className="text-xs text-slate-400 mt-1">Keypoint correspondence lines verified by RANSAC.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={registrationResult.artifacts.inlier_matches}
                  filename="lunar_inlier_matches.png"
                  label="Download Inliers"
                  variant="outline"
                  size="sm"
                />
              </div>
            </div>
          )}

          {/* Change Heatmap */}
          {changeDetectionResult?.artifacts?.change_heatmap && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                  Change Detection Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">Temporal Change Heatmap</h4>
                <p className="text-xs text-slate-400 mt-1">JET colormap overlay accentuating surface variance.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={changeDetectionResult.artifacts.change_heatmap}
                  filename="lunar_change_heatmap.png"
                  label="Download Heatmap"
                  size="sm"
                />
              </div>
            </div>
          )}

          {/* Binary Mask */}
          {changeDetectionResult?.artifacts?.change_mask && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-teal-400 uppercase tracking-wider">
                  Segmentation Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">Binary Change Mask</h4>
                <p className="text-xs text-slate-400 mt-1">Thresholded & morphologically filtered binary raster.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={changeDetectionResult.artifacts.change_mask}
                  filename="lunar_change_mask.png"
                  label="Download Binary Mask"
                  variant="outline"
                  size="sm"
                />
              </div>
            </div>
          )}

          {/* Annotated Changes */}
          {changeDetectionResult?.artifacts?.annotated_visualization && (
            <div className="glass-panel p-4 rounded-xl border border-lunar-800 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">
                  Heuristic Output
                </span>
                <h4 className="text-sm font-bold text-white mt-1">Annotated Candidates</h4>
                <p className="text-xs text-slate-400 mt-1">Bounding boxes labeled by morphological category.</p>
              </div>
              <div className="mt-4 pt-3 border-t border-lunar-800">
                <DownloadButton
                  filePath={changeDetectionResult.artifacts.annotated_visualization}
                  filename="lunar_annotated_regions.png"
                  label="Download Annotated View"
                  variant="outline"
                  size="sm"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
