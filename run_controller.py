#!/usr/bin/env python3
"""
Ultra-Low Latency Phone Game Controller - Standalone Server
Translates Android touch inputs into native Xbox 360 controller inputs on Windows 11.
"""

import sys
import argparse
from server.server import GamepadServer
from server.virtual_gamepad import _VGAMEPAD_AVAILABLE

def main():
    parser = argparse.ArgumentParser(description="Ultra-Low Latency Phone Game Controller Bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--mode", default="auto", choices=["auto", "vgamepad", "mock"],
                        help="Gamepad driver mode (default: auto)")
    args = parser.parse_args()

    print("=" * 60)
    print("🎮 ULTRA-LOW LATENCY PHONE GAME CONTROLLER")
    print("   Tailored for Windows 11 (Tekken, FIFA, Steam, PC Games)")
    print("=" * 60)

    if not _VGAMEPAD_AVAILABLE and sys.platform.startswith('win'):
        print("\n[!] NOTE: 'vgamepad' driver library not detected.")
        print("    For genuine Xbox 360 controller emulation in Windows 11 games:")
        print("    1. Download & run ViGEmBus installer: https://github.com/nefarius/ViGEmBus/releases")
        print("    2. Install python package: pip install vgamepad\n")

    server = GamepadServer(host=args.host, port=args.port, gamepad_mode=args.mode)
    server.start()

if __name__ == "__main__":
    main()
