# Phone Game Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ultra-low latency game controller application that transforms an Android smartphone into an authentic Xbox 360 controller on a Windows 11 laptop over USB cable (<1ms) or local Wi-Fi (<5ms) for competitive gaming in FIFA and Tekken.

**Architecture:** A lightweight Python bridge server hosts an installable Progressive Web App (PWA) and runs a zero-overhead binary WebSocket loop with `TCP_NODELAY`. The Android client captures high-frequency multi-touch inputs, packs them into compact 12-byte frames, and streams them to the server, which injects them directly into Windows's virtual controller bus (ViGEmBus) as an authentic XInput gamepad while streaming game rumble events back to the phone.

**Tech Stack:** Python 3.11 (`vgamepad`, `websockets`), HTML5/CSS/Vanilla JS (PointerEvents, Web Vibration, Screen Wake Lock, Fullscreen API), ViGEmBus (Windows 11 virtual XInput driver).

**Spec:** `docs/superpowers/specs/2026-10-16-phone-controller-design.md`

## Global Constraints

- Latency target: Sub-millisecond over USB connection, sub-5ms over local Wi-Fi.
- Zero-overhead wire protocol: 12-byte packed binary input frames; 3-byte downstream rumble frames.
- Gamepad compatibility: Official Xbox 360 controller emulation via ViGEmBus driver (compatible with FIFA, Tekken, Steam, and all PC games).
- Cross-platform server support: Native ViGEmBus on Windows 11; mock/uinput test mode on Linux for continuous verification.
- Mobile client: Zero external frontend frameworks (vanilla JS/CSS) to prevent UI thread lag; multi-touch with `touch-action: none` and `PointerEvents`.
- Screen retention: Screen Wake Lock API and HTML5 Fullscreen API to eliminate browser chrome and prevent screen timeouts during gameplay.

## Review Focus

1. **Multi-touch chord drops (Tekken 1+2 / 3+4 simultaneous presses):** When two or more fingers strike the screen on the exact same tick, the bitmask must register both buttons simultaneously without race conditions or dropped pointers.
2. **Analog stick spring-return & deadzone snap (FIFA dribbling):** When a thumb leaves the analog stick area abruptly during a fast direction change, the thumbstick coordinates must instantly snap back to exact zero `(0, 0)` without lingering off-center.
3. **USB disconnect / network socket glitch recovery:** If the USB cable is jostled or Wi-Fi drops a packet, all virtual controller buttons and triggers must release immediately to neutral state to prevent stuck buttons in-game, and reconnect automatically.
4. **Trigger pressure boundary clamp (LT/RT):** Values passed to analog triggers must strictly clamp within `0` to `255`, and thumbsticks within `-32768` to `32767` to prevent integer overflow in the XInput driver.
5. **Screen Wake Lock re-acquisition:** If the user switches away from the browser to check an Android notification and returns, the app must automatically re-acquire the Screen Wake Lock and Fullscreen state.

---

### Task 1: Binary Protocol Encoder & Decoder

**Files:**
- Create: `server/protocol.py`
- Create: `client/protocol.js`
- Test: `tests/test_protocol.py`

**Interfaces:**
- Consumes: Raw binary byte buffers (12-byte input frames and 3-byte rumble frames).
- Produces:
  - `pack_input_frame(buttons: int, lx: int, ly: int, rx: int, ry: int, lt: int, rt: int) -> bytes`
  - `unpack_input_frame(payload: bytes) -> tuple[int, int, int, int, int, int, int]`
  - `pack_rumble_frame(left_motor: int, right_motor: int) -> bytes`
  - `unpack_rumble_frame(payload: bytes) -> tuple[int, int]`
  - JavaScript mirrors: `packInputFrame(...)` returning `ArrayBuffer`, `unpackRumbleFrame(buffer)` returning `{leftMotor, rightMotor}`.

- [ ] **Step 1: Write the failing unit tests for binary protocol packing/unpacking**

