import React from 'react';
import {
  LayoutDashboard,
  Layers,
  Cpu,
  BarChart3,
  Satellite,
  ChevronRight,
  ShieldCheck,
  BookOpen,
  Sun
} from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';

export default function Sidebar() {
  const { activeTab, setActiveTab, registrationResult, changeDetectionResult } = usePipeline();

  const navigation = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: LayoutDashboard,
      badge: null,
      description: 'System overview & pipeline'
    },
    {
      id: 'registration',
      name: 'Image Registration',
      icon: Layers,
      badge: registrationResult?.status === 'success' ? 'Active' : null,
      badgeColor: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      description: 'SIFT/ORB & RANSAC Alignment'
    },
    {
      id: 'sun_angle',
      name: 'Sun-Angle Robustness',
      icon: Sun,
      badge: 'New',
      badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      description: 'Illumination & confidence plot'
    },
    {
      id: 'three_sensor',
      name: 'Three-Sensor Analysis',
      icon: Satellite,
      badge: 'Extension',
      badgeColor: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      description: 'OHRC, TMC & IIRS fusion'
    },
    {
      id: 'change_detection',
      name: 'Temporal Change',
      icon: Cpu,
      badge: changeDetectionResult?.status === 'success' ? `${changeDetectionResult.change_metrics?.total_regions_detected || 0} hits` : null,
      badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      description: 'SSIM & crater detection'
    },
    {
      id: 'results',
      name: 'Scientific Results',
      icon: BarChart3,
      badge: (registrationResult || changeDetectionResult) ? 'Ready' : null,
      badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      description: 'Summary, metrics & export'
    },
    {
      id: 'how_it_works',
      name: 'How It Works',
      icon: BookOpen,
      badge: 'Guide',
      badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      description: '8-stage technical pipeline'
    }
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-lunar-950/95 border-r border-lunar-800/80 flex flex-col justify-between select-none">
      <div>
        {/* Navigation Item List */}
        <div className="p-3 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Navigation Menu
          </div>
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-all group ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/50 border border-cyan-500/40 text-white shadow-lg shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-lunar-900/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`p-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                        : 'bg-lunar-900 text-slate-400 group-hover:text-slate-200 border border-lunar-800'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 truncate">
                    <p className={`text-sm font-semibold truncate ${isActive ? 'text-cyan-300' : 'text-slate-200'}`}>
                      {item.name}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">{item.description}</p>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  {item.badge && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                  {isActive && <ChevronRight className="w-4 h-4 text-cyan-400 flex-shrink-0" />}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Telemetry Card */}
      <div className="p-3 border-t border-lunar-800/80">
        <div className="glass-panel p-3 rounded-xl border border-lunar-700/60 bg-lunar-900/40">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>Lunar Orbital Vision</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400 leading-tight">
            Multi-modal sub-pixel spatial registration and anomaly segmentation engine.
          </p>
          <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-lunar-800">
            <span>ISRO / NASA Format</span>
            <span className="font-mono text-cyan-400">v1.0.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
