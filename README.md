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

## 1-Click Automated Setup (Windows 11)

Anyone can clone this repo and run it immediately—**all drivers and dependencies are downloaded and installed automatically**:

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd controller
   ```
2. Double-click **`setup.bat`** (or run `python run_controller.py`).
   - Automatically downloads and installs the official **ViGEmBus** Xbox gamepad driver if missing.
   - Automatically installs required Python packages.
   - Automatically starts the ultra-low latency controller bridge!
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


### 4. Always Ready (Zero-Touch Startup)
If you want the controller server to run automatically in the background without needing a terminal open:
- Double-click **`install_autostart.bat`**.
- Now, whenever your laptop boots or logs in, the controller bridge runs silently in the background (`pythonw.exe`, using negligible CPU/RAM).
- Pick up your phone anytime, tap your home screen icon, and it connects immediately.
- To remove auto-start at any time, run **`uninstall_autostart.bat`**.

### 5. Playing with Laptop Closed (Lid Closed Mode)
If you connect your laptop to a TV or external monitor and want to close the laptop lid:
1. In Windows 11, search for **"Control Panel"** -> **"Power Options"**.
2. Click **"Choose what closing the lid does"**.
3. Under *When I close the lid* (Plugged in), select **"Do nothing"**.
4. Now you can tuck the laptop away with the lid shut while playing games with your phone controller!

### 6. Standalone Android APK Project
A complete native Android app project is included in the `android/` directory:
- Built with hardware acceleration, native immersive fullscreen, and low-latency vibration.
- Bundles the controller UI internally inside APK assets (`android/app/src/main/assets/`).
- Open the `android/` folder in Android Studio and click **Build APK** to generate a standalone `.apk` installable on any Android phone!
---

## Verification & Tests

Run the full automated test suite:
```bash
python3 -m unittest discover -s tests -v
```
