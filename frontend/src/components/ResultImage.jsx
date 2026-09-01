import React, { useState } from 'react';
import { Download, Maximize2, X, Eye, ExternalLink } from 'lucide-react';
import { getArtifactUrl } from '../services/api';

export default function ResultImage({
  title,
  subtitle,
  imagePath,
  badgeText,
  badgeColor = 'bg-cyan-950 text-cyan-400 border-cyan-800',
  downloadFilename,
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const fullUrl = getArtifactUrl(imagePath);

  const handleDownload = () => {
    if (!fullUrl) return;
    const a = document.createElement('a');
    a.href = fullUrl;
    a.download = downloadFilename || `${title.toLowerCase().replace(/\s+/g, '_')}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <>
      <div className="glass-panel rounded-2xl p-4 border border-lunar-700/60 bg-lunar-900/40 flex flex-col justify-between group">
        {/* Title Header */}
        <div className="flex items-start justify-between mb-2.5">
          <div>
            <h4 className="font-semibold text-white text-sm flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-cyan-400" />
              {title}
            </h4>
            {subtitle && <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {badgeText && (
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badgeColor}`}>
              {badgeText}
            </span>
          )}
        </div>

        {/* Image Display */}
        <div className="relative rounded-xl overflow-hidden border border-lunar-800 bg-black/80 aspect-video flex items-center justify-center">
          {fullUrl ? (
            <img
              src={fullUrl}
              alt={title}
              className="w-full h-full object-contain cursor-pointer transition-transform duration-300 group-hover:scale-[1.02]"
              onClick={() => setIsFullscreen(true)}
            />
          ) : (
            <div className="text-center p-4 text-xs text-slate-400">Image Artifact Pending</div>
          )}

          {/* Quick Action Overlay */}
          {fullUrl && (
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 pointer-events-none">
              <button
                onClick={() => setIsFullscreen(true)}
                className="p-2 rounded-lg bg-lunar-900/90 hover:bg-cyan-600 text-white border border-lunar-700 shadow-lg pointer-events-auto transition-colors"
                title="Fullscreen Preview"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <button
                onClick={handleDownload}
                className="p-2 rounded-lg bg-lunar-900/90 hover:bg-cyan-600 text-white border border-lunar-700 shadow-lg pointer-events-auto transition-colors"
                title="Download Artifact"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-3 pt-2.5 border-t border-lunar-800 flex items-center justify-between">
          <span className="text-[10px] text-slate-400 font-mono">PNG High Resolution</span>
          <button
            onClick={handleDownload}
            disabled={!fullUrl}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1 hover:underline disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5" /> Download
          </button>
        </div>
      </div>

      {/* Fullscreen Zoom Modal */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 sm:p-8">
          <div className="relative max-w-6xl w-full max-h-[90vh] flex flex-col items-center">
            <div className="w-full flex items-center justify-between pb-3 text-white">
              <div>
                <h3 className="text-lg font-bold">{title}</h3>
                {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDownload}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> Save Image
                </button>
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="p-2 rounded-lg bg-lunar-800 hover:bg-lunar-700 text-slate-300 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="w-full flex-1 overflow-hidden rounded-xl border border-lunar-700 bg-black/90 flex items-center justify-center p-2">
              <img src={fullUrl} alt={title} className="max-h-[75vh] w-auto object-contain" />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
