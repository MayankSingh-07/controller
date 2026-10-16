// client/touch_engine.js - Multi-touch engine with zero-overhead dispatch
(function (global) {
  'use strict';

  const BTN_A       = 1 << 0;
  const BTN_B       = 1 << 1;
  const BTN_X       = 1 << 2;
  const BTN_Y       = 1 << 3;
  const DPAD_UP     = 1 << 4;
  const DPAD_DOWN   = 1 << 5;
  const DPAD_LEFT   = 1 << 6;
  const DPAD_RIGHT  = 1 << 7;
  const BTN_LB      = 1 << 8;
  const BTN_RB      = 1 << 9;
  const BTN_START   = 1 << 10;
  const BTN_BACK    = 1 << 11;
  const BTN_LS      = 1 << 12;
  const BTN_RS      = 1 << 13;
  const BTN_GUIDE   = 1 << 14;

  const BUTTON_MAP = {
    'a': BTN_A,
    'b': BTN_B,
    'x': BTN_X,
    'y': BTN_Y,
    'dpad_up': DPAD_UP,
    'dpad_down': DPAD_DOWN,
    'dpad_left': DPAD_LEFT,
    'dpad_right': DPAD_RIGHT,
    'lb': BTN_LB,
    'rb': BTN_RB,
    'start': BTN_START,
    'back': BTN_BACK,
    'guide': BTN_GUIDE,
    'ls': BTN_LS,
    'rs': BTN_RS
  };

  class TouchEngine {
    constructor(sendCallback) {
      this.send = sendCallback || function () {};
      this.buttons = 0;
      this.lx = 0;
      this.ly = 0;
      this.rx = 0;
      this.ry = 0;
      this.lt = 0;
      this.rt = 0;

      // Active pointers map: pointerId -> { btn, type }
      this.activePointers = new Map();
      this.stickPointerId = null;
      this.stickCenter = { x: 0, y: 0 };
      this.stickMaxRadius = 45;

      this.initButtons();
      this.initAnalogStick();
    }

    triggerHaptic() {
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        try { navigator.vibrate(12); } catch (e) {}
      }
    }

    dispatchState() {
      if (typeof Protocol !== 'undefined') {
        const frame = Protocol.packInputFrame(
          this.buttons,
          this.lx,
          this.ly,
          this.rx,
          this.ry,
          this.lt,
          this.rt
        );
        this.send(frame);
      }
    }

    initButtons() {
      const buttonElements = document.querySelectorAll('[data-btn]');
      buttonElements.forEach(el => {
        const btnKey = el.getAttribute('data-btn');
        const isTrigger = el.hasAttribute('data-trigger');
        const triggerKey = el.getAttribute('data-trigger');

        const onPointerDown = (e) => {
          e.preventDefault();
          el.setPointerCapture?.(e.pointerId);
          el.classList.add('btn-pressed');
          this.triggerHaptic();

          if (isTrigger) {
            if (triggerKey === 'lt') this.lt = 255;
            if (triggerKey === 'rt') this.rt = 255;
          }

          const mask = BUTTON_MAP[btnKey];
          if (mask) {
            this.buttons |= mask;
          }

          this.activePointers.set(e.pointerId, { el, btnKey, isTrigger, triggerKey });
          this.dispatchState();
        };

        const onPointerUp = (e) => {
          e.preventDefault();
          el.classList.remove('btn-pressed');

          if (isTrigger) {
            if (triggerKey === 'lt') this.lt = 0;
            if (triggerKey === 'rt') this.rt = 0;
          }

          const mask = BUTTON_MAP[btnKey];
          if (mask) {
            this.buttons &= ~mask;
          }

          this.activePointers.delete(e.pointerId);
          this.dispatchState();
        };

        el.addEventListener('pointerdown', onPointerDown, { passive: false });
        el.addEventListener('pointerup', onPointerUp, { passive: false });
        el.addEventListener('pointercancel', onPointerUp, { passive: false });
      });
    }

    initAnalogStick() {
      const stickContainer = document.getElementById('analog-stick');
      const stickThumb = document.getElementById('stick-thumb');
      if (!stickContainer || !stickThumb) return;

      const base = stickContainer.querySelector('.stick-base');

      const onPointerDown = (e) => {
        if (this.stickPointerId !== null) return;
        e.preventDefault();
        base.setPointerCapture?.(e.pointerId);
        this.stickPointerId = e.pointerId;

        const rect = base.getBoundingClientRect();
        this.stickCenter = {
          x: rect.left + rect.width / 2,
          y: rect.top + rect.height / 2
        };

        this.updateStick(e.clientX, e.clientY, stickThumb);
      };

      const onPointerMove = (e) => {
        if (e.pointerId !== this.stickPointerId) return;
        e.preventDefault();
        this.updateStick(e.clientX, e.clientY, stickThumb);
      };

      const onPointerUp = (e) => {
        if (e.pointerId !== this.stickPointerId) return;
        e.preventDefault();
        this.stickPointerId = null;
        stickThumb.style.transform = `translate(0px, 0px)`;
        this.lx = 0;
        this.ly = 0;
        this.dispatchState();
      };

      base.addEventListener('pointerdown', onPointerDown, { passive: false });
      base.addEventListener('pointermove', onPointerMove, { passive: false });
      base.addEventListener('pointerup', onPointerUp, { passive: false });
      base.addEventListener('pointercancel', onPointerUp, { passive: false });
    }

    updateStick(clientX, clientY, stickThumb) {
      const dx = clientX - this.stickCenter.x;
      const dy = clientY - this.stickCenter.y;
      const dist = Math.hypot(dx, dy);

      let clampedX = dx;
      let clampedY = dy;
      if (dist > this.stickMaxRadius) {
        clampedX = (dx / dist) * this.stickMaxRadius;
        clampedY = (dy / dist) * this.stickMaxRadius;
      }

      stickThumb.style.transform = `translate(${clampedX}px, ${clampedY}px)`;

      // Deadzone filtering (10%)
      const normalizedDist = Math.min(1.0, dist / this.stickMaxRadius);
      if (normalizedDist < 0.10) {
        this.lx = 0;
        this.ly = 0;
      } else {
        // Normalize to full range -32768..32767
        // Note: In XInput, positive Y is UP, negative Y is DOWN. Screen Y is inverted!
        this.lx = Math.round((clampedX / this.stickMaxRadius) * 32767);
        this.ly = Math.round((-clampedY / this.stickMaxRadius) * 32767);
      }

      this.dispatchState();
    }
  }

  global.TouchEngine = TouchEngine;
})(typeof window !== 'undefined' ? window : globalThis);
