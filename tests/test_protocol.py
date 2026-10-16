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
