import React, { useMemo } from 'react';
import { MapPin, AlertTriangle, CheckCircle2, XCircle, ArrowRight, Layers } from 'lucide-react';
import { usePipeline } from '../context/PipelineContext';

/**
 * FootprintMap
 *
 * Displays real lunar image footprints using PDS spatial metadata.
 * Falls back to EXIF-based center-point display when PDS data is unavailable.
 * NEVER invents coordinates.
 *
 * Props:
 *   metadataA   – result of extractGeoMetadata() for Image A (EXIF, or null)
 *   metadataB   – result of extractGeoMetadata() for Image B (EXIF, or null)
 *   pdsMetaA    – result of extractPdsMetadata() for Image A (PDS bounding box, or null)
 *   pdsMetaB    – result of extractPdsMetadata() for Image B (PDS bounding box, or null)
 *   labelA      – display label for image A
 *   labelB      – display label for image B
 *   fileA       – File object for image A (passed to registration pipeline)
 *   fileB       – File object for image B (passed to registration pipeline)
 */
export default function FootprintMap({
  metadataA  = null,
  metadataB  = null,
  pdsMetaA   = null,
  pdsMetaB   = null,
  labelA     = 'Source Image',
  labelB     = 'Reference Image',
  fileA      = null,
  fileB      = null,
}) {
  const { setActiveTab, setSourceImage, setReferenceImage } = usePipeline();

  // ── Determine effective footprint for each image ──────────────────────────
  // PDS bounding-box is preferred; EXIF center-point is used as fallback.
  const fpA = useMemo(() => {
    if (pdsMetaA) return { type: 'pds', ...pdsMetaA };
    if (metadataA && metadataA.centerLat != null && metadataA.centerLon != null) {
      return { type: 'exif', centerLat: metadataA.centerLat, centerLon: metadataA.centerLon,
               altitudeM: metadataA.altitudeM, sensor: metadataA.sensor };
    }
    return null;
  }, [pdsMetaA, metadataA]);

  const fpB = useMemo(() => {
    if (pdsMetaB) return { type: 'pds', ...pdsMetaB };
    if (metadataB && metadataB.centerLat != null && metadataB.centerLon != null) {
      return { type: 'exif', centerLat: metadataB.centerLat, centerLon: metadataB.centerLon,
               altitudeM: metadataB.altitudeM, sensor: metadataB.sensor };
    }
    return null;
  }, [pdsMetaB, metadataB]);

  const hasA = fpA !== null;
  const hasB = fpB !== null;
  const hasBoth = hasA && hasB;
  const hasNone = !hasA && !hasB;

  // ── Overlap calculation (PDS bounding-box only) ───────────────────────────
  const overlap = useMemo(() => {
    if (!hasBoth || fpA.type !== 'pds' || fpB.type !== 'pds') return null;

    // Handle longitude wraparound: treat [0,360] by normalising if needed
    const latOverlap = Math.max(0,
      Math.min(fpA.maxLat, fpB.maxLat) - Math.max(fpA.minLat, fpB.minLat)
    );
    const lonOverlap = Math.max(0,
      Math.min(fpA.maxLon, fpB.maxLon) - Math.max(fpA.minLon, fpB.minLon)
    );

    if (latOverlap === 0 || lonOverlap === 0) {
      return { hasOverlap: false, pct: 0 };
    }

    const overlapArea = latOverlap * lonOverlap;
    const areaA = (fpA.maxLat - fpA.minLat) * (fpA.maxLon - fpA.minLon);
    const areaB = (fpB.maxLat - fpB.minLat) * (fpB.maxLon - fpB.minLon);
    const unionArea = areaA + areaB - overlapArea;
    const iou = unionArea > 0 ? overlapArea / unionArea : 0;

    return {
      hasOverlap: true,
      iouPct: (iou * 100).toFixed(1),
      overlapArea: overlapArea.toFixed(4),
      minLat: Math.max(fpA.minLat, fpB.minLat),
      maxLat: Math.min(fpA.maxLat, fpB.maxLat),
      minLon: Math.max(fpA.minLon, fpB.minLon),
      maxLon: Math.min(fpA.maxLon, fpB.maxLon),
    };
  }, [fpA, fpB, hasBoth]);

  const isCandidatePair = overlap?.hasOverlap === true;

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleRunCorrespondence = () => {
    if (fileA) setSourceImage(fileA);
    if (fileB) setReferenceImage(fileB);
    setActiveTab('registration');
  };

  // ── Formatting helpers ────────────────────────────────────────────────────
  const fmtLat = (v) => {
    if (v == null) return '—';
    return `${Math.abs(v).toFixed(5)}° ${v >= 0 ? 'N' : 'S'}`;
  };
  const fmtLon = (v) => {
    if (v == null) return '—';
    return `${Math.abs(v).toFixed(5)}° ${v >= 0 ? 'E' : 'W'}`;
  };
  const fmtDeg = (v) => v != null ? `${v.toFixed(5)}°` : '—';

  // ── SVG spatial plot ──────────────────────────────────────────────────────
  const SpatialPlot = () => {
    if (!hasA && !hasB) return null;

    // Collect all lat/lon extremes to build a world bounding box for the plot
    const allLats = [];
    const allLons = [];
    const addExtents = (fp) => {
      if (!fp) return;
      if (fp.type === 'pds') {
        allLats.push(fp.minLat, fp.maxLat);
        allLons.push(fp.minLon, fp.maxLon);
      } else {
        allLats.push(fp.centerLat);
        allLons.push(fp.centerLon);
      }
    };
    addExtents(fpA);
    addExtents(fpB);

    const rawMinLat = Math.min(...allLats);
    const rawMaxLat = Math.max(...allLats);
    const rawMinLon = Math.min(...allLons);
    const rawMaxLon = Math.max(...allLons);

    // Add 10% padding
    const padLat = Math.max((rawMaxLat - rawMinLat) * 0.15, 0.2);
    const padLon = Math.max((rawMaxLon - rawMinLon) * 0.15, 0.2);
    const minLat = rawMinLat - padLat;
    const maxLat = rawMaxLat + padLat;
    const minLon = rawMinLon - padLon;
    const maxLon = rawMaxLon + padLon;

    const W = 480, H = 260, PAD = 36;
    const rangeW = maxLon - minLon || 1;
    const rangeH = maxLat - minLat || 1;

    const toX = (lon) => PAD + ((lon - minLon) / rangeW) * (W - 2 * PAD);
    const toY = (lat) => H - PAD - ((lat - minLat) / rangeH) * (H - 2 * PAD);

    // Build rect or polygon path for a footprint
    const fpToSvg = (fp, color, opacity) => {
      if (!fp) return null;
      if (fp.type === 'pds') {
        if (fp.hasPolygon && fp.corners) {
          const pts = fp.corners.map(c => `${toX(c.lon)},${toY(c.lat)}`).join(' ');
          return (
            <>
              <polygon points={pts} fill={color} fillOpacity={opacity * 0.35}
                stroke={color} strokeWidth="1.5" strokeOpacity={0.85} />
            </>
          );
        }
        // Bounding box rectangle
        const x = toX(fp.minLon);
        const y = toY(fp.maxLat);
        const w = toX(fp.maxLon) - x;
        const h = toY(fp.minLat) - y;
        return (
          <rect x={x} y={y} width={w} height={h}
            fill={color} fillOpacity={opacity * 0.35}
            stroke={color} strokeWidth="1.5" strokeOpacity={0.85}
            strokeDasharray={fp.type === 'pds' ? 'none' : '4 3'}
          />
        );
      }
      // EXIF: center point only
      const cx = toX(fp.centerLon);
      const cy = toY(fp.centerLat);
      return (
        <>
          <circle cx={cx} cy={cy} r="10" fill={color} fillOpacity="0.2" stroke={color} strokeWidth="1.5" />
          <circle cx={cx} cy={cy} r="4" fill={color} />
        </>
      );
    };

    // Overlap rectangle
    const overlapSvg = () => {
      if (!overlap?.hasOverlap) return null;
      const x = toX(overlap.minLon);
      const y = toY(overlap.maxLat);
      const w = toX(overlap.maxLon) - x;
      const h = toY(overlap.minLat) - y;
      if (w <= 0 || h <= 0) return null;
      return (
        <rect x={x} y={y} width={w} height={h}
          fill="#34d399" fillOpacity="0.25"
          stroke="#34d399" strokeWidth="1.5" strokeDasharray="3 2" />
      );
    };

    // Center marker
    const centerMarker = (fp, color) => {
      if (!fp || fp.type !== 'pds' || fp.centerLat == null) return null;
      return (
        <circle cx={toX(fp.centerLon)} cy={toY(fp.centerLat)}
          r="3" fill={color} opacity="0.9" />
      );
    };

    // Label for a footprint
    const fpLabel = (fp, label, color) => {
      if (!fp) return null;
      const lx = fp.type === 'pds'
        ? toX((fp.minLon + fp.maxLon) / 2)
        : toX(fp.centerLon);
      const ly = fp.type === 'pds'
        ? toY(fp.maxLat) - 4
        : toY(fp.centerLat) - 10;
      return (
        <text x={lx} y={ly} fill={color} fontSize="9" textAnchor="middle"
          fontFamily="monospace" fontWeight="600">
          {label}
        </text>
      );
    };

    return (
      <div className="w-full mt-4">
        <svg viewBox={`0 0 ${W} ${H}`}
          className="w-full rounded-lg bg-slate-950/80 border border-slate-800"
          style={{ maxHeight: 260 }}>

          {/* Grid */}
          {[0.25, 0.5, 0.75].map((f) => (
            <React.Fragment key={f}>
              <line x1={PAD + f * (W - 2 * PAD)} y1={PAD}
                x2={PAD + f * (W - 2 * PAD)} y2={H - PAD}
                stroke="rgba(100,116,139,0.12)" strokeWidth="1" />
              <line x1={PAD} y1={PAD + f * (H - 2 * PAD)}
                x2={W - PAD} y2={PAD + f * (H - 2 * PAD)}
                stroke="rgba(100,116,139,0.12)" strokeWidth="1" />
            </React.Fragment>
          ))}

          {/* Border */}
          <rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD}
            fill="none" stroke="rgba(100,116,139,0.25)" strokeWidth="1" />

          {/* Footprints (A below B so overlap is visible) */}
          {fpToSvg(fpA, '#f59e0b', 0.7)}
          {fpToSvg(fpB, '#22d3ee', 0.7)}
          {overlapSvg()}
          {centerMarker(fpA, '#f59e0b')}
          {centerMarker(fpB, '#22d3ee')}
          {fpLabel(fpA, labelA, '#f59e0b')}
          {fpLabel(fpB, labelB, '#22d3ee')}

          {/* Axis labels */}
          <text x={W / 2} y={H - 4} fill="#475569" fontSize="8"
            textAnchor="middle" fontFamily="monospace">
            Lunar Longitude →
          </text>
          <text transform={`rotate(-90 10 ${H / 2})`}
            x="10" y={H / 2} fill="#475569" fontSize="8"
            textAnchor="middle" fontFamily="monospace">
            Latitude →
          </text>

          {/* Axis tick values */}
          <text x={PAD} y={H - PAD + 12} fill="#334155" fontSize="7"
            textAnchor="middle" fontFamily="monospace">{fmtDeg(minLon)}</text>
          <text x={W - PAD} y={H - PAD + 12} fill="#334155" fontSize="7"
            textAnchor="middle" fontFamily="monospace">{fmtDeg(maxLon)}</text>
          <text x={PAD - 4} y={PAD + 4} fill="#334155" fontSize="7"
            textAnchor="end" fontFamily="monospace">{fmtDeg(maxLat)}</text>
          <text x={PAD - 4} y={H - PAD + 4} fill="#334155" fontSize="7"
            textAnchor="end" fontFamily="monospace">{fmtDeg(minLat)}</text>

          {/* Legend */}
          <rect x={W - PAD - 70} y={PAD + 6} width="8" height="8"
            fill="#f59e0b" fillOpacity="0.4" stroke="#f59e0b" strokeWidth="1" />
          <text x={W - PAD - 58} y={PAD + 14} fill="#f59e0b" fontSize="8"
            fontFamily="monospace">{labelA}</text>
          <rect x={W - PAD - 70} y={PAD + 18} width="8" height="8"
            fill="#22d3ee" fillOpacity="0.4" stroke="#22d3ee" strokeWidth="1" />
          <text x={W - PAD - 58} y={PAD + 26} fill="#22d3ee" fontSize="8"
            fontFamily="monospace">{labelB}</text>
          {overlap?.hasOverlap && (
            <>
              <rect x={W - PAD - 70} y={PAD + 30} width="8" height="8"
                fill="#34d399" fillOpacity="0.4" stroke="#34d399" strokeWidth="1" strokeDasharray="2 1" />
              <text x={W - PAD - 58} y={PAD + 38} fill="#34d399" fontSize="8"
                fontFamily="monospace">Overlap</text>
            </>
          )}
        </svg>
        <p className="text-[10px] text-slate-600 mt-1.5 text-center font-mono">
          {fpA?.type === 'pds' || fpB?.type === 'pds'
            ? 'Footprint bounding boxes from PDS label metadata'
            : 'Center-point only — EXIF GPS metadata (no bounding box)'}
        </p>
      </div>
    );
  };

  // ── Single-image metadata row ──────────────────────────────────────────────
  const FootprintRow = ({ fp, label, color }) => {
    if (!fp) {
      return (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-slate-900/60 border border-slate-800">
          <AlertTriangle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-semibold mb-0.5" style={{ color }}>{label}</div>
            <div className="text-[11px] text-slate-500">
              Footprint data unavailable — no reliable spatial metadata found.
            </div>
          </div>
        </div>
      );
    }

    const isPds = fp.type === 'pds';

    return (
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 shrink-0" style={{ color }} />
          <span className="text-xs font-semibold" style={{ color }}>{label}</span>
          <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded-full border"
            style={{ color, borderColor: color + '40', background: color + '15' }}>
            {isPds ? (fp.hasPolygon ? 'PDS polygon' : 'PDS bbox') : 'EXIF center'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[11px] text-slate-300 font-mono">
          {isPds ? (
            <>
              <span className="text-slate-500">Center Lat</span>
              <span>{fmtLat(fp.centerLat)}</span>
              <span className="text-slate-500">Center Lon</span>
              <span>{fmtLon(fp.centerLon)}</span>
              <span className="text-slate-500">Lat range</span>
              <span>{fmtDeg(fp.minLat)} – {fmtDeg(fp.maxLat)}</span>
              <span className="text-slate-500">Lon range</span>
              <span>{fmtDeg(fp.minLon)} – {fmtDeg(fp.maxLon)}</span>
              {fp.instrument && (
                <>
                  <span className="text-slate-500">Instrument</span>
                  <span className="truncate">{fp.instrument}</span>
                </>
              )}
              {fp.targetName && (
                <>
                  <span className="text-slate-500">Target</span>
                  <span className="truncate">{fp.targetName}</span>
                </>
              )}
              {fp.missionName && (
                <>
                  <span className="text-slate-500">Mission</span>
                  <span className="truncate">{fp.missionName}</span>
                </>
              )}
            </>
          ) : (
            <>
              <span className="text-slate-500">Latitude</span>
              <span>{fmtLat(fp.centerLat)}</span>
              <span className="text-slate-500">Longitude</span>
              <span>{fmtLon(fp.centerLon)}</span>
              {fp.altitudeM != null && (
                <>
                  <span className="text-slate-500">Altitude</span>
                  <span>{fp.altitudeM.toFixed(0)} m</span>
                </>
              )}
              {fp.sensor && (
                <>
                  <span className="text-slate-500">Sensor</span>
                  <span className="truncate">{fp.sensor}</span>
                </>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="hud-panel p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <MapPin className="w-4 h-4 text-cyan-400" />
        <span>Lunar Surface Footprint Map</span>
        {(hasBoth && fpA?.type === 'pds' && fpB?.type === 'pds') && (
          <span className="ml-auto text-[10px] font-mono text-cyan-400/70">PDS spatial analysis</span>
        )}
      </div>

      {/* No data at all */}
      {hasNone ? (
        <div className="flex items-start gap-2 p-4 rounded-lg bg-slate-900/60 border border-slate-700/60">
          <AlertTriangle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <p className="text-xs text-slate-400 leading-relaxed">
            <span className="text-slate-200 font-semibold">Footprint data unavailable.</span>{' '}
            Neither uploaded image contains usable spatial metadata. Upload PDS label files (.lbl)
            alongside your lunar images to enable footprint display and overlap analysis.
          </p>
        </div>
      ) : (
        <>
          {/* Per-image metadata */}
          <div className="space-y-3">
            <FootprintRow fp={fpA} label={labelA} color="#f59e0b" />
            <FootprintRow fp={fpB} label={labelB} color="#22d3ee" />
          </div>

          {/* Overlap status (only when both have PDS bounding boxes) */}
          {hasBoth && fpA.type === 'pds' && fpB.type === 'pds' && (
            <div className={`flex items-start gap-3 p-3 rounded-lg border ${
              isCandidatePair
                ? 'bg-emerald-950/30 border-emerald-700/50'
                : 'bg-slate-900/50 border-slate-800'
            }`}>
              {isCandidatePair
                ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                : <XCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />}
              <div className="min-w-0">
                <div className={`text-xs font-semibold ${isCandidatePair ? 'text-emerald-300' : 'text-slate-400'}`}>
                  {isCandidatePair ? 'Spatial overlap detected' : 'No spatial overlap detected'}
                </div>
                {isCandidatePair && (
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    IoU: {overlap.iouPct}% &nbsp;·&nbsp;
                    Overlap extent: {overlap.overlapArea}° ²
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Angular separation fallback (EXIF center-point only) */}
          {hasBoth && !(fpA.type === 'pds' && fpB.type === 'pds') && (
            <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <span className="text-slate-500">Angular separation (center-points):</span>
              <span className="font-mono text-cyan-300">
                {Math.sqrt(
                  Math.pow((fpA.centerLat ?? 0) - (fpB.centerLat ?? 0), 2) +
                  Math.pow((fpA.centerLon ?? 0) - (fpB.centerLon ?? 0), 2)
                ).toFixed(4)}°
              </span>
            </div>
          )}

          {/* SVG Plot */}
          <SpatialPlot />

          {/* Candidate pair action */}
          {isCandidatePair && (
            <div className="p-4 rounded-lg bg-cyan-950/30 border border-cyan-700/40 space-y-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-semibold text-cyan-300">Candidate Pair Detected</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                These two images share spatial overlap. They are candidates for feature
                correspondence and image registration using the existing SIFT/AKAZE + RANSAC pipeline.
              </p>
              {fileA && fileB ? (
                <button
                  onClick={handleRunCorrespondence}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400
                    text-slate-950 text-xs font-bold transition-all
                    shadow-[0_0_12px_rgba(6,182,212,0.3)] hover:shadow-[0_0_20px_rgba(6,182,212,0.5)]"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Run Correspondence on This Pair
                </button>
              ) : (
                <button
                  onClick={() => setActiveTab('registration')}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-900/50 hover:bg-cyan-900/80
                    text-cyan-300 text-xs font-semibold transition-all border border-cyan-700/50"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Go to Registration Page
                </button>
              )}
            </div>
          )}

          {/* Data source note */}
          <p className="text-[10px] text-slate-600 leading-relaxed">
            {fpA?.type === 'pds' || fpB?.type === 'pds'
              ? 'Footprint extents are real bounding boxes from PDS label metadata. Overlap is calculated from actual bounding-box intersection.'
              : 'Center-point coordinates extracted from EXIF GPS metadata. Footprint extents are unavailable without a PDS label file.'}
          </p>
        </>
      )}
    </div>
  );
}
