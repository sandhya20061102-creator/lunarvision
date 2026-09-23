import React, { useState } from 'react';
import {
  Satellite,
  Layers,
  Sparkles,
  Info,
  ShieldAlert,
  ArrowRight,
  Database,
  Scan,
  Compass,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Eye,
  Activity,
  Sliders
} from 'lucide-react';
import { registerMultiSensorImages } from '../services/api';
import ImageUploader from '../components/ImageUploader';
import MetricCard from '../components/MetricCard';
import ResultImage from '../components/ResultImage';
import LoadingState from '../components/LoadingState';
import ErrorMessage from '../components/ErrorMessage';
import DownloadButton from '../components/DownloadButton';

export default function ThreeSensorPage() {
  const [ohrcFile, setOhrcFile] = useState(null);
  const [ohrcPreview, setOhrcPreview] = useState(null);

  const [tmcFile, setTmcFile] = useState(null);
  const [tmcPreview, setTmcPreview] = useState(null);

  const [iirsFile, setIirsFile] = useState(null);
  const [iirsPreview, setIirsPreview] = useState(null);

  const [hubSensor, setHubSensor] = useState('OHRC'); // 'OHRC', 'TMC', 'IIRS'
  const [targetFeature, setTargetFeature] = useState('Shackleton Crater Rim');
  const [solarElevation, setSolarElevation] = useState('18.5°');

  const [isLoading, setIsLoading] = useState(false);
  const [multiSensorResult, setMultiSensorResult] = useState(null);

  const handleSelectOhrc = (file) => {
    setOhrcFile(file);
    setOhrcPreview(file ? URL.createObjectURL(file) : null);
  };

  const handleSelectTmc = (file) => {
    setTmcFile(file);
    setTmcPreview(file ? URL.createObjectURL(file) : null);
  };

  const handleSelectIirs = (file) => {
    setIirsFile(file);
    setIirsPreview(file ? URL.createObjectURL(file) : null);
  };

  const handleRunPairwiseRegistration = async () => {
    // Determine which files correspond to hub and secondaries
    let hubImg = null;
    let hubName = hubSensor;
    let sensorAImg = null;
    let sensorAName = '';
    let sensorBImg = null;
    let sensorBName = '';

    if (hubSensor === 'OHRC') {
      hubImg = ohrcFile;
      sensorAImg = tmcFile;
      sensorAName = 'TMC';
      sensorBImg = iirsFile;
      sensorBName = 'IIRS';
    } else if (hubSensor === 'TMC') {
      hubImg = tmcFile;
      sensorAImg = ohrcFile;
      sensorAName = 'OHRC';
      sensorBImg = iirsFile;
      sensorBName = 'IIRS';
    } else {
      hubImg = iirsFile;
      sensorAImg = ohrcFile;
      sensorAName = 'OHRC';
      sensorBImg = tmcFile;
      sensorBName = 'TMC';
    }

    if (!hubImg || (!sensorAImg && !sensorBImg)) {
      alert('Please upload the selected Reference Hub image and at least one secondary sensor image.');
      return;
    }

    // Ensure sensorAImg is populated if only sensorBImg was uploaded
    if (!sensorAImg && sensorBImg) {
      sensorAImg = sensorBImg;
      sensorAName = sensorBName;
      sensorBImg = null;
      sensorBName = '';
    }

    setIsLoading(true);
    setMultiSensorResult(null);

    try {
      const data = await registerMultiSensorImages({
        hubImage: hubImg,
        sensorAImage: sensorAImg,
        sensorBImage: sensorBImg,
        hubSensorName: hubName,
        sensorAName: sensorAName,
        sensorBName: sensorBName,
      });
      setMultiSensorResult(data);
    } catch (err) {
      setMultiSensorResult({
        status: 'error',
        reason: err.message || 'Multi-sensor pairwise registration failed.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const pairwise = multiSensorResult?.pairwise_results || {};

  return (
    <div className="space-y-8 pb-12 animate-fadeIn">
      {/* Header Info & Official Extension Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-300 text-xs font-semibold mb-2">
            <Satellite className="w-3.5 h-3.5" />
            Module 02: Three-Sensor Analysis Extension
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Three-Sensor Pairwise Analysis
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Cross-payload spatial and spectral alignment framework evaluating real pairwise correspondences between OHRC (0.25m optical), TMC (5m stereo DEM), and IIRS (infrared).
          </p>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunPairwiseRegistration}
            disabled={isLoading || (!ohrcFile && !tmcFile && !iirsFile)}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-all hover:scale-[1.02]"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Aligning Sensor Pairs...
              </>
            ) : (
              <>
                <Satellite className="w-4 h-4" /> Run Pairwise Analysis
              </>
            )}
          </button>
        </div>
      </div>

      {/* Scientific Transparency Notice */}
      <div className="glass-panel p-4 rounded-2xl border border-cyan-500/40 bg-cyan-950/20 flex items-start gap-3">
        <Info className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <span className="font-bold text-white block mb-0.5">Three-Sensor Analysis Extension Notice:</span>
          This module performs real pairwise computer vision matching between a selected reference hub sensor and secondary payloads. If cross-modal spectral/spatial disparities prevent stable geometric correspondence, the system will not force a false registration.
        </div>
      </div>

      {/* Hub Sensor & Metadata Selection Row */}
      <div className="glass-panel p-5 rounded-2xl border border-lunar-700/60 bg-lunar-900/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-white text-sm sm:text-base flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              Registration Hub & Orbital Metadata
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Select the primary reference coordinate frame and enter optional mission telemetry tags.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Hub Selector */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-lunar-950 border border-cyan-800/80 text-xs">
              <span className="text-slate-400">Reference Hub:</span>
              <select
                value={hubSensor}
                onChange={(e) => setHubSensor(e.target.value)}
                className="bg-transparent font-bold text-cyan-300 focus:outline-none cursor-pointer"
              >
                <option value="OHRC" className="bg-lunar-900 text-white">OHRC (0.25m Optical Hub)</option>
                <option value="TMC" className="bg-lunar-900 text-white">TMC (5.0m Stereo Hub)</option>
                <option value="IIRS" className="bg-lunar-900 text-white">IIRS (Infrared Hub)</option>
              </select>
            </div>

            {/* Target Feature input */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-lunar-950 border border-lunar-800 text-xs">
              <span className="text-slate-400">Target Feature:</span>
              <input
                type="text"
                value={targetFeature}
                onChange={(e) => setTargetFeature(e.target.value)}
                className="bg-transparent text-white font-medium focus:outline-none w-36"
                placeholder="Target crater"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Visual Sensor Relationship Architecture Diagram */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-lunar-700/60 bg-lunar-900/40">
        <h3 className="text-base sm:text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Scan className="w-5 h-5 text-cyan-400" />
          Sensor Modality Relationship Hierarchy
        </h3>
        <p className="text-xs text-slate-400 mb-6 max-w-2xl">
          Visual representation of complementary sensor modalities combining ultra-high spatial resolution, 3D stereo elevation, and infrared mineral spectroscopy.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* OHRC Sensor Card */}
          <div className={`glass-panel p-5 rounded-2xl border ${hubSensor === 'OHRC' ? 'border-cyan-500 bg-cyan-950/40 shadow-lg shadow-cyan-950/40' : 'border-cyan-500/40 bg-gradient-to-b from-cyan-950/40 to-lunar-950'} flex flex-col justify-between`}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {hubSensor === 'OHRC' ? '★ REFERENCE HUB' : 'Spatial Lead'}
                </span>
                <span className="text-xs font-mono text-cyan-300">~0.25 m/px</span>
              </div>
              <h4 className="font-bold text-white text-base">OHRC</h4>
              <p className="text-[11px] text-slate-400 mt-1">Orbiter High Resolution Camera</p>
              <p className="mt-3 text-xs text-slate-300 leading-relaxed">
                Ultra-high-resolution optical imaging resolving decimeter-scale boulder displacements and micro-cratering.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-lunar-800 text-[11px] font-mono text-cyan-400">
              High-Resolution Optical Frame
            </div>
          </div>

          {/* TMC Sensor Card */}
          <div className={`glass-panel p-5 rounded-2xl border ${hubSensor === 'TMC' ? 'border-cyan-500 bg-cyan-950/40 shadow-lg shadow-cyan-950/40' : 'border-blue-500/40 bg-gradient-to-b from-blue-950/40 to-lunar-950'} flex flex-col justify-between`}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  {hubSensor === 'TMC' ? '★ REFERENCE HUB' : 'Topography & DEM'}
                </span>
                <span className="text-xs font-mono text-blue-300">~5.0 m/px</span>
              </div>
              <h4 className="font-bold text-white text-base">TMC</h4>
              <p className="text-[11px] text-slate-400 mt-1">Terrain Mapping Camera</p>
              <p className="mt-3 text-xs text-slate-300 leading-relaxed">
                Triplet stereo imaging generating Digital Elevation Models (DEM) for slope and shadow angle extraction.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-lunar-800 text-[11px] font-mono text-blue-400">
              3D Elevation Layer
            </div>
          </div>

          {/* IIRS Sensor Card */}
          <div className={`glass-panel p-5 rounded-2xl border ${hubSensor === 'IIRS' ? 'border-cyan-500 bg-cyan-950/40 shadow-lg shadow-cyan-950/40' : 'border-cyan-500/40 bg-gradient-to-b from-cyan-950/40 to-lunar-950'} flex flex-col justify-between`}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {hubSensor === 'IIRS' ? '★ REFERENCE HUB' : 'Spectroscopy'}
                </span>
                <span className="text-xs font-mono text-cyan-300">0.8 - 5.0 μm</span>
              </div>
              <h4 className="font-bold text-white text-base">IIRS</h4>
              <p className="text-[11px] text-slate-400 mt-1">Imaging Infrared Spectrometer</p>
              <p className="mt-3 text-xs text-slate-300 leading-relaxed">
                Hyperspectral mineralogical mapping detecting pyroxene, plagioclase, and hydroxyl (OH) absorption bands.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-lunar-800 text-[11px] font-mono text-cyan-400">
              Spectral Signature Layer
            </div>
          </div>
        </div>
      </div>

      {/* 3 Ingestion Upload Slots */}
      <div>
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          Multi-Sensor Image Ingestion Channels
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ImageUploader
            title="OHRC Optical Channel"
            subtitle="High-resolution optical frame (0.25m)"
            file={ohrcFile}
            previewUrl={ohrcPreview}
            onImageSelected={handleSelectOhrc}
            onImageRemoved={() => handleSelectOhrc(null)}
            badgeText={hubSensor === 'OHRC' ? 'HUB REFERENCE' : 'Secondary'}
            badgeColor={hubSensor === 'OHRC' ? 'text-cyan-300 border-cyan-700 bg-cyan-950' : 'text-cyan-400 border-cyan-800 bg-cyan-950/60'}
          />

          <ImageUploader
            title="TMC Stereo Channel"
            subtitle="Stereo terrain frame (5.0m)"
            file={tmcFile}
            previewUrl={tmcPreview}
            onImageSelected={handleSelectTmc}
            onImageRemoved={() => handleSelectTmc(null)}
            badgeText={hubSensor === 'TMC' ? 'HUB REFERENCE' : 'Secondary'}
            badgeColor={hubSensor === 'TMC' ? 'text-cyan-300 border-cyan-700 bg-cyan-950' : 'text-blue-400 border-blue-800 bg-blue-950/60'}
          />

          <ImageUploader
            title="IIRS Infrared Channel"
            subtitle="Hyperspectral band / thermal frame"
            file={iirsFile}
            previewUrl={iirsPreview}
            onImageSelected={handleSelectIirs}
            onImageRemoved={() => handleSelectIirs(null)}
            badgeText={hubSensor === 'IIRS' ? 'HUB REFERENCE' : 'Secondary'}
            badgeColor={hubSensor === 'IIRS' ? 'text-cyan-300 border-cyan-700 bg-cyan-950' : 'text-cyan-400 border-cyan-800 bg-cyan-950/60'}
          />
        </div>
      </div>

      {/* Loading Radar */}
      {isLoading && (
        <LoadingState
          title="Executing Pairwise Cross-Sensor Matching..."
          subtitle="Aligning secondary sensor frames against selected Reference Hub geometry"
          steps={[
            'Preprocessing multi-spectral and optical frames with CLAHE...',
            'Extracting scale-invariant keypoints across sensor modalities...',
            'Evaluating cross-sensor descriptor correspondences...',
            'Computing pairwise RANSAC homography transformations...',
          ]}
        />
      )}

      {/* Real Pairwise Results Section */}
      {multiSensorResult && !isLoading && (
        <div className="space-y-8 animate-fadeIn">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Pairwise Registration Results Summary
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Hub Sensor: {multiSensorResult.hub_sensor}
            </span>
          </div>

          <div className="space-y-6">
            {Object.entries(pairwise).map(([pairKey, pairObj]) => {
              const res = pairObj.result;
              const isPairSuccess = res?.status === 'success';

              return (
                <div key={pairKey} className="glass-panel p-6 rounded-3xl border border-lunar-700/80 bg-lunar-900/40 space-y-6">
                  {/* Pair Header Banner */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-lunar-800">
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-xl border ${isPairSuccess ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'}`}>
                        {isPairSuccess ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white flex items-center gap-2">
                          Pair: {pairObj.pair_name}
                        </h4>
                        <p className="text-xs text-slate-400">
                          {isPairSuccess ? 'Geometric correspondence verified by RANSAC' : 'Registration rejected to avoid false correspondence'}
                        </p>
                      </div>
                    </div>

                    <div>
                      <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${isPairSuccess ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-amber-950 text-amber-300 border-amber-800'}`}>
                        {isPairSuccess ? 'Pair Registered' : 'No Reliable Match'}
                      </span>
                    </div>
                  </div>

                  {/* If Success: Metrics & Artifacts */}
                  {isPairSuccess ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <MetricCard
                          title="Pair RMSE"
                          value={res.metrics.rmse}
                          unit="px"
                          description="Discrepancy across overlapping valid mask"
                          colorScheme="emerald"
                        />
                        <MetricCard
                          title="RANSAC Inliers"
                          value={res.metrics.inlier_count}
                          unit={`/ ${res.metrics.total_good_matches}`}
                          description="Geometric inliers verified between sensors"
                          colorScheme="cyan"
                        />
                        <MetricCard
                          title="Inlier Ratio"
                          value={`${(res.metrics.inlier_ratio * 100).toFixed(1)}%`}
                          description="Consistency of cross-sensor keypoints"
                          colorScheme="cyan"
                        />
                        <MetricCard
                          title="Pair Confidence"
                          value={`${res.metrics.registration_confidence_percentage}%`}
                          progress={res.metrics.registration_confidence_percentage}
                          description="Pairwise registration confidence"
                          colorScheme="cyan"
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ResultImage
                          title="Aligned Secondary Frame"
                          subtitle="Warped to Hub coordinates"
                          imagePath={res.artifacts.aligned_image}
                          badgeText="Aligned Frame"
                        />
                        <ResultImage
                          title="RANSAC Inlier Matches"
                          subtitle={`${res.metrics.inlier_count} verified point correspondences`}
                          imagePath={res.artifacts.inlier_matches}
                          badgeText="Inliers"
                          badgeColor="bg-cyan-950 text-cyan-400 border-cyan-800"
                        />
                        <ResultImage
                          title="Alpha Blend Overlay"
                          subtitle="50/50 transparency fusion"
                          imagePath={res.artifacts.overlay_comparison}
                          badgeText="Fusion View"
                          badgeColor="bg-cyan-950 text-cyan-400 border-cyan-800"
                        />
                      </div>
                    </div>
                  ) : (
                    <ErrorMessage
                      title={`No Reliable Correspondence Found (${pairObj.pair_name})`}
                      reason={res?.reason || "No reliable correspondence was found. The system avoided forcing an inaccurate registration."}
                      details={res?.details}
                      recommendations={[
                        'Cross-sensor registration requires sufficient spatial overlap and identifiable crater rim topography.',
                        'Hyperspectral and optical bands may have extreme reflectance inversion requiring manual ground control points.',
                        'The system deliberately avoids generating distorted warps when inliers are below mathematical confidence limits.',
                      ]}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
