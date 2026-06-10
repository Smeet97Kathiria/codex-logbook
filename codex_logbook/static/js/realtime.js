// Realtime websocket updates for local Codex Logbook dashboards.
(function () {
  const state = {
    socket: null,
    reconnectTimer: null,
    reconnectAttempts: 0,
    refreshTimer: null,
    lastUpdateAt: null,
    desiredSubscription: null
  };

  function isLocalRealtimeAvailable() {
    return window.location.protocol === 'http:' || window.location.protocol === 'https:';
  }

  function getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/updates`;
  }

  function ensureStatusElement() {
    let status = document.getElementById('realtime-status');
    if (status) {
      return status;
    }

    const controls = document.querySelector('.header-controls');
    if (!controls) {
      return null;
    }

    status = document.createElement('span');
    status.id = 'realtime-status';
    status.className = 'realtime-status';
    status.textContent = 'Realtime: connecting';
    status.style.cssText = [
      'display:inline-flex',
      'align-items:center',
      'gap:0.35rem',
      'padding:0.42rem 0.7rem',
      'border:1px solid rgba(122,101,73,0.22)',
      'border-radius:999px',
      'font-size:0.78rem',
      'font-weight:600',
      'color:#7A6549',
      'background:rgba(255,248,235,0.88)',
      'white-space:nowrap'
    ].join(';');
    controls.appendChild(status);
    return status;
  }

  function setStatus(text, mode = 'neutral') {
    const status = ensureStatusElement();
    if (!status) {
      return;
    }

    status.textContent = text;
    const colors = {
      connected: ['#276749', 'rgba(236,253,245,0.92)', 'rgba(39,103,73,0.22)'],
      updating: ['#8A4B11', 'rgba(255,248,235,0.96)', 'rgba(235,106,28,0.28)'],
      offline: ['#8A1F11', 'rgba(255,241,235,0.92)', 'rgba(138,31,17,0.24)'],
      neutral: ['#7A6549', 'rgba(255,248,235,0.88)', 'rgba(122,101,73,0.22)']
    };
    const [color, background, border] = colors[mode] || colors.neutral;
    status.style.color = color;
    status.style.background = background;
    status.style.borderColor = border;
    window.__codexRealtimeConnected = mode === 'connected';
  }

  function projectMatchesCurrentDashboard(message) {
    if (!window.currentLogPath) {
      return true;
    }

    return Array.isArray(message.log_paths) && message.log_paths.includes(window.currentLogPath);
  }

  function scheduleDashboardRefresh(message) {
    if (window.location.pathname === '/' || window.location.pathname === '/overview.html') {
      // Overview pages handle realtime updates through the dispatched
      // codex-logbook:realtime-update event. Avoid invoking the handler here
      // as well, otherwise every websocket event is processed twice.
      return;
    }

    if (!projectMatchesCurrentDashboard(message)) {
      return;
    }

    if (typeof window.handleRealtimeDashboardUpdate === 'function') {
      window.handleRealtimeDashboardUpdate(message);
      return;
    }

    clearTimeout(state.refreshTimer);
    setStatus('Realtime: update received', 'updating');
    state.refreshTimer = setTimeout(() => {
      sessionStorage.setItem('dataRefreshStartTime', Date.now().toString());
      sessionStorage.setItem('dataRefreshTime', '0');
      window.location.reload();
    }, 700);
  }

  function sendJson(message) {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    state.socket.send(JSON.stringify(message));
  }

  function getDefaultSubscription() {
    if (window.location.pathname === '/' || window.location.pathname === '/overview.html') {
      return { type: 'subscribe', scope: 'overview' };
    }

    if (window.currentLogPath) {
      return { type: 'subscribe', scope: 'projects', log_paths: [window.currentLogPath] };
    }

    return null;
  }

  function syncSubscription() {
    const subscription = state.desiredSubscription || getDefaultSubscription();
    if (subscription) {
      sendJson(subscription);
    }
  }

  function connect() {
    if (!isLocalRealtimeAvailable() || !('WebSocket' in window)) {
      return;
    }

    clearTimeout(state.reconnectTimer);
    setStatus('Realtime: connecting');

    const socket = new WebSocket(getWebSocketUrl());
    state.socket = socket;

    socket.addEventListener('open', () => {
      state.reconnectAttempts = 0;
      setStatus('Realtime: live', 'connected');
      syncSubscription();
    });

    socket.addEventListener('message', event => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (error) {
        return;
      }

      if (message.type === 'ping') {
        sendJson({ type: 'pong', version: message.version || 1 });
        return;
      }

      if (message.type === 'connected' || message.type === 'pong' || message.type === 'subscribed') {
        setStatus('Realtime: live', 'connected');
        return;
      }

      if (message.type === 'dashboard_updated') {
        state.lastUpdateAt = Date.now();
        window.dispatchEvent(new CustomEvent('codex-logbook:realtime-update', { detail: message }));
        scheduleDashboardRefresh(message);
      }
    });

    socket.addEventListener('close', () => {
      setStatus('Realtime: reconnecting', 'offline');
      const jitter = Math.floor(Math.random() * 500);
      const delay = Math.min(30000, 1000 * Math.pow(2, state.reconnectAttempts)) + jitter;
      state.reconnectAttempts += 1;
      state.reconnectTimer = setTimeout(connect, delay);
    });

    socket.addEventListener('error', () => {
      setStatus('Realtime: offline', 'offline');
      socket.close();
    });
  }

  window.CodexLogbookRealtime = {
    connect,
    subscribeOverview: () => {
      state.desiredSubscription = { type: 'subscribe', scope: 'overview' };
      syncSubscription();
    },
    subscribeProject: (logPath) => {
      if (!logPath) {
        return;
      }
      state.desiredSubscription = { type: 'subscribe', scope: 'projects', log_paths: [logPath] };
      syncSubscription();
    },
    getState: () => ({ ...state })
  };

  window.addEventListener('DOMContentLoaded', connect);
})();
