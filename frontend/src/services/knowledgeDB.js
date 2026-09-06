/**
 * IndexedDB storage helper for LunarVision Offline Knowledge Base.
 * Stores cached FAQs, technical pipeline data, metrics, and news locally.
 */

const DB_NAME = 'LunarVisionKnowledgeDB';
const DB_VERSION = 1;
const STORE_NAME = 'knowledge_store';

export const openKnowledgeDB = () => {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      console.warn('IndexedDB not supported by browser. Falling back to LocalStorage.');
      resolve(null);
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = (event) => {
      console.error('IndexedDB open error:', event.target.error);
      resolve(null);
    };

    request.onsuccess = (event) => {
      resolve(event.target.result);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'key' });
      }
    };
  });
};

/**
 * Save knowledge base payload to IndexedDB and LocalStorage
 */
export const saveKnowledgeToLocal = async (kbData) => {
  if (!kbData) return;
  const payload = {
    key: 'lunar_kb',
    data: kbData,
    last_updated: new Date().toISOString(),
  };

  // 1. Try LocalStorage backup
  try {
    localStorage.setItem('lunarvision_kb_cache', JSON.stringify(payload));
  } catch (e) {
    console.warn('LocalStorage save failed:', e);
  }

  // 2. Try IndexedDB
  try {
    const db = await openKnowledgeDB();
    if (db) {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.put(payload);
    }
  } catch (err) {
    console.error('Failed to save knowledge to IndexedDB:', err);
  }
};

/**
 * Get locally stored knowledge base
 */
export const getKnowledgeFromLocal = async () => {
  // 1. Try IndexedDB
  try {
    const db = await openKnowledgeDB();
    if (db) {
      const result = await new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.get('lunar_kb');
        req.onsuccess = () => resolve(req.result ? req.result.data : null);
        req.onerror = () => resolve(null);
      });
      if (result) return result;
    }
  } catch (e) {
    console.warn('IndexedDB read error, checking LocalStorage:', e);
  }

  // 2. Fallback to LocalStorage
  try {
    const raw = localStorage.getItem('lunarvision_kb_cache');
    if (raw) {
      const parsed = JSON.parse(raw);
      return parsed.data;
    }
  } catch (e) {
    console.warn('LocalStorage read error:', e);
  }

  return null;
};

/**
 * Client-side keyword search fallback when network and backend are unavailable.
 */
export const queryLocalKnowledgeBase = (kbData, query) => {
  if (!query || !query.trim()) {
    return {
      answer: "Please ask a question about LunarVision, SIFT/AKAZE, RANSAC, or ISRO sensors.",
      suggested_questions: ["What is LunarVision?", "What is RANSAC?", "Explain OHRC, TMC and IIRS"],
    };
  }

  const q = query.toLowerCase().trim();

  if (q.includes('ransac')) {
    return {
      answer: "**RANSAC (Random Sample Consensus)**\n\nIteratively estimates the homography matrix while removing false feature matches caused by crater repetition or shadows.",
      suggested_questions: ["What is Lowe's ratio test?", "What is RMSE?", "What is image registration?"],
    };
  }

  if (q.includes('lowe') || q.includes('ratio test')) {
    return {
      answer: "**Lowe's Ratio Test**\n\nFilters nearest-neighbor descriptor matches by keeping only pairs where `d1/d2 < threshold` (0.75-0.80).",
      suggested_questions: ["What is RANSAC?", "What is SIFT?", "What is AKAZE?"],
    };
  }

  if (q.includes('ohrc') || q.includes('tmc') || q.includes('iirs') || q.includes('sensor')) {
    return {
      answer: "**ISRO Chandrayaan Sensors:**\n\n• **OHRC:** 0.25 m/pixel panchromatic high-res surface camera.\n• **TMC:** 5m spatial resolution 3D stereo mapping.\n• **IIRS:** 0.8-5.0 µm infrared spectrometer.",
      suggested_questions: ["What is LunarVision?", "What file formats are supported?", "What is RANSAC?"],
    };
  }

  if (q.includes('lunarvision') || q.includes('how does')) {
    return {
      answer: "**LunarVision Pipeline:**\n\n1. Preprocessing (CLAHE)\n2. Feature Detection (SIFT/AKAZE)\n3. Matching (Lowe's Ratio Test)\n4. RANSAC Homography Alignment\n5. Image Registration & Warping\n6. SSIM Temporal Change Detection",
      suggested_questions: ["What is RANSAC?", "Explain OHRC, TMC and IIRS", "What is SSIM?"],
    };
  }

  // General search in FAQs if kbData exists
  if (kbData && kbData.faqs) {
    for (const faq of kbData.faqs) {
      if (q.includes(faq.question.toLowerCase()) || faq.question.toLowerCase().includes(q)) {
        return {
          answer: `**${faq.question}**\n\n${faq.answer}`,
          suggested_questions: ["What is RANSAC?", "Explain OHRC, TMC and IIRS", "How does LunarVision work?"],
        };
      }
    }
  }

  return {
    answer: "I am running in **Offline Mode** using browser-cached knowledge.\n\nI can answer questions about:\n• LunarVision pipeline\n• SIFT, AKAZE, RANSAC, Lowe's Ratio Test\n• RMSE, Inlier Ratio, SSIM metrics\n• ISRO OHRC, TMC, IIRS sensors",
    suggested_questions: ["What is LunarVision?", "What is RANSAC?", "Explain OHRC, TMC and IIRS"],
  };
};
