import { useState, useEffect, useRef, useCallback } from 'react';
import { getChatStatus, getOfflineKnowledge } from '../services/api';
import { saveKnowledgeToLocal, getKnowledgeFromLocal } from '../services/knowledgeDB';

/**
 * Custom hook for continuous, automatic connectivity monitoring and background re-sync.
 *
 * States:
 * - OFFLINE: 🔴 Offline — Local Knowledge
 * - RECONNECTING: 🟡 Reconnecting...
 * - ONLINE: 🟢 Online — Knowledge Current
 * - UPDATED: ✓ Knowledge updated (transient 3s state)
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [networkState, setNetworkState] = useState(
    navigator.onLine ? 'ONLINE' : 'OFFLINE'
  );
  const [lastSyncTime, setLastSyncTime] = useState(null);

  const isReachableRef = useRef(navigator.onLine);
  const retryCountRef = useRef(0);
  const syncInProgressRef = useRef(false);

  // Compute exponential backoff delay: 5s, 15s, 30s, max 60s
  const getBackoffDelay = (retryCount) => {
    const delays = [5000, 15000, 30000];
    return delays[retryCount] || 60000;
  };

  /**
   * Automatic background re-fetch and version check.
   */
  const performSilentAutoSync = useCallback(async () => {
    if (syncInProgressRef.current) return;
    syncInProgressRef.current = true;

    try {
      // 1. Fetch knowledge JSON from backend
      const remoteKB = await getOfflineKnowledge();
      if (remoteKB) {
        // 2. Read existing local cache
        const localKB = await getKnowledgeFromLocal();

        const remoteVer = remoteKB.version || '1.0.0';
        const remoteUpdated = remoteKB.last_updated || '';
        const localVer = localKB?.version || null;
        const localUpdated = localKB?.last_updated || null;

        // 3. Compare version and timestamp
        const hasChanged = !localKB || localVer !== remoteVer || localUpdated !== remoteUpdated;

        if (hasChanged) {
          // Save updated knowledge to IndexedDB / localStorage
          await saveKnowledgeToLocal(remoteKB);
          setLastSyncTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
          setNetworkState('UPDATED');

          // Transition back to ONLINE after 3s
          setTimeout(() => {
            setNetworkState('ONLINE');
          }, 3000);
        } else {
          // Stay silent, no spam
          setNetworkState('ONLINE');
        }
      } else {
        setNetworkState('ONLINE');
      }
    } catch (err) {
      console.warn('[AutoSync] Background re-fetch failed, using cached copy:', err);
      // Keep using last good local copy
    } finally {
      syncInProgressRef.current = false;
    }
  }, []);

  /**
   * Periodic ping and connection monitor.
   */
  const checkConnection = useCallback(async () => {
    if (!navigator.onLine) {
      setIsOnline(false);
      setNetworkState('OFFLINE');
      isReachableRef.current = false;
      return;
    }

    try {
      // Ping backend status endpoint
      const statusRes = await getChatStatus();

      if (statusRes && statusRes.status === 'online') {
        const wasOffline = !isReachableRef.current;
        setIsOnline(true);
        isReachableRef.current = true;
        retryCountRef.current = 0;

        if (wasOffline) {
          // Connection restored! Automatically trigger background re-sync
          setNetworkState('RECONNECTING');
          await performSilentAutoSync();
        } else if (networkState !== 'UPDATED') {
          setNetworkState('ONLINE');
        }
      } else {
        throw new Error('Backend returned non-online status');
      }
    } catch (err) {
      const wasOnline = isReachableRef.current;
      setIsOnline(false);
      isReachableRef.current = false;

      if (wasOnline) {
        setNetworkState('OFFLINE');
      } else {
        // We are attempting to reconnect with backoff
        setNetworkState('RECONNECTING');
      }

      retryCountRef.current += 1;
    }
  }, [networkState, performSilentAutoSync]);

  useEffect(() => {
    // Initial check on mount
    getKnowledgeFromLocal().then((cached) => {
      if (!cached && navigator.onLine) {
        performSilentAutoSync();
      }
    });

    const handleOnlineEvent = () => {
      setNetworkState('RECONNECTING');
      checkConnection();
    };

    const handleOfflineEvent = () => {
      setIsOnline(false);
      setNetworkState('OFFLINE');
      isReachableRef.current = false;
    };

    window.addEventListener('online', handleOnlineEvent);
    window.addEventListener('offline', handleOfflineEvent);

    // Initial ping check
    checkConnection();

    // Setup dynamic backoff ping timer
    let timerId;
    const scheduleNextCheck = () => {
      const delay = isReachableRef.current ? 6000 : getBackoffDelay(retryCountRef.current);
      timerId = setTimeout(async () => {
        await checkConnection();
        scheduleNextCheck();
      }, delay);
    };

    scheduleNextCheck();

    return () => {
      window.removeEventListener('online', handleOnlineEvent);
      window.removeEventListener('offline', handleOfflineEvent);
      if (timerId) clearTimeout(timerId);
    };
  }, [checkConnection, performSilentAutoSync]);

  return {
    isOnline,
    networkState,
    lastSyncTime,
  };
}
