import React, { useState } from 'react';
import { Moon, ExternalLink, Menu, X } from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';
import { API_BASE_URL } from '../services/api';

const NAV_ITEMS = [
  { label: 'Home',           tab: 'dashboard'        },
  { label: 'About',          tab: 'how_it_works'     },
  { label: 'Registration',   tab: 'registration'     },
  { label: 'Sun Angle',      tab: 'sun_angle'        },
  { label: '3-Sensor',       tab: 'three_sensor'     },
  { label: 'Temporal Change',tab: 'change_detection' },
  { label: 'Results',        tab: 'results'          },
  { label: 'Contact',        tab: null               }, // placeholder
];

export default function Header() {
  const { setActiveTab, backendHealth, activeTab } = usePipeline();
  const isHealthy = backendHealth.status === 'healthy';
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (tab) => {
    if (tab) setActiveTab(tab);
    setMobileOpen(false);
  };

  return (
    <header
      className="w-full sticky top-0 z-50 flex items-center justify-between px-6 sm:px-10 lg:px-12"
      style={{
        height: '58px',
        background: 'rgba(1, 3, 12, 0.92)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        borderBottom: '1px solid rgba(0, 190, 255, 0.10)',
        boxShadow: '0 2px 20px rgba(0,0,0,0.5)',
      }}
    >
      {/* ── BRAND ── */}
      <button
        className="flex items-center gap-2.5 flex-shrink-0 group"
        onClick={() => handleNav('dashboard')}
      >
        {/* Logo icon with cyan glow */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{
            background: 'rgba(0,20,50,0.80)',
            border: '1px solid rgba(0,200,255,0.35)',
            boxShadow: '0 0 10px rgba(0,190,255,0.30), 0 0 20px rgba(0,160,220,0.15)',
          }}
        >
          <Moon className="w-4 h-4" style={{ color: '#00d8f8' }} />
        </div>
        <span
          className="text-[15px] font-bold tracking-tight leading-none"
          style={{ color: '#e8f4ff' }}
        >
          LunarVision
        </span>
      </button>

      {/* ── CENTER NAV (desktop) ── */}
      <nav className="hidden lg:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
        {NAV_ITEMS.map(({ label, tab }) => {
          const isActive = tab && activeTab === tab;
          return (
            <button
              key={label}
              onClick={() => handleNav(tab)}
              disabled={!tab}
              className={`relative pb-1 text-[13px] font-medium transition-colors ${
                !tab
                  ? 'opacity-40 cursor-not-allowed text-slate-400'
                  : isActive
                  ? 'text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {label}
              {isActive && <div className="nav-active-glow" />}
            </button>
          );
        })}
      </nav>

      {/* ── RIGHT: Status + API Docs ── */}
      <div className="flex items-center gap-3 flex-shrink-0">

        {/* Backend status pill */}
        <div
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold tracking-wide"
          style={{
            background: isHealthy ? 'rgba(0,50,20,0.50)' : 'rgba(50,30,0,0.50)',
            border: `1px solid ${isHealthy ? 'rgba(0,210,100,0.40)' : 'rgba(200,120,0,0.40)'}`,
            color:   isHealthy ? '#00e090' : '#f0a030',
          }}
        >
          <span className="relative flex h-2 w-2">
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              style={{ background: isHealthy ? '#00dd88' : '#f0a030' }}
            />
            <span
              className="relative inline-flex rounded-full h-2 w-2"
              style={{ background: isHealthy ? '#00cc80' : '#e09020' }}
            />
          </span>
          {isHealthy ? 'Backend Connected' : 'Connecting…'}
        </div>

        {/* API Docs button */}
        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noreferrer"
          className="hidden sm:inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[12px] font-semibold transition-all"
          style={{
            border: '1px solid rgba(0,200,255,0.35)',
            color: '#b0e8ff',
            background: 'transparent',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(0,180,255,0.10)';
            e.currentTarget.style.borderColor = 'rgba(0,210,255,0.60)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.borderColor = 'rgba(0,200,255,0.35)';
          }}
        >
          API Docs
          <ExternalLink className="w-3.5 h-3.5 opacity-75" />
        </a>

        {/* Mobile menu toggle */}
        <button
          className="lg:hidden text-slate-300 hover:text-white transition-colors"
          onClick={() => setMobileOpen(v => !v)}
          aria-label="Toggle navigation"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* ── MOBILE NAV DRAWER ── */}
      {mobileOpen && (
        <div
          className="lg:hidden absolute top-full left-0 right-0 py-3 px-6 flex flex-col gap-1"
          style={{
            background: 'rgba(1, 3, 12, 0.97)',
            backdropFilter: 'blur(14px)',
            borderBottom: '1px solid rgba(0,190,255,0.12)',
          }}
        >
          {NAV_ITEMS.map(({ label, tab }) => (
            <button
              key={label}
              onClick={() => handleNav(tab)}
              disabled={!tab}
              className={`text-left py-2.5 text-sm font-medium border-b transition-colors ${
                !tab
                  ? 'opacity-40 cursor-not-allowed text-slate-400 border-slate-800'
                  : tab === activeTab
                  ? 'text-cyan-300 border-cyan-900'
                  : 'text-slate-300 hover:text-white border-slate-800/60'
              }`}
            >
              {label}
            </button>
          ))}

          {/* Mobile: Status + API Docs */}
          <div className="flex items-center gap-3 pt-3 pb-1">
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold"
              style={{
                background: isHealthy ? 'rgba(0,50,20,0.50)' : 'rgba(50,30,0,0.50)',
                border: `1px solid ${isHealthy ? 'rgba(0,210,100,0.40)' : 'rgba(200,120,0,0.40)'}`,
                color: isHealthy ? '#00e090' : '#f0a030',
              }}
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-emerald-400" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              {isHealthy ? 'Backend Connected' : 'Connecting…'}
            </div>
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[12px] font-semibold"
              style={{ border: '1px solid rgba(0,200,255,0.35)', color: '#b0e8ff' }}
              onClick={() => setMobileOpen(false)}
            >
              API Docs <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