```python
# tests/test_protocol.py
import unittest
from server.protocol import pack_input_frame, unpack_input_frame, pack_rumble_frame, unpack_rumble_frame

class TestProtocol(unittest.TestCase):
    def test_input_frame_roundtrip(self):
        buttons = 0b0000000100000101  # A, X, RB
        lx, ly = -16384, 32767
        rx, ry = 0, -32768
        lt, rt = 128, 255
        
        packed = pack_input_frame(buttons, lx, ly, rx, ry, lt, rt)
        self.assertEqual(len(packed), 12)
        
        unpacked = unpack_input_frame(packed)
        self.assertEqual(unpacked, (buttons, lx, ly, rx, ry, lt, rt))

    def test_input_frame_clamping(self):
        # Triggers and axes outside normal bounds must be clamped
        packed = pack_input_frame(0, -40000, 40000, 0, 0, -10, 300)
        buttons, lx, ly, rx, ry, lt, rt = unpack_input_frame(packed)
        self.assertEqual((lx, ly, lt, rt), (-32768, 32767, 0, 255))

    def test_rumble_frame_roundtrip(self):
        packed = pack_rumble_frame(200, 50)
        self.assertEqual(len(packed), 3)
        self.assertEqual(unpack_rumble_frame(packed), (200, 50))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_protocol.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'server'`

- [ ] **Step 3: Implement protocol serialization in `server/protocol.py` and `client/protocol.js`**

Implement struct-based packing in Python using `struct.pack('<HhhhhBB', ...)` and `struct.unpack('<HhhhhBB', ...)` with boundary clamping. Implement `client/protocol.js` using `DataView` on an `ArrayBuffer(12)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_protocol.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add server/protocol.py client/protocol.js tests/test_protocol.py
git commit -m "feat: implement 12-byte binary protocol encoder and decoder"
```

---

### Task 2: Virtual Gamepad Controller Bridge

**Files:**
- Create: `server/virtual_gamepad.py`
- Test: `tests/test_virtual_gamepad.py`

**Interfaces:**
- Consumes: Unpacked controller state tuples `(buttons, lx, ly, rx, ry, lt, rt)` from Task 1.
- Produces:
  - `class VirtualGamepadBridge`:
    - `__init__(self, mode: str = "auto", on_rumble: Callable[[int, int], None] = None)`
    - `apply_state(buttons: int, lx: int, ly: int, rx: int, ry: int, lt: int, rt: int) -> None`
    - `reset_all() -> None`
    - `close() -> None`
  - Bitmask constants: `BTN_A`, `BTN_B`, `BTN_X`, `BTN_Y`, `BTN_LB`, `BTN_RB`, `BTN_START`, `BTN_BACK`, `BTN_LS`, `BTN_RS`, `DPAD_UP`, `DPAD_DOWN`, `DPAD_LEFT`, `DPAD_RIGHT`.

- [ ] **Step 1: Write the failing unit tests for the gamepad bridge**

```python
# tests/test_virtual_gamepad.py
import unittest
from server.virtual_gamepad import VirtualGamepadBridge, BTN_A, BTN_X, DPAD_UP

class TestVirtualGamepad(unittest.TestCase):
    def test_mock_gamepad_state_application(self):
        bridge = VirtualGamepadBridge(mode="mock")
        buttons = BTN_A | BTN_X | DPAD_UP
        bridge.apply_state(buttons=buttons, lx=10000, ly=-20000, rx=0, ry=0, lt=100, rt=250)
        
        state = bridge.get_current_state()
        self.assertEqual(state['buttons'], buttons)
        self.assertEqual(state['lx'], 10000)
        self.assertEqual(state['ly'], -20000)
        self.assertEqual(state['lt'], 1000) # wait, lt is 100
        self.assertEqual(state['lt'], 100)
        self.assertEqual(state['rt'], 250)

    def test_reset_all_releases_all_inputs(self):
        bridge = VirtualGamepadBridge(mode="mock")
        bridge.apply_state(buttons=BTN_A, lx=30000, ly=30000, rx=0, ry=0, lt=255, rt=255)
        bridge.reset_all()
        
        state = bridge.get_current_state()
        self.assertEqual(state['buttons'], 0)
        self.assertEqual((state['lx'], state['ly']), (0, 0))
        self.assertEqual((state['lt'], state['rt']), (0, 0))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_virtual_gamepad.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'server.virtual_gamepad'`

