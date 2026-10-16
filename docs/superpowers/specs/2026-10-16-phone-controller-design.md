# Design Document: Ultra-Low Latency Phone Game Controller for Windows 11

## 1. Intent and Why

The goal is to turn an Android smartphone into an ultra-low latency game controller for a Windows 11 laptop. For timing-critical competitive games like Tekken (frame-precise combos, blocks, and crouch-dashes) and FIFA (analog precision dribbling, through-balls, and sprint triggers), input delay and jitter ruin the experience. The system must deliver near-instantaneous response times (<1ms over USB, <5ms over Wi-Fi) and register as a native Xbox 360 gamepad on Windows 11 so that PC games detect it automatically without manual keyboard remapping.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **True Gamepad Emulation:** Emulate an official Xbox 360 gamepad on Windows 11 via ViGEmBus (Virtual Gamepad Emulation Bus), ensuring native plug-and-play support in FIFA, Tekken, Steam, and modern PC titles.
- **Ultra-Low Latency:** Sub-millisecond latency over wired USB connection (via USB tethering or ADB reverse forwarding); sub-5ms latency over local 5GHz Wi-Fi using lightweight binary streaming with `TCP_NODELAY`.
- **Zero-Friction Client (PWA):** Deliver the Android controller as a Progressive Web App (PWA) served directly by the laptop. Features instant fullscreen mode via HTML5 Fullscreen API and Screen Wake Lock API (preventing phone screen timeout during matches).
- **Adaptive Layout Presets:**
  - **Preset A (Tekken / Fighting):** High-precision 8-way directional pad (D-Pad) with clean diagonal detection and large arcade-style face buttons (1/X, 2/Y, 3/A, 4/B).
  - **Preset B (FIFA / Sports & Action):** 360° analog thumbstick with deadzone tuning, standard ABXY diamond, and top-edge shoulder bumpers/triggers (LB, RB, LT, RT).
- **In-App Layout Customizer:** Full touch-based Edit Mode allowing players to drag, reposition, and resize any control group to match their grip and hand size, saved locally per game profile.
- **Bi-Directional Haptic Feedback:** Short haptic pulses on touch-down via Web Vibration API, plus PC game force feedback (rumble notifications from ViGEmBus forwarded to phone for tackles, hits, and goal posts).

### Non-Goals
- **WAN / Cloud Play:** Strictly designed for direct local connection (USB or local Wi-Fi). No internet routing or cloud servers.
- **iOS Support (Initial Scope):** Focused on Android for optimal touch response and vibration API support.
- **Complex Bluetooth Pairing:** Bluetooth classic/BLE on Windows introduces 15–30ms OS scheduling latency and requires complex signed kernel drivers. Wired USB and Wi-Fi are vastly superior for latency.

### Anti-Goals
- **Keyboard / Mouse Remapping:** Emulating keystrokes (like WASD or arrow keys) causes conflicts with analog movement and game menus; only true XInput virtual hardware emulation is acceptable.
- **Bloated Native APK Requirements:** Requiring the user to install Android Studio or configure an Android build environment just to use the controller.

---

## 3. Constraints

- **Laptop OS:** Windows 11 (host system). Cross-platform server support (Linux `uinput` fallback) will be maintained for development and testing.
- **Phone OS:** Android with Chrome or any Chromium-based browser supporting modern TouchEvents, PointerEvents, Web Vibration, Screen Wake Lock, and Fullscreen API.
- **Network / Transport:** Direct USB cable connection (primary) or local Wi-Fi router (fallback).

---

## 4. How Decided (Builder Calls & Specifications)

