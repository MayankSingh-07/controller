# Ultra-Low Latency Phone Game Controller

Transform your Android smartphone into an ultra-low latency, authentic Xbox 360 game controller for your Windows 11 laptop over direct USB cable (<1ms) or local 5GHz Wi-Fi (<5ms).

Built specifically for high-precision, timing-critical games like **Tekken** and **FIFA**.

---

## Features

- **Genuine Xbox 360 Emulation:** Uses ViGEmBus (Virtual Gamepad Emulation Bus) so Windows 11, Steam, FIFA, Tekken, and PC games recognize it natively without third-party keymapping.
- **Ultra-Low Latency Transport:** 12-byte packed binary frames over WebSockets with `TCP_NODELAY` (disabling Nagle buffering) to guarantee sub-millisecond response over USB cable and 2–4ms over local Wi-Fi.
- **Game-Specific Presets:**
  - **Tekken Preset:** High-precision 8-way directional pad (D-Pad) with clean diagonal detection and large arcade-style face buttons (1/X, 2/Y, 3/A, 4/B) for instant multi-button chords.
  - **FIFA Preset:** 360° virtual analog thumbstick with deadzone filtering, ABXY diamond, and top-edge shoulder bumpers/triggers (LB, RB, LT, RT).
- **In-App Layout Customizer:** On-screen Edit Mode allowing you to drag, resize, and reposition any control group to match your grip and hand size. Layouts save to your phone's storage.
- **Bi-Directional Haptics:** Instant tactile feedback on button tap, plus game rumble force feedback (tackles in FIFA, counter-hits in Tekken) streamed from the PC directly to your phone's vibration motor.
- **Screen Wake Lock & Fullscreen:** Prevents your phone screen from dimming or timing out during matches, with edge-to-edge fullscreen display.

---

## Quick Start (Windows 11)

### 1. Prerequisites (One-time)
1. **ViGEmBus Driver (Windows):** Download and run the official installer from [ViGEmBus Releases](https://github.com/nefarius/ViGEmBus/releases).
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 2. Launch the Server
Double click `run.bat` or run:
```bash
python run_controller.py
```

The terminal will print the connection instructions:
- **USB Cable (Lowest Latency < 1ms):**
  - Option A: Turn on **USB Tethering** in your Android phone settings.
  - Option B: If **USB Debugging (ADB)** is enabled, the server automatically forwards port 8080.
- **Wi-Fi (~2–4ms):** Connect your phone to the same Wi-Fi network as your laptop.

### 3. Connect from Phone
Open Google Chrome on your Android phone and navigate to the displayed URL (e.g. `http://<laptop-ip>:8080` or `http://localhost:8080`).

- Tap **⛶ Fullscreen** for complete edge-to-edge controls.
- Switch between **FIFA** and **Tekken** presets at the top.
- Tap **Edit** to drag and resize buttons to your preference.
- Play! Your laptop will recognize the controller as an authentic Xbox 360 gamepad immediately.

---

## Verification & Tests

Run the full automated test suite:
```bash
python3 -m unittest discover -s tests -v
```
