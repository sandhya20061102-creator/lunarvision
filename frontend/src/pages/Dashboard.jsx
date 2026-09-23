import React from 'react';
import { Target, Clock, Layers, Globe, Upload, Sparkles } from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import RotatingMoon from '../components/RotatingMoon';

/* ──────────────────────────────────────────────────────────
   Static star positions — avoids re-renders
────────────────────────────────────────────────────────── */
const STARS = [
  { top: '7%',  left: '5%',  size: 2,   cls: 'twinkle-1' },
  { top: '14%', left: '22%', size: 1.5, cls: 'twinkle-3' },
  { top: '4%',  left: '40%', size: 1,   cls: 'twinkle-2' },
  { top: '9%',  left: '58%', size: 2,   cls: 'twinkle-4' },
  { top: '3%',  left: '75%', size: 1.5, cls: 'twinkle-1' },
  { top: '18%', left: '88%', size: 1,   cls: 'twinkle-5' },
  { top: '25%', left: '12%', size: 1.5, cls: 'twinkle-2' },
  { top: '35%', left: '3%',  size: 1,   cls: 'twinkle-4' },
  { top: '45%', left: '92%', size: 2,   cls: 'twinkle-3' },
  { top: '55%', left: '7%',  size: 1,   cls: 'twinkle-5' },
  { top: '62%', left: '18%', size: 1.5, cls: 'twinkle-1' },
  { top: '72%', left: '82%', size: 1,   cls: 'twinkle-2' },
  { top: '80%', left: '95%', size: 2,   cls: 'twinkle-4' },
  { top: '88%', left: '35%', size: 1,   cls: 'twinkle-3' },
  { top: '92%', left: '50%', size: 1.5, cls: 'twinkle-5' },
  { top: '30%', left: '48%', size: 1,   cls: 'twinkle-1' },
  { top: '50%', left: '55%', size: 1.5, cls: 'twinkle-3' },
  { top: '20%', left: '70%', size: 1,   cls: 'twinkle-2' },
  { top: '65%', left: '62%', size: 2,   cls: 'twinkle-4' },
  { top: '78%', left: '45%', size: 1,   cls: 'twinkle-1' },
];

/* ──────────────────────────────────────────────────────────
   Feature strip cards matching the reference
────────────────────────────────────────────────────────── */
const FEATURES = [
  {
    tab:      'registration',
    Icon:     Target,
    title:    'Image Registration',
    subtitle: 'Sub-pixel alignment',
  },
  {
    tab:      'change_detection',
    Icon:     Clock,
    title:    'Temporal Change Detection',
    subtitle: 'Track surface alterations',
  },
  {
    tab:      'three_sensor',
    Icon:     Layers,
    title:    'Multi-Sensor Analysis',
    subtitle: 'Cross-payload correspondence',
  },
  {
    tab:      'sun_angle',
    Icon:     Globe,
    title:    'Geospatial Footprint',
    subtitle: 'Location & coverage mapping',
  },
];