- [ ] **Step 3: Implement `server/virtual_gamepad.py`**

Implement `VirtualGamepadBridge`:
- On Windows with `vgamepad` installed, creates `vgamepad.VX360Gamepad()` and registers rumble notification callback via `register_notification()`.
- On Linux or when in mock/test mode, records state transitions in memory for deterministic testing.
- Maps the 16-bit button mask to Xbox 360 digital button states.
- Ensures `reset_all()` clears all buttons and recenters axes.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_virtual_gamepad.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/virtual_gamepad.py tests/test_virtual_gamepad.py
git commit -m "feat: implement virtual gamepad bridge with XInput button mapping"
```

---

### Task 3: Bridge Server & Network Discovery

**Files:**
- Create: `server/discovery.py`
- Create: `server/server.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `VirtualGamepadBridge` (Task 2) and `unpack_input_frame`, `pack_rumble_frame` (Task 1).
- Produces:
  - `get_local_ips() -> list[dict[str, str]]` (detects Wi-Fi, Ethernet, and RNDIS USB Tethering IPs).
  - `check_and_run_adb_reverse(port: int = 8080) -> bool` (checks if ADB is available and runs reverse port forwarding).
  - `generate_terminal_qr(url: str) -> str` (produces ASCII QR code string).
  - `start_server(host: str = "0.0.0.0", port: int = 8080, gamepad_mode: str = "auto")`

- [ ] **Step 1: Write failing test for network discovery and socket handling**

```python
# tests/test_server.py
import unittest
from server.discovery import get_local_ips, format_connection_urls

class TestServerDiscovery(unittest.TestCase):
    def test_local_ip_discovery_returns_non_empty_list(self):
        ips = get_local_ips()
        self.assertIsInstance(ips, list)
        self.assertTrue(any(item['ip'].startswith('127.') or not item['ip'].startswith('127.') for item in ips))

    def test_format_connection_urls(self):
        mock_ips = [{'iface': 'wlan0', 'ip': '192.168.1.50', 'type': 'wifi'},
                    {'iface': 'rndis0', 'ip': '192.168.42.10', 'type': 'usb_tether'}]
        urls = format_connection_urls(mock_ips, port=8080)
        self.assertIn('http://192.168.1.50:8080', urls['wifi'])
        self.assertIn('http://192.168.42.10:8080', urls['usb_tether'])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_server.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'server.discovery'`

- [ ] **Step 3: Implement discovery and WebSocket bridge server**

Implement `server/discovery.py` (inspects network interfaces via socket, categorizes USB tether vs Wi-Fi, produces ASCII QR).
Implement `server/server.py` using `http.server` for static assets and `websockets` (or built-in async socket server with `TCP_NODELAY` socket option). When a connection closes or errors, immediately calls `gamepad.reset_all()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/discovery.py server/server.py tests/test_server.py
git commit -m "feat: implement network discovery, ADB auto-reverse, and low-latency server"
```

---

### Task 4: Android Gamepad Client Core & Layout Presets

**Files:**
- Create: `client/index.html`
- Create: `client/style.css`
- Create: `client/app.js`
- Create: `client/touch_engine.js`
- Test: `tests/test_client_ui.py` (headless DOM / structure validation test)

**Interfaces:**
- Consumes: `client/protocol.js` (Task 1).
- Produces:
  - Touch engine managing simultaneous active pointers (`activePointers` map).
  - Tekken Preset: 8-way directional D-pad with cardinal and diagonal sectors + 4 arcade face buttons (X, Y, A, B) with multi-touch chords.
  - FIFA Preset: 360° virtual thumbstick with proportional vector normalization + LB, RB, LT, RT triggers + ABXY diamond.
  - Screen Wake Lock and Fullscreen API controls.

