import os
import sys
import socket
import hashlib
import base64
import struct
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Optional

from server.protocol import unpack_input_frame, pack_rumble_frame, INPUT_FRAME_SIZE
from server.virtual_gamepad import VirtualGamepadBridge
from server.discovery import get_local_ips, format_connection_urls, generate_terminal_qr, check_and_run_adb_reverse

WS_MAGIC_STRING = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client"))


class ControllerHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CLIENT_DIR, **kwargs)

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def do_GET(self):
        # Check for WebSocket Upgrade
        if self.path.startswith('/ws') and self.headers.get('Upgrade', '').lower() == 'websocket':
            self.handle_websocket()
            return
        # Standard HTTP file serving
        return super().do_GET()

    def handle_websocket(self):
        key = self.headers.get('Sec-WebSocket-Key', '')
        if not key:
            self.send_error(400, "Missing Sec-WebSocket-Key")
            return

        accept_val = base64.b64encode(hashlib.sha1(key.encode('utf-8') + WS_MAGIC_STRING).digest()).decode('utf-8')

        # Send 101 Switching Protocols response
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_val}\r\n"
            "\r\n"
        )
        self.wfile.write(response.encode('utf-8'))
        self.wfile.flush()

        sock = self.connection
        # Ultra-low latency: Disable Nagle's algorithm
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        server_instance: GamepadServer = self.server.gamepad_server
        server_instance.register_client(sock)

        try:
            while not server_instance.stop_event.is_set():
                header = self._recv_exact(sock, 2)
                if not header:
                    break

                b1, b2 = header[0], header[1]
                opcode = b1 & 0x0F
                is_masked = bool(b2 & 0x80)
                length = b2 & 0x7F

                if opcode == 0x08:  # Close frame
                    break

                if length == 126:
                    len_bytes = self._recv_exact(sock, 2)
                    if not len_bytes:
                        break
                    length = struct.unpack('>H', len_bytes)[0]
                elif length == 127:
                    len_bytes = self._recv_exact(sock, 8)
                    if not len_bytes:
                        break
                    length = struct.unpack('>Q', len_bytes)[0]

                mask = self._recv_exact(sock, 4) if is_masked else b''
                if is_masked and not mask:
                    break

                payload = self._recv_exact(sock, length)
                if payload is None:
                    break
                if is_masked and mask:
                    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

                # Opcode 0x02 is Binary Frame
                if opcode == 0x02 and len(payload) == INPUT_FRAME_SIZE:
                    try:
                        state = unpack_input_frame(payload)
                        server_instance.gamepad.apply_state(*state)
                    except Exception as e:
                        pass
        except (ConnectionResetError, BrokenPipeError, socket.error):
            pass
        finally:
            server_instance.unregister_client(sock)


class GamepadServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, gamepad_mode: str = "auto"):
        self.host = host
        self.port = port
        self.stop_event = threading.Event()
        self.clients = set()
        self.clients_lock = threading.Lock()

        # Initialize virtual gamepad bridge with rumble callback
        self.gamepad = VirtualGamepadBridge(mode=gamepad_mode, on_rumble=self.broadcast_rumble)

        self.http_server = ThreadingHTTPServer((self.host, self.port), ControllerHTTPHandler)
        self.http_server.gamepad_server = self

    def register_client(self, sock: socket.socket):
        with self.clients_lock:
            self.clients.add(sock)
        print(f"\n[+] Controller connected from {sock.getpeername()[0]}")

    def unregister_client(self, sock: socket.socket):
        with self.clients_lock:
            self.clients.discard(sock)
        self.gamepad.reset_all()
        print("\n[-] Controller disconnected. Gamepad inputs reset.")

    def broadcast_rumble(self, left_motor: int, right_motor: int):
        """Sends 3-byte binary rumble frame to all connected controller clients."""
        frame = pack_rumble_frame(left_motor, right_motor)
        # Server-to-client WS binary frame: opcode 0x02, unmasked
        ws_frame = bytes([0x82, len(frame)]) + frame

        with self.clients_lock:
            for sock in list(self.clients):
                try:
                    sock.sendall(ws_frame)
                except Exception:
                    self.clients.discard(sock)

    def start(self):
        ips = get_local_ips()
        urls = format_connection_urls(ips, self.port)

        adb_status = check_and_run_adb_reverse(self.port)
        if adb_status:
            print("⚡ ADB reverse port-forwarding active! Phone can connect directly to http://localhost:" + str(self.port))

        print("\n" + generate_terminal_qr(urls.get('wifi') or urls.get('usb_tether') or f"http://localhost:{self.port}"))
        print("\nAvailable Connection URLs:")
        for conn_type, url in urls.items():
            print(f"  • {conn_type.upper():<12}: {url}")
        print("\nServer running... Press Ctrl+C to stop.")

        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.stop_event.set()
        with self.clients_lock:
            for sock in list(self.clients):
                try:
                    sock.close()
                except Exception:
                    pass
            self.clients.clear()
        self.gamepad.close()
        self.http_server.server_close()


def start_server(host: str = "0.0.0.0", port: int = 8080, gamepad_mode: str = "auto"):
    server = GamepadServer(host=host, port=port, gamepad_mode=gamepad_mode)
    server.start()
