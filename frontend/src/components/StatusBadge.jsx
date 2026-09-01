import React from 'react';

export default function StatusBadge({ status, label }) {
  const isHealthy = status === 'healthy' || status === 'online';
  const isChecking = status === 'checking';

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-lunar-900/80 border border-lunar-700/60 shadow-sm text-xs font-medium">
      <span className="relative flex h-2 w-2">
        {isHealthy && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        )}
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            isChecking
              ? 'bg-amber-400 animate-pulse'
              : isHealthy
              ? 'bg-emerald-500'
              : 'bg-rose-500'
          }`}
        ></span>
      </span>
      <span className="text-slate-300">
        {label || (isHealthy ? 'Backend Connected' : isChecking ? 'Checking Backend...' : 'Backend Offline')}
      </span>
    </div>
  );
}
