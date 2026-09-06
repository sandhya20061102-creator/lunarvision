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
import Chatbot from './components/Chatbot';

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
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-lunar-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navigation Header */}
      <Header />

      {/* Main Workspace Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation */}
        <Sidebar />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gradient-to-b from-lunar-950 via-lunar-900/30 to-lunar-950">
          <div className="max-w-7xl mx-auto">
            {renderActivePage()}
          </div>
        </main>
      </div>

      {/* Telemetry Footer */}
      <footer className="border-t border-lunar-800/60 py-3 px-6 bg-lunar-950/80 text-center sm:text-left flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400">
        <div>
          <span>LunarVision CV Engine</span>
          <span className="mx-2 text-slate-400">•</span>
          <span className="text-slate-400">Planetary Surface Registration & Temporal Change Detection</span>
        </div>
        <div className="mt-2 sm:mt-0 font-mono text-[11px] text-cyan-400/80">
          FastAPI + OpenCV + scikit-image + React 18
        </div>
      </footer>

      {/* Offline-First AI Chatbot Widget */}
      <Chatbot />
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
