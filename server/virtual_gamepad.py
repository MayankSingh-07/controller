import sys
from typing import Callable, Optional

# Bitmask constants for all digital buttons
BTN_A       = 1 << 0
BTN_B       = 1 << 1
BTN_X       = 1 << 2
BTN_Y       = 1 << 3
DPAD_UP     = 1 << 4
DPAD_DOWN   = 1 << 5
DPAD_LEFT   = 1 << 6
DPAD_RIGHT  = 1 << 7
BTN_LB      = 1 << 8
BTN_RB      = 1 << 9
BTN_START   = 1 << 10
BTN_BACK    = 1 << 11
BTN_LS      = 1 << 12
BTN_RS      = 1 << 13
BTN_GUIDE   = 1 << 14

BUTTON_LIST = [
    BTN_A, BTN_B, BTN_X, BTN_Y,
    DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT,
    BTN_LB, BTN_RB, BTN_START, BTN_BACK,
    BTN_LS, BTN_RS, BTN_GUIDE
]

# Try importing vgamepad if on Windows or supported platform
_VGAMEPAD_AVAILABLE = False
try:
    import vgamepad as vg
    _VGAMEPAD_AVAILABLE = True
except (ImportError, Exception):
    vg = None


class VirtualGamepadBridge:
    def __init__(self, mode: str = "auto", on_rumble: Optional[Callable[[int, int], None]] = None):
        """
        mode: "auto", "vgamepad", or "mock"
        on_rumble: callback taking (left_motor_speed, right_motor_speed) from 0..255
        """
        self.on_rumble = on_rumble
        self.current_state = {
            'buttons': 0,
            'lx': 0,
            'ly': 0,
            'rx': 0,
            'ry': 0,
            'lt': 0,
            'rt': 0
        }
        
        if mode == "auto":
            if _VGAMEPAD_AVAILABLE:
                self.mode = "vgamepad"
            else:
                self.mode = "mock"
        else:
            self.mode = mode

        self.device = None
        if self.mode == "vgamepad" and _VGAMEPAD_AVAILABLE:
            try:
                self.device = vg.VX360Gamepad()
                if self.on_rumble:
                    def _notification_cb(client, target, large_motor, small_motor, led_number, user_data):
                        # Convert 0..65535 or 0..255 to 0..255 uint8
                        left = int(large_motor) if large_motor <= 255 else int(large_motor * 255 / 65535)
                        right = int(small_motor) if small_motor <= 255 else int(small_motor * 255 / 65535)
                        self.on_rumble(left, right)
                    self.device.register_notification(callback_function=_notification_cb)
            except Exception as e:
                print(f"[VirtualGamepad] Failed to initialize VX360Gamepad: {e}. Falling back to mock mode.")
                self.mode = "mock"

        self._button_map = {}
        if self.mode == "vgamepad" and self.device:
            self._button_map = {
                BTN_A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                BTN_B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                BTN_X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                BTN_Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                BTN_LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                BTN_RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                BTN_START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                BTN_BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                BTN_LS: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                BTN_RS: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                BTN_GUIDE: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            }

    def apply_state(self, buttons: int, lx: int, ly: int, rx: int, ry: int, lt: int, rt: int) -> None:
        """Applies gamepad state snapshot and dispatches to virtual device."""
        self.current_state['buttons'] = buttons
        self.current_state['lx'] = lx
        self.current_state['ly'] = ly
        self.current_state['rx'] = rx
        self.current_state['ry'] = ry
        self.current_state['lt'] = lt
        self.current_state['rt'] = rt

        if self.mode == "vgamepad" and self.device:
            for mask, vg_btn in self._button_map.items():
                if buttons & mask:
                    self.device.press_button(button=vg_btn)
                else:
                    self.device.release_button(button=vg_btn)

            self.device.left_joystick(x_value=lx, y_value=ly)
            self.device.right_joystick(x_value=rx, y_value=ry)
            self.device.left_trigger(value=lt)
            self.device.right_trigger(value=rt)
            self.device.update()

    def reset_all(self) -> None:
        """Instantly releases all buttons and centers joysticks."""
        self.apply_state(buttons=0, lx=0, ly=0, rx=0, ry=0, lt=0, rt=0)
        if self.mode == "vgamepad" and self.device:
            self.device.reset()
            self.device.update()

    def get_current_state(self) -> dict:
        """Returns in-memory snapshot of gamepad state."""
        return dict(self.current_state)

    def _simulate_rumble(self, left: int, right: int) -> None:
        """Internal helper for testing rumble callbacks."""
        if self.on_rumble:
            self.on_rumble(left, right)

    def close(self) -> None:
        """Cleans up virtual device."""
        self.reset_all()
        if self.device:
            del self.device
            self.device = None
