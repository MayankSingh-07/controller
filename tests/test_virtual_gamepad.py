# tests/test_virtual_gamepad.py
import unittest
from server.virtual_gamepad import VirtualGamepadBridge, BTN_A, BTN_B, BTN_X, BTN_Y, DPAD_UP, DPAD_DOWN, BTN_LB, BTN_RB

class TestVirtualGamepad(unittest.TestCase):
    def test_mock_gamepad_state_application(self):
        bridge = VirtualGamepadBridge(mode="mock")
        buttons = BTN_A | BTN_X | DPAD_UP
        bridge.apply_state(buttons=buttons, lx=10000, ly=-20000, rx=0, ry=0, lt=100, rt=250)
        
        state = bridge.get_current_state()
        self.assertEqual(state['buttons'], buttons)
        self.assertEqual(state['lx'], 10000)
        self.assertEqual(state['ly'], -20000)
        self.assertEqual(state['rx'], 0)
        self.assertEqual(state['ry'], 0)
        self.assertEqual(state['lt'], 100)
        self.assertEqual(state['rt'], 250)

    def test_reset_all_releases_all_inputs(self):
        bridge = VirtualGamepadBridge(mode="mock")
        bridge.apply_state(buttons=BTN_A | BTN_B | BTN_LB, lx=30000, ly=30000, rx=-15000, ry=15000, lt=255, rt=255)
        bridge.reset_all()
        
        state = bridge.get_current_state()
        self.assertEqual(state['buttons'], 0)
        self.assertEqual((state['lx'], state['ly']), (0, 0))
        self.assertEqual((state['rx'], state['ry']), (0, 0))
        self.assertEqual((state['lt'], state['rt']), (0, 0))

    def test_rumble_callback_invocation(self):
        rumble_events = []
        def on_rumble(left, right):
            rumble_events.append((left, right))
            
        bridge = VirtualGamepadBridge(mode="mock", on_rumble=on_rumble)
        bridge._simulate_rumble(255, 128)
        self.assertEqual(rumble_events, [(255, 128)])
