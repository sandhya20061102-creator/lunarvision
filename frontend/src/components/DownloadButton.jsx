import React from 'react';
import { Download } from 'lucide-react';
import { getArtifactUrl } from '../services/api';

export default function DownloadButton({
  label = 'Download Output',
  filePath,
  filename,
  variant = 'primary', // 'primary', 'secondary', 'outline'
  size = 'md', // 'sm', 'md', 'lg'
  disabled = false,
}) {
  const fullUrl = getArtifactUrl(filePath);

  const handleDownload = () => {
    if (!fullUrl) return;
    const a = document.createElement('a');
    a.href = fullUrl;
    a.download = filename || 'lunarvision_artifact.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const variants = {
    primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/20 border border-cyan-400/30',
    secondary: 'bg-lunar-800 hover:bg-lunar-700 text-white border border-lunar-600',
    outline: 'bg-transparent hover:bg-lunar-900 text-cyan-400 border border-cyan-500/40 hover:border-cyan-400',
  };

  const sizes = {
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-4 py-2 text-xs sm:text-sm',
    lg: 'px-5 py-2.5 text-sm font-semibold',
  };

  return (
    <button
      onClick={handleDownload}
      disabled={disabled || !fullUrl}
      className={`rounded-xl inline-flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed ${variants[variant] || variants.primary} ${sizes[size] || sizes.md}`}
    >
      <Download className="w-4 h-4" />
      <span>{label}</span>
    </button>
  );
}
