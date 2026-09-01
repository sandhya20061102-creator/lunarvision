import React, { useState, useEffect } from 'react';
import { Compass, Sparkles, Orbit, Radio } from 'lucide-react';

export default function LoadingState({
  title = 'Processing Lunar Imagery...',
  subtitle = 'Executing sub-pixel computer vision alignment pipeline',
  steps = [
    'Applying CLAHE contrast equalization...',
    'Extracting SIFT/ORB keypoint descriptors...',
    'Matching correspondences via BFMatcher...',
    'Computing RANSAC perspective Homography...',
    'Evaluating RMSE and alignment confidence...',
  ],
}) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % steps.length);
    }, 1400);
    return () => clearInterval(interval);
  }, [steps.length]);

  return (
    <div className="glass-panel rounded-2xl p-8 sm:p-12 border border-cyan-500/40 bg-lunar-900/50 flex flex-col items-center justify-center text-center relative overflow-hidden">
      {/* Background glowing orb */}
      <div className="absolute w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none animate-pulse"></div>

      {/* Radar scanning graphic */}
      <div className="relative w-28 h-28 mb-6 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border border-cyan-500/30 animate-ping opacity-40"></div>
        <div className="absolute inset-2 rounded-full border border-dashed border-cyan-400/50 animate-spin" style={{ animationDuration: '8s' }}></div>
        <div className="absolute inset-6 rounded-full border border-blue-500/40 animate-pulse"></div>
        <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
          <Radio className="w-6 h-6 text-slate-950 animate-bounce" />
        </div>
      </div>

      <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
        {title}
      </h3>
      <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-md">
        {subtitle}
      </p>

      {/* Dynamic Step Indicator */}
      <div className="mt-6 px-4 py-2 rounded-full bg-lunar-950/80 border border-cyan-500/30 inline-flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
        <span className="font-mono text-xs text-cyan-300 transition-all">
          {steps[currentStepIndex]}
        </span>
      </div>
    </div>
  );
}
