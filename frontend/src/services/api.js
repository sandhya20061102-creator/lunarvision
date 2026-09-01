import axios from 'axios';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s timeout for CV processing
});

/**
 * Returns full URL for static assets from backend (e.g. /outputs/...)
 */
export const getArtifactUrl = (relativePath) => {
  if (!relativePath) return '';
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath;
  }
  const cleanBase = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  const cleanPath = relativePath.startsWith('/') ? relativePath : `/${relativePath}`;
  return `${cleanBase}${cleanPath}`;
};

/**
 * Check backend health status
 */
export const getBackendHealth = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Unable to connect to LunarVision backend',
    };
  }
};

/**
 * Perform full image registration via POST /api/images/register
 */
export const registerImages = async (sourceFile, referenceFile, preferredDetector = 'SIFT') => {
  const formData = new FormData();
  formData.append('source_image', sourceFile);
  formData.append('reference_image', referenceFile);
  formData.append('preferred_detector', preferredDetector);

  try {
    const response = await apiClient.post('/api/images/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      return error.response.data;
    }
    return {
      status: 'no_match',
      reason: error.message || 'Network error occurred while contacting registration endpoint.',
      details: { error_type: 'network_failure' },
    };
  }
};

/**
 * Perform real pairwise multi-sensor registration via POST /api/images/multi-sensor-register
 */
export const registerMultiSensorImages = async ({
  hubImage,
  sensorAImage,
  sensorBImage,
  hubSensorName = 'OHRC',
  sensorAName = 'TMC',
  sensorBName = 'IIRS',
  preferredDetector = 'SIFT',
}) => {
  const formData = new FormData();
  formData.append('hub_image', hubImage);
  formData.append('sensor_a_image', sensorAImage);
  if (sensorBImage) {
    formData.append('sensor_b_image', sensorBImage);
  }
  formData.append('hub_sensor_name', hubSensorName);
  formData.append('sensor_a_name', sensorAName);
  formData.append('sensor_b_name', sensorBName);
  formData.append('preferred_detector', preferredDetector);

  try {
    const response = await apiClient.post('/api/images/multi-sensor-register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      return error.response.data;
    }
    return {
      status: 'no_match',
      reason: error.message || 'Network error occurred during multi-sensor registration.',
      details: { error_type: 'network_failure' },
    };
  }
};

/**
 * Perform temporal change detection via POST /api/images/change-detection
 */
export const detectTemporalChanges = async (
  sourceFile,
  referenceFile,
  minConfidence = 0.35,
  differenceThreshold = 35
) => {
  const formData = new FormData();
  formData.append('source_image', sourceFile);
  formData.append('reference_image', referenceFile);
  formData.append('min_confidence', minConfidence);
  formData.append('difference_threshold', differenceThreshold);

  try {
    const response = await apiClient.post('/api/images/change-detection', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      return error.response.data;
    }
    return {
      status: 'no_match',
      reason: error.message || 'Network error occurred during change detection.',
      details: { error_type: 'network_failure' },
    };
  }
};
