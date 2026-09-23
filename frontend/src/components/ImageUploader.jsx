import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, RefreshCw, FileText, CheckCircle2, AlertCircle, Database } from 'lucide-react';

const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.img'];

export default function ImageUploader({
  title,
  subtitle,
  file,
  previewUrl,
  onImageSelected,
  onImageRemoved,
  badgeText = 'Required',
  badgeColor = 'text-cyan-400 border-cyan-800 bg-cyan-950/60',
  accept = 'image/png, image/jpeg, image/jpg, image/tiff, image/bmp, .img, .IMG',
}) {
  const fileInputRef = useRef(null);
  const [imgError, setImgError] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const isImgFile = file?.name?.toLowerCase().endsWith('.img');

  const validateAndSelect = (selectedFile) => {
    if (!selectedFile) return;
    setErrorMessage(null);
    setImgError(false);

    const filename = selectedFile.name.toLowerCase();
    const isSupported = ALLOWED_EXTENSIONS.some((ext) => filename.endsWith(ext));

    if (!isSupported && !selectedFile.type.startsWith('image/')) {
      setErrorMessage(
        `Unsupported file type '${selectedFile.name.split('.').pop()}'. Supported formats: PNG, JPG, JPEG, TIFF, BMP, and scientific lunar .IMG files.`
      );
      return;
    }

    onImageSelected(selectedFile);
  };

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    validateAndSelect(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const dropped = e.dataTransfer.files?.[0];
    validateAndSelect(dropped);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-lunar-700/60 bg-lunar-900/30 flex flex-col justify-between transition-all">
      {/* Header info */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white text-sm sm:text-base flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-cyan-400" />
            {title}
          </h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${badgeColor}`}>
          {badgeText}
        </span>
      </div>

      {/* Upload, Preview, or Error Zone */}
      {errorMessage ? (
        <div className="rounded-xl border border-rose-500/50 bg-rose-950/30 p-5 text-center aspect-video flex flex-col items-center justify-center space-y-2">
          <AlertCircle className="w-8 h-8 text-rose-400 mb-1" />
          <p className="text-xs font-bold text-rose-300">File Format Error</p>
          <p className="text-[11px] text-slate-300 max-w-xs">{errorMessage}</p>
          <button
            onClick={() => {
              setErrorMessage(null);
              fileInputRef.current?.click();
            }}
            className="mt-2 px-3 py-1 rounded-lg bg-rose-800/60 hover:bg-rose-700 text-white text-xs font-medium"
          >
            Try Another File
          </button>
        </div>
      ) : previewUrl ? (
        <div className="space-y-3">
          <div className="relative group rounded-xl overflow-hidden border border-lunar-700 bg-black/60 aspect-video flex items-center justify-center">
            {isImgFile || imgError ? (
              /* Scientific .IMG Data Card Preview */
              <div className="w-full h-full p-4 flex flex-col items-center justify-center bg-gradient-to-br from-cyan-950/80 via-lunar-950 to-indigo-950 text-center">
                <div className="p-3 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 mb-2">
                  <Database className="w-6 h-6 animate-pulse" />
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 mb-1">
                  Scientific Lunar .IMG Data
                </span>
                <p className="text-xs font-semibold text-white truncate max-w-[220px]">{file?.name}</p>
                <p className="text-[10px] font-mono text-slate-400 mt-0.5">{formatFileSize(file?.size)} • Binary Raster Payload</p>
              </div>
            ) : (
              /* Standard Web Image Preview */
              <img
                src={previewUrl}
                alt={title}
                onError={() => setImgError(true)}
                className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
              />
            )}

            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-between p-3">
              <div className="text-left text-xs text-white">
                <p className="font-medium truncate max-w-[180px]">{file?.name || 'Selected File'}</p>
                <p className="text-[10px] text-slate-300">{formatFileSize(file?.size)}</p>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-2.5 py-1 rounded-lg bg-cyan-600/80 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1 shadow-md"
              >
                <RefreshCw className="w-3 h-3" /> Replace
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between px-2 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Ready for Computer Vision
            </span>
            <button
              onClick={() => {
                setImgError(false);
                onImageRemoved();
              }}
              className="text-rose-400 hover:text-rose-300 flex items-center gap-1 hover:underline text-[11px]"
            >
              <X className="w-3 h-3" /> Remove
            </button>
          </div>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-lunar-700 hover:border-cyan-500/60 bg-lunar-950/40 hover:bg-lunar-900/40 rounded-xl p-6 text-center cursor-pointer transition-all aspect-video flex flex-col items-center justify-center group"
        >
          <div className="p-3 rounded-full bg-lunar-800/80 group-hover:bg-cyan-500/20 group-hover:text-cyan-400 text-slate-400 border border-lunar-700 group-hover:border-cyan-500/40 transition-colors mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-200 group-hover:text-white">
            Click to upload or drag & drop
          </p>
          <p className="text-xs text-slate-400 mt-1">
            PNG, JPG, TIFF, BMP or scientific lunar <span className="text-cyan-400 font-semibold font-mono">.IMG</span> files
          </p>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
