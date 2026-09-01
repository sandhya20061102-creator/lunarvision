import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, ChevronDown, ChevronUp, Info, HelpCircle } from 'lucide-react';

export default function ErrorMessage({
  title = 'No Reliable Match Detected',
  reason,
  details = null,
  recommendations = [
    'Ensure both images cover overlapping surface coordinates.',
    'Check that lunar imagery has sufficient contrast and distinguishable crater morphology.',
    'Verify that images are not severely blurred, dark, or saturated.',
  ],
}) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-amber-500/50 bg-gradient-to-br from-amber-950/30 to-lunar-900/60 shadow-lg relative overflow-hidden">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex-shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              {title}
            </h3>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800">
              Pipeline Rejected
            </span>
          </div>

          <p className="mt-2 text-sm text-amber-200/90 leading-relaxed font-normal">
            {reason || 'The computer vision pipeline could not establish high-confidence geometric correspondence between the provided lunar images.'}
          </p>

          {/* Recommendations Checklist */}
          {recommendations && recommendations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-amber-800/40">
              <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-2">
                <Info className="w-3.5 h-3.5 text-cyan-400" /> Recommended Actions:
              </h4>
              <ul className="space-y-1 text-xs text-slate-400 list-disc list-inside">
                {recommendations.map((rec, idx) => (
                  <li key={idx} className="leading-snug">
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Technical Diagnostics Accordion */}
          {details && (
            <div className="mt-4">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs text-amber-400 hover:text-amber-300 font-mono inline-flex items-center gap-1 hover:underline"
              >
                {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showDetails ? 'Hide Technical Telemetry' : 'View Diagnostic Telemetry'}
              </button>

              {showDetails && (
                <div className="mt-2 p-3 rounded-lg bg-black/70 border border-amber-900/60 font-mono text-[11px] text-slate-300 overflow-x-auto">
                  <pre>{JSON.stringify(details, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