export default function Dashboard() {
  const { setActiveTab } = usePipeline();

  return (
    <div className="w-full relative overflow-hidden min-h-screen flex flex-col animate-fadeIn">

      {/* ══════════════════════════════════════════════
          BACKGROUND LAYER
      ══════════════════════════════════════════════ */}
      <div className="absolute inset-0 pointer-events-none z-0">

        {/* Deep-space blue radial behind the Moon (right side) */}
        <div
          className="absolute bg-pulse"
          style={{
            top: '5%', right: '-8%',
            width: '62%', height: '88%',
            background:
              'radial-gradient(ellipse at center, rgba(0,60,140,0.30) 0%, rgba(0,20,70,0.15) 45%, transparent 70%)',
            filter: 'blur(40px)',
            borderRadius: '50%',
          }}
        />

        {/* Subtle left-side glow for hero text area */}
        <div
          className="absolute"
          style={{
            top: '15%', left: '-5%',
            width: '40%', height: '50%',
            background:
              'radial-gradient(ellipse at center, rgba(0,130,200,0.08) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />

        {/* Top-left diagonal light streak */}
        <div
          className="absolute light-streak"
          style={{
            top: '15%', left: '0',
            width: '35%', height: '1px',
            background:
              'linear-gradient(90deg, transparent, rgba(0,200,255,0.35), transparent)',
          }}
        />
        {/* Second streak */}
        <div
          className="absolute light-streak-2"
          style={{
            top: '8%', left: '0',
            width: '25%', height: '1px',
            background:
              'linear-gradient(90deg, transparent, rgba(0,160,255,0.20), transparent)',
          }}
        />

        {/* Animated twinkling stars */}
        {STARS.map((s, i) => (
          <div
            key={i}
            className={`absolute rounded-full ${s.cls}`}
            style={{
              top: s.top,
              left: s.left,
              width:  `${s.size}px`,
              height: `${s.size}px`,
              background:
                s.size >= 2
                  ? 'radial-gradient(circle, #ffffff 0%, rgba(180,230,255,0.6) 60%, transparent 100%)'
                  : 'rgba(200,230,255,0.85)',
              boxShadow: s.size >= 2 ? '0 0 4px rgba(200,230,255,0.6)' : 'none',
            }}
          />
        ))}
      </div>

      {/* ══════════════════════════════════════════════
          HERO — two-column layout
      ══════════════════════════════════════════════ */}
      <div className="relative z-10 flex-1 flex flex-col">
        <div className="flex-1 flex flex-col lg:flex-row items-center justify-between px-8 sm:px-12 lg:px-16 pt-10 pb-4 max-w-[1600px] mx-auto w-full gap-8 lg:gap-0">

          {/* ── LEFT: Hero copy & CTAs ── */}
          <div className="w-full lg:w-[48%] flex flex-col gap-7 z-20">

            {/* Eyebrow */}
            <div className="flex items-center gap-3">
              <span className="block w-8 h-[1.5px] bg-cyan-400" style={{ boxShadow: '0 0 6px rgba(0,220,255,0.7)' }} />
              <span
                className="text-[11px] sm:text-xs font-bold uppercase tracking-[0.22em]"
                style={{ color: '#00d8f8' }}
              >
                Multi-Modal Lunar Image Correspondence
              </span>
            </div>

            {/* Main title */}
            <div>
              <h1 className="text-[4rem] sm:text-[5rem] lg:text-[5.8rem] font-extrabold leading-[0.95] tracking-tight">
                <span style={{ color: '#f0f8ff' }}>Lunar</span>
                <span className="glow-text-cyan">Vision</span>
              </h1>
            </div>

            {/* Subtitle */}
            <h2
              className="text-xl sm:text-2xl lg:text-2xl font-light leading-relaxed"
              style={{ color: '#c8dff0' }}
            >
              Match. Register.{' '}
              <span className="font-bold" style={{ color: '#f0f8ff' }}>
                Understand the Moon.
              </span>
            </h2>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-1">
              <button
                onClick={() => setActiveTab('registration')}
                className="btn-primary-lunar px-7 py-3.5 rounded-full font-bold text-sm flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload Images
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className="btn-secondary-lunar px-7 py-3.5 rounded-full font-semibold text-sm flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4 text-cyan-300" />
                Explore Results
              </button>
            </div>

            {/* Mission status strip */}
            <div className="inline-flex items-center gap-2.5 mission-strip px-5 py-2.5 rounded-full self-start">
              <span className="relative flex h-2 w-2 flex-shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-[11px] font-mono tracking-wide" style={{ color: '#a0d8ef' }}>
                Chandrayaan-2
                <span className="opacity-40 mx-1">/</span>
                OHRC
                <span className="opacity-40 mx-1">/</span>
                TMC
                <span className="opacity-40 mx-1">/</span>
                IIRS
                <span className="opacity-40 mx-1">/</span>
                <span style={{ color: '#00e5a0' }}>System Online</span>
              </span>
            </div>
          </div>

          {/* ── RIGHT: Moon visual ── */}
          <div
            className="w-full lg:w-[52%] flex items-center justify-center z-10"
            style={{ height: 'clamp(340px, 55vw, 620px)' }}
          >
            <RotatingMoon />
          </div>
        </div>

        {/* ══════════════════════════════════════════════
            FEATURE CARD STRIP
        ══════════════════════════════════════════════ */}
        <div className="relative z-20 w-full px-6 sm:px-10 lg:px-14 pb-10 max-w-[1600px] mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map(({ tab, Icon, title, subtitle }) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="feature-strip-card rounded-xl px-5 py-4 flex items-center gap-4 text-left group cursor-pointer"
              >
                {/* Icon */}
                <div className="feature-icon-glow w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon className="w-5 h-5" style={{ color: '#00d4f8' }} />
                </div>

                {/* Text */}
                <div className="min-w-0">
                  <p
                    className="text-sm font-semibold leading-tight mb-0.5 group-hover:text-cyan-300 transition-colors"
                    style={{ color: '#e0f0ff' }}
                  >
                    {title}
                  </p>
                  <p className="text-xs leading-tight" style={{ color: '#6a90b0' }}>
                    {subtitle}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
