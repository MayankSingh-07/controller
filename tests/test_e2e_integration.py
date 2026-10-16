# tests/test_e2e_integration.py
import unittest
import socket
import threading
import time

from server.virtual_gamepad import (
    VirtualGamepadBridge,
    BTN_A,
    BTN_B,
    BTN_X,
    BTN_Y,
    DPAD_DOWN,
    DPAD_UP
)
from server.protocol import pack_input_frame, unpack_input_frame
from server.server import GamepadServer

class TestE2EIntegration(unittest.TestCase):
    def test_simulated_client_stream(self):
        # Simulate high-frequency 120Hz packet stream
        gamepad = VirtualGamepadBridge(mode="mock")
        
        # Frame 1: Crouch (Down D-pad) in Tekken
        f1 = pack_input_frame(DPAD_DOWN, 0, 0, 0, 0, 0, 0)
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

        # Frame 4: Sudden finger release (Stick snaps back to 0,0 immediately)
        f4 = pack_input_frame(0, 0, 0, 0, 0, 0, 0)
        state4 = unpack_input_frame(f4)
        gamepad.apply_state(*state4)
        current4 = gamepad.get_current_state()
        self.assertEqual(current4['lx'], 0)
        self.assertEqual(current4['ly'], 0)
        self.assertEqual(current4['buttons'], 0)

    def test_full_server_client_socket_handshake_and_frames(self):
        # Start server on an ephemeral loopback port
        server = GamepadServer(host="127.0.0.1", port=0, gamepad_mode="mock")
        port = server.http_server.server_address[1]
        
        server_thread = threading.Thread(target=server.http_server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.05)

        try:
            # Connect a TCP socket as a client
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", port))
            
            # Perform WebSocket upgrade handshake
            handshake = (
                "GET /ws HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            )
            sock.sendall(handshake.encode('utf-8'))
            response = sock.recv(1024)
            self.assertIn(b"101 Switching Protocols", response)

            # Send a masked binary frame: Button A + RT=255
            payload = pack_input_frame(BTN_A, 0, 0, 0, 0, 0, 255)
            # Frame: FIN(1) + Bin(2) = 0x82; Mask(1) + Len(12) = 0x8c; Mask Key = 0x00000000; Payload
            mask_key = b"\x00\x00\x00\x00"
            ws_packet = bytes([0x82, 0x8c]) + mask_key + payload
            sock.sendall(ws_packet)
            time.sleep(0.05)

            current = server.gamepad.get_current_state()
            self.assertEqual(current['buttons'], BTN_A)
            self.assertEqual(current['rt'], 255)

            # Disconnect: ensure server resets virtual gamepad
            sock.close()
            time.sleep(0.05)
            reset_state = server.gamepad.get_current_state()
            self.assertEqual(reset_state['buttons'], 0)
            self.assertEqual(reset_state['rt'], 0)

        finally:
            server.stop()