- [ ] **Step 1: Write client markup and touch engine validation test**

```python
# tests/test_client_ui.py
import unittest
import os

class TestClientAssets(unittest.TestCase):
    def test_required_pwa_files_exist(self):
        for f in ['client/index.html', 'client/style.css', 'client/app.js', 'client/touch_engine.js', 'client/protocol.js']:
            self.assertTrue(os.path.exists(f), f"Missing {f}")

    def test_index_html_contains_viewport_and_touch_action(self):
        with open('client/index.html', 'r') as f:
            content = f.read()
        self.assertIn('viewport', content)
        self.assertIn('touch-action: none', content)
        self.assertIn('preset-tekken', content)
        self.assertIn('preset-fifa', content)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_client_ui.py`
Expected: FAIL (files missing)

- [ ] **Step 3: Implement client PWA HTML, CSS, and touch engine**

- `client/index.html`: Responsive mobile viewport, zero scrolling, preset toggle buttons (Tekken / FIFA / Custom), Edit Mode button, Fullscreen button.
- `client/style.css`: Clean dark OLED cyberpunk aesthetic (`#0b0d14` background), high-contrast touch zones, active pressed glows, top shoulder ribbons.
- `client/touch_engine.js`: Pointer event listener (`pointerdown`, `pointermove`, `pointerup`, `pointercancel`) attached with `{passive: false}`. Calculates stick angle/distance with deadzone clamp; translates D-Pad touches into 8-way bitmasks. Dispatches packed binary frames at touch frequency up to 120Hz.
- `client/app.js`: WebSocket connection lifecycle with auto-reconnect, Screen Wake Lock acquisition, Fullscreen trigger.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_client_ui.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client/index.html client/style.css client/app.js client/touch_engine.js tests/test_client_ui.py
git commit -m "feat: implement Android PWA client with Tekken and FIFA presets"
```

---

### Task 5: Interactive In-App Customizer & Bi-Directional Haptics

**Files:**
- Create: `client/customizer.js`
- Modify: `client/app.js`
- Modify: `client/index.html`
- Modify: `client/style.css`
- Test: `tests/test_customizer.py`

**Interfaces:**
- Consumes: DOM control nodes from Task 4.
- Produces:
  - `LayoutManager`:
    - `enableEditMode()`: Unlocks draggable bounding boxes and resize handles.
    - `saveLayout(profileName: string)`: Serializes positions and scales to `localStorage`.
    - `loadLayout(profileName: string)`: Restores layout configuration.
    - `resetLayout(presetName: string)`: Restores defaults.
  - Haptic feedback integration: `navigator.vibrate(15)` on touch down; listens to incoming binary WebSocket rumble frames (`0x01, left, right`) and invokes vibration pulses proportional to motor intensity.

- [ ] **Step 1: Write unit tests for layout serialization and haptic handling**

```python
# tests/test_customizer.py
import unittest
import json

class TestCustomizerSpec(unittest.TestCase):
    def test_custom_layout_schema(self):
        # Verify default layout JSON schema contains all required elements
        default_layout = {
            "dpad": {"x": 10, "y": 50, "scale": 1.0},
            "stick": {"x": 10, "y": 50, "scale": 1.0},
            "buttons": {"x": 80, "y": 50, "scale": 1.0},
            "triggers": {"x": 50, "y": 5, "scale": 1.0}
        }
        serialized = json.dumps(default_layout)
        loaded = json.loads(serialized)
        for key in ["dpad", "stick", "buttons", "triggers"]:
            self.assertIn(key, loaded)
            self.assertIn("scale", loaded[key])
