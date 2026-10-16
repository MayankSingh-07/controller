// client/app.js - Main controller application orchestrator
(function () {
  'use strict';

  let socket = null;
  let touchEngine = null;
  let wakeLock = null;
  const indicator = document.getElementById('connection-indicator');

  // --- WebSocket Connection ---
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    if (indicator) {
      indicator.textContent = 'CONNECTING...';
      indicator.className = 'disconnected';
    }

    try {
      socket = new WebSocket(wsUrl);
      socket.binaryType = 'arraybuffer';

      socket.onopen = function () {
        if (indicator) {
          indicator.textContent = 'CONNECTED • <1ms';
          indicator.className = 'connected';
        }
        requestWakeLock();
      };

      socket.onmessage = function (event) {
        if (event.data instanceof ArrayBuffer) {
          const rumble = Protocol.unpackRumbleFrame(event.data);
          if (rumble) {
            handleRumble(rumble.leftMotor, rumble.rightMotor);
          }
        }
      };

      socket.onclose = function () {
        if (indicator) {
          indicator.textContent = 'RECONNECTING...';
          indicator.className = 'disconnected';
        }
        setTimeout(connectWebSocket, 1500);
      };

      socket.onerror = function () {
        socket.close();
      };
    } catch (e) {
      setTimeout(connectWebSocket, 2000);
    }
  }

  function sendPacket(buffer) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(buffer);
    }
  }

  // --- Bi-Directional Force Feedback (Rumble) ---
  function handleRumble(leftMotor, rightMotor) {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      const maxMotor = Math.max(leftMotor, rightMotor);
      if (maxMotor > 0) {
        // Calculate duration based on motor intensity (20ms to 120ms)
        const duration = Math.round(20 + (maxMotor / 255) * 100);
        try {
          navigator.vibrate(duration);
        } catch (e) {}
      }
    }
  }

  // --- Screen Wake Lock ---
  async function requestWakeLock() {
    if ('wakeLock' in navigator) {
      try {
        wakeLock = await navigator.wakeLock.request('screen');
      } catch (err) {}
    }
  }

  document.addEventListener('visibilitychange', async () => {
    if (wakeLock !== null && document.visibilityState === 'visible') {
      await requestWakeLock();
    }
  });

  // --- Fullscreen Toggle ---
  const btnFullscreen = document.getElementById('btn-fullscreen');
  if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen?.().catch(() => {});
      } else {
        document.exitFullscreen?.().catch(() => {});
      }
    });
  }

  // --- Preset Switching ---
  const btnFifa = document.getElementById('preset-fifa');
  const btnTekken = document.getElementById('preset-tekken');

  if (btnFifa && btnTekken) {
    btnFifa.addEventListener('click', () => {
      document.body.classList.remove('preset-tekken');
      document.body.classList.add('preset-fifa');
      btnFifa.classList.add('active');
      btnTekken.classList.remove('active');
    });

    btnTekken.addEventListener('click', () => {
      document.body.classList.remove('preset-fifa');
      document.body.classList.add('preset-tekken');
      btnTekken.classList.add('active');
      btnFifa.classList.remove('active');
    });
  }

  // Initialize on load
  window.addEventListener('DOMContentLoaded', () => {
    touchEngine = new TouchEngine(sendPacket);
    connectWebSocket();
  });
})();
