import React, { useState, useRef, useCallback } from 'react';
import { Sliders, MoveHorizontal } from 'lucide-react';
import { getArtifactUrl } from '../services/api';

export default function ComparisonSlider({
  beforeImage,
  afterImage,
  beforeLabel = 'Reference Image (Baseline)',
  afterLabel = 'Aligned Source (Registered)',
}) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const beforeUrl = getArtifactUrl(beforeImage);
  const afterUrl = getArtifactUrl(afterImage);

  const handleMove = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  }, []);

  const handleTouchMove = (e) => {
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-lunar-700/60 bg-lunar-900/40">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <h3 className="font-semibold text-white text-sm sm:text-base">
            Interactive Split-View Comparator
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-cyan-400 font-medium">◄ {beforeLabel}</span>
          <span className="text-slate-400">|</span>
          <span className="text-indigo-400 font-medium">{afterLabel} ►</span>
        </div>
      </div>

      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onTouchMove={handleTouchMove}
        className="relative w-full aspect-video rounded-xl overflow-hidden select-none border border-lunar-800 bg-black/80 cursor-ew-resize"
      >
        {/* After Image (Background full width) */}
        {afterUrl && (
          <img
            src={afterUrl}
            alt={afterLabel}
            className="absolute inset-0 w-full h-full object-contain pointer-events-none"
          />
        )}

        {/* Before Image (Clipped overlay) */}
        {beforeUrl && (
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
          >
            <img
              src={beforeUrl}
              alt={beforeLabel}
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />
          </div>
        )}

        {/* Draggable Vertical Divider Line */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-cyan-400 cursor-ew-resize flex items-center justify-center shadow-[0_0_10px_rgba(0,242,254,0.7)]"
          style={{ left: `${sliderPosition}%` }}
          onMouseDown={handleMouseDown}
        >
          <div className="w-8 h-8 rounded-full bg-cyan-500 border-2 border-white text-black flex items-center justify-center shadow-xl">
            <MoveHorizontal className="w-4 h-4 text-slate-950 font-bold" />
          </div>
        </div>

        {/* Labels pinned to bottom corners */}
        <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-black/70 backdrop-blur-sm border border-cyan-500/40 text-[11px] font-semibold text-cyan-300 pointer-events-none">
          {beforeLabel}
        </div>
        <div className="absolute bottom-3 right-3 px-2 py-1 rounded bg-black/70 backdrop-blur-sm border border-indigo-500/40 text-[11px] font-semibold text-indigo-300 pointer-events-none">
          {afterLabel}
        </div>
      </div>
    </div>
  );
}