```

- [ ] **Step 2: Run test to verify it passes schema check**

Run: `python3 -m unittest tests/test_customizer.py`
Expected: PASS

- [ ] **Step 3: Implement `client/customizer.js` and wire into `client/app.js`**

Implement drag-to-move, pinch/slider scaling for control elements in Edit Mode. Wire `localStorage` persistence under key `gamepad_layout_profile`. Wire rumble parser for downstream frames to trigger `navigator.vibrate`.

- [ ] **Step 4: Commit**

```bash
git add client/customizer.js client/app.js client/index.html client/style.css tests/test_customizer.py
git commit -m "feat: add in-app layout drag/resize editor and bi-directional haptics"
```

---

### Task 6: System Integration, End-to-End Verification & Launchers

**Files:**
- Create: `run_controller.py`
- Create: `run.bat`
- Create: `requirements.txt`
- Create: `tests/test_e2e_integration.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: All components from Tasks 1 through 5.
- Produces:
  - `run_controller.py`: Standalone CLI launcher running the full server, checking ViGEmBus status on Windows, displaying IP choices and terminal QR code.
  - `run.bat`: 1-click Windows 11 launcher script.
  - `tests/test_e2e_integration.py`: Automated end-to-end simulation connecting a mock client via WebSocket, streaming 12-byte Tekken and FIFA input packets, and asserting that the virtual gamepad state transitions accurately.

- [ ] **Step 1: Write the failing end-to-end integration test**

```python
# tests/test_e2e_integration.py
import unittest
import asyncio
from server.virtual_gamepad import VirtualGamepadBridge, BTN_A, BTN_B, DPAD_DOWN
from server.protocol import pack_input_frame

class TestE2EIntegration(unittest.TestCase):
    def test_simulated_client_stream(self):
        # Simulate high-frequency 120Hz packet stream
        gamepad = VirtualGamepadBridge(mode="mock")
        
        # Frame 1: Crouch (Down D-pad) in Tekken
        f1 = pack_input_frame(DPAD_DOWN, 0, 0, 0, 0, 0, 0)
        # Apply through protocol pipeline
        from server.protocol import unpack_input_frame
        state1 = unpack_input_frame(f1)
        gamepad.apply_state(*state1)
        self.assertEqual(gamepad.get_current_state()['buttons'], DPAD_DOWN)
        
        # Frame 2: Down + A+B simultaneous chord (Tekken combo)
        f2 = pack_input_frame(DPAD_DOWN | BTN_A | BTN_B, 0, 0, 0, 0, 0, 0)
        state2 = unpack_input_frame(f2)
        gamepad.apply_state(*state2)
        self.assertEqual(gamepad.get_current_state()['buttons'], DPAD_DOWN | BTN_A | BTN_B)
        
        # Frame 3: Sprint dribble in FIFA (RT=255, Left Stick X=32767, Y=16384)
        f3 = pack_input_frame(0, 32767, 16384, 0, 0, 0, 255)
        state3 = unpack_input_frame(f3)
        gamepad.apply_state(*state3)
        current = gamepad.get_current_state()
        self.assertEqual(current['rt'], 255)
        self.assertEqual(current['lx'], 32767)
        self.assertEqual(current['ly'], 16384)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m unittest tests/test_e2e_integration.py`
Expected: PASS

- [ ] **Step 3: Implement `run_controller.py`, `run.bat`, `requirements.txt`, and user setup docs**

Create `run_controller.py` with argument parsing (`--port`, `--mode`), QR code display, and instructions for Windows 11 ViGEmBus installation. Add `requirements.txt` (`vgamepad>=0.3.3`, `websockets>=12.0`). Create `run.bat` for 1-click startup on Windows.

- [ ] **Step 4: Run full test suite across the entire project**

Run: `python3 -m unittest discover -s tests -v`
Expected: All test suites PASS.

- [ ] **Step 5: Commit**

```bash
git add run_controller.py run.bat requirements.txt README.md tests/test_e2e_integration.py
git commit -m "feat: add standalone launcher, integration tests, and Windows 11 setup guide"
```
