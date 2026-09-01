import React from 'react';
import {
  Layers,
  Sparkles,
  Cpu,
  BarChart3,
  Satellite,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Zap,
  Clock,
  Compass
} from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import PipelineVisualizer from '../components/PipelineVisualizer';

export default function Dashboard() {
  const { setActiveTab, backendHealth, registrationResult, changeDetectionResult } = usePipeline();

  const isHealthy = backendHealth.status === 'healthy';

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Hero Welcome Banner */}
      <div className="glass-panel rounded-3xl p-6 sm:p-10 relative overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-lunar-900/90 via-lunar-950 to-lunar-900/80 shadow-2xl">
        {/* Glow circles */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 text-xs font-semibold mb-4 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
            Full-Stack Planetary Vision System
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            LunarVision
          </h1>
          <p className="text-lg sm:text-xl font-medium text-cyan-300/90 mt-1">
            Multi-Modal Lunar Image Correspondence and Temporal Change Detection
          </p>

          <p className="mt-4 text-slate-300 text-sm sm:text-base leading-relaxed max-w-3xl">
            LunarVision is an end-to-end computer vision platform engineered for planetary surface exploration.
            It performs sub-pixel image registration on temporal orbital imagery, normalizes solar illumination, computes RANSAC homography transformations, and identifies surface alterations such as new impact craters, boulder displacements, and regolith disturbances.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <button
              onClick={() => setActiveTab('registration')}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/25 flex items-center gap-2 transition-all hover:scale-[1.02]"
            >
              <Layers className="w-4 h-4" /> Start Image Registration
            </button>
            <button
              onClick={() => setActiveTab('change_detection')}
              className="px-6 py-3 rounded-xl bg-lunar-900/90 hover:bg-lunar-800 text-slate-200 hover:text-white border border-lunar-700 font-semibold text-sm flex items-center gap-2 transition-all hover:scale-[1.02]"
            >
              <Cpu className="w-4 h-4" /> Detect Temporal Changes
            </button>
          </div>
        </div>
      </div>

      {/* System Status Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Backend Server</span>
            <div className={`p-2 rounded-lg ${isHealthy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-xl font-bold text-white">
            {isHealthy ? 'FastAPI 0.141 Online' : 'Connecting...'}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {isHealthy ? 'Port 8000 (CORS Enabled)' : 'Verifying local endpoint'}
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Vision Stack</span>
            <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-xl font-bold text-white">
            OpenCV {backendHealth.data?.opencv_version || '4.13.0'}
          </p>
          <p className="mt-1 text-xs text-slate-400">SIFT, AKAZE & RANSAC</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Science Metrics</span>
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <Compass className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-xl font-bold text-white">
            scikit-image {backendHealth.data?.skimage_version || '0.26.0'}
          </p>
          <p className="mt-1 text-xs text-slate-400">SSIM & Intensity Differencing</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Session Status</span>
            <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-xl font-bold text-white">
            {registrationResult ? 'Active Registration' : 'Ready for Ingestion'}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {changeDetectionResult ? `${changeDetectionResult.change_metrics?.total_regions_detected} anomalies detected` : 'No pipeline errors'}
          </p>
        </div>
      </div>

      {/* Pipeline Architecture Diagram */}
      <PipelineVisualizer currentStage={registrationResult ? (changeDetectionResult ? 'completed' : 5) : null} />

      {/* Quick Launch Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          Primary Operational Modules
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1 */}
          <div
            onClick={() => setActiveTab('registration')}
            className="glass-panel p-6 rounded-2xl border border-lunar-700/60 hover:border-cyan-500/60 bg-lunar-900/30 cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-cyan-950/40 group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 w-fit mb-4 group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                1. Image Registration
              </h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Upload baseline and temporal secondary images. The system extracts SIFT/AKAZE keypoints, matches descriptors using Lowe's ratio test, and computes perspective homography via RANSAC.
              </p>
            </div>
            <div className="mt-6 flex items-center justify-between text-xs text-cyan-400 font-semibold group-hover:translate-x-1 transition-transform">
              <span>Open Registration Module</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </div>

          {/* Card 2 */}
          <div
            onClick={() => setActiveTab('three_sensor')}
            className="glass-panel p-6 rounded-2xl border border-lunar-700/60 hover:border-purple-500/60 bg-lunar-900/30 cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-purple-950/40 group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30 w-fit mb-4 group-hover:scale-110 transition-transform">
                <Satellite className="w-6 h-6" />
              </div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors">
                  2. Three-Sensor Analysis
                </h3>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800">
                  Extension
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Multi-sensor fusion framework designed for OHRC (High-Res Optical), TMC (Terrain Stereo Mapping), and IIRS (Hyperspectral Mineralogy) cross-modal correspondence.
              </p>
            </div>
            <div className="mt-6 flex items-center justify-between text-xs text-purple-400 font-semibold group-hover:translate-x-1 transition-transform">
              <span>Explore Sensor Architecture</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </div>

          {/* Card 3 */}
          <div
            onClick={() => setActiveTab('change_detection')}
            className="glass-panel p-6 rounded-2xl border border-lunar-700/60 hover:border-emerald-500/60 bg-lunar-900/30 cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-emerald-950/40 group flex flex-col justify-between"
          >
            <div>
              <div className="p-3 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 w-fit mb-4 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                3. Temporal Change Detection
              </h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                SSIM dissimilarity, illumination compensation, and connected component analysis to isolate and label candidate surface variations into explainable morphological classes.
              </p>
            </div>
            <div className="mt-6 flex items-center justify-between text-xs text-emerald-400 font-semibold group-hover:translate-x-1 transition-transform">
              <span>Detect Surface Alterations</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
