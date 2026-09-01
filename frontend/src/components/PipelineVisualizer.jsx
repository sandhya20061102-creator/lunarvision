import React from 'react';
import {
  SlidersHorizontal,
  Sparkles,
  GitCompare,
  Layers,
  Activity,
  Cpu,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

export default function PipelineVisualizer({ currentStage = null }) {
  const stages = [
    { id: 1, name: 'CLAHE & Prep', icon: SlidersHorizontal, desc: 'Contrast & Normalization' },
    { id: 2, name: 'SIFT / AKAZE', icon: Sparkles, desc: 'Keypoint Extraction' },
    { id: 3, name: 'BF + Ratio Test', icon: GitCompare, desc: 'Lowe’s Correspondence' },
    { id: 4, name: 'RANSAC Warp', icon: Layers, desc: 'Perspective Homography' },
    { id: 5, name: 'RMSE & Metrics', icon: Activity, desc: 'Quality Confidence' },
    { id: 6, name: 'SSIM & Heatmap', icon: Cpu, desc: 'Temporal Alteration' },
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/30">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-white text-sm sm:text-base flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            Orbital Computer Vision Pipeline Architecture
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Sequential multi-stage geometric alignment and anomaly segmentation flow
          </p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-lunar-950 border border-lunar-800 text-cyan-400">
          6 Active Modules
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone = currentStage === 'completed' || (typeof currentStage === 'number' && currentStage >= stage.id);
          const isCurrent = typeof currentStage === 'number' && currentStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border transition-all flex flex-col justify-between ${
                isCurrent
                  ? 'bg-cyan-950/60 border-cyan-500/60 shadow-md shadow-cyan-500/20'
                  : isDone
                  ? 'bg-lunar-900/80 border-emerald-500/40'
                  : 'bg-lunar-950/60 border-lunar-800/80 opacity-90'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    STAGE 0{stage.id}
                  </span>
                  {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-lunar-700"></span>
                  )}
                </div>

                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`p-1.5 rounded-lg ${isCurrent ? 'bg-cyan-500/20 text-cyan-400' : 'bg-lunar-800 text-slate-300'}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <h4 className="text-xs font-semibold text-white truncate">{stage.name}</h4>
                </div>

                <p className="text-[10px] text-slate-400 leading-tight">{stage.desc}</p>
              </div>

              {idx < stages.length - 1 && (
                <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                  {/* Visual connector */}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
