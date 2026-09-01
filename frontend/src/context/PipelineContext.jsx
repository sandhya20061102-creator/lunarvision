import React, { createContext, useContext, useState, useEffect } from 'react';
import { getBackendHealth } from '../services/api';

const PipelineContext = createContext();

export function PipelineProvider({ children }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [backendHealth, setBackendHealth] = useState({
    status: 'checking',
    data: null,
    error: null,
  });

  // Stored registration result
  const [registrationResult, setRegistrationResult] = useState(null);

  // Stored change detection result
  const [changeDetectionResult, setChangeDetectionResult] = useState(null);

  // Stored files for caching across tabs
  const [sourceFile, setSourceFile] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null);
  const [sourcePreview, setSourcePreview] = useState(null);
  const [referencePreview, setReferencePreview] = useState(null);

  const refreshHealth = async () => {
    const res = await getBackendHealth();
    if (res.success) {
      setBackendHealth({
        status: 'healthy',
        data: res.data,
        error: null,
      });
    } else {
      setBackendHealth({
        status: 'offline',
        data: null,
        error: res.error,
      });
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const setSourceImage = (file) => {
    setSourceFile(file);
    if (file) {
      setSourcePreview(URL.createObjectURL(file));
    } else {
      setSourcePreview(null);
    }
  };

  const setReferenceImage = (file) => {
    setReferenceFile(file);
    if (file) {
      setReferencePreview(URL.createObjectURL(file));
    } else {
      setReferencePreview(null);
    }
  };

  const clearAllData = () => {
    setRegistrationResult(null);
    setChangeDetectionResult(null);
    setSourceFile(null);
    setReferenceFile(null);
    setSourcePreview(null);
    setReferencePreview(null);
  };

  return (
    <PipelineContext.Provider
      value={{
        activeTab,
        setActiveTab,
        backendHealth,
        refreshHealth,
        registrationResult,
        setRegistrationResult,
        changeDetectionResult,
        setChangeDetectionResult,
        sourceFile,
        referenceFile,
        sourcePreview,
        referencePreview,
        setSourceImage,
        setReferenceImage,
        clearAllData,
      }}
    >
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline() {
  const context = useContext(PipelineContext);
  if (!context) {
    throw new Error('usePipeline must be used within a PipelineProvider');
  }
  return context;
}
