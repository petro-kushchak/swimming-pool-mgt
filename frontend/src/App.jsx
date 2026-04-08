import React, { useState, useEffect, useCallback, useRef } from 'react';
import PoolCard from './components/PoolCard';

function App() {
  const [config, setConfig] = useState(null);
  const [pools, setPools] = useState([]);
  const [poolStatuses, setPoolStatuses] = useState({});
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    loadConfig();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch('config.json');
      if (!response.ok) {
        throw new Error('Failed to load config');
      }
      const data = await response.json();
      
      if (!data.apiKey) {
        setError('API key is not configured');
        return;
      }
      
      setConfig(data);
      await loadPools(data);
    } catch (err) {
      console.error('Config load error:', err);
      setError('Failed to load configuration');
    }
  };

  const loadPools = async (cfg) => {
    try {
      const response = await fetch(`${cfg.apiUrl}/api/v1/pools`, {
        headers: { 'X-API-Key': cfg.apiKey }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setPools(data);
      setLoading(false);
      connectWebSocket(cfg);
    } catch (err) {
      console.error('Failed to load pools:', err);
      setError('Failed to connect to server');
      setLoading(false);
    }
  };

  const connectWebSocket = (cfg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const url = cfg.apiKey 
      ? `${cfg.wsUrl}/api/v1/ws/status?api_key=${cfg.apiKey}`
      : `${cfg.wsUrl}/api/v1/ws/status`;

    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      reconnectAttempts.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handlePoolUpdate(data);
      } catch (err) {
        console.error('Failed to parse message:', err);
      }
    };

    wsRef.current.onclose = () => {
      setConnected(false);
      scheduleReconnect(cfg);
    };

    wsRef.current.onerror = () => {
      setConnected(false);
    };
  };

  const scheduleReconnect = (cfg) => {
    const maxAttempts = 10;
    if (reconnectAttempts.current >= maxAttempts) {
      return;
    }

    reconnectAttempts.current++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current - 1), 30000);
    
    setTimeout(() => {
      if (!connected) {
        connectWebSocket(cfg);
      }
    }, delay);
  };

  const handlePoolUpdate = (data) => {
    if (data.error) {
      console.error('Pool update error:', data.error);
      return;
    }

    setPoolStatuses(prev => ({
      ...prev,
      [data.pool_id]: { ...prev[data.pool_id], ...data }
    }));
  };

  const handleAction = async (poolId, action) => {
    if (!config) return;

    try {
      const endpoint = action === 'resume' ? 'resume' : action;
      const response = await fetch(`${config.apiUrl}/api/v1/pools/${poolId}/${endpoint}`, {
        method: 'PUT',
        headers: { 'X-API-Key': config.apiKey }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      showToast(result.message || `${action} successful`, 'success');
    } catch (err) {
      console.error(`Failed to ${action}:`, err);
      showToast(`Failed to ${action} pool`, 'error');
    }
  };

  const handleRefresh = async () => {
    if (!config) return;

    setRefreshing(true);
    
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        await new Promise(resolve => setTimeout(resolve, 100));
        connectWebSocket(config);
      }

      const response = await fetch(`${config.apiUrl}/api/v1/pools`, {
        headers: { 'X-API-Key': config.apiKey }
      });

      if (response.ok) {
        const data = await response.json();
        setPools(data);
        setPoolStatuses({});
        showToast('Refreshed', 'success');
      }
    } catch (err) {
      console.error('Refresh failed:', err);
      showToast('Refresh failed', 'error');
    } finally {
      setTimeout(() => setRefreshing(false), 500);
    }
  };

  const showToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  if (error) {
    return (
      <div className="config-error">
        <span className="material-symbols-rounded">error</span>
        <h2>Configuration Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (loading || !config) {
    return (
      <div className="loading-state">
        <span className="material-symbols-rounded">pool</span>
        <p>Loading pools...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>
          <span className="material-symbols-rounded">pool</span>
          Pool Management
        </h1>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          <span className="material-symbols-rounded">
            {connected ? 'wifi' : 'wifi_off'}
          </span>
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <div className="pools-grid">
        {pools.map(pool => (
          <PoolCard
            key={pool.id}
            pool={pool}
            status={poolStatuses[pool.id] || {}}
            onAction={handleAction}
          />
        ))}
      </div>

      <button 
        className={`fab ${refreshing ? 'refreshing' : ''}`}
        onClick={handleRefresh}
        title="Refresh"
      >
        <span className="material-symbols-rounded">refresh</span>
      </button>

      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            <span className="material-symbols-rounded">
              {toast.type === 'success' ? 'check_circle' : toast.type === 'error' ? 'error' : 'info'}
            </span>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
