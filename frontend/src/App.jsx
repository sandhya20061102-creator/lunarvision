import React from 'react';
import { PipelineProvider, usePipeline } from './context/PipelineContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import RegistrationPage from './pages/RegistrationPage';
import ThreeSensorPage from './pages/ThreeSensorPage';
import ChangeDetectionPage from './pages/ChangeDetectionPage';
import ResultsPage from './pages/ResultsPage';
import HowItWorksPage from './pages/HowItWorksPage';
import SunAnglePage from './pages/SunAnglePage';


function MainAppLayout() {
  const { activeTab } = usePipeline();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'registration':
        return <RegistrationPage />;
      case 'three_sensor':
        return <ThreeSensorPage />;
      case 'change_detection':
        return <ChangeDetectionPage />;
      case 'results':
        return <ResultsPage />;
      case 'how_it_works':
        return <HowItWorksPage />;
      case 'sun_angle': return <SunAnglePage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen space-bg text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navigation Header */}
      <Header />

      {/* Main Workspace Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation - Only show when not on dashboard for a cleaner landing page, or keep it if required. Since reference has no sidebar, we hide it on dashboard. */}
        {/* Sidebar hidden */}

        {/* Dynamic Page Content */}
        <main className={`flex-1 overflow-y-auto ${activeTab === 'dashboard' ? 'dashboard-override' : 'p-4 sm:p-6 lg:p-8'}`}
          style={activeTab !== 'dashboard' ? { background: 'linear-gradient(180deg, #010108 0%, #020a18 100%)' } : undefined}
        >
          <div className={activeTab === 'dashboard' ? 'w-full h-full' : 'max-w-7xl mx-auto'}>
            {renderActivePage()}
          </div>
        </main>
      </div>

      {/* Telemetry Footer */}
      <footer
        className="py-2.5 px-8 flex flex-col sm:flex-row items-center justify-between text-[11px] z-40"
        style={{
          background: 'rgba(1, 3, 12, 0.90)',
          borderTop: '1px solid rgba(0, 180, 255, 0.08)',
          color: '#4a6a80',
        }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#3a5a70' }}>LunarVision CV Engine</span>
          <span style={{ color: '#2a3a45' }}>•</span>
          <span style={{ color: '#2a4055' }}>Planetary Surface Registration &amp; Temporal Change Detection</span>
        </div>
        <div className="mt-1 sm:mt-0 font-mono" style={{ color: '#00a8c8', opacity: 0.7 }}>
          FastAPI + OpenCV + scikit-image + React 18
        </div>
      </footer>

      {/* Offline-First AI Chatbot Widget */}
      
    </div>
  );
}

export default function App() {
  return (
    <PipelineProvider>
      <MainAppLayout />
    </PipelineProvider>
  );
}
