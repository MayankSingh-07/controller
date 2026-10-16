// client/customizer.js - Interactive Gamepad Layout Editor & Profile Manager
(function (global) {
  'use strict';

  const STORAGE_PREFIX = 'gamepad_layout_profile_';

  class LayoutManager {
    constructor() {
      this.isEditing = false;
      this.currentProfile = 'default';
      this.clusters = [
        { id: 'left-cluster', el: document.getElementById('left-cluster'), x: 0, y: 0, scale: 1.0 },
        { id: 'right-cluster', el: document.getElementById('right-cluster'), x: 0, y: 0, scale: 1.0 },
        { id: 'triggers-cluster', el: document.getElementById('triggers-cluster'), x: 0, y: 0, scale: 1.0 }
      ];

      this.toolbar = document.getElementById('customizer-toolbar');
      this.initDragEvents();
      this.initToolbar();
      this.loadLayout(this.currentProfile);
    }

    enableEditMode() {
      this.isEditing = true;
      document.body.classList.add('editing-active');
      if (this.toolbar) {
        this.toolbar.classList.remove('toolbar-hidden');
      }
    }

    disableEditMode() {
      this.isEditing = false;
      document.body.classList.remove('editing-active');
      if (this.toolbar) {
        this.toolbar.classList.add('toolbar-hidden');
      }
      this.saveLayout(this.currentProfile);
    }

    saveLayout(profileName = 'default') {
      const data = {};
      this.clusters.forEach(c => {
        data[c.id] = { x: c.x, y: c.y, scale: c.scale };
      });
      try {
        localStorage.setItem(STORAGE_PREFIX + profileName, JSON.stringify(data));
      } catch (e) {}
    }

    loadLayout(profileName = 'default') {
      try {
        const raw = localStorage.getItem(STORAGE_PREFIX + profileName);
        if (!raw) return;
        const data = JSON.parse(raw);
        this.clusters.forEach(c => {
          if (data[c.id] && c.el) {
            c.x = data[c.id].x || 0;
            c.y = data[c.id].y || 0;
            c.scale = data[c.id].scale || 1.0;
            c.el.style.transform = `translate(${c.x}px, ${c.y}px) scale(${c.scale})`;
          }
        });
      } catch (e) {}
    }

    resetLayout(profileName = 'default') {
      try {
        localStorage.removeItem(STORAGE_PREFIX + profileName);
      } catch (e) {}
      this.clusters.forEach(c => {
        c.x = 0;
        c.y = 0;
        c.scale = 1.0;
        if (c.el) {
          c.el.style.transform = '';
        }
      });
    }

    initToolbar() {
      const btnEdit = document.getElementById('btn-edit-mode');
      const btnExit = document.getElementById('btn-exit-edit');
      const btnSave = document.getElementById('btn-save-layout');
      const btnReset = document.getElementById('btn-reset-layout');

      if (btnEdit) {
        btnEdit.addEventListener('click', () => {
          if (this.isEditing) {
            this.disableEditMode();
          } else {
            this.enableEditMode();
          }
        });
      }

      if (btnExit) {
        btnExit.addEventListener('click', () => this.disableEditMode());
      }

      if (btnSave) {
        btnSave.addEventListener('click', () => {
          this.saveLayout(this.currentProfile);
          this.disableEditMode();
        });
      }

      if (btnReset) {
        btnReset.addEventListener('click', () => {
          this.resetLayout(this.currentProfile);
        });
      }
    }

    initDragEvents() {
      this.clusters.forEach(item => {
        if (!item.el) return;

        let startPointerX = 0;
        let startPointerY = 0;
        let startX = 0;
        let startY = 0;
        let dragging = false;

        item.el.addEventListener('pointerdown', (e) => {
          if (!this.isEditing) return;
          e.stopPropagation();
          dragging = true;
          item.el.setPointerCapture?.(e.pointerId);

          startPointerX = e.clientX;
          startPointerY = e.clientY;
          startX = item.x;
          startY = item.y;
        });

        item.el.addEventListener('pointermove', (e) => {
          if (!this.isEditing || !dragging) return;
          e.stopPropagation();

          const dx = e.clientX - startPointerX;
          const dy = e.clientY - startPointerY;

          item.x = startX + dx;
          item.y = startY + dy;
          item.el.style.transform = `translate(${item.x}px, ${item.y}px) scale(${item.scale})`;
        });

        const endDrag = (e) => {
          if (!this.isEditing || !dragging) return;
          dragging = false;
        };

        item.el.addEventListener('pointerup', endDrag);
        item.el.addEventListener('pointercancel', endDrag);
      });
    }
  }

  global.LayoutManager = LayoutManager;
})(typeof window !== 'undefined' ? window : globalThis);
