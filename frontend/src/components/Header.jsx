import React from 'react';
import { Moon, Sparkles, RefreshCw, ExternalLink, Activity, Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import { API_BASE_URL } from '../services/api';

export default function Header() {
  const { backendHealth, refreshHealth } = usePipeline();
  const isHealthy = backendHealth.status === 'healthy';
  const isChecking = backendHealth.status === 'checking';

  return (
    <header className="border-b border-lunar-800/90 bg-lunar-950/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand logo & tagline */}
        <div className="flex items-center gap-3">
          <div className="relative p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-purple-600/10 border border-cyan-500/40 shadow-lg shadow-cyan-500/10">
            <Moon className="w-6 h-6 text-cyan-400" />
            <Sparkles className="w-3.5 h-3.5 text-blue-300 absolute top-1 right-1 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                LunarVision <span className="text-cyan-400 font-mono text-xs font-normal">CV</span>
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                Scientific Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Multi-Modal Lunar Image Correspondence & Temporal Change Detection
            </p>
          </div>
        </div>

        {/* Status controls & telemetry */}
        <div className="flex items-center gap-3">
          {/* Backend Diagnostics Badge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-lunar-900/80 border border-lunar-800 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            {isHealthy ? (
              <span className="font-mono text-[11px] text-slate-300">
                OpenCV {backendHealth.data?.opencv_version} • skimage {backendHealth.data?.skimage_version}
              </span>
            ) : (
              <span className="text-[11px] text-slate-400">FastAPI Port 8000</span>
            )}
          </div>

          {/* Live Connectivity Badge */}
          <div
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border shadow-sm text-xs font-medium transition-all ${
              isHealthy
                ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                : isChecking
                ? 'bg-amber-950/40 border-amber-800/60 text-amber-300'
                : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
            }`}
          >
            <span className="relative flex h-2 w-2">
              {isHealthy && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isChecking ? 'bg-amber-400 animate-pulse' : isHealthy ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              ></span>
            </span>
            <span>{isHealthy ? 'Backend Connected' : isChecking ? 'Connecting...' : 'Backend Offline'}</span>
          </div>

          {/* Refresh Health Button */}
          <button
            onClick={refreshHealth}
            title="Refresh Backend Health Status"
            className="p-2 rounded-lg bg-lunar-900/80 hover:bg-lunar-800 border border-lunar-700/80 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {/* Swagger Docs Link */}
          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-lunar-900/80 hover:bg-lunar-800 border border-lunar-700/80 text-xs font-medium text-slate-300 hover:text-cyan-400 transition-colors"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        </div>
      </div>
    </header>
  );
}
