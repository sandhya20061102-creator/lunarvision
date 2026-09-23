import React from 'react';
import { Activity, HelpCircle } from 'lucide-react';

export default function MetricCard({
  title,
  value,
  unit = '',
  description,
  icon: Icon = Activity,
  progress = null, // value from 0 to 100
  statusBadge = null,
  colorScheme = 'cyan', // 'cyan', 'emerald', 'indigo', 'amber'
}) {
  const colorMap = {
    cyan: {
      border: 'border-cyan-500/30',
      bgGlow: 'from-cyan-500/10 to-blue-500/5',
      iconColor: 'text-cyan-400',
      iconBg: 'bg-cyan-500/20 border-cyan-500/30',
      progressBar: 'bg-cyan-400',
    },
    emerald: {
      border: 'border-emerald-500/30',
      bgGlow: 'from-emerald-500/10 to-teal-500/5',
      iconColor: 'text-emerald-400',
      iconBg: 'bg-emerald-500/20 border-emerald-500/30',
      progressBar: 'bg-emerald-400',
    },
    indigo: {
      border: 'border-indigo-500/30',
      bgGlow: 'from-indigo-500/10 to-cyan-500/5',
      iconColor: 'text-indigo-400',
      iconBg: 'bg-indigo-500/20 border-indigo-500/30',
      progressBar: 'bg-indigo-400',
    },
    amber: {
      border: 'border-amber-500/30',
      bgGlow: 'from-amber-500/10 to-orange-500/5',
      iconColor: 'text-amber-400',
      iconBg: 'bg-amber-500/20 border-amber-500/30',
      progressBar: 'bg-amber-400',
    },
  };

  const scheme = colorMap[colorScheme] || colorMap.cyan;

  return (
    <div className={`glass-panel p-4 sm:p-5 rounded-xl border ${scheme.border} bg-gradient-to-br ${scheme.bgGlow} relative overflow-hidden flex flex-col justify-between`}>
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
            {title}
          </span>
          <div className={`p-2 rounded-lg border ${scheme.iconBg} ${scheme.iconColor}`}>
            <Icon className="w-4 h-4" />
          </div>
        </div>

        <div className="flex items-baseline gap-1.5 mt-1">
          <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">
            {value ?? '--'}
          </span>
          {unit && <span className="text-sm font-semibold text-slate-400">{unit}</span>}
        </div>

        {description && (
          <p className="mt-1.5 text-xs text-slate-400 leading-snug">
            {description}
          </p>
        )}
      </div>

      {/* Optional Progress Bar or Status Badge */}
      <div className="mt-4 pt-3 border-t border-lunar-800/80">
        {progress !== null ? (
          <div>
            <div className="flex justify-between text-[11px] text-slate-400 mb-1 font-mono">
              <span>Confidence Level</span>
              <span className="font-semibold text-white">{progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-lunar-950 rounded-full overflow-hidden border border-lunar-800">
              <div
                className={`h-full ${scheme.progressBar} rounded-full transition-all duration-500`}
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              ></div>
            </div>
          </div>
        ) : statusBadge ? (
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Classification</span>
            <span className="font-semibold px-2 py-0.5 rounded bg-lunar-900 border border-lunar-700 text-slate-200">
              {statusBadge}
            </span>
          </div>
        ) : (
          <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
            <span>Validated Telemetry</span>
          </div>
        )}
      </div>
    </div>
  );
}
