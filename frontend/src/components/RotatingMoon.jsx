import React from 'react';

export default function RotatingMoon() {
  return (
    <div className="relative flex items-center justify-center w-full h-full">

      {/* ── Ambient radial glow behind the Moon ── */}
      <div
        className="absolute rounded-full pointer-events-none bg-pulse"
        style={{
          width: '70%',
          height: '70%',
          background: 'radial-gradient(circle, rgba(0,160,255,0.18) 0%, rgba(0,80,180,0.10) 40%, transparent 70%)',
          filter: 'blur(30px)',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      />

      {/* ── Outermost orbital ring ── */}
      <div className="orbit-ring orbit-ring-4 absolute" />

      {/* ── Ring 1: large, solid thin cyan ── */}
      <div className="orbit-ring orbit-ring-1 absolute" />

      {/* ── Ring 2: medium, dashed electric blue ── */}
      <div className="orbit-ring orbit-ring-2 absolute" />

      {/* ── Ring 3: small inner, brighter cyan ── */}
      <div className="orbit-ring orbit-ring-3 absolute" />

      {/* ── Orbital particles moving along ring paths ── */}
      <div className="orbital-particle particle-1 absolute" />
      <div className="orbital-particle particle-sm particle-2 absolute" style={{
        width: '4px', height: '4px',
        background: 'radial-gradient(circle, #80f8ff 0%, rgba(0,220,255,0.4) 60%, transparent 100%)',
        boxShadow: '0 0 6px #80f8ff, 0 0 12px rgba(0,200,255,0.3)',
      }} />
      <div className="orbital-particle particle-3 absolute" />
      <div className="orbital-particle particle-4 absolute" style={{
        width: '4px', height: '4px',
        background: 'radial-gradient(circle, #b0f8ff 0%, rgba(0,210,255,0.3) 60%, transparent 100%)',
        boxShadow: '0 0 5px #b0f8ff',
      }} />

      {/* ── The Moon — floating + very slow rotation ── */}
      <div
        className="relative z-10 animate-moon-float"
        style={{
          width: 'min(62%, 420px)',
          height: 'min(62%, 420px)',
        }}
      >
        {/* Outer atmosphere glow */}
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            inset: '-12%',
            background: 'radial-gradient(circle, rgba(0,190,255,0.12) 0%, rgba(0,120,200,0.08) 40%, transparent 70%)',
            filter: 'blur(18px)',
          }}
        />
        {/* Inner subtle cyan rim light */}
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            inset: '-4%',
            boxShadow: '0 0 40px rgba(0,200,255,0.25), 0 0 80px rgba(0,150,220,0.12)',
            borderRadius: '50%',
          }}
        />

        <img
          src="/assets/moon.png"
          alt="Lunar surface — Chandrayaan-2 imagery"
          className="w-full h-full object-cover rounded-full animate-moon-rotate"
          style={{
            filter: 'brightness(0.92) contrast(1.05) saturate(0.85)',
            boxShadow:
              '0 0 50px rgba(0,190,255,0.30), 0 0 100px rgba(0,140,220,0.15), 0 0 160px rgba(0,80,180,0.10)',
          }}
          draggable={false}
        />
      </div>
    </div>
  );
}
