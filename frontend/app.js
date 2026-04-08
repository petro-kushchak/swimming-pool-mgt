/* Pool Management Frontend Application */

class PoolApp {
  constructor() {
    this.config = null;
    this.pools = new Map();
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.apiKey = '';
    
    this.elements = {
      poolsGrid: document.getElementById('poolsGrid'),
      loadingState: document.getElementById('loadingState'),
      connectionStatus: document.getElementById('connectionStatus'),
      fabRefresh: document.getElementById('fabRefresh'),
      toastContainer: document.getElementById('toastContainer'),
      confirmDialog: document.getElementById('confirmDialog'),
    };
    
    this.init();
  }

  async init() {
    const configOk = await this.loadConfig();
    if (!configOk) {
      return;
    }
    this.bindEvents();
    await this.loadInitialData();
    this.connectWebSocket();
  }

  async loadConfig() {
    try {
      const response = await fetch(`config.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error('Failed to load config');
      }
      this.config = await response.json();
      
      if (!this.config.apiKey) {
        this.showConfigError('API key is not configured. Please set API_KEY in your deployment configuration.');
        return false;
      }
      
      this.apiKey = this.config.apiKey;
      return true;
    } catch (error) {
      console.error('Failed to load config:', error);
      this.showConfigError('Failed to load configuration. Please check your deployment.');
      return false;
    }
  }

  getApiBase() {
    return this.config?.apiUrl || '';
  }

  getWsUrl() {
    const base = this.config?.wsUrl || '';
    return `${base}/api/v1/ws/status`;
  }

  bindEvents() {
    this.elements.fabRefresh.addEventListener('click', () => this.refreshAll());
    
    window.addEventListener('online', () => this.connectWebSocket());
    window.addEventListener('offline', () => this.handleDisconnect());
  }

  async loadInitialData() {
    try {
      const response = await fetch(`${this.getApiBase()}/api/v1/pools`, {
        headers: this.getHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const pools = await response.json();
      
      if (pools.length === 0) {
        this.showEmptyState();
        return;
      }
      
      this.renderPools(pools);
      this.connectWebSocket();
    } catch (error) {
      console.error('Failed to load pools:', error);
      this.showErrorState('Failed to connect to server');
    }
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    return headers;
  }

  connectWebSocket() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const url = this.apiKey ? `${this.getWsUrl()}?api_key=${this.apiKey}` : this.getWsUrl();
    
    try {
      this.ws = new WebSocket(url);
      this.setupWebSocketHandlers();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleDisconnect();
    }
  }

  setupWebSocketHandlers() {
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.updateConnectionStatus(true);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlePoolUpdate(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.handleDisconnect();
      
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleDisconnect();
    };
  }

  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.elements.connectionStatus.classList.contains('disconnected')) {
        this.connectWebSocket();
      }
    }, delay);
  }

  updateConnectionStatus(connected) {
    const statusEl = this.elements.connectionStatus;
    const iconEl = statusEl.querySelector('.status-icon');
    const textEl = statusEl.querySelector('.status-text');
    
    statusEl.classList.remove('connected', 'disconnected');
    
    if (connected) {
      statusEl.classList.add('connected');
      iconEl.textContent = 'wifi';
      textEl.textContent = 'Connected';
    } else {
      statusEl.classList.add('disconnected');
      iconEl.textContent = 'wifi_off';
      textEl.textContent = 'Disconnected';
    }
  }

  handleDisconnect() {
    this.updateConnectionStatus(false);
  }

  handlePoolUpdate(data) {
    if (data.error) {
      console.error('Pool update error:', data.error);
      return;
    }

    const { pool_id, ...status } = data;
    this.pools.set(pool_id, { ...this.pools.get(pool_id), ...status });
    this.updatePoolCard(pool_id, status);
  }

  renderPools(pools) {
    this.elements.loadingState.style.display = 'none';
    
    pools.forEach(pool => {
      this.pools.set(pool.id, pool);
      const card = this.createPoolCard(pool);
      this.elements.poolsGrid.appendChild(card);
    });
  }

  createPoolCard(pool) {
    const template = document.getElementById('poolCardTemplate');
    const card = template.content.cloneNode(true).querySelector('.pool-card');
    
    card.dataset.poolId = pool.id;
    
    const nameEl = card.querySelector('.pool-name');
    const locationEl = card.querySelector('.pool-location');
    nameEl.textContent = pool.name;
    locationEl.textContent = pool.location || '';
    
    const startBtn = card.querySelector('.action-start');
    const stopBtn = card.querySelector('.action-stop');
    const resumeBtn = card.querySelector('.action-resume');
    
    startBtn.addEventListener('click', () => this.handleAction(pool.id, 'start'));
    stopBtn.addEventListener('click', () => this.handleAction(pool.id, 'stop'));
    resumeBtn.addEventListener('click', () => this.handleAction(pool.id, 'resume'));
    
    this.renderSchedule(pool, card);
    this.renderDevice(pool, card);
    
    this.updatePoolCard(pool.id, {});
    
    return card;
  }

  renderSchedule(pool, card) {
    const scheduleSection = card.querySelector('#scheduleSection');
    
    if (!pool.schedule || pool.schedule.length === 0) {
      scheduleSection.style.display = 'none';
      return;
    }
    
    scheduleSection.style.display = 'block';
    const scheduleList = card.querySelector('.schedule-list');
    
    pool.schedule.forEach(entry => {
      const li = document.createElement('li');
      li.className = 'schedule-item';
      li.innerHTML = `
        <span class="time">${entry.startAt}</span>
        <span class="duration">${entry.duration}</span>
      `;
      scheduleList.appendChild(li);
    });
  }

  renderDevice(pool, card) {
    const deviceSection = card.querySelector('#deviceSection');
    
    if (!pool.device) {
      deviceSection.style.display = 'none';
      return;
    }
    
    deviceSection.style.display = 'block';
    const deviceNameEl = card.querySelector('.device-name');
    const deviceStatusEl = card.querySelector('.device-status');
    
    deviceNameEl.textContent = pool.device.name;
    deviceStatusEl.textContent = 'Configured';
    deviceStatusEl.classList.add('online');
  }

  updatePoolCard(poolId, status) {
    const card = this.elements.poolsGrid.querySelector(`[data-pool-id="${poolId}"]`);
    if (!card) return;

    const chip = card.querySelector('.pool-status-chip');
    const chipIcon = chip.querySelector('.chip-icon');
    const chipText = chip.querySelector('.chip-text');
    
    const statusRing = card.querySelector('.status-ring');
    const ringProgress = statusRing.querySelector('.ring-progress');
    const ringIcon = card.querySelector('.ring-icon .material-symbols-rounded');
    
    const statusLabel = card.querySelector('.status-label');
    const statusTime = card.querySelector('.status-time');
    const statusRemaining = card.querySelector('.status-remaining');
    
    const startBtn = card.querySelector('.action-start');
    const stopBtn = card.querySelector('.action-stop');
    const resumeBtn = card.querySelector('.action-resume');
    
    chip.classList.remove('filtering', 'stopped', 'scheduled', 'manual');
    statusRing.classList.remove('filtering', 'stopped', 'scheduled');
    
    let state = 'stopped';
    let label = 'Stopped';
    let icon = 'stop';
    let progress = 0;
    
    if (status.manual_override === true || status.manual_override === 'running') {
      state = 'manual';
      label = 'Manual';
      icon = 'play_arrow';
      progress = 100;
    } else if (status.filtering) {
      state = 'filtering';
      label = 'Filtering';
      icon = 'water';
      progress = status.remaining_minutes 
        ? Math.max(0, 100 - (status.remaining_minutes / 60) * 100) 
        : 100;
    } else if (status.next_filter) {
      state = 'scheduled';
      label = 'Scheduled';
      icon = 'schedule';
      progress = 0;
    }
    
    chip.classList.add(state);
    chipIcon.textContent = icon;
    chipText.textContent = label;
    
    statusRing.classList.add(state);
    ringProgress.style.strokeDashoffset = 100 - progress;
    ringIcon.textContent = icon;
    
    statusLabel.textContent = status.filtering ? 'Active' : status.next_filter ? 'Next' : 'Idle';
    
    if (status.ends_at) {
      statusTime.textContent = `Ends at ${status.ends_at}`;
    } else if (status.next_filter) {
      statusTime.textContent = `Next at ${status.next_filter}`;
    } else if (status.last_filtered) {
      statusTime.textContent = `Last: ${status.last_filtered}`;
    } else {
      statusTime.textContent = '';
    }
    
    if (status.remaining_minutes !== null && status.remaining_minutes !== undefined) {
      statusRemaining.textContent = `${status.remaining_minutes} min remaining`;
      statusRemaining.style.display = 'block';
    } else {
      statusRemaining.style.display = 'none';
    }
    
    const hasManualOverride = status.manual_override !== null && status.manual_override !== undefined;
    const isFiltering = status.filtering;
    
    startBtn.disabled = isFiltering || hasManualOverride;
    stopBtn.disabled = !isFiltering && !hasManualOverride;
    resumeBtn.disabled = !hasManualOverride;
    
    const scheduleItems = card.querySelectorAll('.schedule-item');
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    
    scheduleItems.forEach(item => {
      const timeStr = item.querySelector('.time').textContent;
      const [h, m] = timeStr.split(':').map(Number);
      const timeMinutes = h * 60 + m;
      
      item.classList.toggle('active', timeMinutes <= currentMinutes && timeMinutes + 180 > currentMinutes);
    });
  }

  async handleAction(poolId, action) {
    const endpoint = action === 'resume' ? 'resume' : action;
    const method = 'PUT';
    
    try {
      const response = await fetch(`${this.getApiBase()}/api/v1/pools/${poolId}/${endpoint}`, {
        method,
        headers: this.getHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.message) {
        this.showToast(result.message, 'success');
      }
    } catch (error) {
      console.error(`Failed to ${action} pool:`, error);
      this.showToast(`Failed to ${action} pool`, 'error');
    }
  }

  async refreshAll() {
    this.elements.fabRefresh.classList.add('refreshing');
    
    try {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.close();
        await new Promise(resolve => setTimeout(resolve, 100));
        this.connectWebSocket();
      }
      
      const response = await fetch(`${this.getApiBase()}/api/v1/pools`, {
        headers: this.getHeaders(),
      });
      
      if (response.ok) {
        const pools = await response.json();
        this.elements.poolsGrid.innerHTML = '';
        this.pools.clear();
        this.renderPools(pools);
        this.showToast('Refreshed', 'success');
      }
    } catch (error) {
      console.error('Refresh failed:', error);
      this.showToast('Refresh failed', 'error');
    } finally {
      setTimeout(() => {
        this.elements.fabRefresh.classList.remove('refreshing');
      }, 500);
    }
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    toast.innerHTML = `
      <span class="material-symbols-rounded">${icon}</span>
      <span>${message}</span>
    `;
    
    this.elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add('hiding');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  showConfigError(message) {
    this.elements.loadingState.innerHTML = `
      <span class="material-symbols-rounded" style="font-size: 48px; color: var(--md-error);">key</span>
      <p style="color: var(--md-on-surface); font-weight: 500;">Configuration Error</p>
      <p style="color: var(--md-on-surface-variant);">${message}</p>
    `;
  }

  showEmptyState() {
    this.elements.loadingState.innerHTML = `
      <span class="material-symbols-rounded" style="font-size: 48px; color: var(--md-outline);">pool</span>
      <p>No pools configured</p>
    `;
  }

  showErrorState(message) {
    this.elements.loadingState.innerHTML = `
      <span class="material-symbols-rounded" style="font-size: 48px; color: var(--md-error);">error</span>
      <p>${message}</p>
      <button class="action-button action-start" onclick="location.reload()">
        <span class="material-symbols-rounded">refresh</span>
        Retry
      </button>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new PoolApp();
});