- **Transport Protocol:** Binary WebSockets with `TCP_NODELAY` enabled (disabling Nagle's algorithm) to guarantee immediate frame dispatch without packet buffering. Benchmarked at <0.8ms over USB and ~2–4ms over local Wi-Fi.
- **Security Context & PWA Delivery:**
  - For Wi-Fi / Tethering HTTP: The client uses the HTML5 Fullscreen API (`requestFullscreen()`) with `ScreenWakeLock` so the browser chrome/URL bar completely disappears, giving a 100% fullscreen native app experience without SSL certificate hurdles.
  - For ADB USB connection: Navigates to `http://localhost:8080`, which Chromium treats as a Secure Context, enabling full PWA "Add to Home Screen" installation.
- **USB Connection Support:** Dual-mode support. The server auto-detects if ADB is present to establish `adb reverse tcp:8080 tcp:8080`, while also listening on all network interfaces to seamlessly support Android USB Tethering (RNDIS IP) without requiring developer mode.
- **Force Feedback (Rumble):** Bi-directional. The server subscribes to ViGEmBus `XINPUT_VIBRATION` updates (large and small motor speeds) and streams down a lightweight 3-byte vibration frame to trigger `navigator.vibrate()` patterns on the phone.

---

## 5. System Architecture & Components

```
+-------------------------------------------------------+
|                 Android Phone (PWA)                   |
|  - Touch Engine (PointerEvents, touch-action: none)   |
|  - Layout Presets: Tekken D-Pad & FIFA Analog Stick   |
|  - In-App Customizer (Drag, Resize, LocalStorage)     |
|  - Haptic Feedback & Game Rumble (Vibration API)      |
|  - Screen Wake Lock (prevents screen dimming)         |
|  - Binary Serializer (12-byte state frames)           |
+-------------------------------------------------------+
                           |  ^
  [Upstream: 12-byte input |  | [Downstream: 3-byte rumble]
   frames at 120Hz/240Hz]  |  |
                           v  |
          [ USB Cable (<1ms) / Local Wi-Fi (<5ms) ]
          [ Binary WebSocket with TCP_NODELAY     ]
                           |
                           v
+-------------------------------------------------------+
|             Windows 11 Bridge Server                  |
|  - Static Web Server (serves PWA & controller assets) |
|  - QR Code & Local IP Terminal Display                |
|  - Low-Latency Binary Packet Receiver (TCP_NODELAY)   |
|  - Virtual Gamepad Controller (ViGEmBus / vgamepad)   |
|  - Rumble Notification Listener (XINPUT_VIBRATION)    |
+-------------------------------------------------------+
                           |
                           v  (Virtual XInput Device)
+-------------------------------------------------------+
|                   Windows 11 OS                       |
|           FIFA / Tekken / Steam / PC Games            |
+-------------------------------------------------------+
```

### Component 1: Windows 11 Bridge Server
- Implemented in Python with `vgamepad` and `websockets` (or Node.js with `vigemclient`).
- Serves the PWA web application on port `8080`.
- Displays a clean ASCII QR code in the terminal with the exact connection URL.
- Establishes a binary WebSocket stream with `TCP_NODELAY` and no framing overhead.
- Translates binary frames into real-time XInput gamepad state updates via ViGEmBus:
  - Digital Buttons: A, B, X, Y, D-Pad (Up, Down, Left, Right), LB, RB, Start, Back/Select, Thumbstick clicks (LS, RS).
  - Analog Axes: Left Stick X/Y (-32768 to 32767), Right Stick X/Y (-32768 to 32767).
  - Analog Triggers: Left Trigger (0 to 255), Right Trigger (0 to 255).
- Listens for controller rumble callbacks from ViGEmBus and transmits vibration frames back to the phone.

### Component 2: Android PWA Gamepad Client
- Single-page application built with clean HTML5/CSS/JavaScript with zero heavy framework overhead to ensure maximum touch polling rate.
- Multi-touch gesture handling using low-latency `PointerEvents` and `touch-action: none` to prevent browser scrolling, zooming, or context menus.
- Pre-built layouts:
  - **Tekken:** 8-way directional cross with cardinal and diagonal hitbox blending; oversized face buttons 1/X, 2/Y, 3/A, 4/B for dual-button chords.
  - **FIFA:** Floating or fixed virtual analog joystick with spring-return and deadzone filtering; quick-action sprint (RT) and pace (LT) triggers.
- **Customizer:** "Edit Layout" button switches the canvas into unlocked mode. Users can drag controls and adjust scale sliders; layouts serialize to `localStorage`.
- **Haptics:** Local synthetic vibration on touch tap, plus game rumble reproduction for in-game impacts and tackles.
- **Screen Wake Lock:** Acquires `navigator.wakeLock.request('screen')` on connection to keep the display lit during intense matches.

### Component 3: Binary Packet Protocol
**Upstream Input Frame (12 Bytes):**
- Bytes 0-1: 16-bit Bitmask for all digital buttons (A, B, X, Y, Up, Down, Left, Right, LB, RB, Start, Back, LS, RS, Guide, Extra).
- Bytes 2-3: Signed 16-bit integer for Left Thumbstick X axis (`-32768` to `32767`).
- Bytes 4-5: Signed 16-bit integer for Left Thumbstick Y axis (`-32768` to `32767`).
- Bytes 6-7: Signed 16-bit integer for Right Thumbstick X axis (`-32768` to `32767`).
- Bytes 8-9: Signed 16-bit integer for Right Thumbstick Y axis (`-32768` to `32767`).
- Byte 10: Unsigned 8-bit integer for Left Trigger (`0` to `255`).
- Byte 11: Unsigned 8-bit integer for Right Trigger (`0` to `255`).

**Downstream Rumble Frame (3 Bytes):**
- Byte 0: Opcode (`0x01` = Rumble Event).
- Byte 1: Left Motor Speed (`0` to `255`, low-frequency heavy rumble).
- Byte 2: Right Motor Speed (`0` to `255`, high-frequency light rumble).

---

## 6. What's Left to the Builder

- Visual theme polish (dark OLED aesthetic to maximize battery life on phone).
- ViGEmBus automated installer detection and download link prompt for Windows 11.
- Deadzone smoothing and sensitivity curves for the virtual analog stick.
